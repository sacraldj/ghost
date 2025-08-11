#!/usr/bin/env python3
"""
Public API Client для бесплатных источников данных
Работает без API ключей
"""

import requests
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import json

logger = logging.getLogger(__name__)

class PublicAPIClient:
    """Клиент для работы с бесплатными Public APIs"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GHOST-News-Engine/1.0 (Public API Client)',
            'Accept': 'application/json'
        })
        
        # Ограничения запросов
        self.rate_limits = {}
        self.last_request_time = {}
    
    def get_coin_data(self, source: str, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Получает данные о криптовалютах из различных источников"""
        try:
            if source == 'coingecko':
                return self._get_coingecko_data(endpoint, params)
            elif source == 'binance':
                return self._get_binance_data(endpoint, params)
            elif source == 'coincap':
                return self._get_coincap_data(endpoint, params)
            else:
                logger.error(f"Неизвестный источник: {source}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка получения данных из {source}: {e}")
            return None
    
    def _get_coingecko_data(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Получает данные из CoinGecko API"""
        try:
            # Проверяем ограничения
            if not self._check_rate_limit('coingecko', 50, 60):
                logger.warning("Превышен лимит запросов к CoinGecko")
                return None
            
            url = f"https://api.coingecko.com/api/v3{endpoint}"
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Получены данные из CoinGecko: {endpoint}")
            
            return data
            
        except Exception as e:
            logger.error(f"Ошибка CoinGecko API: {e}")
            return None
    
    def _get_binance_data(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Получает данные из Binance Public API"""
        try:
            # Проверяем ограничения
            if not self._check_rate_limit('binance', 1200, 60):
                logger.warning("Превышен лимит запросов к Binance")
                return None
            
            url = f"https://api.binance.com/api/v3{endpoint}"
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Получены данные из Binance: {endpoint}")
            
            return data
            
        except Exception as e:
            logger.error(f"Ошибка Binance API: {e}")
            return None
    
    def _get_coincap_data(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Получает данные из CoinCap API"""
        try:
            # Проверяем ограничения
            if not self._check_rate_limit('coincap', 100, 60):
                logger.warning("Превышен лимит запросов к CoinCap")
                return None
            
            url = f"https://api.coincap.io/v2{endpoint}"
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Получены данные из CoinCap: {endpoint}")
            
            return data
            
        except Exception as e:
            logger.error(f"Ошибка CoinCap API: {e}")
            return None
    
    def _check_rate_limit(self, source: str, max_requests: int, window_seconds: int) -> bool:
        """Проверяет ограничения запросов"""
        current_time = time.time()
        
        if source not in self.rate_limits:
            self.rate_limits[source] = []
            self.last_request_time[source] = current_time
        
        # Удаляем старые запросы
        self.rate_limits[source] = [
            req_time for req_time in self.rate_limits[source]
            if current_time - req_time < window_seconds
        ]
        
        # Проверяем лимит
        if len(self.rate_limits[source]) >= max_requests:
            return False
        
        # Добавляем текущий запрос
        self.rate_limits[source].append(current_time)
        self.last_request_time[source] = current_time
        
        return True
    
    def get_top_cryptocurrencies(self, limit: int = 100) -> List[Dict]:
        """Получает топ криптовалют по рыночной капитализации"""
        try:
            # Пробуем CoinGecko
            data = self._get_coingecko_data(
                "/coins/markets",
                {
                    "vs_currency": "usd",
                    "order": "market_cap_desc",
                    "per_page": limit,
                    "page": 1,
                    "sparkline": False
                }
            )
            
            if data:
                return self._format_coingecko_markets(data)
            
            # Fallback к CoinCap
            data = self._get_coincap_data("/assets", {"limit": limit})
            if data:
                return self._format_coincap_assets(data)
            
            return []
            
        except Exception as e:
            logger.error(f"Ошибка получения топ криптовалют: {e}")
            return []
    
    def get_crypto_price(self, coin_ids: List[str], currencies: List[str] = None) -> Dict:
        """Получает текущие цены криптовалют"""
        if currencies is None:
            currencies = ["usd"]
        
        try:
            # CoinGecko поддерживает множественные ID
            if len(coin_ids) <= 250:  # Лимит CoinGecko
                data = self._get_coingecko_data(
                    "/simple/price",
                    {
                        "ids": ",".join(coin_ids),
                        "vs_currencies": ",".join(currencies)
                    }
                )
                
                if data:
                    return data
            
            # Fallback - получаем по одному
            prices = {}
            for coin_id in coin_ids:
                try:
                    data = self._get_coingecko_data(
                        "/simple/price",
                        {"ids": coin_id, "vs_currencies": ",".join(currencies)}
                    )
                    if data:
                        prices.update(data)
                    
                    time.sleep(0.1)  # Небольшая задержка
                    
                except Exception as e:
                    logger.error(f"Ошибка получения цены для {coin_id}: {e}")
                    continue
            
            return prices
            
        except Exception as e:
            logger.error(f"Ошибка получения цен: {e}")
            return {}
    
    def get_market_data(self, symbol: str = "BTCUSDT") -> Optional[Dict]:
        """Получает рыночные данные (Binance)"""
        try:
            data = self._get_binance_data("/ticker/24hr", {"symbol": symbol})
            if data:
                return self._format_binance_ticker(data)
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения рыночных данных: {e}")
            return None
    
    def _format_coingecko_markets(self, data: List[Dict]) -> List[Dict]:
        """Форматирует данные рынков CoinGecko"""
        formatted = []
        for coin in data:
            formatted.append({
                'id': coin.get('id'),
                'symbol': coin.get('symbol', '').upper(),
                'name': coin.get('name'),
                'current_price': coin.get('current_price'),
                'market_cap': coin.get('market_cap'),
                'market_cap_rank': coin.get('market_cap_rank'),
                'volume_24h': coin.get('total_volume'),
                'price_change_24h': coin.get('price_change_24h'),
                'price_change_percentage_24h': coin.get('price_change_percentage_24h'),
                'last_updated': coin.get('last_updated'),
                'source': 'coingecko'
            })
        return formatted
    
    def _format_coincap_assets(self, data: Dict) -> List[Dict]:
        """Форматирует данные активов CoinCap"""
        formatted = []
        for coin in data.get('data', []):
            formatted.append({
                'id': coin.get('id'),
                'symbol': coin.get('symbol', '').upper(),
                'name': coin.get('name'),
                'current_price': float(coin.get('priceUsd', 0)),
                'market_cap': float(coin.get('marketCapUsd', 0)),
                'market_cap_rank': coin.get('rank'),
                'volume_24h': float(coin.get('volumeUsd24Hr', 0)),
                'price_change_24h': float(coin.get('changePercent24Hr', 0)),
                'last_updated': coin.get('timestamp'),
                'source': 'coincap'
            })
        return formatted
    
    def _format_binance_ticker(self, data: Dict) -> Dict:
        """Форматирует данные тикера Binance"""
        return {
            'symbol': data.get('symbol'),
            'price': float(data.get('lastPrice', 0)),
            'price_change': float(data.get('priceChange', 0)),
            'price_change_percent': float(data.get('priceChangePercent', 0)),
            'volume_24h': float(data.get('volume', 0)),
            'quote_volume_24h': float(data.get('quoteVolume', 0)),
            'high_24h': float(data.get('highPrice', 0)),
            'low_24h': float(data.get('lowPrice', 0)),
            'count_24h': int(data.get('count', 0)),
            'source': 'binance'
        }

def main():
    """Тестирование Public API Client"""
    logging.basicConfig(level=logging.INFO)
    
    client = PublicAPIClient()
    
    print("🚀 Тестирование Public API Client...")
    
    # Тест 1: Топ криптовалют
    print("\n📊 Получаем топ криптовалют...")
    top_coins = client.get_top_cryptocurrencies(10)
    print(f"Получено {len(top_coins)} криптовалют:")
    
    for coin in top_coins[:5]:
        print(f"  {coin['symbol']}: ${coin['current_price']:.2f} (MC: ${coin['market_cap']:,.0f})")
    
    # Тест 2: Цены конкретных монет
    print("\n💰 Получаем цены...")
    prices = client.get_crypto_price(['bitcoin', 'ethereum', 'binancecoin'])
    print("Цены:")
    for coin, price_data in prices.items():
        print(f"  {coin}: ${price_data.get('usd', 'N/A')}")
    
    # Тест 3: Рыночные данные BTC
    print("\n📈 Получаем рыночные данные BTC...")
    market_data = client.get_market_data("BTCUSDT")
    if market_data:
        print(f"BTC/USDT: ${market_data['price']:.2f}")
        print(f"Изменение 24ч: {market_data['price_change_percent']:.2f}%")
        print(f"Объем 24ч: ${market_data['volume_24h']:,.0f}")

if __name__ == "__main__":
    main()
