"""
GHOST News Engine - Источники новостей
Собирает новости из лучших источников для анализа крипторынка
"""

import os
import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import asyncio
import aiohttp
from dataclasses import dataclass

@dataclass
class NewsSource:
    name: str
    url: str
    api_key: str = None
    category: str = "crypto"
    reliability_score: float = 0.8
    update_frequency: int = 300  # секунды

class NewsSources:
    """Класс для управления источниками новостей"""
    
    def __init__(self):
        self.sources = self._initialize_sources()
        self.influential_people = self._initialize_influential_people()
        self.companies = self._initialize_companies()
    
    def _initialize_sources(self) -> Dict[str, NewsSource]:
        """Инициализация лучших источников новостей"""
        return {
            # Крипто-новости
            "coindesk": NewsSource(
                name="CoinDesk",
                url="https://api.coindesk.com/v1/news",
                category="crypto",
                reliability_score=0.9
            ),
            "cointelegraph": NewsSource(
                name="CoinTelegraph",
                url="https://cointelegraph.com/api/v1/news",
                category="crypto",
                reliability_score=0.85
            ),
            "decrypt": NewsSource(
                name="Decrypt",
                url="https://api.decrypt.co/news",
                category="crypto",
                reliability_score=0.8
            ),
            
            # Финансовые новости
            "reuters": NewsSource(
                name="Reuters",
                url="https://api.reuters.com/v1/news",
                api_key=os.getenv("REUTERS_API_KEY"),
                category="finance",
                reliability_score=0.95
            ),
            "bloomberg": NewsSource(
                name="Bloomberg",
                url="https://api.bloomberg.com/v1/news",
                api_key=os.getenv("BLOOMBERG_API_KEY"),
                category="finance",
                reliability_score=0.95
            ),
            "cnbc": NewsSource(
                name="CNBC",
                url="https://api.cnbc.com/v1/news",
                category="finance",
                reliability_score=0.9
            ),
            
            # Технологические новости
            "techcrunch": NewsSource(
                name="TechCrunch",
                url="https://api.techcrunch.com/v1/news",
                category="tech",
                reliability_score=0.85
            ),
            "theverge": NewsSource(
                name="The Verge",
                url="https://api.theverge.com/v1/news",
                category="tech",
                reliability_score=0.8
            ),
            
            # Регулятивные новости
            "sec": NewsSource(
                name="SEC",
                url="https://api.sec.gov/v1/news",
                category="regulation",
                reliability_score=0.98
            ),
            "cftc": NewsSource(
                name="CFTC",
                url="https://api.cftc.gov/v1/news",
                category="regulation",
                reliability_score=0.98
            ),
            
            # Макроэкономические новости
            "federalreserve": NewsSource(
                name="Federal Reserve",
                url="https://api.federalreserve.gov/v1/news",
                category="macro",
                reliability_score=0.99
            ),
            "ecb": NewsSource(
                name="European Central Bank",
                url="https://api.ecb.europa.eu/v1/news",
                category="macro",
                reliability_score=0.99
            ),
        }
    
    def _initialize_influential_people(self) -> Dict[str, Dict]:
        """Инициализация влиятельных лиц"""
        return {
            # Крипто-лидеры
            "vitalik_buterin": {
                "name": "Vitalik Buterin",
                "twitter": "@VitalikButerin",
                "company": "Ethereum",
                "influence_score": 0.95,
                "categories": ["crypto", "defi", "ethereum"]
            },
            "cz_binance": {
                "name": "CZ (Changpeng Zhao)",
                "twitter": "@cz_binance",
                "company": "Binance",
                "influence_score": 0.9,
                "categories": ["crypto", "exchange", "binance"]
            },
            "sbf": {
                "name": "Sam Bankman-Fried",
                "twitter": "@SBF_FTX",
                "company": "FTX",
                "influence_score": 0.85,
                "categories": ["crypto", "exchange", "ftx"]
            },
            
            # Технологические лидеры
            "elon_musk": {
                "name": "Elon Musk",
                "twitter": "@elonmusk",
                "company": "Tesla/SpaceX",
                "influence_score": 0.98,
                "categories": ["tech", "crypto", "tesla", "spacex"]
            },
            "jack_dorsey": {
                "name": "Jack Dorsey",
                "twitter": "@jack",
                "company": "Block/Square",
                "influence_score": 0.9,
                "categories": ["tech", "crypto", "block"]
            },
            "mark_zuckerberg": {
                "name": "Mark Zuckerberg",
                "twitter": "@finkd",
                "company": "Meta",
                "influence_score": 0.85,
                "categories": ["tech", "meta", "metaverse"]
            },
            
            # Финансовые лидеры
            "warren_buffett": {
                "name": "Warren Buffett",
                "twitter": "@WarrenBuffett",
                "company": "Berkshire Hathaway",
                "influence_score": 0.95,
                "categories": ["finance", "investment"]
            },
            "ray_dalio": {
                "name": "Ray Dalio",
                "twitter": "@RayDalio",
                "company": "Bridgewater Associates",
                "influence_score": 0.9,
                "categories": ["finance", "macro", "investment"]
            },
            
            # Регуляторы
            "jerome_powell": {
                "name": "Jerome Powell",
                "twitter": "@federalreserve",
                "company": "Federal Reserve",
                "influence_score": 0.99,
                "categories": ["regulation", "macro", "federal_reserve"]
            },
            "gary_gensler": {
                "name": "Gary Gensler",
                "twitter": "@SECGov",
                "company": "SEC",
                "influence_score": 0.95,
                "categories": ["regulation", "sec", "crypto"]
            },
            
            # Крипто-предприниматели
            "saylor": {
                "name": "Michael Saylor",
                "twitter": "@saylor",
                "company": "MicroStrategy",
                "influence_score": 0.85,
                "categories": ["crypto", "bitcoin", "investment"]
            },
            "pomp": {
                "name": "Anthony Pompliano",
                "twitter": "@APompliano",
                "company": "Pomp Investments",
                "influence_score": 0.8,
                "categories": ["crypto", "bitcoin", "investment"]
            },
            "novogratz": {
                "name": "Mike Novogratz",
                "twitter": "@novogratz",
                "company": "Galaxy Digital",
                "influence_score": 0.85,
                "categories": ["crypto", "investment", "galaxy"]
            }
        }
    
    def _initialize_companies(self) -> Dict[str, Dict]:
        """Инициализация важных компаний"""
        return {
            # Крипто-компании
            "binance": {
                "name": "Binance",
                "twitter": "@binance",
                "category": "exchange",
                "influence_score": 0.9,
                "keywords": ["binance", "bnb", "crypto exchange"]
            },
            "coinbase": {
                "name": "Coinbase",
                "twitter": "@coinbase",
                "category": "exchange",
                "influence_score": 0.85,
                "keywords": ["coinbase", "crypto exchange", "public company"]
            },
            "ethereum": {
                "name": "Ethereum Foundation",
                "twitter": "@ethereum",
                "category": "blockchain",
                "influence_score": 0.9,
                "keywords": ["ethereum", "eth", "smart contracts"]
            },
            "bitcoin": {
                "name": "Bitcoin",
                "twitter": "@bitcoin",
                "category": "cryptocurrency",
                "influence_score": 0.95,
                "keywords": ["bitcoin", "btc", "digital gold"]
            },
            
            # Технологические гиганты
            "tesla": {
                "name": "Tesla",
                "twitter": "@Tesla",
                "category": "automotive",
                "influence_score": 0.9,
                "keywords": ["tesla", "tsla", "electric vehicles", "bitcoin"]
            },
            "apple": {
                "name": "Apple",
                "twitter": "@Apple",
                "category": "technology",
                "influence_score": 0.85,
                "keywords": ["apple", "aapl", "iphone", "crypto"]
            },
            "google": {
                "name": "Google",
                "twitter": "@Google",
                "category": "technology",
                "influence_score": 0.85,
                "keywords": ["google", "alphabet", "googl", "blockchain"]
            },
            "microsoft": {
                "name": "Microsoft",
                "twitter": "@Microsoft",
                "category": "technology",
                "influence_score": 0.8,
                "keywords": ["microsoft", "msft", "azure", "blockchain"]
            },
            
            # Финансовые институты
            "jpmorgan": {
                "name": "JPMorgan Chase",
                "twitter": "@jpmorgan",
                "category": "banking",
                "influence_score": 0.9,
                "keywords": ["jpmorgan", "jpm", "blockchain", "crypto"]
            },
            "goldman_sachs": {
                "name": "Goldman Sachs",
                "twitter": "@GoldmanSachs",
                "category": "investment",
                "influence_score": 0.9,
                "keywords": ["goldman sachs", "gs", "crypto", "investment"]
            },
            "blackrock": {
                "name": "BlackRock",
                "twitter": "@BlackRock",
                "category": "investment",
                "influence_score": 0.95,
                "keywords": ["blackrock", "blk", "etf", "bitcoin"]
            },
            
            # Регулятивные органы
            "sec": {
                "name": "Securities and Exchange Commission",
                "twitter": "@SECGov",
                "category": "regulation",
                "influence_score": 0.98,
                "keywords": ["sec", "regulation", "crypto", "securities"]
            },
            "federal_reserve": {
                "name": "Federal Reserve",
                "twitter": "@federalreserve",
                "category": "regulation",
                "influence_score": 0.99,
                "keywords": ["federal reserve", "fed", "interest rates", "monetary policy"]
            }
        }
    
    def get_all_sources(self) -> Dict[str, NewsSource]:
        """Получить все источники новостей"""
        return self.sources
    
    def get_influential_people(self) -> Dict[str, Dict]:
        """Получить список влиятельных лиц"""
        return self.influential_people
    
    def get_companies(self) -> Dict[str, Dict]:
        """Получить список важных компаний"""
        return self.companies
    
    def get_sources_by_category(self, category: str) -> Dict[str, NewsSource]:
        """Получить источники по категории"""
        return {k: v for k, v in self.sources.items() if v.category == category}
    
    def get_high_reliability_sources(self, threshold: float = 0.8) -> Dict[str, NewsSource]:
        """Получить источники с высокой надежностью"""
        return {k: v for k, v in self.sources.items() if v.reliability_score >= threshold}

if __name__ == "__main__":
    # Тестирование
    news_sources = NewsSources()
    print(f"Всего источников: {len(news_sources.get_all_sources())}")
    print(f"Влиятельных лиц: {len(news_sources.get_influential_people())}")
    print(f"Важных компаний: {len(news_sources.get_companies())}")
    
    # Вывод высоконадежных источников
    reliable_sources = news_sources.get_high_reliability_sources(0.9)
    print(f"\nВысоконадежные источники (>0.9):")
    for name, source in reliable_sources.items():
        print(f"- {source.name}: {source.reliability_score}")
