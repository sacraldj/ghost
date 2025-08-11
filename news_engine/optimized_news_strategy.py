#!/usr/bin/env python3
"""
GHOST Optimized News Strategy
Оптимизированная стратегия сбора новостей с разными интервалами
"""

import asyncio
import aiohttp
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import yaml
import time

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NewsSource:
    """Источник новостей с настройками"""
    def __init__(self, name: str, interval: int, priority: int, enabled: bool = True):
        self.name = name
        self.interval = interval  # секунды
        self.priority = priority  # 1-5 (1 - высший)
        self.enabled = enabled
        self.last_check = 0
        self.error_count = 0
        self.max_errors = 3

class OptimizedNewsEngine:
    """Оптимизированный News Engine с разными интервалами"""
    
    def __init__(self, db_path: str = "ghost_news.db"):
        self.db_path = db_path
        self.init_database()
        self.setup_sources()
        
    def setup_sources(self):
        """Настройка источников с разными интервалами"""
        self.sources = {
            # Критические источники (высокая частота)
            "breaking_news": NewsSource("Breaking News", 30, 1),  # 30 сек
            "twitter_important": NewsSource("Twitter Important", 60, 1),  # 1 мин
            
            # Основные источники (средняя частота)
            "reuters": NewsSource("Reuters", 300, 2),  # 5 мин
            "bloomberg": NewsSource("Bloomberg", 300, 2),  # 5 мин
            "cryptonews": NewsSource("CryptoNews", 180, 2),  # 3 мин
            "cointelegraph": NewsSource("CoinTelegraph", 180, 2),  # 3 мин
            
            # Дополнительные источники (низкая частота)
            "reddit_crypto": NewsSource("Reddit Crypto", 600, 3),  # 10 мин
            "regulatory": NewsSource("Regulatory", 900, 3),  # 15 мин
            "analytics": NewsSource("Analytics", 1200, 4),  # 20 мин
            
            # Фоновые источники (очень низкая частота)
            "weekly_reports": NewsSource("Weekly Reports", 3600, 5),  # 1 час
            "monthly_analysis": NewsSource("Monthly Analysis", 86400, 5),  # 1 день
        }
    
    def init_database(self):
        """Инициализация базы данных"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Основная таблица новостей
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS news_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_name TEXT,
                    title TEXT,
                    content TEXT,
                    url TEXT,
                    published_at TIMESTAMP,
                    sentiment REAL DEFAULT 0.0,
                    influence REAL DEFAULT 0.5,
                    urgency REAL DEFAULT 0.0,
                    is_important BOOLEAN DEFAULT FALSE,
                    priority_level INTEGER DEFAULT 3,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица метрик производительности
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS source_metrics (
                    source_name TEXT PRIMARY KEY,
                    last_check TIMESTAMP,
                    success_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    avg_response_time REAL DEFAULT 0.0,
                    last_error TEXT,
                    status TEXT DEFAULT 'active'
                )
            """)
            
            # Индексы для оптимизации
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_published_at ON news_items(published_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_name ON news_items(source_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_priority ON news_items(priority_level)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_important ON news_items(is_important)")
            
            conn.commit()
    
    async def fetch_from_source(self, source: NewsSource) -> List[Dict]:
        """Получение новостей из конкретного источника"""
        try:
            start_time = time.time()
            
            # Имитация запроса к API
            await asyncio.sleep(0.1)  # Имитация сетевого запроса
            
            # Генерируем тестовые новости в зависимости от источника
            news_items = self.generate_test_news(source.name)
            
            response_time = time.time() - start_time
            
            # Обновляем метрики
            self.update_source_metrics(source.name, True, response_time)
            
            return news_items
            
        except Exception as e:
            logger.error(f"Ошибка получения новостей из {source.name}: {e}")
            self.update_source_metrics(source.name, False, 0, str(e))
            return []
    
    def generate_test_news(self, source_name: str) -> List[Dict]:
        """Генерация тестовых новостей для разных источников"""
        base_news = {
            "reuters": [
                {"title": "Bitcoin ETF approval boosts institutional adoption", "sentiment": 0.8, "urgency": 0.9},
                {"title": "Ethereum upgrade improves scalability", "sentiment": 0.6, "urgency": 0.7},
            ],
            "bloomberg": [
                {"title": "Major banks announce crypto services", "sentiment": 0.7, "urgency": 0.8},
                {"title": "Regulatory clarity expected soon", "sentiment": 0.5, "urgency": 0.6},
            ],
            "breaking_news": [
                {"title": "BREAKING: Bitcoin reaches new all-time high!", "sentiment": 0.9, "urgency": 1.0},
                {"title": "URGENT: Major exchange hack reported", "sentiment": -0.8, "urgency": 1.0},
            ],
            "twitter_important": [
                {"title": "Elon Musk tweets about Bitcoin adoption", "sentiment": 0.7, "urgency": 0.8},
                {"title": "Vitalik comments on Ethereum future", "sentiment": 0.6, "urgency": 0.7},
            ]
        }
        
        news = base_news.get(source_name, [
            {"title": f"News from {source_name}", "sentiment": 0.0, "urgency": 0.5}
        ])
        
        return [
            {
                "source": source_name,
                "title": item["title"],
                "content": f"Content for {item['title']}",
                "url": f"https://{source_name.lower()}.com/news",
                "sentiment": item["sentiment"],
                "urgency": item["urgency"],
                "published_at": datetime.now().isoformat()
            }
            for item in news
        ]
    
    def update_source_metrics(self, source_name: str, success: bool, response_time: float, error: str = None):
        """Обновление метрик источника"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if success:
                cursor.execute("""
                    INSERT OR REPLACE INTO source_metrics 
                    (source_name, last_check, success_count, avg_response_time, status)
                    VALUES (?, ?, 
                        COALESCE((SELECT success_count FROM source_metrics WHERE source_name = ?), 0) + 1,
                        COALESCE((SELECT avg_response_time FROM source_metrics WHERE source_name = ?), 0) * 0.9 + ? * 0.1,
                        'active'
                    )
                """, (source_name, datetime.now().isoformat(), source_name, source_name, response_time))
            else:
                cursor.execute("""
                    INSERT OR REPLACE INTO source_metrics 
                    (source_name, last_check, error_count, last_error, status)
                    VALUES (?, ?, 
                        COALESCE((SELECT error_count FROM source_metrics WHERE source_name = ?), 0) + 1,
                        ?
                    )
                """, (source_name, datetime.now().isoformat(), source_name, error))
            
            conn.commit()
    
    def save_news(self, items: List[Dict]) -> int:
        """Сохранение новостей с оптимизацией"""
        if not items:
            return 0
        
        saved_count = 0
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for item in items:
                try:
                    # Проверяем дубликаты по заголовку и источнику
                    cursor.execute("""
                        SELECT id FROM news_items 
                        WHERE source_name = ? AND title = ? 
                        AND published_at > datetime('now', '-1 hour')
                    """, (item["source"], item["title"]))
                    
                    if cursor.fetchone():
                        continue  # Пропускаем дубликаты
                    
                    # Определяем важность
                    is_important = (
                        item["sentiment"] > 0.7 or 
                        item["sentiment"] < -0.7 or 
                        item["urgency"] > 0.8 or
                        "BREAKING" in item["title"] or
                        "URGENT" in item["title"]
                    )
                    
                    cursor.execute("""
                        INSERT INTO news_items(
                            source_name, title, content, url, published_at,
                            sentiment, urgency, is_important, priority_level
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        item["source"], item["title"], item["content"], 
                        item["url"], item["published_at"], item["sentiment"],
                        item["urgency"], is_important, 
                        1 if is_important else 3
                    ))
                    
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(f"Ошибка сохранения новости: {e}")
            
            conn.commit()
        
        return saved_count
    
    async def run_optimized(self):
        """Оптимизированный основной цикл"""
        logger.info("🚀 Запуск GHOST Optimized News Engine")
        
        while True:
            try:
                current_time = time.time()
                tasks = []
                
                # Проверяем каждый источник по его интервалу
                for source_name, source in self.sources.items():
                    if not source.enabled:
                        continue
                    
                    # Проверяем, нужно ли обновлять этот источник
                    if current_time - source.last_check >= source.interval:
                        tasks.append(self.fetch_from_source(source))
                        source.last_check = current_time
                
                if tasks:
                    # Параллельно получаем новости из всех готовых источников
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    all_items = []
                    for result in results:
                        if isinstance(result, Exception):
                            logger.error(f"Ошибка сбора данных: {result}")
                        else:
                            all_items.extend(result)
                    
                    if all_items:
                        saved_count = self.save_news(all_items)
                        logger.info(f"💾 Сохранено {saved_count} новых новостей")
                        
                        # Проверяем важные новости
                        important_count = sum(1 for item in all_items if item.get("is_important", False))
                        if important_count > 0:
                            logger.warning(f"🚨 Обнаружено {important_count} важных новостей!")
                
                # Адаптивная пауза (1-5 секунд в зависимости от нагрузки)
                pause = min(5, max(1, len(tasks) * 0.5))
                await asyncio.sleep(pause)
                
            except Exception as e:
                logger.error(f"Критическая ошибка в цикле: {e}")
                await asyncio.sleep(10)

async def main():
    """Главная функция"""
    engine = OptimizedNewsEngine()
    await engine.run_optimized()

if __name__ == "__main__":
    asyncio.run(main())
