"""
Signal Candle Tracker
Автоматическое отслеживание новых сигналов и запуск сбора свечей
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
import json
import os

# Импорты для работы с БД
try:
    from supabase import create_client, Client
except ImportError:
    logging.warning("⚠️ Supabase client not available")
    create_client = None

from core.bybit_websocket import get_bybit_client, CandleData

logger = logging.getLogger(__name__)

@dataclass
class SignalInfo:
    """Информация о сигнале для отслеживания"""
    signal_id: str
    symbol: str
    side: str  # LONG/SHORT
    entry_min: float
    entry_max: float
    tp1: float
    tp2: float
    sl: float
    posted_ts: int  # unix timestamp
    status: str = 'sim_open'

class SignalCandleTracker:
    """Трекер для автоматического сбора свечей по сигналам"""
    
    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        # Supabase клиент
        self.supabase: Optional[Client] = None
        if create_client and supabase_url and supabase_key:
            self.supabase = create_client(supabase_url, supabase_key)
            logger.info("✅ Supabase client initialized")
        else:
            logger.warning("⚠️ Supabase client not available")
        
        # Bybit WebSocket клиент
        self.bybit_client = get_bybit_client()
        self.bybit_client.add_candle_callback(self._handle_candle_data)
        
        # Активные подписки и сигналы
        self.tracked_signals: Dict[str, SignalInfo] = {}  # signal_id -> SignalInfo
        self.symbol_subscriptions: Dict[str, Set[str]] = {}  # symbol -> set of signal_ids
        self.last_check_time = 0
        
        # Настройки
        self.max_tracking_days = 7  # максимум дней отслеживания
        self.check_interval = 30    # интервал проверки новых сигналов (секунды)
        
        # Статистика
        self.stats = {
            'signals_tracked': 0,
            'candles_saved': 0,
            'symbols_active': 0,
            'last_signal_check': None,
            'start_time': time.time()
        }
        
        logger.info("SignalCandleTracker initialized")
    
    async def start_tracking(self):
        """Запуск основного цикла отслеживания"""
        logger.info("🚀 Starting signal tracking...")
        
        try:
            while True:
                # Проверяем новые сигналы
                await self._check_new_signals()
                
                # Проверяем устаревшие подписки
                await self._cleanup_old_subscriptions()
                
                # Обновляем статистику
                self._update_stats()
                
                # Ждем следующую проверку
                await asyncio.sleep(self.check_interval)
                
        except Exception as e:
            logger.error(f"❌ Error in tracking loop: {e}")
            raise
    
    async def _check_new_signals(self):
        """Проверка новых сигналов в таблице v_trades"""
        if not self.supabase:
            return
        
        try:
            # Получаем сигналы, которые еще не отслеживаются
            current_time = int(time.time())
            cutoff_time = current_time - (self.max_tracking_days * 24 * 3600)
            
            # Запрос к v_trades на новые сигналы
            response = self.supabase.table('v_trades').select(
                'id, symbol, side, entry_min, entry_max, tp1, tp2, sl, posted_ts, status'
            ).gte('posted_ts', cutoff_time).eq('status', 'sim_open').execute()
            
            if response.data:
                for signal_data in response.data:
                    signal_id = signal_data['id']
                    
                    # Проверяем, не отслеживаем ли уже
                    if signal_id not in self.tracked_signals:
                        
                        # Проверяем, что символ валидный
                        symbol = signal_data['symbol']
                        if not symbol or len(symbol) < 3:
                            logger.warning(f"⚠️ Invalid symbol for signal {signal_id}: {symbol}")
                            continue
                        
                        # Создаем объект сигнала
                        signal = SignalInfo(
                            signal_id=signal_id,
                            symbol=symbol,
                            side=signal_data['side'],
                            entry_min=float(signal_data['entry_min'] or 0),
                            entry_max=float(signal_data['entry_max'] or 0), 
                            tp1=float(signal_data['tp1'] or 0),
                            tp2=float(signal_data['tp2'] or 0),
                            sl=float(signal_data['sl'] or 0),
                            posted_ts=signal_data['posted_ts'],
                            status=signal_data['status']
                        )
                        
                        # Запускаем отслеживание
                        await self._start_signal_tracking(signal)
            
            self.stats['last_signal_check'] = datetime.now()
            
        except Exception as e:
            logger.error(f"❌ Error checking new signals: {e}")
    
    async def _start_signal_tracking(self, signal: SignalInfo):
        """Запуск отслеживания конкретного сигнала"""
        try:
            logger.info(f"📊 Starting tracking for signal {signal.signal_id} ({signal.symbol})")
            
            # Добавляем в отслеживаемые
            self.tracked_signals[signal.signal_id] = signal
            
            # Регистрируем подписку в БД
            await self._create_subscription_record(signal)
            
            # Подписываемся на WebSocket если еще не подписаны
            if signal.symbol not in self.symbol_subscriptions:
                self.symbol_subscriptions[signal.symbol] = set()
                
                # Подписываемся на 1-секундные свечи
                success = await self.bybit_client.subscribe_to_klines(signal.symbol, "1")
                if success:
                    logger.info(f"✅ Subscribed to {signal.symbol} klines")
                else:
                    logger.error(f"❌ Failed to subscribe to {signal.symbol}")
                    return
            
            # Добавляем signal_id к подпискам символа
            self.symbol_subscriptions[signal.symbol].add(signal.signal_id)
            
            self.stats['signals_tracked'] += 1
            self.stats['symbols_active'] = len(self.symbol_subscriptions)
            
        except Exception as e:
            logger.error(f"❌ Error starting tracking for {signal.signal_id}: {e}")
    
    async def _create_subscription_record(self, signal: SignalInfo):
        """Создание записи подписки в БД"""
        if not self.supabase:
            return
        
        try:
            subscription_data = {
                'signal_id': signal.signal_id,
                'symbol': signal.symbol,
                'start_time': int(time.time()),
                'status': 'active',
                'candles_collected': 0
            }
            
            response = self.supabase.table('signal_websocket_subscriptions').insert(subscription_data).execute()
            
            if response.data:
                logger.debug(f"✅ Created subscription record for {signal.signal_id}")
            
        except Exception as e:
            logger.error(f"❌ Error creating subscription record: {e}")
    
    async def _handle_candle_data(self, candle: CandleData):
        """Обработка новых данных свечей"""
        try:
            # Найдем все сигналы, которые отслеживают этот символ
            if candle.symbol in self.symbol_subscriptions:
                signal_ids = self.symbol_subscriptions[candle.symbol]
                
                for signal_id in signal_ids:
                    await self._save_candle_for_signal(signal_id, candle)
            
        except Exception as e:
            logger.error(f"❌ Error handling candle data: {e}")
    
    async def _save_candle_for_signal(self, signal_id: str, candle: CandleData):
        """Сохранение свечи для конкретного сигнала"""
        if not self.supabase:
            return
        
        try:
            candle_data = {
                'signal_id': signal_id,
                'symbol': candle.symbol,
                'timestamp': candle.timestamp,
                'open': candle.open,
                'high': candle.high,
                'low': candle.low,
                'close': candle.close,
                'volume': candle.volume,
                'quote_volume': candle.quote_volume
            }
            
            # Используем upsert для избежания дублей
            response = self.supabase.table('signal_candles_1s').upsert(candle_data).execute()
            
            if response.data:
                self.stats['candles_saved'] += 1
                
                # Обновляем счетчик свечей в подписке
                await self._update_subscription_stats(signal_id)
                
            logger.debug(f"💾 Saved candle for {signal_id}: {candle.symbol} @ {candle.close}")
            
        except Exception as e:
            logger.error(f"❌ Error saving candle for {signal_id}: {e}")
    
    async def _update_subscription_stats(self, signal_id: str):
        """Обновление статистики подписки"""
        if not self.supabase:
            return
        
        try:
            current_time = int(time.time())
            
            # Сначала получаем текущее значение
            response = self.supabase.table('signal_websocket_subscriptions').select('candles_collected').eq('signal_id', signal_id).single().execute()
            
            current_count = 0
            if response.data:
                current_count = response.data.get('candles_collected', 0)
            
            # Обновляем с инкрементом
            update_response = self.supabase.table('signal_websocket_subscriptions').update({
                'candles_collected': current_count + 1,
                'last_candle_time': current_time,
                'updated_at': datetime.now().isoformat()
            }).eq('signal_id', signal_id).execute()
            
        except Exception as e:
            logger.debug(f"Error updating subscription stats: {e}")  # debug level, не критично
    
    async def _cleanup_old_subscriptions(self):
        """Очистка устаревших подписок"""
        try:
            current_time = time.time()
            cutoff_time = current_time - (self.max_tracking_days * 24 * 3600)
            
            # Список сигналов для удаления
            signals_to_remove = []
            
            for signal_id, signal in self.tracked_signals.items():
                # Проверяем возраст сигнала
                if signal.posted_ts < cutoff_time:
                    signals_to_remove.append(signal_id)
                    logger.info(f"🧹 Removing old signal {signal_id} (age: {current_time - signal.posted_ts}s)")
            
            # Удаляем устаревшие сигналы
            for signal_id in signals_to_remove:
                await self._stop_signal_tracking(signal_id)
            
        except Exception as e:
            logger.error(f"❌ Error in cleanup: {e}")
    
    async def _stop_signal_tracking(self, signal_id: str):
        """Остановка отслеживания сигнала"""
        try:
            if signal_id not in self.tracked_signals:
                return
            
            signal = self.tracked_signals[signal_id]
            symbol = signal.symbol
            
            # Удаляем из подписок символа
            if symbol in self.symbol_subscriptions:
                self.symbol_subscriptions[symbol].discard(signal_id)
                
                # Если больше нет сигналов для этого символа, отписываемся от WebSocket
                if not self.symbol_subscriptions[symbol]:
                    await self.bybit_client.unsubscribe_from_klines(symbol, "1")
                    del self.symbol_subscriptions[symbol]
                    logger.info(f"🛑 Unsubscribed from {symbol} klines")
            
            # Обновляем статус подписки в БД
            await self._complete_subscription(signal_id)
            
            # Удаляем из отслеживаемых
            del self.tracked_signals[signal_id]
            
            self.stats['symbols_active'] = len(self.symbol_subscriptions)
            
            logger.info(f"✅ Stopped tracking signal {signal_id}")
            
        except Exception as e:
            logger.error(f"❌ Error stopping signal tracking: {e}")
    
    async def _complete_subscription(self, signal_id: str):
        """Завершение подписки в БД"""
        if not self.supabase:
            return
        
        try:
            response = self.supabase.table('signal_websocket_subscriptions').update({
                'status': 'completed',
                'end_time': int(time.time()),
                'updated_at': datetime.now().isoformat()
            }).eq('signal_id', signal_id).execute()
            
        except Exception as e:
            logger.error(f"❌ Error completing subscription: {e}")
    
    def _update_stats(self):
        """Обновление внутренней статистики"""
        self.stats['signals_tracked'] = len(self.tracked_signals)
        self.stats['symbols_active'] = len(self.symbol_subscriptions)
    
    def get_statistics(self) -> dict:
        """Получение статистики трекера"""
        uptime = time.time() - self.stats['start_time']
        
        return {
            **self.stats,
            'tracked_signals': list(self.tracked_signals.keys()),
            'active_symbols': list(self.symbol_subscriptions.keys()),
            'uptime_seconds': round(uptime),
            'candles_per_hour': round(self.stats['candles_saved'] / max(uptime / 3600, 1))
        }
    
    async def stop(self):
        """Остановка трекера"""
        logger.info("🛑 Stopping Signal Candle Tracker...")
        
        # Останавливаем отслеживание всех сигналов
        for signal_id in list(self.tracked_signals.keys()):
            await self._stop_signal_tracking(signal_id)
        
        # Останавливаем Bybit клиент
        await self.bybit_client.stop_all()
        
        logger.info("✅ Signal Candle Tracker stopped")

# Глобальный экземпляр трекера
_signal_tracker = None

def get_signal_tracker() -> SignalCandleTracker:
    """Получить singleton экземпляр трекера"""
    global _signal_tracker
    if _signal_tracker is None:
        # Получаем переменные окружения
        supabase_url = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SECRET_KEY')
        
        _signal_tracker = SignalCandleTracker(supabase_url, supabase_key)
    return _signal_tracker

# Тестирование
async def test_signal_tracker():
    """Тестирование трекера"""
    print("🧪 Testing Signal Candle Tracker...")
    
    tracker = get_signal_tracker()
    
    # Запускаем трекер в фоне
    tracking_task = asyncio.create_task(tracker.start_tracking())
    
    # Ждем немного
    await asyncio.sleep(10)
    
    # Показываем статистику
    stats = tracker.get_statistics()
    print(f"📈 Tracker stats: {json.dumps(stats, indent=2)}")
    
    # Останавливаем
    tracking_task.cancel()
    await tracker.stop()
    
    print("✅ Test completed")

if __name__ == "__main__":
    asyncio.run(test_signal_tracker())
