"""
Virtual Position Database Integration
Реализация методов работы с базой данных для виртуальных позиций
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import json

logger = logging.getLogger(__name__)

class VirtualPositionDB:
    """Класс для работы с базой данных виртуальных позиций"""
    
    def __init__(self, supabase_client=None):
        self.supabase = supabase_client
    
    def set_supabase(self, supabase_client):
        """Установить Supabase клиент"""
        self.supabase = supabase_client
    
    async def save_position(
        self, 
        position_id: str, 
        signal_id: str, 
        v_trade_id: str,
        position_data: Dict[str, Any]
    ) -> bool:
        """Сохранить виртуальную позицию в базу данных"""
        try:
            if not self.supabase:
                logger.warning("⚠️ Supabase client not available")
                return False
            
            # Подготавливаем данные для сохранения
            db_data = {
                'id': position_id,
                'signal_id': signal_id,
                'v_trade_id': v_trade_id,
                'symbol': position_data['symbol'],
                'side': position_data['side'],
                'strategy_id': position_data.get('strategy_id', 'S_A_TP1_BE_TP2'),
                
                # Параметры позиции
                'position_size_usd': float(position_data['position_size_usd']),
                'leverage': int(position_data['leverage']),
                'margin_usd': float(position_data['margin_usd']),
                
                # Цены из сигнала
                'signal_entry_min': float(position_data['signal_entry_min']) if position_data.get('signal_entry_min') else None,
                'signal_entry_max': float(position_data['signal_entry_max']) if position_data.get('signal_entry_max') else None,
                'signal_tp1': float(position_data['signal_tp1']) if position_data.get('signal_tp1') else None,
                'signal_tp2': float(position_data['signal_tp2']) if position_data.get('signal_tp2') else None,
                'signal_tp3': float(position_data['signal_tp3']) if position_data.get('signal_tp3') else None,
                'signal_sl': float(position_data['signal_sl']) if position_data.get('signal_sl') else None,
                
                # Текущие параметры
                'avg_entry_price': float(position_data['avg_entry_price']) if position_data.get('avg_entry_price') else None,
                'current_price': float(position_data['current_price']) if position_data.get('current_price') else None,
                'current_pnl_usd': float(position_data.get('current_pnl_usd', 0)),
                'current_pnl_percent': float(position_data.get('current_pnl_percent', 0)),
                
                # Статус
                'status': position_data.get('status', 'PENDING'),
                'filled_percent': float(position_data.get('filled_percent', 0)),
                'tp1_filled_percent': float(position_data.get('tp1_filled_percent', 0)),
                'tp2_filled_percent': float(position_data.get('tp2_filled_percent', 0)),
                'tp3_filled_percent': float(position_data.get('tp3_filled_percent', 0)),
                'remaining_percent': float(position_data.get('remaining_percent', 100)),
                
                # Временные метки
                'signal_time': position_data['signal_time'].isoformat() if position_data.get('signal_time') else None,
                'entry_timeout': position_data['entry_timeout'].isoformat() if position_data.get('entry_timeout') else None,
                'first_entry_time': position_data['first_entry_time'].isoformat() if position_data.get('first_entry_time') else None,
                'last_update_time': position_data['last_update_time'].isoformat() if position_data.get('last_update_time') else None,
                'close_time': position_data['close_time'].isoformat() if position_data.get('close_time') else None,
                
                # Метаданные
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Сохраняем в таблицу virtual_positions
            result = self.supabase.table('virtual_positions').insert(db_data).execute()
            
            if result.data:
                logger.info(f"✅ Virtual position saved to DB: {position_data['symbol']} {position_data['side']} (ID: {position_id})")
                return True
            else:
                logger.error(f"❌ Failed to save virtual position to DB")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error saving virtual position to DB: {e}")
            return False
    
    async def save_entry(
        self,
        position_id: str,
        entry_price: float,
        entry_size_usd: float,
        entry_percent: float,
        entry_type: str = 'MARKET',
        entry_reason: str = None
    ) -> bool:
        """Сохранить вход в позицию"""
        try:
            if not self.supabase:
                logger.warning("⚠️ Supabase client not available")
                return False
            
            entry_data = {
                'position_id': position_id,
                'entry_price': float(entry_price),
                'entry_size_usd': float(entry_size_usd),
                'entry_percent': float(entry_percent),
                'entry_type': entry_type,
                'entry_reason': entry_reason or f"{entry_type} entry at ${entry_price}",
                'entry_time': datetime.now(timezone.utc).isoformat(),
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Сохраняем в таблицу position_entries
            result = self.supabase.table('position_entries').insert(entry_data).execute()
            
            if result.data:
                logger.info(f"✅ Position entry saved to DB: {entry_percent:.1f}% at ${entry_price}")
                return True
            else:
                logger.error(f"❌ Failed to save position entry to DB")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error saving position entry to DB: {e}")
            return False
    
    async def save_exit(
        self,
        position_id: str,
        exit_price: float,
        exit_size_usd: float,
        exit_percent: float,
        pnl_usd: float,
        pnl_percent: float,
        exit_type: str,
        exit_reason: str = None
    ) -> bool:
        """Сохранить выход из позиции"""
        try:
            if not self.supabase:
                logger.warning("⚠️ Supabase client not available")
                return False
            
            exit_data = {
                'position_id': position_id,
                'exit_price': float(exit_price),
                'exit_size_usd': float(exit_size_usd),
                'exit_percent': float(exit_percent),
                'pnl_usd': float(pnl_usd),
                'pnl_percent': float(pnl_percent),
                'exit_type': exit_type,
                'exit_reason': exit_reason or f"{exit_type} exit at ${exit_price}",
                'exit_time': datetime.now(timezone.utc).isoformat(),
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Сохраняем в таблицу position_exits
            result = self.supabase.table('position_exits').insert(exit_data).execute()
            
            if result.data:
                logger.info(f"✅ Position exit saved to DB: {exit_percent:.1f}% at ${exit_price} (PnL: {pnl_percent:.2f}%)")
                return True
            else:
                logger.error(f"❌ Failed to save position exit to DB")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error saving position exit to DB: {e}")
            return False
    
    async def log_event(
        self,
        position_id: str,
        event_type: str,
        description: str,
        price_at_event: Optional[float] = None,
        pnl_at_event: Optional[float] = None,
        event_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Логировать событие позиции"""
        try:
            if not self.supabase:
                logger.warning("⚠️ Supabase client not available")
                return False
            
            event_db_data = {
                'position_id': position_id,
                'event_type': event_type,
                'event_description': description,
                'price_at_event': float(price_at_event) if price_at_event else None,
                'pnl_at_event': float(pnl_at_event) if pnl_at_event else None,
                'event_data': json.dumps(event_data) if event_data else None,
                'event_time': datetime.now(timezone.utc).isoformat(),
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Сохраняем в таблицу position_events
            result = self.supabase.table('position_events').insert(event_db_data).execute()
            
            if result.data:
                logger.debug(f"✅ Position event logged: {event_type} - {description}")
                return True
            else:
                logger.error(f"❌ Failed to log position event to DB")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error logging position event to DB: {e}")
            return False
    
    async def update_position_status(
        self,
        position_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Обновить статус позиции"""
        try:
            if not self.supabase:
                logger.warning("⚠️ Supabase client not available")
                return False
            
            # Подготавливаем данные для обновления
            update_data = {}
            
            # Обновляем разрешенные поля
            allowed_fields = [
                'avg_entry_price', 'current_price', 'current_pnl_usd', 'current_pnl_percent',
                'status', 'filled_percent', 'tp1_filled_percent', 'tp2_filled_percent', 
                'tp3_filled_percent', 'remaining_percent', 'first_entry_time', 
                'last_update_time', 'close_time'
            ]
            
            for field in allowed_fields:
                if field in updates:
                    value = updates[field]
                    
                    # Конвертируем datetime в ISO формат
                    if field.endswith('_time') and value:
                        if isinstance(value, datetime):
                            value = value.isoformat()
                    
                    # Конвертируем числа в float
                    elif field in ['avg_entry_price', 'current_price', 'current_pnl_usd', 'current_pnl_percent']:
                        if value is not None:
                            value = float(value)
                    
                    # Конвертируем проценты в float
                    elif field.endswith('_percent'):
                        if value is not None:
                            value = float(value)
                    
                    update_data[field] = value
            
            # Автоматически обновляем updated_at
            update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            # Выполняем обновление
            result = self.supabase.table('virtual_positions').update(update_data).eq('id', position_id).execute()
            
            if result.data:
                logger.debug(f"✅ Position status updated: {position_id}")
                return True
            else:
                logger.error(f"❌ Failed to update position status")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating position status: {e}")
            return False
    
    async def save_candle(
        self,
        position_id: str,
        symbol: str,
        timeframe: str,
        candle_data: Dict[str, Any]
    ) -> bool:
        """Сохранить данные свечи для позиции"""
        try:
            if not self.supabase:
                logger.warning("⚠️ Supabase client not available")
                return False
            
            candle_db_data = {
                'position_id': position_id,
                'symbol': symbol,
                'timeframe': timeframe,
                'open_time': candle_data['open_time'].isoformat() if isinstance(candle_data['open_time'], datetime) else candle_data['open_time'],
                'close_time': candle_data['close_time'].isoformat() if isinstance(candle_data['close_time'], datetime) else candle_data['close_time'],
                'open_price': float(candle_data['open_price']),
                'high_price': float(candle_data['high_price']),
                'low_price': float(candle_data['low_price']),
                'close_price': float(candle_data['close_price']),
                'volume': float(candle_data.get('volume', 0)),
                'sma_20': float(candle_data['sma_20']) if candle_data.get('sma_20') else None,
                'ema_12': float(candle_data['ema_12']) if candle_data.get('ema_12') else None,
                'rsi_14': float(candle_data['rsi_14']) if candle_data.get('rsi_14') else None,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Сохраняем в таблицу position_candles
            result = self.supabase.table('position_candles').insert(candle_db_data).execute()
            
            if result.data:
                logger.debug(f"✅ Candle data saved for {symbol} {timeframe}")
                return True
            else:
                logger.error(f"❌ Failed to save candle data")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error saving candle data: {e}")
            return False
    
    async def get_active_positions(self) -> list:
        """Получить активные позиции из базы данных"""
        try:
            if not self.supabase:
                logger.warning("⚠️ Supabase client not available")
                return []
            
            # Получаем активные позиции
            result = self.supabase.table('virtual_positions').select('*').in_('status', [
                'PENDING', 'PARTIAL_FILL', 'FILLED', 'TP1_HIT', 'TP2_HIT', 'TP3_HIT'
            ]).execute()
            
            if result.data:
                logger.info(f"📊 Retrieved {len(result.data)} active positions from DB")
                return result.data
            else:
                logger.info("📊 No active positions found in DB")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error getting active positions: {e}")
            return []

# Глобальный экземпляр для использования
virtual_position_db = VirtualPositionDB()
