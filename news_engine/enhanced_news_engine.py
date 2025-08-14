"""
GHOST Enhanced News Engine
Асинхронный движок для сбора, анализа и хранения новостей
"""

import asyncio
import aiohttp
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import hashlib
import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
import yaml
import os
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ghost_news_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class NewsItem:
    """Структура новостного элемента"""
    item_type: str  # "news", "tweet", "regulatory"
    source_name: str
    author: Optional[str]
    title: str
    content: Optional[str]
    published_at: datetime
    url: Optional[str]
    external_id: Optional[str]
    influence: float = 0.0
    sentiment: float = 0.0
    urgency: float = 0.0
    source_trust: float = 0.5
    source_type: str = "unknown"
    category: Optional[str] = None
    keywords: Optional[List[str]] = None
    entities: Optional[List[str]] = None
    summary: Optional[str] = None
    is_important: bool = False
    priority_level: int = 1

class NewsEngineConfig:
    """Конфигурация News Engine"""
    
    def __init__(self, config_path: str = "news_engine_config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """Загрузка конфигурации"""
        default_config = {
            "database": {
                "path": "ghost_news.db",
                "type": "sqlite"
            },
            "sources": {
                "newsapi": {
                    "enabled": True,
                    "api_key": "",
                    "base_url": "https://newsapi.org/v2",
                    "keywords": ["crypto", "bitcoin", "ethereum", "blockchain"],
                    "interval": 60
                },
                "twitter": {
                    "enabled": False,
                    "bearer_token": "",
                    "keywords": ["#crypto", "#bitcoin", "#ethereum"],
                    "interval": 30
                },
                "cryptocompare": {
                    "enabled": True,
                    "api_key": "",
                    "base_url": "https://min-api.cryptocompare.com/data",
                    "interval": 120
                }
            },
            "trust_scores": {
                "Reuters": 0.95,
                "Bloomberg": 0.90,
                "CoinTelegraph": 0.7,
                "CoinDesk": 0.8,
                "CryptoNews": 0.6,
                "*": 0.5
            },
            "influence": {
                "tweet": {
                    "weight_followers": 0.6,
                    "weight_retweets": 0.3,
                    "weight_likes": 0.1
                },
                "news": {
                    "base_influence": {
                        "Reuters": 0.9,
                        "Bloomberg": 0.9,
                        "CoinTelegraph": 0.7,
                        "UnknownBlog": 0.4
                    }
                }
            },
            "sentiment": {
                "method": "vader",
                "thresholds": {
                    "positive": 0.1,
                    "negative": -0.1
                }
            },
            "urgency": {
                "decay_hours": 24,
                "instant_keywords": ["BREAKING", "URGENT", "CRASH", "EXPLOSION"]
            },
            "processing": {
                "batch_size": 50,
                "max_retries": 3,
                "timeout": 10
            }
        }
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                # Рекурсивное слияние конфигураций
                return self._merge_configs(default_config, user_config)
        return default_config
    
    def _merge_configs(self, default: Dict, user: Dict) -> Dict:
        """Рекурсивное слияние конфигураций"""
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result

class SentimentAnalyzer:
    """Анализатор настроения"""
    
    def __init__(self, method: str = "vader"):
        self.method = method
        if method == "vader":
            try:
                nltk.download('vader_lexicon', quiet=True)
                self.analyzer = SentimentIntensityAnalyzer()
            except Exception as e:
                logger.error(f"Ошибка инициализации VADER: {e}")
                self.analyzer = None
    
    def analyze(self, text: str) -> float:
        """Анализ настроения текста"""
        if not text or not self.analyzer:
            return 0.0
        
        try:
            scores = self.analyzer.polarity_scores(text)
            return scores["compound"]  # -1 до 1
        except Exception as e:
            logger.error(f"Ошибка анализа настроения: {e}")
            return 0.0

class NewsDatabase:
    """Работа с базой данных новостей"""
    
    def __init__(self, db_path: str):
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
                    item_type TEXT NOT NULL,
                    source_name TEXT,
                    author TEXT,
                    title TEXT,
                    content TEXT,
                    published_at TIMESTAMP,
                    url TEXT,
                    external_id TEXT,
                    influence REAL DEFAULT 0.0,
                    sentiment REAL DEFAULT 0.0,
                    urgency REAL DEFAULT 0.0,
                    source_trust REAL DEFAULT 0.5,
                    source_type TEXT DEFAULT 'unknown',
                    category TEXT,
                    keywords TEXT,
                    entities TEXT,
                    summary TEXT,
                    is_important BOOLEAN DEFAULT FALSE,
                    priority_level INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    content_hash TEXT,
                    UNIQUE(item_type, external_id, source_name, title, published_at)
                )
            """)
            
            # Создание индексов
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_published_at ON news_items(published_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_name ON news_items(source_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sentiment ON news_items(sentiment)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_influence ON news_items(influence)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_urgency ON news_items(urgency)")
            
            # Таблица доверия к источникам
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS source_trust (
                    source_name TEXT PRIMARY KEY,
                    trust_score REAL DEFAULT 0.5,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def save_items(self, items: List[NewsItem]) -> int:
        """Сохранение новостных элементов"""
        if not items:
            return 0
        
        saved_count = 0
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for item in items:
                try:
                    # Создание хэша контента для дубликатов
                    content_hash = self._create_content_hash(item)
                    
                    cursor.execute("""
                        INSERT OR IGNORE INTO news_items(
                            item_type, source_name, author, title, content, 
                            published_at, url, external_id, influence, sentiment,
                            urgency, source_trust, source_type, category,
                            keywords, entities, summary, is_important, 
                            priority_level, content_hash
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        item.item_type, item.source_name, item.author, item.title,
                        item.content, item.published_at.isoformat(), item.url,
                        item.external_id, item.influence, item.sentiment,
                        item.urgency, item.source_trust, item.source_type,
                        item.category, json.dumps(item.keywords) if item.keywords else None,
                        json.dumps(item.entities) if item.entities else None,
                        item.summary, item.is_important, item.priority_level,
                        content_hash
                    ))
                    
                    if cursor.rowcount > 0:
                        saved_count += 1
                        
                except Exception as e:
                    logger.error(f"Ошибка сохранения элемента {item.title[:50]}: {e}")
            
            conn.commit()
        
        return saved_count
    
    def _create_content_hash(self, item: NewsItem) -> str:
        """Создание хэша контента для проверки дубликатов"""
        content = f"{item.title}{item.content or ''}{item.source_name}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get_recent_news(self, minutes: int = 15, limit: int = 100) -> List[Dict]:
        """Получение недавних новостей"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM news_items 
                WHERE published_at >= datetime('now', '-{} minutes')
                ORDER BY published_at DESC
                LIMIT ?
            """.format(minutes), (limit,))
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

class NewsProcessor:
    """Обработчик новостей"""
    
    def __init__(self, config: NewsEngineConfig):
        self.config = config
        self.sentiment_analyzer = SentimentAnalyzer(config.config["sentiment"]["method"])
    
    def process_item(self, item: NewsItem) -> NewsItem:
        """Обработка одного новостного элемента"""
        # 1. Расчет доверия к источнику
        item.source_trust = self._calculate_source_trust(item.source_name)
        
        # 2. Анализ настроения
        text_for_sentiment = f"{item.title} {item.content or ''}"
        item.sentiment = self.sentiment_analyzer.analyze(text_for_sentiment)
        
        # 3. Расчет влияния
        item.influence = self._calculate_influence(item)
        
        # 4. Расчет срочности
        item.urgency = self._calculate_urgency(item)
        
        # 5. Определение важности
        item.is_important = self._is_important(item)
        
        # 6. Определение приоритета
        item.priority_level = self._calculate_priority(item)
        
        return item
    
    def _calculate_source_trust(self, source_name: str) -> float:
        """Расчет доверия к источнику"""
        trust_scores = self.config.config["trust_scores"]
        return trust_scores.get(source_name, trust_scores.get("*", 0.5))
    
    def _calculate_influence(self, item: NewsItem) -> float:
        """Расчет влияния"""
        if item.item_type == "tweet":
            # Для твитов используем статистику (если доступна)
            return min(1.0, item.source_trust * 0.8)
        else:
            # Для новостей используем базовое влияние источника
            base_influence = self.config.config["influence"]["news"]["base_influence"]
            return base_influence.get(item.source_name, 0.5)
    
    def _calculate_urgency(self, item: NewsItem) -> float:
        """Расчет срочности"""
        now = datetime.now()
        age_hours = (now - item.published_at).total_seconds() / 3600
        decay_hours = self.config.config["urgency"]["decay_hours"]
        
        # Базовая срочность по времени
        urgency = max(0.0, 1.0 - age_hours / decay_hours)
        
        # Проверка ключевых слов срочности
        instant_keywords = self.config.config["urgency"]["instant_keywords"]
        title_upper = item.title.upper()
        for keyword in instant_keywords:
            if keyword in title_upper:
                urgency = max(urgency, 0.9)
                break
        
        return urgency
    
    def _is_important(self, item: NewsItem) -> bool:
        """Определение важности новости"""
        return (item.influence > 0.7 or 
                abs(item.sentiment) > 0.5 or 
                item.urgency > 0.8 or
                item.source_trust > 0.8)
    
    def _calculate_priority(self, item: NewsItem) -> int:
        """Расчет приоритета"""
        priority = 1
        
        if item.is_important:
            priority += 2
        if item.urgency > 0.8:
            priority += 1
        if abs(item.sentiment) > 0.7:
            priority += 1
        if item.source_trust > 0.9:
            priority += 1
        
        return min(priority, 5)

class NewsAPIClient:
    """Клиент для работы с NewsAPI"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.base_url = config["base_url"]
        self.api_key = config["api_key"]
        self.keywords = config["keywords"]
    
    async def fetch_news(self, session: aiohttp.ClientSession) -> List[NewsItem]:
        """Получение новостей из NewsAPI"""
        if not self.api_key:
            logger.warning("NewsAPI ключ не настроен")
            return []
        
        items = []
        for keyword in self.keywords:
            try:
                url = f"{self.base_url}/everything"
                params = {
                    "q": keyword,
                    "apiKey": self.api_key,
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": 20
                }
                
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        articles = data.get("articles", [])
                        
                        for article in articles:
                            item = NewsItem(
                                item_type="news",
                                source_name=article.get("source", {}).get("name", "Unknown"),
                                author=article.get("author"),
                                title=article.get("title", ""),
                                content=article.get("description", ""),
                                published_at=datetime.fromisoformat(article.get("publishedAt", "").replace("Z", "+00:00")),
                                url=article.get("url"),
                                external_id=article.get("url"),  # Используем URL как внешний ID
                                source_type="media"
                            )
                            items.append(item)
                    else:
                        logger.error(f"NewsAPI ошибка: {response.status}")
                        
            except Exception as e:
                logger.error(f"Ошибка получения новостей для {keyword}: {e}")
        
        return items

class CryptoCompareClient:
    """Клиент для работы с CryptoCompare"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.base_url = config["base_url"]
        self.api_key = config.get("api_key", "")
    
    async def fetch_news(self, session: aiohttp.ClientSession) -> List[NewsItem]:
        """Получение новостей из CryptoCompare"""
        items = []
        
        try:
            url = f"{self.base_url}/news/"
            headers = {"authorization": f"Apikey {self.api_key}"} if self.api_key else {}
            
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    news_list = data.get("Data", [])
                    
                    for news in news_list:
                        item = NewsItem(
                            item_type="news",
                            source_name=news.get("source", "CryptoCompare"),
                            author=news.get("author", ""),
                            title=news.get("title", ""),
                            content=news.get("body", ""),
                            published_at=datetime.fromtimestamp(news.get("published_on", 0)),
                            url=news.get("url"),
                            external_id=str(news.get("id")),
                            source_type="crypto_media"
                        )
                        items.append(item)
                else:
                    logger.error(f"CryptoCompare ошибка: {response.status}")
                    
        except Exception as e:
            logger.error(f"Ошибка получения новостей из CryptoCompare: {e}")
        
        return items

class EnhancedNewsEngine:
    """Улучшенный News Engine"""
    
    def __init__(self, config_path: str = "news_engine_config.yaml"):
        self.config = NewsEngineConfig(config_path)
        self.db = NewsDatabase(self.config.config["database"]["path"])
        self.processor = NewsProcessor(self.config)
        
        # Инициализация клиентов
        self.clients = {}
        if self.config.config["sources"]["newsapi"]["enabled"]:
            self.clients["newsapi"] = NewsAPIClient(self.config.config["sources"]["newsapi"])
        if self.config.config["sources"]["cryptocompare"]["enabled"]:
            self.clients["cryptocompare"] = CryptoCompareClient(self.config.config["sources"]["cryptocompare"])
    
    async def run(self):
        """Основной цикл работы"""
        logger.info("🚀 Запуск GHOST Enhanced News Engine")
        
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    # Параллельный сбор данных
                    tasks = []
                    for name, client in self.clients.items():
                        tasks.append(self._fetch_with_retry(session, client))
                    
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Обработка результатов
                    all_items = []
                    for result in results:
                        if isinstance(result, Exception):
                            logger.error(f"Ошибка сбора данных: {result}")
                        else:
                            all_items.extend(result)
                    
                    if all_items:
                        # Обработка и сохранение
                        processed_items = [self.processor.process_item(item) for item in all_items]
                        saved_count = self.db.save_items(processed_items)
                        
                        logger.info(f"💾 Сохранено {saved_count} новых новостей из {len(all_items)} полученных")
                        
                        # Проверка важных новостей
                        important_news = [item for item in processed_items if item.is_important]
                        if important_news:
                            logger.warning(f"🚨 Обнаружено {len(important_news)} важных новостей!")
                            for news in important_news[:3]:  # Показываем первые 3
                                logger.warning(f"  - {news.title[:100]}... (влияние: {news.influence:.2f}, настроение: {news.sentiment:.2f})")
                    
                    # Пауза перед следующим циклом
                    await asyncio.sleep(60)
                    
                except Exception as e:
                    logger.error(f"Критическая ошибка в цикле: {e}")
                    await asyncio.sleep(30)  # Короткая пауза при ошибке
    
    async def _fetch_with_retry(self, session: aiohttp.ClientSession, client) -> List[NewsItem]:
        """Получение данных с повторными попытками"""
        max_retries = self.config.config["processing"]["max_retries"]
        
        for attempt in range(max_retries):
            try:
                return await client.fetch_news(session)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                logger.warning(f"Попытка {attempt + 1} не удалась, повтор через 5 секунд...")
                await asyncio.sleep(5)
        
        return []

async def main():
    """Главная функция"""
    engine = EnhancedNewsEngine()
    await engine.run()

if __name__ == "__main__":
    asyncio.run(main())
