#!/usr/bin/env python3
"""
GHOST Simple News Engine
Упрощенная версия для тестирования
"""

import asyncio
import aiohttp
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import yaml
import os
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleNewsItem:
    """Упрощенная структура новостного элемента"""
    def __init__(self, source: str, title: str, content: str = "", url: str = ""):
        self.source = source
        self.title = title
        self.content = content
        self.url = url
        self.published_at = datetime.now()
        self.sentiment = 0.0  # Простой анализ настроения
        self.influence = 0.5
        self.is_important = False

class SimpleNewsEngine:
    """Упрощенный News Engine"""
    
    def __init__(self, db_path: str = "ghost_news.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Создание таблицы новостей
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
                    is_important BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Создание индексов
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_published_at ON news_items(published_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_name ON news_items(source_name)")
            
            conn.commit()
    
    def simple_sentiment_analysis(self, text: str) -> float:
        """Простой анализ настроения"""
        text_lower = text.lower()
        
        positive_words = ['bullish', 'surge', 'rally', 'gain', 'profit', 'growth', 'positive', 'good', 'up']
        negative_words = ['bearish', 'crash', 'drop', 'loss', 'decline', 'sell-off', 'negative', 'bad', 'down']
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 0.5 + (positive_count - negative_count) * 0.1
        elif negative_count > positive_count:
            return -0.5 - (negative_count - positive_count) * 0.1
        else:
            return 0.0
    
    async def fetch_crypto_news(self) -> List[SimpleNewsItem]:
        """Получение крипто новостей"""
        items = []
        
        # Тестовые новости
        test_news = [
            {
                "source": "CoinTelegraph",
                "title": "Bitcoin reaches new all-time high as institutional adoption grows",
                "content": "Bitcoin has reached a new all-time high as institutional adoption continues to grow. Major financial institutions are increasingly investing in cryptocurrency.",
                "url": "https://cointelegraph.com/news/bitcoin-ath"
            },
            {
                "source": "Reuters",
                "title": "Ethereum upgrade boosts DeFi ecosystem development",
                "content": "The latest Ethereum upgrade has significantly boosted the DeFi ecosystem development. New features enable better scalability and lower fees.",
                "url": "https://reuters.com/ethereum-upgrade"
            },
            {
                "source": "CryptoNews",
                "title": "Market shows mixed signals as regulatory uncertainty persists",
                "content": "The crypto market is showing mixed signals as regulatory uncertainty continues to affect investor confidence. Analysts expect clarity soon.",
                "url": "https://cryptonews.com/market-signals"
            },
            {
                "source": "Bloomberg",
                "title": "Major banks announce crypto custody services",
                "content": "Several major banks have announced new cryptocurrency custody services, signaling growing institutional acceptance of digital assets.",
                "url": "https://bloomberg.com/banks-crypto"
            },
            {
                "source": "CoinDesk",
                "title": "DeFi protocols see record-breaking TVL growth",
                "content": "Decentralized finance protocols are experiencing record-breaking total value locked (TVL) growth as new yield farming opportunities emerge.",
                "url": "https://coindesk.com/defi-tvl-growth"
            }
        ]
        
        for news in test_news:
            item = SimpleNewsItem(
                source=news["source"],
                title=news["title"],
                content=news["content"],
                url=news["url"]
            )
            
            # Анализ настроения
            item.sentiment = self.simple_sentiment_analysis(news["title"] + " " + news["content"])
            
            # Определение важности
            item.influence = 0.8 if news["source"] in ["Reuters", "Bloomberg"] else 0.6
            item.is_important = abs(item.sentiment) > 0.3 or item.influence > 0.7
            
            items.append(item)
        
        return items
    
    def save_news(self, items: List[SimpleNewsItem]) -> int:
        """Сохранение новостей в базу данных"""
        if not items:
            return 0
        
        saved_count = 0
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for item in items:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO news_items(
                            source_name, title, content, url, published_at,
                            sentiment, influence, is_important
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        item.source, item.title, item.content, item.url,
                        item.published_at.isoformat(), item.sentiment,
                        item.influence, item.is_important
                    ))
                    
                    if cursor.rowcount > 0:
                        saved_count += 1
                        
                except Exception as e:
                    logger.error(f"Ошибка сохранения новости {item.title[:50]}: {e}")
            
            conn.commit()
        
        return saved_count
    
    async def run(self):
        """Основной цикл работы"""
        logger.info("🚀 Запуск GHOST Simple News Engine")
        
        while True:
            try:
                # Получение новостей
                news_items = await self.fetch_crypto_news()
                
                if news_items:
                    # Сохранение в базу данных
                    saved_count = self.save_news(news_items)
                    
                    logger.info(f"💾 Сохранено {saved_count} новых новостей")
                    
                    # Проверка важных новостей
                    important_news = [item for item in news_items if item.is_important]
                    if important_news:
                        logger.warning(f"🚨 Обнаружено {len(important_news)} важных новостей!")
                        for news in important_news[:3]:
                            logger.warning(f"  - {news.title[:100]}... (настроение: {news.sentiment:.2f})")
                
                # Пауза перед следующим циклом (5 минут)
                logger.info("⏳ Ожидание 5 минут до следующего сбора...")
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Ошибка в цикле: {e}")
                await asyncio.sleep(60)  # Короткая пауза при ошибке

async def main():
    """Главная функция"""
    engine = SimpleNewsEngine()
    await engine.run()

if __name__ == "__main__":
    asyncio.run(main())
