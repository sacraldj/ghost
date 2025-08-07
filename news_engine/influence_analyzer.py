"""
GHOST News Engine - Анализатор влияния
Анализирует влияние новостей и важность событий для рынка
"""

import re
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import logging
from collections import Counter
import numpy as np
from textblob import TextBlob
import spacy

# Загружаем модель spaCy для NLP
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # Если модель не установлена, используем базовую обработку
    nlp = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class InfluenceScore:
    news_id: str
    title: str
    source: str
    published_at: datetime
    influence_score: float
    market_impact: float
    sentiment_score: float
    urgency_score: float
    reach_score: float
    credibility_score: float
    keywords: List[str]
    entities: List[str]
    summary: str

class InfluenceAnalyzer:
    """Анализатор влияния новостей на рынок"""
    
    def __init__(self):
        self.keywords = self._load_keywords()
        self.entities = self._load_entities()
        self.source_credibility = self._load_source_credibility()
        self.influential_people = self._load_influential_people()
        
    def _load_keywords(self) -> Dict[str, float]:
        """Загрузить ключевые слова с весами"""
        return {
            # Криптовалюты
            "bitcoin": 0.9, "btc": 0.9, "ethereum": 0.85, "eth": 0.85,
            "binance": 0.8, "coinbase": 0.8, "solana": 0.75, "cardano": 0.7,
            
            # Регулятивные термины
            "sec": 0.95, "regulation": 0.9, "compliance": 0.85,
            "cftc": 0.9, "federal reserve": 0.95, "fed": 0.95,
            
            # Технологические термины
            "blockchain": 0.8, "defi": 0.8, "nft": 0.7, "web3": 0.75,
            "smart contract": 0.8, "token": 0.7, "wallet": 0.6,
            
            # Макроэкономические термины
            "inflation": 0.9, "interest rate": 0.95, "cpi": 0.9,
            "recession": 0.95, "gdp": 0.85, "unemployment": 0.8,
            
            # Компании
            "tesla": 0.8, "apple": 0.75, "google": 0.75, "microsoft": 0.75,
            "amazon": 0.75, "meta": 0.7, "netflix": 0.65,
            
            # Влиятельные лица
            "elon musk": 0.95, "vitalik buterin": 0.9, "cz": 0.85,
            "warren buffett": 0.9, "ray dalio": 0.85, "jerome powell": 0.95,
            
            # События
            "etf": 0.9, "halving": 0.85, "fork": 0.8, "airdrop": 0.6,
            "ico": 0.7, "ido": 0.7, "launch": 0.7, "partnership": 0.75,
            
            # Эмоциональные слова
            "crash": 0.9, "pump": 0.8, "dump": 0.8, "moon": 0.6,
            "bear": 0.8, "bull": 0.8, "fomo": 0.7, "hodl": 0.6,
            
            # Временные маркеры
            "breaking": 0.9, "urgent": 0.85, "exclusive": 0.8,
            "announcement": 0.8, "update": 0.7, "release": 0.7
        }
    
    def _load_entities(self) -> Dict[str, float]:
        """Загрузить важные сущности"""
        return {
            # Криптобиржи
            "Binance": 0.9, "Coinbase": 0.85, "Kraken": 0.8, "FTX": 0.8,
            "Kucoin": 0.75, "Bybit": 0.75, "OKX": 0.75,
            
            # Блокчейн-проекты
            "Ethereum": 0.9, "Bitcoin": 0.95, "Solana": 0.8, "Cardano": 0.75,
            "Polkadot": 0.75, "Polygon": 0.75, "Avalanche": 0.75,
            
            # Финансовые институты
            "JPMorgan": 0.9, "Goldman Sachs": 0.9, "BlackRock": 0.95,
            "Fidelity": 0.85, "Morgan Stanley": 0.85,
            
            # Регуляторы
            "SEC": 0.95, "CFTC": 0.9, "Federal Reserve": 0.95,
            "European Central Bank": 0.9, "Bank of England": 0.85,
            
            # Технологические компании
            "Tesla": 0.85, "Apple": 0.8, "Google": 0.8, "Microsoft": 0.8,
            "Amazon": 0.8, "Meta": 0.75, "Netflix": 0.7
        }
    
    def _load_source_credibility(self) -> Dict[str, float]:
        """Загрузить рейтинги доверия к источникам"""
        return {
            # Высоконадежные источники
            "Reuters": 0.95, "Bloomberg": 0.95, "CNBC": 0.9,
            "Wall Street Journal": 0.95, "Financial Times": 0.95,
            "Associated Press": 0.9, "BBC": 0.9,
            
            # Крипто-специализированные
            "CoinDesk": 0.85, "CoinTelegraph": 0.8, "Decrypt": 0.8,
            "The Block": 0.85, "CryptoSlate": 0.75,
            
            # Технологические
            "TechCrunch": 0.85, "The Verge": 0.8, "Wired": 0.85,
            "Ars Technica": 0.8, "VentureBeat": 0.8,
            
            # Официальные источники
            "SEC": 0.98, "Federal Reserve": 0.98, "White House": 0.95,
            "European Commission": 0.9, "Bank of England": 0.9
        }
    
    def _load_influential_people(self) -> Dict[str, Dict]:
        """Загрузить список влиятельных лиц"""
        return {
            "elonmusk": {
                "name": "Elon Musk",
                "influence_score": 0.98,
                "categories": ["tech", "crypto", "tesla", "spacex"],
                "keywords": ["tesla", "bitcoin", "dogecoin", "spacex"]
            },
            "VitalikButerin": {
                "name": "Vitalik Buterin",
                "influence_score": 0.95,
                "categories": ["crypto", "ethereum", "defi"],
                "keywords": ["ethereum", "defi", "smart contracts", "web3"]
            },
            "cz_binance": {
                "name": "CZ (Changpeng Zhao)",
                "influence_score": 0.9,
                "categories": ["crypto", "exchange", "binance"],
                "keywords": ["binance", "bnb", "crypto exchange"]
            },
            "saylor": {
                "name": "Michael Saylor",
                "influence_score": 0.85,
                "categories": ["crypto", "bitcoin", "investment"],
                "keywords": ["bitcoin", "microstrategy", "investment"]
            },
            "novogratz": {
                "name": "Mike Novogratz",
                "influence_score": 0.85,
                "categories": ["crypto", "investment", "galaxy"],
                "keywords": ["galaxy digital", "crypto investment"]
            },
            "pomp": {
                "name": "Anthony Pompliano",
                "influence_score": 0.8,
                "categories": ["crypto", "bitcoin", "investment"],
                "keywords": ["bitcoin", "pomp investments"]
            }
        }
    
    def analyze_news_influence(self, news_item: Dict) -> InfluenceScore:
        """Анализировать влияние новости"""
        title = news_item.get('title', '')
        content = news_item.get('content', '')
        source = news_item.get('source', '')
        published_at = news_item.get('published_at', datetime.now())
        
        # Анализ ключевых слов
        keyword_score = self._analyze_keywords(title + " " + content)
        
        # Анализ настроений
        sentiment_score = self._analyze_sentiment(title + " " + content)
        
        # Анализ срочности
        urgency_score = self._analyze_urgency(title, content, published_at)
        
        # Анализ охвата
        reach_score = self._analyze_reach(source, title)
        
        # Анализ доверия к источнику
        credibility_score = self._analyze_credibility(source)
        
        # Общий балл влияния
        influence_score = self._calculate_influence_score(
            keyword_score, sentiment_score, urgency_score, 
            reach_score, credibility_score
        )
        
        # Влияние на рынок
        market_impact = self._calculate_market_impact(
            influence_score, sentiment_score, keyword_score
        )
        
        # Извлечение ключевых слов и сущностей
        keywords = self._extract_keywords(title + " " + content)
        entities = self._extract_entities(title + " " + content)
        
        # Создание краткого содержания
        summary = self._generate_summary(title, content)
        
        return InfluenceScore(
            news_id=news_item.get('id', ''),
            title=title,
            source=source,
            published_at=published_at,
            influence_score=influence_score,
            market_impact=market_impact,
            sentiment_score=sentiment_score,
            urgency_score=urgency_score,
            reach_score=reach_score,
            credibility_score=credibility_score,
            keywords=keywords,
            entities=entities,
            summary=summary
        )
    
    def _analyze_keywords(self, text: str) -> float:
        """Анализировать ключевые слова"""
        text_lower = text.lower()
        total_score = 0
        found_keywords = 0
        
        for keyword, weight in self.keywords.items():
            if keyword.lower() in text_lower:
                total_score += weight
                found_keywords += 1
        
        return total_score / max(found_keywords, 1)
    
    def _analyze_sentiment(self, text: str) -> float:
        """Анализировать настроения текста"""
        try:
            blob = TextBlob(text)
            return blob.sentiment.polarity
        except:
            return 0.0
    
    def _analyze_urgency(self, title: str, content: str, published_at: datetime) -> float:
        """Анализировать срочность новости"""
        urgency_score = 0.5  # Базовый балл
        
        # Временные маркеры
        urgency_words = ["breaking", "urgent", "exclusive", "just in", "live"]
        text_lower = (title + " " + content).lower()
        
        for word in urgency_words:
            if word in text_lower:
                urgency_score += 0.2
        
        # Свежесть новости
        hours_ago = (datetime.now() - published_at).total_seconds() / 3600
        if hours_ago < 1:
            urgency_score += 0.3
        elif hours_ago < 6:
            urgency_score += 0.2
        elif hours_ago < 24:
            urgency_score += 0.1
        
        return min(urgency_score, 1.0)
    
    def _analyze_reach(self, source: str, title: str) -> float:
        """Анализировать потенциальный охват"""
        reach_score = 0.5  # Базовый балл
        
        # Известные источники
        major_sources = ["reuters", "bloomberg", "cnbc", "wsj", "ft"]
        if source.lower() in major_sources:
            reach_score += 0.3
        
        # Вирусные слова в заголовке
        viral_words = ["crash", "pump", "moon", "bear", "bull", "etf", "sec"]
        title_lower = title.lower()
        for word in viral_words:
            if word in title_lower:
                reach_score += 0.1
        
        return min(reach_score, 1.0)
    
    def _analyze_credibility(self, source: str) -> float:
        """Анализировать доверие к источнику"""
        return self.source_credibility.get(source, 0.5)
    
    def _calculate_influence_score(self, keyword_score: float, sentiment_score: float,
                                 urgency_score: float, reach_score: float, 
                                 credibility_score: float) -> float:
        """Рассчитать общий балл влияния"""
        weights = {
            'keyword': 0.3,
            'sentiment': 0.2,
            'urgency': 0.2,
            'reach': 0.15,
            'credibility': 0.15
        }
        
        influence_score = (
            keyword_score * weights['keyword'] +
            abs(sentiment_score) * weights['sentiment'] +
            urgency_score * weights['urgency'] +
            reach_score * weights['reach'] +
            credibility_score * weights['credibility']
        )
        
        return min(influence_score, 1.0)
    
    def _calculate_market_impact(self, influence_score: float, sentiment_score: float,
                               keyword_score: float) -> float:
        """Рассчитать влияние на рынок"""
        # Базовое влияние
        market_impact = influence_score * 0.7
        
        # Корректировка по настроениям
        if sentiment_score > 0.3:
            market_impact += 0.2  # Позитивное влияние
        elif sentiment_score < -0.3:
            market_impact -= 0.2  # Негативное влияние
        
        # Корректировка по ключевым словам
        if keyword_score > 0.8:
            market_impact += 0.1  # Высокая релевантность
        
        return max(min(market_impact, 1.0), -1.0)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Извлечь ключевые слова"""
        text_lower = text.lower()
        found_keywords = []
        
        for keyword in self.keywords.keys():
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords[:10]  # Топ-10 ключевых слов
    
    def _extract_entities(self, text: str) -> List[str]:
        """Извлечь важные сущности"""
        if nlp:
            doc = nlp(text)
            entities = []
            for ent in doc.ents:
                if ent.label_ in ['ORG', 'PERSON', 'GPE']:
                    entities.append(ent.text)
            return entities
        else:
            # Простая извлечение по списку
            text_lower = text.lower()
            found_entities = []
            for entity in self.entities.keys():
                if entity.lower() in text_lower:
                    found_entities.append(entity)
            return found_entities
    
    def _generate_summary(self, title: str, content: str) -> str:
        """Создать краткое содержание"""
        # Простой алгоритм извлечения ключевых предложений
        sentences = content.split('.')
        if len(sentences) > 1:
            return sentences[0][:200] + "..."
        else:
            return title[:200] + "..."
    
    def analyze_tweet_influence(self, tweet: Dict) -> Dict:
        """Анализировать влияние твита"""
        text = tweet.get('text', '')
        author = tweet.get('author_id', '')
        created_at = tweet.get('created_at', '')
        metrics = tweet.get('public_metrics', {})
        
        # Анализ влияния автора
        author_influence = self.influential_people.get(author, {}).get('influence_score', 0.5)
        
        # Анализ содержания
        keyword_score = self._analyze_keywords(text)
        sentiment_score = self._analyze_sentiment(text)
        
        # Анализ метрик
        engagement_score = self._calculate_engagement_score(metrics)
        
        # Общий балл влияния твита
        tweet_influence = (
            author_influence * 0.4 +
            keyword_score * 0.3 +
            abs(sentiment_score) * 0.2 +
            engagement_score * 0.1
        )
        
        return {
            'tweet_id': tweet.get('id', ''),
            'text': text,
            'author': author,
            'created_at': created_at,
            'influence_score': tweet_influence,
            'sentiment_score': sentiment_score,
            'keyword_score': keyword_score,
            'engagement_score': engagement_score,
            'metrics': metrics
        }
    
    def _calculate_engagement_score(self, metrics: Dict) -> float:
        """Рассчитать балл вовлеченности"""
        total_engagement = (
            metrics.get('retweet_count', 0) +
            metrics.get('like_count', 0) +
            metrics.get('reply_count', 0) * 2 +
            metrics.get('quote_count', 0) * 1.5
        )
        
        # Нормализация (высокая вовлеченность = 1.0)
        if total_engagement > 10000:
            return 1.0
        elif total_engagement > 1000:
            return 0.8
        elif total_engagement > 100:
            return 0.6
        elif total_engagement > 10:
            return 0.4
        else:
            return 0.2

if __name__ == "__main__":
    # Тестирование
    analyzer = InfluenceAnalyzer()
    
    # Тестовая новость
    test_news = {
        'title': 'Breaking: Bitcoin ETF Approved by SEC',
        'content': 'The Securities and Exchange Commission has approved the first Bitcoin ETF, marking a major milestone for cryptocurrency adoption.',
        'source': 'Reuters',
        'published_at': datetime.now()
    }
    
    # Анализ влияния
    influence_score = analyzer.analyze_news_influence(test_news)
    print(f"Влияние новости: {influence_score.influence_score:.3f}")
    print(f"Влияние на рынок: {influence_score.market_impact:.3f}")
    print(f"Настроения: {influence_score.sentiment_score:.3f}")
    print(f"Ключевые слова: {influence_score.keywords}")
