"""
GHOST News Engine - API клиенты
Интеграция с различными новостными API для сбора данных
"""

import os
import requests
import json
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class NewsItem:
    title: str
    content: str
    url: str
    source: str
    published_at: datetime
    category: str
    sentiment_score: float = 0.0
    importance_score: float = 0.0
    keywords: List[str] = None
    author: str = None
    summary: str = None

class NewsAPIClient:
    """Базовый класс для API клиентов новостей"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GHOST-News-Engine/1.0'
        })
    
    async def fetch_news(self, query: str = None, limit: int = 50) -> List[NewsItem]:
        """Получить новости (должен быть переопределен в наследниках)"""
        raise NotImplementedError

class NewsAPIClient(NewsAPIClient):
    """Клиент для NewsAPI.org"""
    
    def __init__(self):
        super().__init__(api_key=os.getenv("NEWS_API_KEY"))
        self.base_url = "https://newsapi.org/v2"
    
    async def fetch_news(self, query: str = "cryptocurrency OR bitcoin OR ethereum", limit: int = 50) -> List[NewsItem]:
        """Получить новости из NewsAPI"""
        try:
            url = f"{self.base_url}/everything"
            params = {
                'q': query,
                'apiKey': self.api_key,
                'pageSize': limit,
                'sortBy': 'publishedAt',
                'language': 'en'
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            news_items = []
            
            for article in data.get('articles', []):
                news_item = NewsItem(
                    title=article.get('title', ''),
                    content=article.get('content', ''),
                    url=article.get('url', ''),
                    source=article.get('source', {}).get('name', ''),
                    published_at=datetime.fromisoformat(article.get('publishedAt', '').replace('Z', '+00:00')),
                    category='crypto',
                    author=article.get('author', ''),
                    summary=article.get('description', '')
                )
                news_items.append(news_item)
            
            return news_items
            
        except Exception as e:
            logger.error(f"Ошибка при получении новостей из NewsAPI: {e}")
            return []

class TwitterAPIClient:
    """Клиент для Twitter API (через Twitter API v2)"""
    
    def __init__(self):
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        self.base_url = "https://api.twitter.com/2"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.bearer_token}',
            'User-Agent': 'GHOST-News-Engine/1.0'
        })
    
    async def fetch_user_tweets(self, username: str, limit: int = 10) -> List[Dict]:
        """Получить твиты пользователя"""
        try:
            # Сначала получаем ID пользователя
            user_url = f"{self.base_url}/users/by/username/{username}"
            user_response = self.session.get(user_url)
            user_response.raise_for_status()
            user_data = user_response.json()
            user_id = user_data['data']['id']
            
            # Получаем твиты
            tweets_url = f"{self.base_url}/users/{user_id}/tweets"
            params = {
                'max_results': limit,
                'tweet.fields': 'created_at,public_metrics,entities',
                'exclude': 'retweets,replies'
            }
            
            tweets_response = self.session.get(tweets_url, params=params)
            tweets_response.raise_for_status()
            tweets_data = tweets_response.json()
            
            return tweets_data.get('data', [])
            
        except Exception as e:
            logger.error(f"Ошибка при получении твитов для {username}: {e}")
            return []
    
    async def search_tweets(self, query: str, limit: int = 10) -> List[Dict]:
        """Поиск твитов по запросу"""
        try:
            url = f"{self.base_url}/tweets/search/recent"
            params = {
                'query': query,
                'max_results': limit,
                'tweet.fields': 'created_at,public_metrics,entities,author_id',
                'user.fields': 'username,name'
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            return data.get('data', [])
            
        except Exception as e:
            logger.error(f"Ошибка при поиске твитов: {e}")
            return []

class CoinGeckoAPIClient:
    """Клиент для CoinGecko API"""
    
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.session = requests.Session()
    
    async def fetch_trending_coins(self) -> List[Dict]:
        """Получить трендовые монеты"""
        try:
            url = f"{self.base_url}/search/trending"
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            return data.get('coins', [])
            
        except Exception as e:
            logger.error(f"Ошибка при получении трендовых монет: {e}")
            return []
    
    async def fetch_coin_news(self, coin_id: str) -> List[Dict]:
        """Получить новости по конкретной монете"""
        try:
            url = f"{self.base_url}/coins/{coin_id}/status_updates"
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            return data.get('status_updates', [])
            
        except Exception as e:
            logger.error(f"Ошибка при получении новостей монеты {coin_id}: {e}")
            return []

class AlphaVantageAPIClient:
    """Клиент для Alpha Vantage API (финансовые новости)"""
    
    def __init__(self):
        self.api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.base_url = "https://www.alphavantage.co/query"
        self.session = requests.Session()
    
    async def fetch_news_sentiment(self, tickers: List[str] = None) -> List[Dict]:
        """Получить новости с анализом настроений"""
        try:
            params = {
                'function': 'NEWS_SENTIMENT',
                'apikey': self.api_key,
                'topics': 'blockchain,technology',
                'time_from': '20240101T0000',
                'limit': 50
            }
            
            if tickers:
                params['tickers'] = ','.join(tickers)
            
            response = self.session.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            return data.get('feed', [])
            
        except Exception as e:
            logger.error(f"Ошибка при получении новостей Alpha Vantage: {e}")
            return []

class CryptoCompareAPIClient:
    """Клиент для CryptoCompare API"""
    
    def __init__(self):
        self.api_key = os.getenv("CRYPTOCOMPARE_API_KEY")
        self.base_url = "https://min-api.cryptocompare.com"
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({
                'authorization': f'Apikey {self.api_key}'
            })
    
    async def fetch_news(self, limit: int = 50) -> List[Dict]:
        """Получить крипто-новости"""
        try:
            url = f"{self.base_url}/data/v2/news/"
            params = {
                'lang': 'EN',
                'sortOrder': 'latest'
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            return data.get('Data', [])[:limit]
            
        except Exception as e:
            logger.error(f"Ошибка при получении новостей CryptoCompare: {e}")
            return []

class NewsAggregator:
    """Агрегатор новостей из всех источников"""
    
    def __init__(self):
        self.clients = {
            'newsapi': NewsAPIClient(),
            'twitter': TwitterAPIClient(),
            'coingecko': CoinGeckoAPIClient(),
            'alphavantage': AlphaVantageAPIClient(),
            'cryptocompare': CryptoCompareAPIClient()
        }
    
    async def fetch_all_news(self, query: str = "cryptocurrency") -> List[NewsItem]:
        """Получить новости из всех источников"""
        all_news = []
        
        # Получаем новости из NewsAPI
        try:
            newsapi_news = await self.clients['newsapi'].fetch_news(query)
            all_news.extend(newsapi_news)
            logger.info(f"Получено {len(newsapi_news)} новостей из NewsAPI")
        except Exception as e:
            logger.error(f"Ошибка NewsAPI: {e}")
        
        # Получаем новости из CryptoCompare
        try:
            cryptocompare_news = await self.clients['cryptocompare'].fetch_news()
            # Конвертируем в формат NewsItem
            for news in cryptocompare_news:
                news_item = NewsItem(
                    title=news.get('title', ''),
                    content=news.get('body', ''),
                    url=news.get('url', ''),
                    source=news.get('source', 'CryptoCompare'),
                    published_at=datetime.fromtimestamp(news.get('published_on', 0)),
                    category='crypto',
                    summary=news.get('body', '')[:200]
                )
                all_news.append(news_item)
            logger.info(f"Получено {len(cryptocompare_news)} новостей из CryptoCompare")
        except Exception as e:
            logger.error(f"Ошибка CryptoCompare: {e}")
        
        return all_news
    
    async def fetch_influential_tweets(self, usernames: List[str]) -> List[Dict]:
        """Получить твиты влиятельных лиц"""
        all_tweets = []
        
        for username in usernames:
            try:
                tweets = await self.clients['twitter'].fetch_user_tweets(username)
                all_tweets.extend(tweets)
                logger.info(f"Получено {len(tweets)} твитов от {username}")
            except Exception as e:
                logger.error(f"Ошибка при получении твитов {username}: {e}")
        
        return all_tweets
    
    async def fetch_market_sentiment(self, tickers: List[str] = None) -> List[Dict]:
        """Получить анализ настроений рынка"""
        try:
            sentiment_data = await self.clients['alphavantage'].fetch_news_sentiment(tickers)
            logger.info(f"Получено {len(sentiment_data)} записей настроений")
            return sentiment_data
        except Exception as e:
            logger.error(f"Ошибка при получении настроений: {e}")
            return []

if __name__ == "__main__":
    # Тестирование
    async def test_news_aggregator():
        aggregator = NewsAggregator()
        
        # Тест получения новостей
        news = await aggregator.fetch_all_news("bitcoin")
        print(f"Получено {len(news)} новостей")
        
        # Тест получения твитов
        influential_users = ["elonmusk", "VitalikButerin", "cz_binance"]
        tweets = await aggregator.fetch_influential_tweets(influential_users)
        print(f"Получено {len(tweets)} твитов")
        
        # Тест настроений
        sentiment = await aggregator.fetch_market_sentiment(["BTC", "ETH"])
        print(f"Получено {len(sentiment)} записей настроений")
    
    asyncio.run(test_news_aggregator())
