"""
Virtual Position Manager - управление виртуальными позициями
"""
import asyncio
import logging
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from enum import Enum
import json

from core.market_price_service import market_price_service, MarketPrice
from core.virtual_position_db import virtual_position_db
from signals.parsers.signal_parser_base import ParsedSignal, SignalDirection

logger = logging.getLogger(__name__)

class PositionStatus(Enum):
    """Статусы позиции"""
    PENDING = "PENDING"           # Ожидает входа
    PARTIAL_FILL = "PARTIAL_FILL" # Частично заполнена
    FILLED = "FILLED"             # Полностью заполнена
    TP1_HIT = "TP1_HIT"          # Достигнут TP1
    TP2_HIT = "TP2_HIT"          # Достигнут TP2
    TP3_HIT = "TP3_HIT"          # Достигнут TP3
    SL_HIT = "SL_HIT"            # Достигнут Stop Loss
    CLOSED = "CLOSED"             # Закрыта вручную
    EXPIRED = "EXPIRED"           # Истекла по времени

class EventType(Enum):
    """Типы событий позиции"""
    POSITION_CREATED = "POSITION_CREATED"
    ENTRY_FILLED = "ENTRY_FILLED"
    PRICE_UPDATE = "PRICE_UPDATE"
    TP1_REACHED = "TP1_REACHED"
    TP2_REACHED = "TP2_REACHED"
    TP3_REACHED = "TP3_REACHED"
    SL_REACHED = "SL_REACHED"
    PARTIAL_CLOSE = "PARTIAL_CLOSE"
    POSITION_CLOSED = "POSITION_CLOSED"
    TIMEOUT = "TIMEOUT"
    ERROR = "ERROR"
    MANUAL_ACTION = "MANUAL_ACTION"

@dataclass
class VirtualPosition:
    """Виртуальная позиция"""
    id: str
    symbol: str
    side: str  # LONG/SHORT
    position_size_usd: float
    leverage: int
    margin_usd: float
    
    # Цены из сигнала
    signal_entry_min: Optional[float]
    signal_entry_max: Optional[float]
    signal_tp1: Optional[float]
    signal_tp2: Optional[float]
    signal_tp3: Optional[float]
    signal_sl: Optional[float]
    
    # Текущее состояние
    avg_entry_price: Optional[float] = None
    current_price: Optional[float] = None
    current_pnl_usd: float = 0.0
    current_pnl_percent: float = 0.0
    
    status: PositionStatus = PositionStatus.PENDING
    filled_percent: float = 0.0
    remaining_percent: float = 100.0
    
    # Временные метки
    signal_time: datetime = None
    entry_timeout: datetime = None
    first_entry_time: Optional[datetime] = None
    last_update_time: Optional[datetime] = None
    close_time: Optional[datetime] = None

class VirtualPositionManager:
    """Менеджер виртуальных позиций"""
    
    def __init__(self, supabase_client=None):
        self.supabase = supabase_client
        self.active_positions: Dict[str, VirtualPosition] = {}
        self.monitoring_task = None
        self.monitoring_interval = 5  # секунд
        self.entry_timeout_hours = 48  # часов для входа
        
        # Настраиваем DB клиент
        if supabase_client:
            virtual_position_db.set_supabase(supabase_client)
        
    def set_supabase(self, supabase_client):
        """Установить Supabase клиент"""
        self.supabase = supabase_client
        virtual_position_db.set_supabase(supabase_client)
    
    async def create_position_from_signal(
        self, 
        signal: ParsedSignal, 
        v_trade_id: str,
        position_size_usd: float = 100.0,
        leverage: int = 10
    ) -> Optional[str]:
        """
        Создать виртуальную позицию из сигнала
        
        Args:
            signal: Парсированный сигнал
            v_trade_id: ID записи в v_trades
            position_size_usd: Размер позиции в USD
            leverage: Плечо
        
        Returns:
            position_id или None при ошибке
        """
        try:
            # Генерируем ID позиции
            position_id = str(uuid.uuid4())
            
            # Рассчитываем маржу
            margin_usd = position_size_usd / leverage
            
            # Определяем цены из сигнала
            signal_entry_min = None
            signal_entry_max = None
            
            if hasattr(signal, 'entry_zone') and signal.entry_zone:
                signal_entry_min = min(signal.entry_zone)
                signal_entry_max = max(signal.entry_zone)
            elif hasattr(signal, 'entry_single') and signal.entry_single:
                signal_entry_min = signal.entry_single
                signal_entry_max = signal.entry_single
            
            # Извлекаем цели и стоп-лосс
            signal_tp1 = signal.targets[0] if signal.targets and len(signal.targets) > 0 else None
            signal_tp2 = signal.targets[1] if signal.targets and len(signal.targets) > 1 else None
            signal_tp3 = signal.targets[2] if signal.targets and len(signal.targets) > 2 else None
            signal_sl = signal.stop_loss if signal.stop_loss else None
            
            # Создаем позицию
            position = VirtualPosition(
                id=position_id,
                symbol=signal.symbol,
                side='LONG' if signal.direction in [SignalDirection.LONG, SignalDirection.BUY] else 'SHORT',
                position_size_usd=position_size_usd,
                leverage=leverage,
                margin_usd=margin_usd,
                signal_entry_min=signal_entry_min,
                signal_entry_max=signal_entry_max,
                signal_tp1=signal_tp1,
                signal_tp2=signal_tp2,
                signal_tp3=signal_tp3,
                signal_sl=signal_sl,
                signal_time=datetime.now(timezone.utc),
                entry_timeout=datetime.now(timezone.utc) + timedelta(hours=self.entry_timeout_hours)
            )
            
            # Сохраняем в базу данных
            if await self._save_position_to_db(position, signal.signal_id, v_trade_id):
                # Добавляем в активные позиции
                self.active_positions[position_id] = position
                
                # Логируем событие создания
                await self._log_position_event(
                    position_id,
                    EventType.POSITION_CREATED,
                    f"Position created from signal {signal.symbol} {signal.direction.value}",
                    event_data={
                        'signal_id': signal.signal_id,
                        'v_trade_id': v_trade_id,
                        'position_size_usd': position_size_usd,
                        'leverage': leverage
                    }
                )
                
                # Сразу пытаемся войти по рыночной цене
                await self._attempt_market_entry(position_id)
                
                logger.info(f"✅ Virtual position created: {position.symbol} {position.side} ${position_size_usd} (ID: {position_id})")
                return position_id
            else:
                logger.error(f"❌ Failed to save position to database")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating virtual position: {e}")
            return None
    
    async def _attempt_market_entry(self, position_id: str) -> bool:
        """Попытка входа по рыночной цене"""
        try:
            position = self.active_positions.get(position_id)
            if not position:
                return False
            
            # Получаем текущую рыночную цену
            price_data = await market_price_service.get_market_price(position.symbol)
            if not price_data:
                logger.error(f"❌ Failed to get market price for {position.symbol}")
                return False
            
            current_price = price_data.price
            
            # Проверяем, подходит ли текущая цена для входа
            can_enter = self._can_enter_at_price(position, current_price)
            
            if can_enter:
                # Входим по рыночной цене
                await self._execute_market_entry(position_id, current_price, 100.0)  # 100% позиции
                return True
            else:
                logger.info(f"💡 Market price ${current_price} not in entry zone for {position.symbol} {position.side}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error attempting market entry for {position_id}: {e}")
            return False
    
    def _can_enter_at_price(self, position: VirtualPosition, price: float) -> bool:
        """Проверить, можно ли войти по данной цене"""
        # Если нет зоны входа, входим по любой цене
        if not position.signal_entry_min or not position.signal_entry_max:
            return True
        
        # Проверяем, попадает ли цена в зону входа (с небольшим допуском)
        tolerance = 0.005  # 0.5% допуск
        
        if position.side == 'LONG':
            # Для LONG хотим купить дешевле или в зоне
            max_entry = position.signal_entry_max * (1 + tolerance)
            return price <= max_entry
        else:
            # Для SHORT хотим продать дороже или в зоне
            min_entry = position.signal_entry_min * (1 - tolerance)
            return price >= min_entry
    
    async def _execute_market_entry(
        self, 
        position_id: str, 
        entry_price: float, 
        entry_percent: float = 100.0
    ) -> bool:
        """Выполнить вход по рыночной цене"""
        try:
            position = self.active_positions.get(position_id)
            if not position:
                return False
            
            # Рассчитываем размер входа
            entry_size_usd = position.position_size_usd * (entry_percent / 100.0)
            
            # Обновляем позицию
            if position.avg_entry_price is None:
                position.avg_entry_price = entry_price
            else:
                # Рассчитываем среднюю цену входа
                total_filled = position.filled_percent / 100.0
                new_avg_price = (
                    (position.avg_entry_price * total_filled * position.position_size_usd + 
                     entry_price * entry_size_usd) /
                    ((total_filled * position.position_size_usd) + entry_size_usd)
                )
                position.avg_entry_price = new_avg_price
            
            position.filled_percent = min(100.0, position.filled_percent + entry_percent)
            position.remaining_percent = 100.0 - position.filled_percent
            position.current_price = entry_price
            
            # Обновляем статус
            if position.filled_percent >= 100.0:
                position.status = PositionStatus.FILLED
                position.first_entry_time = datetime.now(timezone.utc)
            else:
                position.status = PositionStatus.PARTIAL_FILL
                if position.first_entry_time is None:
                    position.first_entry_time = datetime.now(timezone.utc)
            
            position.last_update_time = datetime.now(timezone.utc)
            
            # Сохраняем вход в базу данных
            if await self._save_entry_to_db(position_id, entry_price, entry_size_usd, entry_percent):
                # Логируем событие входа
                await self._log_position_event(
                    position_id,
                    EventType.ENTRY_FILLED,
                    f"Market entry: ${entry_price} ({entry_percent:.1f}%)",
                    price_at_event=entry_price,
                    event_data={
                        'entry_price': entry_price,
                        'entry_size_usd': entry_size_usd,
                        'entry_percent': entry_percent,
                        'filled_percent': position.filled_percent
                    }
                )
                
                logger.info(f"🎯 Market entry executed: {position.symbol} {position.side} at ${entry_price} ({entry_percent:.1f}%)")
                return True
            else:
                logger.error(f"❌ Failed to save entry to database")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error executing market entry: {e}")
            return False
    
    async def update_position_prices(self) -> None:
        """Обновить цены для всех активных позиций"""
        if not self.active_positions:
            return
        
        try:
            # Получаем уникальные символы
            symbols = list(set(pos.symbol for pos in self.active_positions.values()))
            
            # Получаем цены для всех символов
            prices = await market_price_service.get_multiple_prices(symbols)
            
            # Обновляем позиции
            for position_id, position in self.active_positions.items():
                if position.symbol in prices:
                    new_price = prices[position.symbol].price
                    await self._update_position_price(position_id, new_price)
                    
        except Exception as e:
            logger.error(f"❌ Error updating position prices: {e}")
    
    async def _update_position_price(self, position_id: str, new_price: float) -> None:
        """Обновить цену конкретной позиции"""
        try:
            position = self.active_positions.get(position_id)
            if not position or not position.avg_entry_price:
                return
            
            old_price = position.current_price
            position.current_price = new_price
            position.last_update_time = datetime.now(timezone.utc)
            
            # Рассчитываем PnL
            if position.side == 'LONG':
                price_change = (new_price - position.avg_entry_price) / position.avg_entry_price
            else:
                price_change = (position.avg_entry_price - new_price) / position.avg_entry_price
            
            position.current_pnl_percent = price_change * 100 * position.leverage
            position.current_pnl_usd = position.position_size_usd * (price_change * position.leverage)
            
            # Проверяем достижение целей или стоп-лосса
            await self._check_tp_sl_levels(position_id)
            
            # Логируем значительные изменения цены (> 1%)
            if old_price and abs((new_price - old_price) / old_price) > 0.01:
                await self._log_position_event(
                    position_id,
                    EventType.PRICE_UPDATE,
                    f"Price update: ${old_price:.6f} → ${new_price:.6f} (PnL: {position.current_pnl_percent:.2f}%)",
                    price_at_event=new_price,
                    pnl_at_event=position.current_pnl_usd
                )
                
        except Exception as e:
            logger.error(f"❌ Error updating position price: {e}")
    
    async def _check_tp_sl_levels(self, position_id: str) -> None:
        """Проверить достижение уровней TP/SL"""
        try:
            position = self.active_positions.get(position_id)
            if not position or not position.current_price:
                return
            
            current_price = position.current_price
            
            # Проверяем Stop Loss
            if position.signal_sl and self._is_sl_hit(position, current_price):
                await self._execute_sl(position_id)
                return
            
            # Проверяем Take Profit уровни
            if position.signal_tp1 and self._is_tp_hit(position, current_price, position.signal_tp1):
                if position.status not in [PositionStatus.TP1_HIT, PositionStatus.TP2_HIT, PositionStatus.TP3_HIT]:
                    await self._execute_tp(position_id, 1, position.signal_tp1)
            
            if position.signal_tp2 and self._is_tp_hit(position, current_price, position.signal_tp2):
                if position.status not in [PositionStatus.TP2_HIT, PositionStatus.TP3_HIT]:
                    await self._execute_tp(position_id, 2, position.signal_tp2)
            
            if position.signal_tp3 and self._is_tp_hit(position, current_price, position.signal_tp3):
                if position.status != PositionStatus.TP3_HIT:
                    await self._execute_tp(position_id, 3, position.signal_tp3)
                    
        except Exception as e:
            logger.error(f"❌ Error checking TP/SL levels: {e}")
    
    def _is_tp_hit(self, position: VirtualPosition, current_price: float, tp_price: float) -> bool:
        """Проверить, достигнут ли Take Profit"""
        if position.side == 'LONG':
            return current_price >= tp_price
        else:
            return current_price <= tp_price
    
    def _is_sl_hit(self, position: VirtualPosition, current_price: float) -> bool:
        """Проверить, достигнут ли Stop Loss"""
        if not position.signal_sl:
            return False
        
        if position.side == 'LONG':
            return current_price <= position.signal_sl
        else:
            return current_price >= position.signal_sl
    
    async def _execute_tp(self, position_id: str, tp_level: int, tp_price: float) -> None:
        """Выполнить Take Profit"""
        try:
            position = self.active_positions.get(position_id)
            if not position:
                return
            
            # Определяем процент закрытия (стандартная стратегия)
            close_percent = {1: 50.0, 2: 30.0, 3: 20.0}.get(tp_level, 0.0)  # 50% на TP1, 30% на TP2, 20% на TP3
            
            if close_percent > position.remaining_percent:
                close_percent = position.remaining_percent
            
            # Выполняем частичное закрытие
            await self._execute_partial_close(position_id, tp_price, close_percent, f"TP{tp_level}")
            
            # Обновляем статус
            if tp_level == 1:
                position.status = PositionStatus.TP1_HIT
            elif tp_level == 2:
                position.status = PositionStatus.TP2_HIT
            elif tp_level == 3:
                position.status = PositionStatus.TP3_HIT
            
            # Логируем событие
            event_type = {1: EventType.TP1_REACHED, 2: EventType.TP2_REACHED, 3: EventType.TP3_REACHED}.get(tp_level)
            await self._log_position_event(
                position_id,
                event_type,
                f"TP{tp_level} reached at ${tp_price:.6f}, closed {close_percent:.1f}%",
                price_at_event=tp_price,
                pnl_at_event=position.current_pnl_usd
            )
            
            logger.info(f"🎯 TP{tp_level} hit: {position.symbol} at ${tp_price:.6f}, closed {close_percent:.1f}%")
            
        except Exception as e:
            logger.error(f"❌ Error executing TP{tp_level}: {e}")
    
    async def _execute_sl(self, position_id: str) -> None:
        """Выполнить Stop Loss"""
        try:
            position = self.active_positions.get(position_id)
            if not position or not position.signal_sl:
                return
            
            # Закрываем всю оставшуюся позицию
            await self._execute_partial_close(position_id, position.signal_sl, position.remaining_percent, "SL")
            
            # Обновляем статус
            position.status = PositionStatus.SL_HIT
            position.close_time = datetime.now(timezone.utc)
            
            # Логируем событие
            await self._log_position_event(
                position_id,
                EventType.SL_REACHED,
                f"Stop Loss reached at ${position.signal_sl:.6f}, position closed",
                price_at_event=position.signal_sl,
                pnl_at_event=position.current_pnl_usd
            )
            
            # Удаляем из активных позиций
            if position_id in self.active_positions:
                del self.active_positions[position_id]
            
            logger.info(f"🛑 Stop Loss hit: {position.symbol} at ${position.signal_sl:.6f}")
            
        except Exception as e:
            logger.error(f"❌ Error executing Stop Loss: {e}")
    
    async def _execute_partial_close(
        self, 
        position_id: str, 
        exit_price: float, 
        close_percent: float, 
        exit_type: str
    ) -> None:
        """Выполнить частичное закрытие позиции"""
        try:
            position = self.active_positions.get(position_id)
            if not position:
                return
            
            # Рассчитываем размер закрытия
            close_size_usd = position.position_size_usd * (close_percent / 100.0)
            
            # Рассчитываем PnL
            if position.side == 'LONG':
                price_change = (exit_price - position.avg_entry_price) / position.avg_entry_price
            else:
                price_change = (position.avg_entry_price - exit_price) / position.avg_entry_price
            
            pnl_percent = price_change * 100 * position.leverage
            pnl_usd = close_size_usd * (price_change * position.leverage)
            
            # Обновляем позицию
            position.remaining_percent = max(0.0, position.remaining_percent - close_percent)
            
            # Сохраняем выход в базу данных
            await self._save_exit_to_db(position_id, exit_price, close_size_usd, close_percent, pnl_usd, pnl_percent, exit_type)
            
            # Проверяем, полностью ли закрыта позиция
            if position.remaining_percent <= 0.1:  # Допуск 0.1%
                position.status = PositionStatus.CLOSED
                position.close_time = datetime.now(timezone.utc)
                
                # Удаляем из активных позиций
                if position_id in self.active_positions:
                    del self.active_positions[position_id]
                
                await self._log_position_event(
                    position_id,
                    EventType.POSITION_CLOSED,
                    f"Position fully closed",
                    price_at_event=exit_price,
                    pnl_at_event=position.current_pnl_usd
                )
            
            logger.info(f"📈 Partial close: {position.symbol} {close_percent:.1f}% at ${exit_price:.6f} (PnL: {pnl_percent:.2f}%)")
            
        except Exception as e:
            logger.error(f"❌ Error executing partial close: {e}")
    
    async def start_monitoring(self) -> None:
        """Запустить мониторинг позиций"""
        if self.monitoring_task is not None:
            return
        
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("🔄 Virtual position monitoring started")
    
    async def stop_monitoring(self) -> None:
        """Остановить мониторинг позиций"""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
            logger.info("⏹️ Virtual position monitoring stopped")
    
    async def _monitoring_loop(self) -> None:
        """Основной цикл мониторинга"""
        while True:
            try:
                await self.update_position_prices()
                await asyncio.sleep(self.monitoring_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    # Методы для работы с базой данных
    async def _save_position_to_db(self, position: VirtualPosition, signal_id: str, v_trade_id: str) -> bool:
        """Сохранить позицию в базу данных"""
        try:
            position_data = {
                'symbol': position.symbol,
                'side': position.side,
                'position_size_usd': position.position_size_usd,
                'leverage': position.leverage,
                'margin_usd': position.margin_usd,
                'signal_entry_min': position.signal_entry_min,
                'signal_entry_max': position.signal_entry_max,
                'signal_tp1': position.signal_tp1,
                'signal_tp2': position.signal_tp2,
                'signal_tp3': position.signal_tp3,
                'signal_sl': position.signal_sl,
                'avg_entry_price': position.avg_entry_price,
                'current_price': position.current_price,
                'current_pnl_usd': position.current_pnl_usd,
                'current_pnl_percent': position.current_pnl_percent,
                'status': position.status.value,
                'filled_percent': position.filled_percent,
                'remaining_percent': position.remaining_percent,
                'signal_time': position.signal_time,
                'entry_timeout': position.entry_timeout,
                'first_entry_time': position.first_entry_time,
                'last_update_time': position.last_update_time,
                'close_time': position.close_time
            }
            
            return await virtual_position_db.save_position(position.id, signal_id, v_trade_id, position_data)
            
        except Exception as e:
            logger.error(f"❌ Error saving position to DB: {e}")
            return False
    
    async def _save_entry_to_db(self, position_id: str, entry_price: float, entry_size_usd: float, entry_percent: float) -> bool:
        """Сохранить вход в базу данных"""
        return await virtual_position_db.save_entry(
            position_id=position_id,
            entry_price=entry_price,
            entry_size_usd=entry_size_usd,
            entry_percent=entry_percent,
            entry_type='MARKET',
            entry_reason=f'Market entry at ${entry_price:.6f}'
        )
    
    async def _save_exit_to_db(self, position_id: str, exit_price: float, exit_size_usd: float, exit_percent: float, pnl_usd: float, pnl_percent: float, exit_type: str) -> bool:
        """Сохранить выход в базу данных"""
        return await virtual_position_db.save_exit(
            position_id=position_id,
            exit_price=exit_price,
            exit_size_usd=exit_size_usd,
            exit_percent=exit_percent,
            pnl_usd=pnl_usd,
            pnl_percent=pnl_percent,
            exit_type=exit_type,
            exit_reason=f'{exit_type} exit at ${exit_price:.6f}'
        )
    
    async def _log_position_event(
        self, 
        position_id: str, 
        event_type: EventType, 
        description: str, 
        price_at_event: Optional[float] = None,
        pnl_at_event: Optional[float] = None,
        event_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Логировать событие позиции"""
        logger.info(f"📝 Position Event: {position_id} | {event_type.value} | {description}")
        
        return await virtual_position_db.log_event(
            position_id=position_id,
            event_type=event_type.value,
            description=description,
            price_at_event=price_at_event,
            pnl_at_event=pnl_at_event,
            event_data=event_data
        )

# Глобальный экземпляр менеджера
virtual_position_manager = VirtualPositionManager()

async def main():
    """Тестирование менеджера позиций"""
    logging.basicConfig(level=logging.INFO)
    
    # Тест создания позиции (заглушка)
    logger.info("🧪 Testing Virtual Position Manager...")
    
    # Здесь можно добавить тесты
    
if __name__ == "__main__":
    asyncio.run(main())
