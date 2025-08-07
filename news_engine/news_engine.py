"""
GHOST News Engine - Главный движок
Объединяет все компоненты для сбора, анализа и обработки новостей
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import sqlite3
import os

from news_sources import NewsSources
from news_apis import NewsAggregator, NewsItem
from influence_analyzer import InfluenceAnalyzer, InfluenceScore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ProcessedNews:
    """Обработанная новость с полным анализом"""
    id: str
    title: str
    content: str
    url: str
    source: str
    published_at: datetime
    category: str
    influence_score: float
    market_impact: float
    sentiment_score: float
    urgency_score: float
    reach_score: float
    credibility_score: float
    keywords: List[str]
    entities: List[str]
    summary: str
    processed_at: datetime
    is_important: bool
    priority_level: int

class NewsEngine:
    """Главный движок новостей GHOST"""
    
    def __init__(self, db_path: str = "news_engine.db"):
        self.db_path = db_path
        self.sources = NewsSources()
        self.aggregator = NewsAggregator()
        self.analyzer = InfluenceAnalyzer()
        self.setup_database()
        
    def setup_database(self):
        """Настройка базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица новостей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news (
                id TEXT PRIMARY KEY,
                title TEXT,
                content TEXT,
                url TEXT,
                source TEXT,
                published_at TIMESTAMP,
                category TEXT,
                influence_score REAL,
                market_impact REAL,
                sentiment_score REAL,
                urgency_score REAL,
                reach_score REAL,
                credibility_score REAL,
                keywords TEXT,
                entities TEXT,
                summary TEXT,
                processed_at TIMESTAMP,
                is_important BOOLEAN,
                priority_level INTEGER
            )
        ''')
        
        # Таблица твитов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tweets (
                id TEXT PRIMARY KEY,
                text TEXT,
                author TEXT,
                created_at TIMESTAMP,
                influence_score REAL,
                sentiment_score REAL,
                keyword_score REAL,
                engagement_score REAL,
                metrics TEXT,
                processed_at TIMESTAMP
            )
        ''')
        
        # Таблица настроений рынка
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_sentiment (
                id TEXT PRIMARY KEY,
                ticker TEXT,
                sentiment_score REAL,
                news_count INTEGER,
                positive_count INTEGER,
                negative_count INTEGER,
                neutral_count INTEGER,
                timestamp TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def collect_news(self, query: str = "cryptocurrency OR bitcoin OR ethereum") -> List[NewsItem]:
        """Собрать новости из всех источников"""
        logger.info("Начинаем сбор новостей...")
        
        try:
            # Получаем новости из всех API
            news_items = await self.aggregator.fetch_all_news(query)
            logger.info(f"Собрано {len(news_items)} новостей")
            
            return news_items
            
        except Exception as e:
            logger.error(f"Ошибка при сборе новостей: {e}")
            return []
    
    async def collect_influential_tweets(self) -> List[Dict]:
        """Собрать твиты влиятельных лиц"""
        logger.info("Начинаем сбор твитов влиятельных лиц...")
        
        try:
            # Получаем список влиятельных лиц
            influential_people = self.sources.get_influential_people()
            usernames = [person['twitter'].replace('@', '') for person in influential_people.values()]
            
            # Получаем твиты
            tweets = await self.aggregator.fetch_influential_tweets(usernames)
            logger.info(f"Собрано {len(tweets)} твитов")
            
            return tweets
            
        except Exception as e:
            logger.error(f"Ошибка при сборе твитов: {e}")
            return []
    
    async def collect_market_sentiment(self, tickers: List[str] = None) -> List[Dict]:
        """Собрать данные о настроениях рынка"""
        logger.info("Начинаем сбор данных о настроениях рынка...")
        
        try:
            if tickers is None:
                tickers = ["BTC", "ETH", "BNB", "SOL", "ADA"]
            
            sentiment_data = await self.aggregator.fetch_market_sentiment(tickers)
            logger.info(f"Собрано {len(sentiment_data)} записей настроений")
            
            return sentiment_data
            
        except Exception as e:
            logger.error(f"Ошибка при сборе настроений: {e}")
            return []
    
    def analyze_news_influence(self, news_items: List[NewsItem]) -> List[ProcessedNews]:
        """Анализировать влияние новостей"""
        logger.info("Начинаем анализ влияния новостей...")
        
        processed_news = []
        
        for news_item in news_items:
            try:
                # Конвертируем в словарь для анализа
                news_dict = {
                    'title': news_item.title,
                    'content': news_item.content,
                    'source': news_item.source,
                    'published_at': news_item.published_at
                }
                
                # Анализируем влияние
                influence_score = self.analyzer.analyze_news_influence(news_dict)
                
                # Определяем важность и приоритет
                is_important = influence_score.influence_score > 0.7
                priority_level = self._calculate_priority_level(influence_score)
                
                # Создаем обработанную новость
                processed_news_item = ProcessedNews(
                    id=news_item.url,  # Используем URL как ID
                    title=news_item.title,
                    content=news_item.content,
                    url=news_item.url,
                    source=news_item.source,
                    published_at=news_item.published_at,
                    category=news_item.category,
                    influence_score=influence_score.influence_score,
                    market_impact=influence_score.market_impact,
                    sentiment_score=influence_score.sentiment_score,
                    urgency_score=influence_score.urgency_score,
                    reach_score=influence_score.reach_score,
                    credibility_score=influence_score.credibility_score,
                    keywords=influence_score.keywords,
                    entities=influence_score.entities,
                    summary=influence_score.summary,
                    processed_at=datetime.now(),
                    is_important=is_important,
                    priority_level=priority_level
                )
                
                processed_news.append(processed_news_item)
                
            except Exception as e:
                logger.error(f"Ошибка при анализе новости: {e}")
                continue
        
        logger.info(f"Проанализировано {len(processed_news)} новостей")
        return processed_news
    
    def analyze_tweets_influence(self, tweets: List[Dict]) -> List[Dict]:
        """Анализировать влияние твитов"""
        logger.info("Начинаем анализ влияния твитов...")
        
        analyzed_tweets = []
        
        for tweet in tweets:
            try:
                # Анализируем влияние твита
                tweet_analysis = self.analyzer.analyze_tweet_influence(tweet)
                analyzed_tweets.append(tweet_analysis)
                
            except Exception as e:
                logger.error(f"Ошибка при анализе твита: {e}")
                continue
        
        logger.info(f"Проанализировано {len(analyzed_tweets)} твитов")
        return analyzed_tweets
    
    def _calculate_priority_level(self, influence_score: InfluenceScore) -> int:
        """Рассчитать уровень приоритета новости"""
        base_priority = 1
        
        # Повышаем приоритет для важных новостей
        if influence_score.influence_score > 0.8:
            base_priority += 3
        elif influence_score.influence_score > 0.6:
            base_priority += 2
        elif influence_score.influence_score > 0.4:
            base_priority += 1
        
        # Повышаем приоритет для срочных новостей
        if influence_score.urgency_score > 0.8:
            base_priority += 2
        elif influence_score.urgency_score > 0.6:
            base_priority += 1
        
        # Повышаем приоритет для высоконадежных источников
        if influence_score.credibility_score > 0.9:
            base_priority += 1
        
        return min(base_priority, 10)  # Максимальный приоритет = 10
    
    def save_processed_news(self, processed_news: List[ProcessedNews]):
        """Сохранить обработанные новости в базу данных"""
        logger.info("Сохраняем обработанные новости в базу данных...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for news in processed_news:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO news (
                        id, title, content, url, source, published_at, category,
                        influence_score, market_impact, sentiment_score, urgency_score,
                        reach_score, credibility_score, keywords, entities, summary,
                        processed_at, is_important, priority_level
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    news.id, news.title, news.content, news.url, news.source,
                    news.published_at, news.category, news.influence_score,
                    news.market_impact, news.sentiment_score, news.urgency_score,
                    news.reach_score, news.credibility_score, json.dumps(news.keywords),
                    json.dumps(news.entities), news.summary, news.processed_at,
                    news.is_important, news.priority_level
                ))
                
            except Exception as e:
                logger.error(f"Ошибка при сохранении новости: {e}")
                continue
        
        conn.commit()
        conn.close()
        logger.info(f"Сохранено {len(processed_news)} новостей")
    
    def save_analyzed_tweets(self, analyzed_tweets: List[Dict]):
        """Сохранить проанализированные твиты в базу данных"""
        logger.info("Сохраняем проанализированные твиты в базу данных...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for tweet in analyzed_tweets:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO tweets (
                        id, text, author, created_at, influence_score,
                        sentiment_score, keyword_score, engagement_score,
                        metrics, processed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    tweet['tweet_id'], tweet['text'], tweet['author'],
                    tweet['created_at'], tweet['influence_score'],
                    tweet['sentiment_score'], tweet['keyword_score'],
                    tweet['engagement_score'], json.dumps(tweet['metrics']),
                    datetime.now()
                ))
                
            except Exception as e:
                logger.error(f"Ошибка при сохранении твита: {e}")
                continue
        
        conn.commit()
        conn.close()
        logger.info(f"Сохранено {len(analyzed_tweets)} твитов")
    
    def get_important_news(self, limit: int = 20) -> List[ProcessedNews]:
        """Получить важные новости из базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM news 
            WHERE is_important = 1 
            ORDER BY influence_score DESC, published_at DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        processed_news = []
        for row in rows:
            try:
                news = ProcessedNews(
                    id=row[0], title=row[1], content=row[2], url=row[3],
                    source=row[4], published_at=datetime.fromisoformat(row[5]),
                    category=row[6], influence_score=row[7], market_impact=row[8],
                    sentiment_score=row[9], urgency_score=row[10], reach_score=row[11],
                    credibility_score=row[12], keywords=json.loads(row[13]),
                    entities=json.loads(row[14]), summary=row[15],
                    processed_at=datetime.fromisoformat(row[16]),
                    is_important=bool(row[17]), priority_level=row[18]
                )
                processed_news.append(news)
            except Exception as e:
                logger.error(f"Ошибка при загрузке новости: {e}")
                continue
        
        return processed_news
    
    async def run_full_cycle(self):
        """Запустить полный цикл сбора и анализа новостей"""
        logger.info("Запускаем полный цикл сбора и анализа новостей...")
        
        try:
            # 1. Собираем новости
            news_items = await self.collect_news()
            
            # 2. Анализируем влияние новостей
            processed_news = self.analyze_news_influence(news_items)
            
            # 3. Сохраняем обработанные новости
            self.save_processed_news(processed_news)
            
            # 4. Собираем твиты влиятельных лиц
            tweets = await self.collect_influential_tweets()
            
            # 5. Анализируем влияние твитов
            analyzed_tweets = self.analyze_tweets_influence(tweets)
            
            # 6. Сохраняем проанализированные твиты
            self.save_analyzed_tweets(analyzed_tweets)
            
            # 7. Собираем данные о настроениях рынка
            sentiment_data = await self.collect_market_sentiment()
            
            logger.info("Полный цикл завершен успешно!")
            
            return {
                'news_count': len(processed_news),
                'tweets_count': len(analyzed_tweets),
                'sentiment_count': len(sentiment_data),
                'important_news': len([n for n in processed_news if n.is_important])
            }
            
        except Exception as e:
            logger.error(f"Ошибка в полном цикле: {e}")
            return None

if __name__ == "__main__":
    # Тестирование движка новостей
    async def test_news_engine():
        engine = NewsEngine()
        
        # Запускаем полный цикл
        result = await engine.run_full_cycle()
        
        if result:
            print(f"Результаты работы движка:")
            print(f"- Новостей обработано: {result['news_count']}")
            print(f"- Твитов проанализировано: {result['tweets_count']}")
            print(f"- Важных новостей: {result['important_news']}")
            
            # Получаем важные новости
            important_news = engine.get_important_news(5)
            print(f"\nТоп-5 важных новостей:")
            for i, news in enumerate(important_news, 1):
                print(f"{i}. {news.title}")
                print(f"   Влияние: {news.influence_score:.3f}")
                print(f"   Источник: {news.source}")
                print()
    
    asyncio.run(test_news_engine())
