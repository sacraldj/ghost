#!/usr/bin/env python3
"""
Система отслеживания TP1/TP2/SL в реальном времени
Мониторит активные сигналы и обновляет их статус
"""

import asyncio
import websockets
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Set
from dataclasses import dataclass
import aiohttp

logger = logging.getLogger(__name__)

@dataclass
class ActiveSignal:
    """Активный сигнал для отслеживания"""
    signal_id: str
    trader_id: str
    symbol: str
    side: str
    entry: float
    tp1: float
    tp2: float
    sl: float
    entry_time: datetime
    status: str  # 'waiting', 'entered', 'tp1', 'tp2', 'sl'
    current_price: float = 0
    max_profit_pct: float = 0
    max_loss_pct: float = 0

class RealtimeTracker:
    """Отслеживание сигналов в реальном времени"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.active_signals: Dict[str, ActiveSignal] = {}
        self.ws_connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.binance_ws_url = "wss://stream.binance.com:9443/ws"
        self.running = False
        
    async def load_active_signals(self):
        """Загрузить активные сигналы из БД"""
        try:
            # Получаем сигналы за последние 24 часа
            yesterday = (datetime.now() - timedelta(hours=24)).isoformat()
            
            signals = self.supabase.table('signals_parsed').select('*').gte('posted_at', yesterday).eq('is_valid', True).execute()
            
            for signal in signals.data:
                if signal['symbol'] and signal['entry'] and signal['tp1']:
                    active_signal = ActiveSignal(
                        signal_id=signal['signal_id'],
                        trader_id=signal['trader_id'],
                        symbol=signal['symbol'],
                        side=signal['side'],
                        entry=signal['entry'],
                        tp1=signal['tp1'],
                        tp2=signal.get('tp2', 0),
                        sl=signal.get('sl', 0),
                        entry_time=datetime.fromisoformat(signal['posted_at'].replace('Z', '+00:00')),
                        status='waiting'
                    )
                    
                    self.active_signals[signal['signal_id']] = active_signal
                    
            print(f"📊 Загружено активных сигналов: {len(self.active_signals)}")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки активных сигналов: {e}")
    
    async def subscribe_to_prices(self):
        """Подписка на цены через Binance WebSocket"""
        try:
            # Получаем уникальные символы
            symbols = list(set(signal.symbol.lower() for signal in self.active_signals.values()))
            
            if not symbols:
                print("❌ Нет символов для отслеживания")
                return
            
            # Формируем стримы для ticker
            streams = [f"{symbol}@ticker" for symbol in symbols]
            
            ws_url = f"{self.binance_ws_url}/stream?streams={'/'.join(streams)}"
            
            print(f"🔌 Подключение к Binance WebSocket: {len(symbols)} символов")
            
            async with websockets.connect(ws_url) as websocket:
                while self.running:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=30)
                        data = json.loads(message)
                        
                        if 'data' in data:
                            ticker = data['data']
                            symbol = ticker['s']
                            price = float(ticker['c'])
                            
                            await self.process_price_update(symbol, price)
                            
                    except asyncio.TimeoutError:
                        # Отправляем ping для поддержания соединения
                        await websocket.ping()
                    except Exception as e:
                        logger.error(f"Ошибка WebSocket: {e}")
                        break
                        
        except Exception as e:
            logger.error(f"Ошибка подключения к WebSocket: {e}")
    
    async def process_price_update(self, symbol: str, price: float):
        """Обработка обновления цены"""
        try:
            updated_signals = []
            
            for signal in self.active_signals.values():
                if signal.symbol.upper() == symbol.upper():
                    signal.current_price = price
                    
                    # Рассчитываем прибыль/убыток
                    if signal.side == "Buy":
                        profit_pct = ((price - signal.entry) / signal.entry) * 100
                        loss_pct = ((signal.entry - price) / signal.entry) * 100
                    else:  # Sell
                        profit_pct = ((signal.entry - price) / signal.entry) * 100
                        loss_pct = ((price - signal.entry) / signal.entry) * 100
                    
                    signal.max_profit_pct = max(signal.max_profit_pct, profit_pct)
                    signal.max_loss_pct = max(signal.max_loss_pct, loss_pct)
                    
                    # Проверяем достижение целей
                    old_status = signal.status
                    
                    if signal.side == "Buy":
                        if signal.tp2 and price >= signal.tp2 and signal.status != 'tp2':
                            signal.status = 'tp2'
                        elif signal.tp1 and price >= signal.tp1 and signal.status != 'tp1':
                            signal.status = 'tp1'
                        elif signal.sl and price <= signal.sl and signal.status not in ['tp1', 'tp2']:
                            signal.status = 'sl'
                        elif price >= signal.entry * 0.99 and signal.status == 'waiting':  # 1% толерантность
                            signal.status = 'entered'
                    else:  # Sell
                        if signal.tp2 and price <= signal.tp2 and signal.status != 'tp2':
                            signal.status = 'tp2'
                        elif signal.tp1 and price <= signal.tp1 and signal.status != 'tp1':
                            signal.status = 'tp1'
                        elif signal.sl and price >= signal.sl and signal.status not in ['tp1', 'tp2']:
                            signal.status = 'sl'
                        elif price <= signal.entry * 1.01 and signal.status == 'waiting':  # 1% толерантность
                            signal.status = 'entered'
                    
                    # Если статус изменился, сохраняем в БД
                    if old_status != signal.status:
                        updated_signals.append(signal)
                        print(f"🎯 {signal.symbol} {signal.side}: {old_status} → {signal.status} (${price:.4f})")
            
            # Сохраняем обновления в БД
            for signal in updated_signals:
                await self.save_signal_update(signal)
                
        except Exception as e:
            logger.error(f"Ошибка обработки цены: {e}")
    
    async def save_signal_update(self, signal: ActiveSignal):
        """Сохранить обновление сигнала"""
        try:
            # Создаем запись в signal_events
            event_data = {
                'signal_id': signal.signal_id,
                'event_type': signal.status,
                'event_time': datetime.now().isoformat(),
                'price': signal.current_price,
                'profit_pct': signal.max_profit_pct,
                'loss_pct': signal.max_loss_pct,
                'notes': f"Достигнут {signal.status} по цене {signal.current_price}"
            }
            
            self.supabase.table('signal_events').upsert(event_data).execute()
            
            # Обновляем основную таблицу сигналов
            update_data = {
                'signal_id': signal.signal_id,
                'current_status': signal.status,
                'current_price': signal.current_price,
                'max_profit_pct': signal.max_profit_pct,
                'max_loss_pct': signal.max_loss_pct,
                'last_update': datetime.now().isoformat()
            }
            
            self.supabase.table('signals_parsed').update(update_data).eq('signal_id', signal.signal_id).execute()
            
        except Exception as e:
            logger.error(f"Ошибка сохранения обновления сигнала: {e}")
    
    async def cleanup_old_signals(self):
        """Очистка старых сигналов"""
        try:
            # Удаляем сигналы старше 48 часов
            cutoff_time = datetime.now() - timedelta(hours=48)
            
            signals_to_remove = []
            for signal_id, signal in self.active_signals.items():
                if signal.entry_time < cutoff_time:
                    signals_to_remove.append(signal_id)
            
            for signal_id in signals_to_remove:
                del self.active_signals[signal_id]
                
            if signals_to_remove:
                print(f"🧹 Удалено старых сигналов: {len(signals_to_remove)}")
                
        except Exception as e:
            logger.error(f"Ошибка очистки старых сигналов: {e}")
    
    async def start_tracking(self):
        """Запуск отслеживания"""
        self.running = True
        print("🚀 ЗАПУСК РЕАЛЬНОГО ОТСЛЕЖИВАНИЯ СИГНАЛОВ")
        
        await self.load_active_signals()
        
        # Запускаем задачи
        tasks = [
            asyncio.create_task(self.subscribe_to_prices()),
            asyncio.create_task(self.periodic_cleanup())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            print("⏹️ Остановка отслеживания...")
            self.running = False
            for task in tasks:
                task.cancel()
    
    async def periodic_cleanup(self):
        """Периодическая очистка"""
        while self.running:
            try:
                await asyncio.sleep(3600)  # Каждый час
                await self.cleanup_old_signals()
                await self.load_active_signals()  # Перезагружаем новые сигналы
            except Exception as e:
                logger.error(f"Ошибка периодической очистки: {e}")
    
    def stop_tracking(self):
        """Остановка отслеживания"""
        self.running = False
        print("⏹️ Отслеживание остановлено")

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    from supabase import create_client
    
    load_dotenv()
    
    supabase = create_client(
        os.getenv('NEXT_PUBLIC_SUPABASE_URL'),
        os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    )
    
    tracker = RealtimeTracker(supabase)
    
    try:
        asyncio.run(tracker.start_tracking())
    except KeyboardInterrupt:
        tracker.stop_tracking()
