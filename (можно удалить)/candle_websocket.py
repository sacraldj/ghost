"""
GHOST Live Candle WebSocket Collector
Собирает live свечи через WebSocket как у Дарена для анализа сигналов
"""

import asyncio
import json
import websockets
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
import aiohttp
from supabase import create_client, Client

logger = logging.getLogger(__name__)

@dataclass
class CandleData:
    """Структура свечи"""
    symbol: str
    timeframe: str
    open_time: datetime
    close_time: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    trades_count: int
    vwap: Optional[float] = None

class LiveCandleCollector:
    """Сборщик live свечей через WebSocket"""
    
    def __init__(self, supabase_client: Optional[Client] = None):
        self.supabase = supabase_client
        self.active_subscriptions: Dict[str, Dict[str, Any]] = {}
        self.callback_handlers: List[Callable] = []
        self.is_running = False
        
        # Настройки WebSocket
        self.bybit_ws_url = "wss://stream.bybit.com/v5/public/spot"
        self.binance_ws_url = "wss://stream.binance.com:9443/ws/"
        
        # Буфер для свечей
        self.candle_buffer: Dict[str, CandleData] = {}
        
        logger.info("Live Candle Collector initialized")
    
    def add_callback(self, callback: Callable[[CandleData], None]):
        """Добавить callback для обработки новых свечей"""
        self.callback_handlers.append(callback)
    
    async def subscribe_to_symbol(self, symbol: str, timeframes: List[str] = ["1m", "5m", "15m"]):
        """Подписка на live свечи символа"""
        try:
            normalized_symbol = symbol.upper()
            
            # Подписываемся только на Bybit (Binance заблокирован HTTP 451)
            await self._subscribe_bybit(normalized_symbol, timeframes)
            
            logger.info(f"✅ Subscribed to {normalized_symbol} on Bybit, timeframes: {timeframes}")
            
        except Exception as e:
            logger.error(f"❌ Error subscribing to {symbol}: {e}")
    
    async def _subscribe_bybit(self, symbol: str, timeframes: List[str]):
        """Подписка на Bybit WebSocket"""
        try:
            # Создаем задачу WebSocket подключения
            task = asyncio.create_task(self._bybit_websocket_handler(symbol, timeframes))
            
            # Сохраняем подписку
            subscription_key = f"bybit_{symbol}"
            self.active_subscriptions[subscription_key] = {
                "exchange": "bybit",
                "symbol": symbol,
                "timeframes": timeframes,
                "task": task,
                "status": "connecting"
            }
            
        except Exception as e:
            logger.error(f"❌ Error setting up Bybit subscription for {symbol}: {e}")
    
    async def _bybit_websocket_handler(self, symbol: str, timeframes: List[str]):
        """Обработчик Bybit WebSocket"""
        try:
            # Формируем список подписок
            topics = [f"kline.{tf}.{symbol}" for tf in timeframes]
            subscribe_message = {
                "op": "subscribe",
                "args": topics
            }
            
            async with websockets.connect(self.bybit_ws_url) as websocket:
                # Отправляем подписку
                await websocket.send(json.dumps(subscribe_message))
                logger.info(f"📡 Bybit WebSocket connected for {symbol}")
                
                # Обновляем статус
                subscription_key = f"bybit_{symbol}"
                if subscription_key in self.active_subscriptions:
                    self.active_subscriptions[subscription_key]["status"] = "connected"
                
                # Слушаем сообщения
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        await self._process_bybit_message(data, symbol)
                    except Exception as e:
                        logger.error(f"❌ Error processing Bybit message: {e}")
                        
        except Exception as e:
            logger.error(f"❌ Bybit WebSocket error for {symbol}: {e}")
            
            # Обновляем статус
            subscription_key = f"bybit_{symbol}"
            if subscription_key in self.active_subscriptions:
                self.active_subscriptions[subscription_key]["status"] = "error"
    
    async def _process_bybit_message(self, data: Dict[str, Any], symbol: str):
        """Обработка сообщения от Bybit"""
        try:
            if data.get("topic", "").startswith("kline"):
                # Извлекаем данные свечи
                kline_data = data.get("data", [])
                
                for kline in kline_data:
                    candle = await self._parse_bybit_candle(kline, symbol)
                    if candle:
                        await self._process_new_candle(candle)
                        
        except Exception as e:
            logger.error(f"❌ Error processing Bybit message: {e}")
    
    async def _parse_bybit_candle(self, kline: Dict[str, Any], symbol: str) -> Optional[CandleData]:
        """Парсинг свечи от Bybit"""
        try:
            # Извлекаем timeframe из topic
            timeframe = kline.get("interval", "1m")
            
            # Конвертируем timestamp
            open_time = datetime.fromtimestamp(int(kline["start"]) / 1000)
            close_time = datetime.fromtimestamp(int(kline["end"]) / 1000)
            
            return CandleData(
                symbol=symbol,
                timeframe=timeframe,
                open_time=open_time,
                close_time=close_time,
                open_price=float(kline["open"]),
                high_price=float(kline["high"]),
                low_price=float(kline["low"]),
                close_price=float(kline["close"]),
                volume=float(kline["volume"]),
                trades_count=int(kline.get("count", 0))
            )
            
        except Exception as e:
            logger.error(f"❌ Error parsing Bybit candle: {e}")
            return None
    
    async def _subscribe_binance(self, symbol: str, timeframes: List[str]):
        """Подписка на Binance WebSocket (резерв)"""
        try:
            # Binance использует lowercase
            binance_symbol = symbol.lower()
            
            task = asyncio.create_task(self._binance_websocket_handler(binance_symbol, timeframes))
            
            subscription_key = f"binance_{symbol}"
            self.active_subscriptions[subscription_key] = {
                "exchange": "binance",
                "symbol": symbol,
                "timeframes": timeframes,
                "task": task,
                "status": "connecting"
            }
            
        except Exception as e:
            logger.error(f"❌ Error setting up Binance subscription for {symbol}: {e}")
    
    async def _binance_websocket_handler(self, symbol: str, timeframes: List[str]):
        """Обработчик Binance WebSocket"""
        try:
            # Формируем streams для Binance
            streams = [f"{symbol}@kline_{tf}" for tf in timeframes]
            stream_url = f"{self.binance_ws_url}{'/'.join(streams)}"
            
            async with websockets.connect(stream_url) as websocket:
                logger.info(f"📡 Binance WebSocket connected for {symbol}")
                
                subscription_key = f"binance_{symbol.upper()}"
                if subscription_key in self.active_subscriptions:
                    self.active_subscriptions[subscription_key]["status"] = "connected"
                
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        await self._process_binance_message(data, symbol.upper())
                    except Exception as e:
                        logger.error(f"❌ Error processing Binance message: {e}")
                        
        except Exception as e:
            logger.error(f"❌ Binance WebSocket error for {symbol}: {e}")
            
            subscription_key = f"binance_{symbol.upper()}"
            if subscription_key in self.active_subscriptions:
                self.active_subscriptions[subscription_key]["status"] = "error"
    
    async def _process_binance_message(self, data: Dict[str, Any], symbol: str):
        """Обработка сообщения от Binance"""
        try:
            if "k" in data:  # Kline data
                kline = data["k"]
                
                candle = await self._parse_binance_candle(kline, symbol)
                if candle:
                    await self._process_new_candle(candle)
                    
        except Exception as e:
            logger.error(f"❌ Error processing Binance message: {e}")
    
    async def _parse_binance_candle(self, kline: Dict[str, Any], symbol: str) -> Optional[CandleData]:
        """Парсинг свечи от Binance"""
        try:
            open_time = datetime.fromtimestamp(int(kline["t"]) / 1000)
            close_time = datetime.fromtimestamp(int(kline["T"]) / 1000)
            
            return CandleData(
                symbol=symbol,
                timeframe=kline["i"],  # interval
                open_time=open_time,
                close_time=close_time,
                open_price=float(kline["o"]),
                high_price=float(kline["h"]),
                low_price=float(kline["l"]),
                close_price=float(kline["c"]),
                volume=float(kline["v"]),
                trades_count=int(kline["n"])
            )
            
        except Exception as e:
            logger.error(f"❌ Error parsing Binance candle: {e}")
            return None
    
    async def _process_new_candle(self, candle: CandleData):
        """Обработка новой свечи"""
        try:
            # Создаем уникальный ключ для свечи
            candle_key = f"{candle.symbol}_{candle.timeframe}_{candle.open_time.isoformat()}"
            
            # Обновляем буфер
            self.candle_buffer[candle_key] = candle
            
            # Сохраняем в базу
            if self.supabase:
                await self._save_candle_to_db(candle)
            
            # Вызываем callbacks
            for callback in self.callback_handlers:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(candle)
                    else:
                        callback(candle)
                except Exception as e:
                    logger.error(f"❌ Error in callback: {e}")
            
            logger.debug(f"📊 New candle: {candle.symbol} {candle.timeframe} @ {candle.close_price}")
            
        except Exception as e:
            logger.error(f"❌ Error processing new candle: {e}")
    
    async def _save_candle_to_db(self, candle: CandleData):
        """Сохранение свечи в базу данных"""
        try:
            candle_data = {
                "symbol": candle.symbol,
                "timeframe": candle.timeframe,
                "open_time": candle.open_time.isoformat(),
                "open_price": candle.open_price,
                "high_price": candle.high_price,
                "low_price": candle.low_price,
                "close_price": candle.close_price,
                "volume": candle.volume,
                "trades_count": candle.trades_count,
                "vwap": candle.vwap,
                "updated_at": datetime.now().isoformat()
            }
            
            # Используем upsert для обновления свечей
            result = self.supabase.table("trader_candles").upsert(
                candle_data,
                on_conflict="symbol,timeframe,open_time"
            ).execute()
            
            if result.data:
                logger.debug(f"💾 Candle saved: {candle.symbol} {candle.timeframe}")
            
        except Exception as e:
            logger.error(f"❌ Error saving candle to DB: {e}")
    
    async def get_recent_candles(self, symbol: str, timeframe: str = "1m", limit: int = 100) -> List[CandleData]:
        """Получение последних свечей из базы"""
        try:
            if not self.supabase:
                return []
            
            result = self.supabase.table("trader_candles") \
                .select("*") \
                .eq("symbol", symbol) \
                .eq("timeframe", timeframe) \
                .order("open_time", desc=True) \
                .limit(limit) \
                .execute()
            
            candles = []
            for row in result.data:
                candle = CandleData(
                    symbol=row["symbol"],
                    timeframe=row["timeframe"],
                    open_time=datetime.fromisoformat(row["open_time"]),
                    close_time=datetime.fromisoformat(row["open_time"]) + timedelta(minutes=1),  # Приблизительно
                    open_price=float(row["open_price"]),
                    high_price=float(row["high_price"]),
                    low_price=float(row["low_price"]),
                    close_price=float(row["close_price"]),
                    volume=float(row["volume"]),
                    trades_count=int(row["trades_count"]),
                    vwap=float(row["vwap"]) if row["vwap"] else None
                )
                candles.append(candle)
            
            return candles
            
        except Exception as e:
            logger.error(f"❌ Error getting recent candles: {e}")
            return []
    
    def get_subscription_status(self) -> Dict[str, Any]:
        """Получение статуса всех подписок"""
        status = {
            "total_subscriptions": len(self.active_subscriptions),
            "active_subscriptions": 0,
            "error_subscriptions": 0,
            "connecting_subscriptions": 0,
            "subscriptions": {}
        }
        
        for key, sub in self.active_subscriptions.items():
            status["subscriptions"][key] = {
                "exchange": sub["exchange"],
                "symbol": sub["symbol"],
                "timeframes": sub["timeframes"],
                "status": sub["status"]
            }
            
            if sub["status"] == "connected":
                status["active_subscriptions"] += 1
            elif sub["status"] == "error":
                status["error_subscriptions"] += 1
            elif sub["status"] == "connecting":
                status["connecting_subscriptions"] += 1
        
        return status
    
    async def start(self):
        """Запуск сборщика свечей"""
        self.is_running = True
        logger.info("🚀 Live Candle Collector started")
    
    async def stop(self):
        """Остановка сборщика свечей"""
        self.is_running = False
        
        # Останавливаем все WebSocket подключения
        for key, subscription in self.active_subscriptions.items():
            try:
                if "task" in subscription:
                    subscription["task"].cancel()
            except Exception as e:
                logger.error(f"❌ Error stopping subscription {key}: {e}")
        
        self.active_subscriptions.clear()
        logger.info("🛑 Live Candle Collector stopped")


# Глобальный экземпляр
candle_collector = None

def get_candle_collector(supabase_client: Optional[Client] = None) -> LiveCandleCollector:
    """Получение глобального экземпляра сборщика свечей"""
    global candle_collector
    if candle_collector is None:
        candle_collector = LiveCandleCollector(supabase_client)
    return candle_collector


# Тестирование
async def test_candle_collector():
    """Тестирование сборщика свечей"""
    print("🧪 ТЕСТИРОВАНИЕ LIVE CANDLE COLLECTOR")
    print("=" * 60)
    
    collector = get_candle_collector()
    
    # Добавляем callback для тестирования
    def on_new_candle(candle: CandleData):
        print(f"📊 New candle: {candle.symbol} {candle.timeframe} @ {candle.close_price}")
    
    collector.add_callback(on_new_candle)
    
    # Подписываемся на BTCUSDT
    await collector.subscribe_to_symbol("BTCUSDT", ["1m"])
    
    # Запускаем
    await collector.start()
    
    print("🔄 Listening for candles for 30 seconds...")
    await asyncio.sleep(30)
    
    # Показываем статистику
    status = collector.get_subscription_status()
    print(f"📊 Subscription status: {status}")
    
    # Останавливаем
    await collector.stop()
    
    print("✅ Test completed!")


if __name__ == "__main__":
    asyncio.run(test_candle_collector())
