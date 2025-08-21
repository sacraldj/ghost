"""
Bybit WebSocket Client для получения 1-секундных свечей
Интеграция с системой сигналов для автоматического сбора данных
"""

import asyncio
import websockets
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logger = logging.getLogger(__name__)

@dataclass
class CandleData:
    """Данные свечи"""
    symbol: str
    timestamp: int  # unix timestamp в секундах
    open: float
    high: float
    low: float
    close: float
    volume: float
    quote_volume: float = 0.0

class BybitWebSocketClient:
    """WebSocket клиент для Bybit API"""
    
    def __init__(self):
        # Bybit WebSocket URLs
        self.ws_url_public = "wss://stream.bybit.com/v5/public/linear"
        self.ws_url_private = "wss://stream.bybit.com/v5/private"
        
        # Активные подключения и подписки
        self.connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.subscriptions: Dict[str, List[str]] = {}  # symbol -> [callbacks]
        self.active_symbols: set = set()
        
        # Callback функции для обработки данных
        self.candle_callbacks: List[Callable[[CandleData], None]] = []
        
        # Статистика
        self.stats = {
            'total_candles': 0,
            'symbols_tracked': 0,
            'last_candle_time': None,
            'start_time': time.time()
        }
        
        logger.info("BybitWebSocketClient initialized")
    
    def add_candle_callback(self, callback: Callable[[CandleData], None]):
        """Добавить callback для обработки свечей"""
        self.candle_callbacks.append(callback)
        logger.info(f"Added candle callback: {callback.__name__}")
    
    async def subscribe_to_klines(self, symbol: str, interval: str = "1"):
        """
        Подписка на получение свечей (klines) для символа
        interval: 1, 3, 5, 15, 30, 60, 120, 240, 360, 720, D, M, W
        """
        try:
            # Формируем topic для подписки
            topic = f"kline.{interval}.{symbol}"
            
            # Подключаемся к WebSocket если еще не подключены
            if symbol not in self.connections:
                ws = await websockets.connect(self.ws_url_public)
                self.connections[symbol] = ws
                logger.info(f"✅ Connected to Bybit WebSocket for {symbol}")
                
                # Запускаем обработчик сообщений в фоне
                asyncio.create_task(self._handle_messages(symbol, ws))
            
            # Отправляем запрос на подписку
            subscribe_msg = {
                "op": "subscribe",
                "args": [topic]
            }
            
            await self.connections[symbol].send(json.dumps(subscribe_msg))
            
            # Добавляем в активные подписки
            if symbol not in self.subscriptions:
                self.subscriptions[symbol] = []
            self.subscriptions[symbol].append(topic)
            self.active_symbols.add(symbol)
            
            logger.info(f"✅ Subscribed to {topic}")
            self.stats['symbols_tracked'] = len(self.active_symbols)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error subscribing to {symbol}: {e}")
            return False
    
    async def unsubscribe_from_klines(self, symbol: str, interval: str = "1"):
        """Отписка от получения свечей для символа"""
        try:
            topic = f"kline.{interval}.{symbol}"
            
            if symbol in self.connections and symbol in self.subscriptions:
                # Отправляем запрос на отписку
                unsubscribe_msg = {
                    "op": "unsubscribe", 
                    "args": [topic]
                }
                
                await self.connections[symbol].send(json.dumps(unsubscribe_msg))
                
                # Удаляем из подписок
                if topic in self.subscriptions[symbol]:
                    self.subscriptions[symbol].remove(topic)
                
                # Если больше нет подписок для символа, закрываем соединение
                if not self.subscriptions[symbol]:
                    await self.connections[symbol].close()
                    del self.connections[symbol]
                    del self.subscriptions[symbol]
                    self.active_symbols.discard(symbol)
                
                logger.info(f"✅ Unsubscribed from {topic}")
                self.stats['symbols_tracked'] = len(self.active_symbols)
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Error unsubscribing from {symbol}: {e}")
            return False
    
    async def _handle_messages(self, symbol: str, websocket):
        """Обработка входящих WebSocket сообщений"""
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._process_message(symbol, data)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"❌ JSON decode error for {symbol}: {e}")
                except Exception as e:
                    logger.error(f"❌ Error processing message for {symbol}: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning(f"⚠️ WebSocket connection closed for {symbol}")
        except Exception as e:
            logger.error(f"❌ WebSocket error for {symbol}: {e}")
        finally:
            # Очищаем соединение
            if symbol in self.connections:
                del self.connections[symbol]
            if symbol in self.subscriptions:
                del self.subscriptions[symbol]
            self.active_symbols.discard(symbol)
    
    async def _process_message(self, symbol: str, data: dict):
        """Обработка конкретного сообщения"""
        try:
            # Проверяем тип сообщения
            if data.get("topic", "").startswith("kline"):
                # Это данные свечи
                kline_data = data.get("data", [])
                
                for kline in kline_data:
                    # Извлекаем данные свечи
                    candle = CandleData(
                        symbol=kline.get("symbol", symbol),
                        timestamp=int(kline.get("start", 0)) // 1000,  # конвертируем из миллисекунд
                        open=float(kline.get("open", 0)),
                        high=float(kline.get("high", 0)),
                        low=float(kline.get("low", 0)),
                        close=float(kline.get("close", 0)),
                        volume=float(kline.get("volume", 0)),
                        quote_volume=float(kline.get("turnover", 0))
                    )
                    
                    # Обновляем статистику
                    self.stats['total_candles'] += 1
                    self.stats['last_candle_time'] = datetime.fromtimestamp(candle.timestamp)
                    
                    # Вызываем все зарегистрированные callbacks
                    for callback in self.candle_callbacks:
                        try:
                            await callback(candle) if asyncio.iscoroutinefunction(callback) else callback(candle)
                        except Exception as e:
                            logger.error(f"❌ Error in candle callback {callback.__name__}: {e}")
                    
                    logger.debug(f"📊 New candle: {symbol} @ {candle.close} (vol: {candle.volume})")
            
            elif "success" in data:
                # Ответ на подписку/отписку
                if data["success"]:
                    logger.debug(f"✅ Operation successful for {symbol}: {data}")
                else:
                    logger.error(f"❌ Operation failed for {symbol}: {data}")
            
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")
    
    async def get_symbol_info(self, symbol: str) -> Optional[dict]:
        """Получение информации о торговой паре через REST API"""
        try:
            import aiohttp
            
            url = "https://api.bybit.com/v5/market/instruments-info"
            params = {
                "category": "linear",
                "symbol": symbol
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("retCode") == 0:
                            instruments = data.get("result", {}).get("list", [])
                            if instruments:
                                return instruments[0]
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting symbol info for {symbol}: {e}")
            return None
    
    def get_statistics(self) -> dict:
        """Получение статистики работы WebSocket клиента"""
        uptime = time.time() - self.stats['start_time']
        
        return {
            **self.stats,
            'active_symbols': list(self.active_symbols),
            'active_connections': len(self.connections),
            'uptime_seconds': round(uptime),
            'candles_per_second': round(self.stats['total_candles'] / max(uptime, 1), 2)
        }
    
    async def stop_all(self):
        """Остановка всех WebSocket соединений"""
        logger.info("🛑 Stopping all WebSocket connections...")
        
        for symbol in list(self.active_symbols):
            try:
                await self.unsubscribe_from_klines(symbol)
            except Exception as e:
                logger.error(f"Error stopping {symbol}: {e}")
        
        # Закрываем оставшиеся соединения
        for ws in self.connections.values():
            try:
                await ws.close()
            except Exception:
                pass
        
        self.connections.clear()
        self.subscriptions.clear()
        self.active_symbols.clear()
        
        logger.info("✅ All WebSocket connections stopped")

# Глобальный экземпляр клиента
_bybit_client = None

def get_bybit_client() -> BybitWebSocketClient:
    """Получить singleton экземпляр Bybit WebSocket клиента"""
    global _bybit_client
    if _bybit_client is None:
        _bybit_client = BybitWebSocketClient()
    return _bybit_client

# Тестирование
async def test_bybit_websocket():
    """Тестирование WebSocket подключения к Bybit"""
    print("🧪 Testing Bybit WebSocket...")
    
    client = get_bybit_client()
    
    # Добавляем callback для вывода данных
    def print_candle(candle: CandleData):
        print(f"📊 {candle.symbol}: {candle.close} @ {datetime.fromtimestamp(candle.timestamp)}")
    
    client.add_candle_callback(print_candle)
    
    # Подписываемся на BTCUSDT
    success = await client.subscribe_to_klines("BTCUSDT", "1")
    
    if success:
        print("✅ Subscribed to BTCUSDT 1-second klines")
        print("⏱️ Listening for 30 seconds...")
        
        # Слушаем 30 секунд
        await asyncio.sleep(30)
        
        # Показываем статистику
        stats = client.get_statistics()
        print(f"📈 Statistics: {stats}")
        
        # Останавливаем
        await client.stop_all()
        print("✅ Test completed")
    else:
        print("❌ Failed to subscribe")

if __name__ == "__main__":
    asyncio.run(test_bybit_websocket())
