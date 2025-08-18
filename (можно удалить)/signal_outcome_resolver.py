"""
GHOST SIGNAL OUTCOME RESOLVER
Симуляция исходов торговых сигналов на основе исторических данных
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

import asyncpg
import numpy as np

logger = logging.getLogger(__name__)

class OutcomeResult(Enum):
    TP1_ONLY = "TP1_ONLY"      # Достигнут только TP1
    TP2_FULL = "TP2_FULL"      # Достигнуты TP1 и TP2
    TP3_FULL = "TP3_FULL"      # Достигнуты TP1, TP2, TP3
    SL_HIT = "SL"              # Сработал стоп-лосс
    BE_EXIT = "BE"             # Выход в безубыток
    TIMEOUT = "TIMEOUT"        # Таймаут сигнала
    NO_FILL = "NOFILL"         # Цена не дошла до входа

@dataclass
class SignalOutcome:
    """Результат симуляции сигнала"""
    signal_id: int
    trader_id: str
    entry_exec_price_sim: Optional[float] = None
    tp1_hit_at: Optional[datetime] = None
    tp2_hit_at: Optional[datetime] = None
    tp3_hit_at: Optional[datetime] = None
    sl_hit_at: Optional[datetime] = None
    max_favorable: float = 0.0
    max_adverse: float = 0.0
    duration_to_tp1_min: Optional[int] = None
    duration_to_tp2_min: Optional[int] = None
    final_result: OutcomeResult = OutcomeResult.NO_FILL
    pnl_sim: float = 0.0
    roi_sim: float = 0.0
    fee_sim: float = 0.0
    calc_mode: str = "candles"
    simulation_version: str = "v1.0"

class SignalOutcomeResolver:
    """Основной класс для симуляции исходов сигналов"""
    
    def __init__(self, db_connection_string: str):
        self.db_connection_string = db_connection_string
        self._connection_pool: Optional[asyncpg.Pool] = None
        
        # Настройки симуляции
        self.simulation_config = {
            'timeout_hours': 48,        # Максимальное время ожидания сигнала
            'fee_rate': 0.00055,        # Комиссия биржи (0.055%)
            'slippage_rate': 0.0005,    # Проскальзывание (0.05%)
            'position_split': {         # Разделение позиции по стратегии
                'tp1': 0.5,            # 50% на TP1
                'tp2': 0.5,            # 50% на TP2+
            },
            'be_after_tp1': True,       # Перенос SL в BE после TP1
            'min_candle_data': 10,      # Минимум свечей для анализа
        }
    
    async def init_connection(self):
        """Инициализация пула соединений"""
        try:
            self._connection_pool = await asyncpg.create_pool(
                self.db_connection_string,
                min_size=2,
                max_size=10
            )
            logger.info("SignalOutcomeResolver: Database connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            raise
    
    async def close_connection(self):
        """Закрытие пула соединений"""
        if self._connection_pool:
            await self._connection_pool.close()
            self._connection_pool = None
    
    async def resolve_signal_outcome(self, signal_id: int) -> Optional[SignalOutcome]:
        """Главная функция резолвинга исхода сигнала"""
        if not self._connection_pool:
            await self.init_connection()
        
        try:
            # Получаем данные сигнала
            signal_data = await self._get_signal_data(signal_id)
            if not signal_data:
                logger.error(f"Signal {signal_id} not found")
                return None
            
            # Получаем исторические данные цен
            candles = await self._get_historical_candles(
                signal_data['symbol'],
                signal_data['posted_at'],
                self.simulation_config['timeout_hours']
            )
            
            if len(candles) < self.simulation_config['min_candle_data']:
                logger.warning(f"Insufficient candle data for signal {signal_id}")
                return SignalOutcome(
                    signal_id=signal_id,
                    trader_id=signal_data['trader_id'],
                    final_result=OutcomeResult.NO_FILL
                )
            
            # Симулируем исход
            outcome = await self._simulate_signal_outcome(signal_data, candles)
            
            # Сохраняем результат
            await self._save_outcome(outcome)
            
            return outcome
            
        except Exception as e:
            logger.error(f"Error resolving signal outcome {signal_id}: {e}")
            return None
    
    async def resolve_pending_signals(self, limit: int = 100) -> int:
        """Обработка ожидающих сигналов"""
        if not self._connection_pool:
            await self.init_connection()
        
        try:
            # Получаем сигналы без исходов
            async with self._connection_pool.acquire() as conn:
                pending_signals = await conn.fetch("""
                    SELECT sp.signal_id 
                    FROM signals_parsed sp
                    LEFT JOIN signal_outcomes so ON sp.signal_id = so.signal_id
                    WHERE so.signal_id IS NULL 
                    AND sp.is_valid = true
                    AND sp.posted_at < NOW() - INTERVAL '1 hour'
                    ORDER BY sp.posted_at ASC
                    LIMIT $1
                """, limit)
            
            resolved_count = 0
            
            for row in pending_signals:
                signal_id = row['signal_id']
                try:
                    outcome = await self.resolve_signal_outcome(signal_id)
                    if outcome:
                        resolved_count += 1
                        logger.debug(f"Resolved signal {signal_id}: {outcome.final_result.value}")
                except Exception as e:
                    logger.error(f"Error resolving signal {signal_id}: {e}")
                    continue
            
            logger.info(f"Resolved {resolved_count} pending signals")
            return resolved_count
            
        except Exception as e:
            logger.error(f"Error resolving pending signals: {e}")
            return 0
    
    async def _get_signal_data(self, signal_id: int) -> Optional[Dict[str, Any]]:
        """Получение данных сигнала"""
        async with self._connection_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT 
                    signal_id, trader_id, symbol, side, entry_type,
                    entry, range_low, range_high, tp1, tp2, tp3, sl,
                    leverage_hint, posted_at
                FROM signals_parsed 
                WHERE signal_id = $1
            """, signal_id)
            
            return dict(row) if row else None
    
    async def _get_historical_candles(self, symbol: str, start_time: datetime, hours: int) -> List[Dict[str, Any]]:
        """Получение исторических свечей"""
        end_time = start_time + timedelta(hours=hours)
        
        async with self._connection_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT open_time, open_price, high_price, low_price, close_price, volume
                FROM candles 
                WHERE symbol = $1 
                AND timeframe = '1m'
                AND open_time >= $2 
                AND open_time <= $3
                ORDER BY open_time ASC
            """, symbol, start_time, end_time)
            
            return [dict(row) for row in rows]
    
    async def _simulate_signal_outcome(self, signal_data: Dict[str, Any], candles: List[Dict[str, Any]]) -> SignalOutcome:
        """Симуляция исхода сигнала"""
        outcome = SignalOutcome(
            signal_id=signal_data['signal_id'],
            trader_id=signal_data['trader_id']
        )
        
        # Определяем цену входа
        entry_price = self._determine_entry_price(signal_data, candles)
        if not entry_price:
            outcome.final_result = OutcomeResult.NO_FILL
            return outcome
        
        outcome.entry_exec_price_sim = entry_price
        
        # Симулируем движение цены после входа
        entry_candle_index = self._find_entry_candle_index(candles, entry_price, signal_data)
        if entry_candle_index == -1:
            outcome.final_result = OutcomeResult.NO_FILL
            return outcome
        
        # Анализируем движение цены
        result = self._analyze_price_movement(
            signal_data, 
            candles[entry_candle_index:], 
            entry_price,
            outcome
        )
        
        # Рассчитываем PnL
        self._calculate_pnl(signal_data, outcome)
        
        return outcome
    
    def _determine_entry_price(self, signal_data: Dict[str, Any], candles: List[Dict[str, Any]]) -> Optional[float]:
        """Определение цены входа на основе типа входа"""
        entry_type = signal_data['entry_type']
        
        if entry_type == 'market':
            # Для market ордера берем цену первой свечи
            if candles:
                return float(candles[0]['open_price'])
        
        elif entry_type == 'limit':
            # Для limit ордера проверяем, дошла ли цена до уровня
            target_price = float(signal_data['entry'])
            for candle in candles:
                low = float(candle['low_price'])
                high = float(candle['high_price'])
                if low <= target_price <= high:
                    return target_price
        
        elif entry_type == 'range':
            # Для range входа ищем попадание в диапазон
            range_low = float(signal_data['range_low'])
            range_high = float(signal_data['range_high'])
            
            for candle in candles:
                low = float(candle['low_price'])
                high = float(candle['high_price'])
                
                # Проверяем пересечение диапазонов
                if not (high < range_low or low > range_high):
                    # Возвращаем среднюю цену диапазона
                    return (range_low + range_high) / 2
        
        return None
    
    def _find_entry_candle_index(self, candles: List[Dict[str, Any]], entry_price: float, signal_data: Dict[str, Any]) -> int:
        """Поиск индекса свечи входа"""
        for i, candle in enumerate(candles):
            low = float(candle['low_price'])
            high = float(candle['high_price'])
            
            if low <= entry_price <= high:
                return i
        
        return -1
    
    def _analyze_price_movement(self, signal_data: Dict[str, Any], candles: List[Dict[str, Any]], 
                               entry_price: float, outcome: SignalOutcome) -> OutcomeResult:
        """Анализ движения цены после входа"""
        side = signal_data['side']
        tp1 = signal_data.get('tp1')
        tp2 = signal_data.get('tp2')
        tp3 = signal_data.get('tp3')
        sl = signal_data.get('sl')
        
        # Переменные для отслеживания
        max_favorable = 0.0
        max_adverse = 0.0
        tp1_hit = False
        tp2_hit = False
        tp3_hit = False
        sl_hit = False
        current_sl = sl  # Может измениться после TP1 (BE)
        
        for i, candle in enumerate(candles):
            high = float(candle['high_price'])
            low = float(candle['low_price'])
            candle_time = candle['open_time']
            
            if side == 'BUY':
                # Обновляем максимумы
                current_favorable = ((high - entry_price) / entry_price) * 100
                current_adverse = ((low - entry_price) / entry_price) * 100
                
                max_favorable = max(max_favorable, current_favorable)
                max_adverse = min(max_adverse, current_adverse)
                
                # Проверяем SL
                if current_sl and low <= float(current_sl):
                    outcome.sl_hit_at = candle_time
                    sl_hit = True
                    break
                
                # Проверяем TP1
                if tp1 and not tp1_hit and high >= float(tp1):
                    outcome.tp1_hit_at = candle_time
                    outcome.duration_to_tp1_min = i
                    tp1_hit = True
                    
                    # Переносим SL в BE после TP1
                    if self.simulation_config['be_after_tp1']:
                        current_sl = entry_price
                
                # Проверяем TP2
                if tp2 and tp1_hit and not tp2_hit and high >= float(tp2):
                    outcome.tp2_hit_at = candle_time
                    outcome.duration_to_tp2_min = i
                    tp2_hit = True
                
                # Проверяем TP3
                if tp3 and tp2_hit and not tp3_hit and high >= float(tp3):
                    outcome.tp3_hit_at = candle_time
                    tp3_hit = True
                    break
            
            else:  # SELL
                # Обновляем максимумы (для SELL логика обратная)
                current_favorable = ((entry_price - low) / entry_price) * 100
                current_adverse = ((high - entry_price) / entry_price) * 100
                
                max_favorable = max(max_favorable, current_favorable)
                max_adverse = min(max_adverse, current_adverse)
                
                # Проверяем SL
                if current_sl and high >= float(current_sl):
                    outcome.sl_hit_at = candle_time
                    sl_hit = True
                    break
                
                # Проверяем TP1
                if tp1 and not tp1_hit and low <= float(tp1):
                    outcome.tp1_hit_at = candle_time
                    outcome.duration_to_tp1_min = i
                    tp1_hit = True
                    
                    # Переносим SL в BE после TP1
                    if self.simulation_config['be_after_tp1']:
                        current_sl = entry_price
                
                # Проверяем TP2
                if tp2 and tp1_hit and not tp2_hit and low <= float(tp2):
                    outcome.tp2_hit_at = candle_time
                    outcome.duration_to_tp2_min = i
                    tp2_hit = True
                
                # Проверяем TP3
                if tp3 and tp2_hit and not tp3_hit and low <= float(tp3):
                    outcome.tp3_hit_at = candle_time
                    tp3_hit = True
                    break
        
        # Сохраняем экстремумы
        outcome.max_favorable = max_favorable
        outcome.max_adverse = max_adverse
        
        # Определяем финальный результат
        if sl_hit:
            if tp1_hit and current_sl == entry_price:
                outcome.final_result = OutcomeResult.BE_EXIT
            else:
                outcome.final_result = OutcomeResult.SL_HIT
        elif tp3_hit:
            outcome.final_result = OutcomeResult.TP3_FULL
        elif tp2_hit:
            outcome.final_result = OutcomeResult.TP2_FULL
        elif tp1_hit:
            outcome.final_result = OutcomeResult.TP1_ONLY
        else:
            outcome.final_result = OutcomeResult.TIMEOUT
        
        return outcome.final_result
    
    def _calculate_pnl(self, signal_data: Dict[str, Any], outcome: SignalOutcome):
        """Расчет PnL на основе стратегии Ghost"""
        if outcome.final_result == OutcomeResult.NO_FILL:
            return
        
        entry_price = outcome.entry_exec_price_sim
        side = signal_data['side']
        tp1 = signal_data.get('tp1')
        tp2 = signal_data.get('tp2')
        
        # Размер позиции (условная маржа $100)
        margin = 100.0
        leverage = signal_data.get('leverage_hint', 10)
        position_size = margin * leverage / entry_price
        
        total_pnl = 0.0
        total_fees = 0.0
        
        if outcome.final_result == OutcomeResult.TP1_ONLY:
            # Закрыли 50% на TP1, остальное в BE
            if tp1:
                tp1_pnl = self._calculate_leg_pnl(
                    entry_price, float(tp1), position_size * 0.5, side
                )
                total_pnl += tp1_pnl
                total_fees += margin * 0.5 * self.simulation_config['fee_rate']
                
                # Вторая половина в BE (0 PnL)
                total_fees += margin * 0.5 * self.simulation_config['fee_rate']
        
        elif outcome.final_result == OutcomeResult.TP2_FULL:
            # 50% на TP1, 50% на TP2
            if tp1 and tp2:
                tp1_pnl = self._calculate_leg_pnl(
                    entry_price, float(tp1), position_size * 0.5, side
                )
                tp2_pnl = self._calculate_leg_pnl(
                    entry_price, float(tp2), position_size * 0.5, side
                )
                total_pnl += tp1_pnl + tp2_pnl
                total_fees += margin * self.simulation_config['fee_rate']
        
        elif outcome.final_result == OutcomeResult.SL_HIT:
            # Весь объем по стопу
            sl_price = float(signal_data['sl'])
            sl_pnl = self._calculate_leg_pnl(
                entry_price, sl_price, position_size, side
            )
            total_pnl += sl_pnl
            total_fees += margin * self.simulation_config['fee_rate']
        
        elif outcome.final_result == OutcomeResult.BE_EXIT:
            # Только комиссии
            total_fees += margin * self.simulation_config['fee_rate']
        
        # Комиссия на вход
        total_fees += margin * self.simulation_config['fee_rate']
        
        # Итоговые значения
        outcome.pnl_sim = total_pnl - total_fees
        outcome.roi_sim = (outcome.pnl_sim / margin) * 100
        outcome.fee_sim = total_fees
    
    def _calculate_leg_pnl(self, entry_price: float, exit_price: float, 
                          position_size: float, side: str) -> float:
        """Расчет PnL для части позиции"""
        if side == 'BUY':
            return (exit_price - entry_price) * position_size
        else:  # SELL
            return (entry_price - exit_price) * position_size
    
    async def _save_outcome(self, outcome: SignalOutcome):
        """Сохранение результата в БД"""
        async with self._connection_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO signal_outcomes 
                (signal_id, trader_id, entry_exec_price_sim, tp1_hit_at, tp2_hit_at, tp3_hit_at,
                 sl_hit_at, max_favorable, max_adverse, duration_to_tp1_min, duration_to_tp2_min,
                 final_result, pnl_sim, roi_sim, fee_sim, calc_mode, simulation_version)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                ON CONFLICT (signal_id) DO UPDATE SET
                    entry_exec_price_sim = EXCLUDED.entry_exec_price_sim,
                    tp1_hit_at = EXCLUDED.tp1_hit_at,
                    tp2_hit_at = EXCLUDED.tp2_hit_at,
                    tp3_hit_at = EXCLUDED.tp3_hit_at,
                    sl_hit_at = EXCLUDED.sl_hit_at,
                    max_favorable = EXCLUDED.max_favorable,
                    max_adverse = EXCLUDED.max_adverse,
                    duration_to_tp1_min = EXCLUDED.duration_to_tp1_min,
                    duration_to_tp2_min = EXCLUDED.duration_to_tp2_min,
                    final_result = EXCLUDED.final_result,
                    pnl_sim = EXCLUDED.pnl_sim,
                    roi_sim = EXCLUDED.roi_sim,
                    fee_sim = EXCLUDED.fee_sim,
                    calculated_at = NOW()
            """,
                outcome.signal_id,
                outcome.trader_id,
                outcome.entry_exec_price_sim,
                outcome.tp1_hit_at,
                outcome.tp2_hit_at,
                outcome.tp3_hit_at,
                outcome.sl_hit_at,
                outcome.max_favorable,
                outcome.max_adverse,
                outcome.duration_to_tp1_min,
                outcome.duration_to_tp2_min,
                outcome.final_result.value,
                outcome.pnl_sim,
                outcome.roi_sim,
                outcome.fee_sim,
                outcome.calc_mode,
                outcome.simulation_version
            )

# Глобальный экземпляр резолвера
signal_outcome_resolver: Optional[SignalOutcomeResolver] = None

async def get_signal_outcome_resolver() -> SignalOutcomeResolver:
    """Получение глобального экземпляра резолвера"""
    global signal_outcome_resolver
    if signal_outcome_resolver is None:
        # Здесь должна быть ваша строка подключения к БД
        db_connection = "postgresql://username:password@localhost:5432/ghost_db"
        signal_outcome_resolver = SignalOutcomeResolver(db_connection)
        await signal_outcome_resolver.init_connection()
    return signal_outcome_resolver
