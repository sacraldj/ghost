#!/usr/bin/env python3
"""
GHOST Critical News Engine
Сверхбыстрый сбор критически важных новостей каждую секунду
"""

import asyncio
import aiohttp
import sqlite3
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('critical_news_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CriticalNewsItem:
    """Критически важная новость"""
    def __init__(self, source: str, title: str, content: str = "", url: str = ""):
        self.source = source
        self.title = title
        self.content = content
        self.url = url
        self.published_at = datetime.now()
        self.sentiment = 0.0
        self.urgency = 1.0  # Максимальная срочность
        self.is_critical = True
        self.priority = 1  # Высший приоритет

class CriticalNewsEngine:
    """Сверхбыстрый News Engine для критических новостей"""
    
    def __init__(self, db_path: str = "ghost_news.db"):
        self.db_path = db_path
        self.init_database()
        self.setup_critical_sources()
        self.last_critical_alert = 0
        
    def setup_critical_sources(self):
        """Настройка критически важных источников"""
        self.critical_sources = {
            # Рыночные данные (каждую секунду)
            "binance_price": {
                "name": "Binance Price",
                "interval": 1,  # 1 секунда
                "url": "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",
                "type": "price"
            },
            "coinbase_price": {
                "name": "Coinbase Price", 
                "interval": 1,
                "url": "https://api.coinbase.com/v2/prices/BTC-USD/spot",
                "type": "price"
            },
            "breaking_news": {
                "name": "Breaking News",
                "interval": 1,
                "url": "https://api.newsapi.org/v2/everything?q=crypto&sortBy=publishedAt&apiKey=test",
                "type": "news"
            },
            "twitter_critical": {
                "name": "Twitter Critical",
                "interval": 1,
                "url": "https://api.twitter.com/2/tweets/search/recent?query=crypto",
                "type": "social"
            },
            "regulatory_alerts": {
                "name": "Regulatory Alerts",
                "interval": 1,
                "url": "https://api.sec.gov/news/pressreleases",
                "type": "regulatory"
            }
        }
        
        self.last_check = {name: 0 for name in self.critical_sources.keys()}
    
    def init_database(self):
        """Инициализация базы данных для критических новостей"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Таблица критических новостей
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS critical_news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_name TEXT,
                    title TEXT,
                    content TEXT,
                    url TEXT,
                    published_at TIMESTAMP,
                    sentiment REAL DEFAULT 0.0,
                    urgency REAL DEFAULT 1.0,
                    is_critical BOOLEAN DEFAULT TRUE,
                    priority INTEGER DEFAULT 1,
                    market_impact REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица рыночных данных
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    price REAL,
                    change_24h REAL,
                    volume REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица критических алертов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS critical_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_type TEXT,
                    message TEXT,
                    severity INTEGER DEFAULT 1,
                    is_processed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Индексы для быстрого поиска
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_critical_timestamp ON critical_news(published_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_critical_source ON critical_news(source_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_symbol ON market_data(symbol)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_timestamp ON market_data(timestamp)")
            
            conn.commit()
    
    async def fetch_critical_data(self, source_name: str, source_config: Dict) -> List[CriticalNewsItem]:
        """Получение критических данных из источника"""
        try:
            start_time = time.time()
            
            # Имитация сверхбыстрого запроса
            await asyncio.sleep(0.01)  # 10ms имитация
            
            items = []
            
            if source_config["type"] == "price":
                # Рыночные данные
                items = self.generate_market_data(source_name)
            elif source_config["type"] == "news":
                # Критические новости
                items = self.generate_critical_news(source_name)
            elif source_config["type"] == "social":
                # Социальные медиа
                items = self.generate_social_alerts(source_name)
            elif source_config["type"] == "regulatory":
                # Регулятивные алерты
                items = self.generate_regulatory_alerts(source_name)
            
            response_time = time.time() - start_time
            logger.info(f"⚡ {source_name}: {len(items)} items in {response_time:.3f}s")
            
            return items
            
        except Exception as e:
            logger.error(f"❌ Ошибка {source_name}: {e}")
            return []
    
    def generate_market_data(self, source_name: str) -> List[CriticalNewsItem]:
        """Генерация рыночных данных"""
        import random
        
        symbols = ["BTC", "ETH", "BNB", "ADA", "SOL"]
        items = []
        
        for symbol in symbols:
            # Имитация изменения цены
            base_price = {
                "BTC": 43250,
                "ETH": 2650,
                "BNB": 320,
                "ADA": 0.45,
                "SOL": 95
            }
            
            price_change = random.uniform(-0.05, 0.05)  # ±5%
            current_price = base_price[symbol] * (1 + price_change)
            
            # Определяем критичность изменения
            is_critical = abs(price_change) > 0.02  # >2% изменение
            
            if is_critical:
                item = CriticalNewsItem(
                    source=source_name,
                    title=f"🚨 {symbol} price {'📈' if price_change > 0 else '📉'} {price_change:.2%}",
                    content=f"{symbol} price changed by {price_change:.2%} to ${current_price:.2f}",
                    url=f"https://{source_name.lower()}.com/{symbol}"
                )
                item.sentiment = 0.8 if price_change > 0 else -0.8
                items.append(item)
        
        return items
    
    def generate_critical_news(self, source_name: str) -> List[CriticalNewsItem]:
        """Генерация критических новостей"""
        critical_news = [
            {
                "title": "🚨 BREAKING: Bitcoin reaches new all-time high!",
                "content": "Bitcoin has reached a new all-time high as institutional adoption accelerates.",
                "sentiment": 0.9
            },
            {
                "title": "⚠️ URGENT: Major exchange hack reported",
                "content": "A major cryptocurrency exchange has reported a security breach.",
                "sentiment": -0.8
            },
            {
                "title": "⚡ FLASH: SEC approves Bitcoin ETF",
                "content": "The Securities and Exchange Commission has approved the first Bitcoin ETF.",
                "sentiment": 0.9
            },
            {
                "title": "🔥 CRITICAL: Ethereum gas fees spike 500%",
                "content": "Ethereum network congestion causes gas fees to spike dramatically.",
                "sentiment": -0.6
            }
        ]
        
        # Выбираем случайную критическую новость
        import random
        news = random.choice(critical_news)
        
        item = CriticalNewsItem(
            source=source_name,
            title=news["title"],
            content=news["content"],
            url=f"https://{source_name.lower()}.com/breaking"
        )
        item.sentiment = news["sentiment"]
        
        return [item] if random.random() < 0.1 else []  # 10% вероятность
    
    def generate_social_alerts(self, source_name: str) -> List[CriticalNewsItem]:
        """Генерация социальных алертов"""
        social_alerts = [
            {
                "title": "🐋 Elon Musk tweets about Bitcoin",
                "content": "Elon Musk just tweeted about Bitcoin adoption.",
                "sentiment": 0.7
            },
            {
                "title": "👑 Vitalik comments on Ethereum",
                "content": "Vitalik Buterin made important comments about Ethereum's future.",
                "sentiment": 0.6
            }
        ]
        
        import random
        if random.random() < 0.05:  # 5% вероятность
            alert = random.choice(social_alerts)
            item = CriticalNewsItem(
                source=source_name,
                title=alert["title"],
                content=alert["content"],
                url=f"https://twitter.com/crypto"
            )
            item.sentiment = alert["sentiment"]
            return [item]
        
        return []
    
    def generate_regulatory_alerts(self, source_name: str) -> List[CriticalNewsItem]:
        """Генерация регулятивных алертов"""
        regulatory_alerts = [
            {
                "title": "🏛️ SEC announces new crypto regulations",
                "content": "The SEC has announced new cryptocurrency regulations.",
                "sentiment": -0.3
            },
            {
                "title": "⚖️ CFTC files charges against crypto firm",
                "content": "The CFTC has filed charges against a major cryptocurrency firm.",
                "sentiment": -0.5
            }
        ]
        
        import random
        if random.random() < 0.02:  # 2% вероятность
            alert = random.choice(regulatory_alerts)
            item = CriticalNewsItem(
                source=source_name,
                title=alert["title"],
                content=alert["content"],
                url=f"https://sec.gov/news"
            )
            item.sentiment = alert["sentiment"]
            return [item]
        
        return []
    
    def save_critical_news(self, items: List[CriticalNewsItem]) -> int:
        """Сохранение критических новостей"""
        if not items:
            return 0
        
        saved_count = 0
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for item in items:
                try:
                    cursor.execute("""
                        INSERT INTO critical_news(
                            source_name, title, content, url, published_at,
                            sentiment, urgency, is_critical, priority
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        item.source, item.title, item.content, item.url,
                        item.published_at.isoformat(), item.sentiment,
                        item.urgency, item.is_critical, item.priority
                    ))
                    
                    saved_count += 1
                    
                    # Создаем критический алерт
                    if abs(item.sentiment) > 0.7 or "BREAKING" in item.title or "URGENT" in item.title:
                        cursor.execute("""
                            INSERT INTO critical_alerts(
                                alert_type, message, severity
                            ) VALUES (?, ?, ?)
                        """, (
                            "critical_news",
                            f"{item.source}: {item.title}",
                            1 if "BREAKING" in item.title else 2
                        ))
                    
                except Exception as e:
                    logger.error(f"Ошибка сохранения критической новости: {e}")
            
            conn.commit()
        
        return saved_count
    
    async def run_critical(self):
        """Сверхбыстрый основной цикл"""
        logger.info("🚀 Запуск GHOST Critical News Engine (каждую секунду)")
        
        while True:
            try:
                current_time = time.time()
                tasks = []
                
                # Проверяем каждый критический источник каждую секунду
                for source_name, source_config in self.critical_sources.items():
                    if current_time - self.last_check[source_name] >= source_config["interval"]:
                        tasks.append(self.fetch_critical_data(source_name, source_config))
                        self.last_check[source_name] = current_time
                
                if tasks:
                    # Параллельно получаем все критические данные
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    all_items = []
                    for result in results:
                        if isinstance(result, Exception):
                            logger.error(f"Ошибка сбора критических данных: {result}")
                        else:
                            all_items.extend(result)
                    
                    if all_items:
                        saved_count = self.save_critical_news(all_items)
                        
                        if saved_count > 0:
                            logger.warning(f"🚨 КРИТИЧЕСКИЕ НОВОСТИ: {saved_count} сохранено!")
                            
                            # Проверяем время последнего алерта
                            if current_time - self.last_critical_alert > 60:  # Не чаще раза в минуту
                                logger.critical("🔥 КРИТИЧЕСКИЙ АЛЕРТ: Важные новости обнаружены!")
                                self.last_critical_alert = current_time
                
                # Сверхбыстрая пауза (100ms)
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Критическая ошибка в цикле: {e}")
                await asyncio.sleep(1)

async def main():
    """Главная функция"""
    engine = CriticalNewsEngine()
    await engine.run_critical()

if __name__ == "__main__":
    asyncio.run(main())
