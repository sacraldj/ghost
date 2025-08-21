"""
Market Price Service - получение реальных рыночных цен с биржи
"""
import asyncio
import logging
import json
from typing import Optional, Dict, List
from datetime import datetime, timezone
import aiohttp
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MarketPrice:
    """Структура рыночной цены"""
    symbol: str
    price: float
    timestamp: datetime
    source: str
    
    def to_dict(self) -> dict:
        return {
            'symbol': self.symbol,
            'price': self.price,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source
        }

class MarketPriceService:
    """Сервис для получения рыночных цен с различных бирж"""
    
    def __init__(self):
        self.session = None
        self.cache = {}
        self.cache_ttl = 5  # Кеш на 5 секунд
        
    async def _get_session(self):
        """Получить HTTP сессию"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Закрыть HTTP сессию"""
        if self.session:
            await self.session.close()
            self.session = None
    
    def _is_cache_valid(self, symbol: str) -> bool:
        """Проверить валидность кеша"""
        if symbol not in self.cache:
            return False
        
        cache_time = self.cache[symbol]['timestamp']
        now = datetime.now(timezone.utc)
        return (now - cache_time).total_seconds() < self.cache_ttl
    
    async def get_bybit_price(self, symbol: str) -> Optional[MarketPrice]:
        """Получить цену с Bybit"""
        try:
            session = await self._get_session()
            url = f"https://api.bybit.com/v5/market/tickers?category=linear&symbol={symbol}"
            
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"❌ Bybit API error: HTTP {response.status}")
                    return None
                
                data = await response.json()
                
                if data.get('retCode') == 0 and data.get('result', {}).get('list'):
                    price_data = data['result']['list'][0]
                    price = float(price_data['lastPrice'])
                    
                    return MarketPrice(
                        symbol=symbol,
                        price=price,
                        timestamp=datetime.now(timezone.utc),
                        source='bybit'
                    )
                else:
                    logger.error(f"❌ Bybit API invalid response: {data}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error fetching Bybit price for {symbol}: {e}")
            return None
    
    async def get_binance_price(self, symbol: str) -> Optional[MarketPrice]:
        """Получить цену с Binance"""
        try:
            session = await self._get_session()
            url = f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol}"
            
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"❌ Binance API error: HTTP {response.status}")
                    return None
                
                data = await response.json()
                
                if 'price' in data:
                    price = float(data['price'])
                    
                    return MarketPrice(
                        symbol=symbol,
                        price=price,
                        timestamp=datetime.now(timezone.utc),
                        source='binance'
                    )
                else:
                    logger.error(f"❌ Binance API invalid response: {data}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error fetching Binance price for {symbol}: {e}")
            return None
    
    async def get_market_price(self, symbol: str, prefer_exchange: str = 'bybit') -> Optional[MarketPrice]:
        """
        Получить рыночную цену с предпочитаемой биржи и fallback
        
        Args:
            symbol: Торговая пара (например, DOGEUSDT)
            prefer_exchange: Предпочитаемая биржа ('bybit' или 'binance')
        """
        # Проверяем кеш
        if self._is_cache_valid(symbol):
            cached = self.cache[symbol]
            logger.debug(f"📊 Using cached price for {symbol}: ${cached['price']}")
            return MarketPrice(
                symbol=symbol,
                price=cached['price'],
                timestamp=cached['timestamp'],
                source=cached['source']
            )
        
        # Получаем свежую цену
        price_data = None
        
        if prefer_exchange == 'bybit':
            # Сначала пробуем Bybit
            price_data = await self.get_bybit_price(symbol)
            if price_data is None:
                # Fallback на Binance
                logger.warning(f"⚠️ Bybit failed for {symbol}, trying Binance...")
                price_data = await self.get_binance_price(symbol)
        else:
            # Сначала пробуем Binance
            price_data = await self.get_binance_price(symbol)
            if price_data is None:
                # Fallback на Bybit
                logger.warning(f"⚠️ Binance failed for {symbol}, trying Bybit...")
                price_data = await self.get_bybit_price(symbol)
        
        # Кешируем результат
        if price_data:
            self.cache[symbol] = {
                'price': price_data.price,
                'timestamp': price_data.timestamp,
                'source': price_data.source
            }
            logger.info(f"💰 Market price for {symbol}: ${price_data.price} ({price_data.source})")
        else:
            logger.error(f"❌ Failed to get market price for {symbol} from all exchanges")
        
        return price_data
    
    async def get_multiple_prices(self, symbols: List[str], prefer_exchange: str = 'bybit') -> Dict[str, MarketPrice]:
        """Получить цены для нескольких символов параллельно"""
        tasks = []
        for symbol in symbols:
            task = asyncio.create_task(self.get_market_price(symbol, prefer_exchange))
            tasks.append((symbol, task))
        
        results = {}
        for symbol, task in tasks:
            try:
                price_data = await task
                if price_data:
                    results[symbol] = price_data
                else:
                    logger.warning(f"⚠️ No price data for {symbol}")
            except Exception as e:
                logger.error(f"❌ Error getting price for {symbol}: {e}")
        
        return results
    
    async def test_connection(self) -> bool:
        """Тест подключения к биржам"""
        try:
            # Тестируем на популярной паре
            test_symbol = 'BTCUSDT'
            price_data = await self.get_market_price(test_symbol)
            
            if price_data and price_data.price > 0:
                logger.info(f"✅ Market price service test OK: {test_symbol} = ${price_data.price}")
                return True
            else:
                logger.error("❌ Market price service test failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Market price service test error: {e}")
            return False

# Глобальный экземпляр сервиса
market_price_service = MarketPriceService()

async def main():
    """Тестирование сервиса"""
    logger.basicConfig(level=logging.INFO)
    
    # Тест подключения
    if await market_price_service.test_connection():
        logger.info("✅ Market price service ready")
    else:
        logger.error("❌ Market price service not ready")
    
    # Тест получения цен
    symbols = ['DOGEUSDT', 'BTCUSDT', 'ETHUSDT']
    prices = await market_price_service.get_multiple_prices(symbols)
    
    for symbol, price_data in prices.items():
        logger.info(f"💰 {symbol}: ${price_data.price} from {price_data.source}")
    
    await market_price_service.close()

if __name__ == "__main__":
    asyncio.run(main())
