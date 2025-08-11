#!/usr/bin/env python3
"""
RSS Parser для бесплатных источников новостей
Парсит RSS feeds без необходимости в API ключах
"""

import requests
import feedparser
from datetime import datetime, timezone
from typing import List, Dict, Any
import logging
from urllib.parse import urlparse
import time

logger = logging.getLogger(__name__)

class RSSParser:
    """Парсер RSS feeds для бесплатных источников новостей"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GHOST-News-Engine/1.0 (RSS Parser)'
        })
    
    def parse_rss_feed(self, url: str, max_articles: int = 20) -> List[Dict[str, Any]]:
        """Парсит RSS feed и возвращает список новостей"""
        try:
            logger.info(f"Парсим RSS feed: {url}")
            
            # Получаем RSS feed
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Парсим XML
            feed = feedparser.parse(response.content)
            
            if feed.bozo:
                logger.warning(f"RSS feed содержит ошибки: {url}")
            
            articles = []
            for entry in feed.entries[:max_articles]:
                try:
                    article = self._parse_entry(entry, url)
                    if article:
                        articles.append(article)
                except Exception as e:
                    logger.error(f"Ошибка парсинга статьи: {e}")
                    continue
            
            logger.info(f"Получено {len(articles)} статей из {url}")
            return articles
            
        except Exception as e:
            logger.error(f"Ошибка парсинга RSS feed {url}: {e}")
            return []
    
    def _parse_entry(self, entry, source_url: str) -> Dict[str, Any]:
        """Парсит отдельную статью из RSS feed"""
        try:
            # Извлекаем заголовок
            title = entry.get('title', '').strip()
            if not title:
                return None
            
            # Извлекаем описание
            description = ''
            if hasattr(entry, 'summary'):
                description = entry.get('summary', '').strip()
            elif hasattr(entry, 'description'):
                description = entry.get('description', '').strip()
            
            # Извлекаем ссылку
            link = entry.get('link', '')
            
            # Извлекаем дату публикации
            published_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published_date = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
            else:
                published_date = datetime.now(timezone.utc)
            
            # Определяем источник по URL
            source_name = self._extract_source_name(source_url)
            
            # Создаем объект новости
            article = {
                'title': title,
                'description': description,
                'link': link,
                'published_date': published_date,
                'source_name': source_name,
                'source_url': source_url,
                'type': 'rss',
                'raw_data': entry
            }
            
            return article
            
        except Exception as e:
            logger.error(f"Ошибка парсинга статьи: {e}")
            return None
    
    def _extract_source_name(self, url: str) -> str:
        """Извлекает название источника из URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Маппинг доменов на названия
            source_mapping = {
                'www.coindesk.com': 'CoinDesk',
                'cointelegraph.com': 'CoinTelegraph',
                'cryptonews.com': 'CryptoNews',
                'news.bitcoin.com': 'Bitcoin News',
                'coindesk.com': 'CoinDesk'
            }
            
            return source_mapping.get(domain, domain)
            
        except Exception:
            return 'Unknown Source'
    
    def filter_articles_by_keywords(self, articles: List[Dict], keywords: List[str]) -> List[Dict]:
        """Фильтрует статьи по ключевым словам"""
        if not keywords:
            return articles
        
        filtered_articles = []
        keywords_lower = [kw.lower() for kw in keywords]
        
        for article in articles:
            title_lower = article.get('title', '').lower()
            description_lower = article.get('description', '').lower()
            
            # Проверяем, содержит ли статья хотя бы одно ключевое слово
            if any(kw in title_lower or kw in description_lower for kw in keywords_lower):
                filtered_articles.append(article)
        
        return filtered_articles
    
    def get_multiple_feeds(self, feeds_config: List[Dict]) -> List[Dict]:
        """Получает новости из нескольких RSS feeds"""
        all_articles = []
        
        for feed_config in feeds_config:
            try:
                url = feed_config.get('url')
                max_articles = feed_config.get('max_articles', 20)
                keywords = feed_config.get('keywords', [])
                
                if not url:
                    continue
                
                # Получаем статьи
                articles = self.parse_rss_feed(url, max_articles)
                
                # Фильтруем по ключевым словам
                if keywords:
                    articles = self.filter_articles_by_keywords(articles, keywords)
                
                all_articles.extend(articles)
                
                # Небольшая задержка между запросами
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Ошибка получения RSS feed {feed_config}: {e}")
                continue
        
        # Сортируем по дате публикации (новые сначала)
        all_articles.sort(key=lambda x: x.get('published_date', datetime.min), reverse=True)
        
        return all_articles

def main():
    """Тестирование RSS парсера"""
    logging.basicConfig(level=logging.INFO)
    
    parser = RSSParser()
    
    # Тестовые RSS feeds
    test_feeds = [
        {
            'url': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
            'max_articles': 5,
            'keywords': ['bitcoin', 'crypto']
        },
        {
            'url': 'https://cointelegraph.com/rss',
            'max_articles': 5,
            'keywords': ['ethereum', 'defi']
        }
    ]
    
    print("🚀 Тестирование RSS парсера...")
    articles = parser.get_multiple_feeds(test_feeds)
    
    print(f"\n📰 Получено {len(articles)} статей:")
    for i, article in enumerate(articles[:10], 1):
        print(f"\n{i}. {article['title']}")
        print(f"   Источник: {article['source_name']}")
        print(f"   Дата: {article['published_date']}")
        print(f"   Ссылка: {article['link']}")

if __name__ == "__main__":
    main()
