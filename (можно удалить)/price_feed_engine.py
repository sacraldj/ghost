#!/usr/bin/env python3
"""
GHOST Price Feed Engine - Модуль сбора ценовых данных
Получение цен BTC и ETH каждую секунду с Binance и Coinbase
Формирование свечей по разным интервалам
Сохранение всех данных в базу данных с точным временем
"""

import asyncio
import aiohttp
import sqlite3
import logging
import time
import json
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import yaml
import os
from pathlib import Path
import pandas as pd
import numpy as np

# GHOST-META
__version__ = "1.0.0"
__author__ = "GHOST Team"
__description__ = "Модуль сбора ценовых данных с Binance и Coinbase"
__dependencies__ = ["aiohttp", "pyyaml", "sqlite3", "pandas", "numpy"]

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('price_feed_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CandleInterval(Enum):
    """Интервалы для формирования свечей"""
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAY_1 = "1d"

@dataclass
class PriceData:
    """Структура для хранения ценовых данных"""
    symbol: str
    price: float
    volume: float
    timestamp: datetime
    source: str
    bid: Optional[float] = None
    ask: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None

@dataclass
class Candle:
    """Структура для хранения свечи"""
    symbol: str
    interval: str
    open_time: datetime
    close_time: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    trade_count: int = 0

class PriceFeedEngine:
    """Основной класс для сбора ценовых данных"""
    
    def __init__(self, db_path: str = "ghost_news.db"):
        self.db_path = db_path
        self.session: Optional[aiohttp.ClientSession] = None
        self.running = False
        self.price_buffer: Dict[str, List[PriceData]] = {}
        self.candle_buffers: Dict[str, Dict[str, List[PriceData]]] = {}
        
        # Настройки API
        self.binance_base_url = "https://api.binance.com/api/v3"
        self.coinbase_base_url = "https://api.coinbase.com/v2"
        
        # Символы для отслеживания
        self.symbols = ["BTC", "ETH"]
        
        # Интервалы для свечей
        self.intervals = [interval.value for interval in CandleInterval]
        
        # Инициализация базы данных
        self._init_database()
        
        # Инициализация буферов
        self._init_buffers()
    
    def _init_database(self):
        """Инициализация базы данных с новыми таблицами"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Включение WAL режима для лучшей производительности
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=10000")
            cursor.execute("PRAGMA temp_store=MEMORY")
            
            # Таблица для хранения всех ценовых данных
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS price_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    price REAL NOT NULL,
                    volume REAL,
                    timestamp DATETIME NOT NULL,
                    source TEXT NOT NULL,
                    bid REAL,
                    ask REAL,
                    high_24h REAL,
                    low_24h REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица для хранения свечей
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS candles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    interval TEXT NOT NULL,
                    open_time DATETIME NOT NULL,
                    close_time DATETIME NOT NULL,
                    open_price REAL NOT NULL,
                    high_price REAL NOT NULL,
                    low_price REAL NOT NULL,
                    close_price REAL NOT NULL,
                    volume REAL NOT NULL,
                    trade_count INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Создание индексов для быстрого поиска
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_price_data_symbol_timestamp 
                ON price_data(symbol, timestamp DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_price_data_timestamp 
                ON price_data(timestamp DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_candles_symbol_interval_time 
                ON candles(symbol, interval, close_time DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_candles_timestamp 
                ON candles(close_time DESC)
            """)
            
            conn.commit()
            conn.close()
            logger.info("База данных инициализирована успешно")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации базы данных: {e}")
            raise
    
    def _init_buffers(self):
        """Инициализация буферов для цен и свечей"""
        for symbol in self.symbols:
            self.price_buffer[symbol] = []
            
            self.candle_buffers[symbol] = {}
            for interval in self.intervals:
                self.candle_buffers[symbol][interval] = []
        
        logger.info("Буферы инициализированы")
    
    async def _create_session(self):
        """Создание HTTP сессии"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=10)
            self.session = aiohttp.ClientSession(timeout=timeout)
            logger.info("HTTP сессия создана")
    
    async def _close_session(self):
        """Закрытие HTTP сессии"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("HTTP сессия закрыта")
    
    async def _fetch_binance_price(self, symbol: str) -> Optional[PriceData]:
        """Получение цены с Binance"""
        try:
            if not self.session:
                await self._create_session()
            
            # Получение текущей цены
            ticker_url = f"{self.binance_base_url}/ticker/24hr"
            params = {"symbol": f"{symbol}USDT"}
            
            async with self.session.get(ticker_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    return PriceData(
                        symbol=symbol,
                        price=float(data['lastPrice']),
                        volume=float(data['volume']),
                        timestamp=datetime.now(timezone.utc),
                        source="binance",
                        bid=float(data['bidPrice']) if data['bidPrice'] != '0.00000000' else None,
                        ask=float(data['askPrice']) if data['askPrice'] != '0.00000000' else None,
                        high_24h=float(data['highPrice']) if data['highPrice'] != '0.00000000' else None,
                        low_24h=float(data['lowPrice']) if data['lowPrice'] != '0.00000000' else None
                    )
                else:
                    logger.warning(f"Binance API вернул статус {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Ошибка получения цены с Binance для {symbol}: {e}")
            return None
    
    async def _fetch_coinbase_price(self, symbol: str) -> Optional[PriceData]:
        """Получение цены с Coinbase"""
        try:
            if not self.session:
                await self._create_session()
            
            # Получение текущей цены
            ticker_url = f"{self.coinbase_base_url}/products/{symbol}-USD/ticker"
            
            async with self.session.get(ticker_url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    return PriceData(
                        symbol=symbol,
                        price=float(data['price']),
                        volume=float(data['volume']) if 'volume' in data else 0.0,
                        timestamp=datetime.now(timezone.utc),
                        source="coinbase",
                        bid=float(data['bid']) if 'bid' in data else None,
                        ask=float(data['ask']) if 'ask' in data else None
                    )
                else:
                    logger.warning(f"Coinbase API вернул статус {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Ошибка получения цены с Coinbase для {symbol}: {e}")
            return None
    
    def _save_price_data(self, price_data: PriceData) -> bool:
        """Сохранение ценовых данных в базу"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO price_data (symbol, price, volume, timestamp, source, bid, ask, high_24h, low_24h)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                price_data.symbol,
                price_data.price,
                price_data.volume,
                price_data.timestamp.isoformat(),
                price_data.source,
                price_data.bid,
                price_data.ask,
                price_data.high_24h,
                price_data.low_24h
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения ценовых данных: {e}")
            return False
    
    def _add_to_buffer(self, price_data: PriceData):
        """Добавление данных в буфер"""
        symbol = price_data.symbol
        
        # Добавление в основной буфер цен
        self.price_buffer[symbol].append(price_data)
        
        # Ограничение размера буфера (храним последние 1000 записей)
        if len(self.price_buffer[symbol]) > 1000:
            self.price_buffer[symbol] = self.price_buffer[symbol][-1000:]
        
        # Добавление в буферы для каждого интервала
        for interval in self.intervals:
            self.candle_buffers[symbol][interval].append(price_data)
            
            # Ограничение размера буфера свечей
            if len(self.candle_buffers[symbol][interval]) > 1000:
                self.candle_buffers[symbol][interval] = self.candle_buffers[symbol][interval][-1000:]
    
    def _form_candles(self, symbol: str, interval: str) -> List[Candle]:
        """Формирование свечей из буфера"""
        if symbol not in self.candle_buffers or interval not in self.candle_buffers[symbol]:
            return []
        
        price_data_list = self.candle_buffers[symbol][interval]
        if not price_data_list:
            return []
        
        candles = []
        
        # Группировка по временным интервалам
        if interval == CandleInterval.MINUTE_1.value:
            group_key = lambda x: x.timestamp.replace(second=0, microsecond=0)
        elif interval == CandleInterval.MINUTE_5.value:
            group_key = lambda x: x.timestamp.replace(minute=(x.timestamp.minute // 5) * 5, second=0, microsecond=0)
        elif interval == CandleInterval.MINUTE_15.value:
            group_key = lambda x: x.timestamp.replace(minute=(x.timestamp.minute // 15) * 15, second=0, microsecond=0)
        elif interval == CandleInterval.HOUR_1.value:
            group_key = lambda x: x.timestamp.replace(minute=0, second=0, microsecond=0)
        elif interval == CandleInterval.HOUR_4.value:
            group_key = lambda x: x.timestamp.replace(hour=(x.timestamp.hour // 4) * 4, minute=0, second=0, microsecond=0)
        elif interval == CandleInterval.DAY_1.value:
            group_key = lambda x: x.timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            return []
        
        # Группировка данных
        grouped_data = {}
        for price_data in price_data_list:
            key = group_key(price_data)
            if key not in grouped_data:
                grouped_data[key] = []
            grouped_data[key].append(price_data)
        
        # Формирование свечей
        for time_key, prices in grouped_data.items():
            if len(prices) < 2:  # Нужно минимум 2 точки для свечи
                continue
            
            prices.sort(key=lambda x: x.timestamp)
            
            candle = Candle(
                symbol=symbol,
                interval=interval,
                open_time=time_key,
                close_time=time_key + self._get_interval_timedelta(interval),
                open_price=prices[0].price,
                high_price=max(p.price for p in prices),
                low_price=min(p.price for p in prices),
                close_price=prices[-1].price,
                volume=sum(p.volume for p in prices),
                trade_count=len(prices)
            )
            
            candles.append(candle)
        
        return candles
    
    def _get_interval_timedelta(self, interval: str) -> timedelta:
        """Получение временного интервала для свечи"""
        if interval == CandleInterval.MINUTE_1.value:
            return timedelta(minutes=1)
        elif interval == CandleInterval.MINUTE_5.value:
            return timedelta(minutes=5)
        elif interval == CandleInterval.MINUTE_15.value:
            return timedelta(minutes=15)
        elif interval == CandleInterval.HOUR_1.value:
            return timedelta(hours=1)
        elif interval == CandleInterval.HOUR_4.value:
            return timedelta(hours=4)
        elif interval == CandleInterval.DAY_1.value:
            return timedelta(days=1)
        else:
            return timedelta(minutes=1)
    
    def _save_candles(self, candles: List[Candle]) -> bool:
        """Сохранение свечей в базу данных"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for candle in candles:
                cursor.execute("""
                    INSERT INTO candles (symbol, interval, open_time, close_time, open_price, high_price, low_price, close_price, volume, trade_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    candle.symbol,
                    candle.interval,
                    candle.open_time.isoformat(),
                    candle.close_time.isoformat(),
                    candle.open_price,
                    candle.high_price,
                    candle.low_price,
                    candle.close_price,
                    candle.volume,
                    candle.trade_count
                ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения свечей: {e}")
            return False
    
    async def _fetch_all_prices(self) -> List[PriceData]:
        """Получение цен со всех источников"""
        tasks = []
        
        # Создание задач для получения цен
        for symbol in self.symbols:
            tasks.append(self._fetch_binance_price(symbol))
            tasks.append(self._fetch_coinbase_price(symbol))
        
        # Выполнение всех задач параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Фильтрация результатов
        valid_prices = []
        for result in results:
            if isinstance(result, PriceData):
                valid_prices.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Ошибка получения цены: {result}")
        
        return valid_prices
    
    async def _process_price_cycle(self):
        """Один цикл обработки цен"""
        try:
            # Получение цен
            prices = await self._fetch_all_prices()
            
            if not prices:
                logger.warning("Не удалось получить цены")
                return
            
            # Сохранение и буферизация
            for price_data in prices:
                if self._save_price_data(price_data):
                    self._add_to_buffer(price_data)
                    logger.debug(f"Цена {price_data.symbol}: {price_data.price} сохранена")
            
            # Формирование и сохранение свечей
            for symbol in self.symbols:
                for interval in self.intervals:
                    candles = self._form_candles(symbol, interval)
                    if candles:
                        if self._save_candles(candles):
                            logger.debug(f"Свечи {symbol} {interval}: {len(candles)} сохранены")
            
        except Exception as e:
            logger.error(f"Ошибка в цикле обработки цен: {e}")
    
    async def start(self):
        """Запуск движка сбора цен"""
        logger.info("Запуск Price Feed Engine...")
        
        try:
            await self._create_session()
            self.running = True
            
            while self.running:
                start_time = time.time()
                
                await self._process_price_cycle()
                
                # Пауза до следующей секунды
                elapsed = time.time() - start_time
                if elapsed < 1.0:
                    await asyncio.sleep(1.0 - elapsed)
                
        except KeyboardInterrupt:
            logger.info("Получен сигнал остановки")
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
        finally:
            await self._close_session()
            logger.info("Price Feed Engine остановлен")
    
    def stop(self):
        """Остановка движка"""
        self.running = False
        logger.info("Запрошена остановка Price Feed Engine")
    
    async def get_latest_prices(self, symbols: Optional[List[str]] = None) -> Dict[str, PriceData]:
        """Получение последних цен для указанных символов"""
        if symbols is None:
            symbols = self.symbols
        
        latest_prices = {}
        for symbol in symbols:
            if symbol in self.price_buffer and self.price_buffer[symbol]:
                latest_prices[symbol] = self.price_buffer[symbol][-1]
        
        return latest_prices
    
    async def get_candles(self, symbol: str, interval: str, limit: int = 100) -> List[Candle]:
        """Получение свечей из базы данных"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT symbol, interval, open_time, close_time, open_price, high_price, low_price, close_price, volume, trade_count
                FROM candles
                WHERE symbol = ? AND interval = ?
                ORDER BY close_time DESC
                LIMIT ?
            """, (symbol, interval, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            candles = []
            for row in rows:
                candle = Candle(
                    symbol=row[0],
                    interval=row[1],
                    open_time=datetime.fromisoformat(row[2]),
                    close_time=datetime.fromisoformat(row[3]),
                    open_price=row[4],
                    high_price=row[5],
                    low_price=row[6],
                    close_price=row[7],
                    volume=row[8],
                    trade_count=row[9]
                )
                candles.append(candle)
            
            return candles
            
        except Exception as e:
            logger.error(f"Ошибка получения свечей: {e}")
            return []

async def main():
    """Основная функция для запуска"""
    engine = PriceFeedEngine()
    
    try:
        await engine.start()
    except KeyboardInterrupt:
        engine.stop()

if __name__ == "__main__":
    asyncio.run(main())
