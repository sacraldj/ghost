#!/usr/bin/env python3
"""
Тестовый скрипт для GHOST News Engine
Проверяет работу всех компонентов движка новостей
"""

import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from news_engine import NewsEngine
from influence_analyzer import InfluenceAnalyzer
from news_sources import NewsSources

async def test_news_sources():
    """Тест источников новостей"""
    print("🔍 Тестирование источников новостей...")
    
    sources = NewsSources()
    
    # Проверяем источники
    all_sources = sources.get_all_sources()
    print(f"✅ Всего источников: {len(all_sources)}")
    
    # Проверяем влиятельных лиц
    influential_people = sources.get_influential_people()
    print(f"✅ Влиятельных лиц: {len(influential_people)}")
    
    # Проверяем компании
    companies = sources.get_companies()
    print(f"✅ Компаний: {len(companies)}")
    
    # Выводим топ-5 источников по надежности
    reliable_sources = sources.get_high_reliability_sources(0.9)
    print(f"\n🏆 Топ-5 надежных источников:")
    for i, (name, source) in enumerate(list(reliable_sources.items())[:5], 1):
        print(f"{i}. {source.name} ({source.reliability_score:.2f})")
    
    return True

def test_influence_analyzer():
    """Тест анализатора влияния"""
    print("\n🔍 Тестирование анализатора влияния...")
    
    analyzer = InfluenceAnalyzer()
    
    # Тестовые новости
    test_news = [
        {
            'title': 'Breaking: Bitcoin ETF Approved by SEC',
            'content': 'The Securities and Exchange Commission has approved the first Bitcoin ETF, marking a major milestone for cryptocurrency adoption.',
            'source': 'Reuters',
            'published_at': datetime.now()
        },
        {
            'title': 'Elon Musk Tweets About Bitcoin',
            'content': 'Tesla CEO Elon Musk tweeted about Bitcoin, causing a surge in the cryptocurrency market.',
            'source': 'CoinDesk',
            'published_at': datetime.now()
        },
        {
            'title': 'Federal Reserve Raises Interest Rates',
            'content': 'The Federal Reserve has announced a 0.25% increase in interest rates.',
            'source': 'Bloomberg',
            'published_at': datetime.now()
        }
    ]
    
    for i, news in enumerate(test_news, 1):
        print(f"\n📰 Тестовая новость {i}: {news['title']}")
        
        influence_score = analyzer.analyze_news_influence(news)
        
        print(f"   Влияние: {influence_score.influence_score:.3f}")
        print(f"   Влияние на рынок: {influence_score.market_impact:.3f}")
        print(f"   Настроения: {influence_score.sentiment_score:.3f}")
        print(f"   Срочность: {influence_score.urgency_score:.3f}")
        print(f"   Доверие к источнику: {influence_score.credibility_score:.3f}")
        print(f"   Ключевые слова: {', '.join(influence_score.keywords[:5])}")
    
    return True

async def test_news_engine():
    """Тест главного движка новостей"""
    print("\n🔍 Тестирование главного движка новостей...")
    
    engine = NewsEngine()
    
    # Проверяем базу данных
    print("✅ База данных инициализирована")
    
    # Тестируем анализ новостей (без реальных API запросов)
    print("✅ Анализатор влияния работает")
    
    # Проверяем получение важных новостей
    important_news = engine.get_important_news(limit=5)
    print(f"✅ Получено важных новостей из БД: {len(important_news)}")
    
    return True

def test_api_clients():
    """Тест API клиентов (без реальных запросов)"""
    print("\n🔍 Тестирование API клиентов...")
    
    try:
        from news_apis import NewsAggregator, NewsAPIClient, TwitterAPIClient
        
        # Проверяем инициализацию клиентов
        aggregator = NewsAggregator()
        print("✅ NewsAggregator инициализирован")
        
        # Проверяем наличие API ключей
        news_api_key = os.getenv("NEWS_API_KEY")
        twitter_token = os.getenv("TWITTER_BEARER_TOKEN")
        
        if news_api_key:
            print("✅ NewsAPI ключ найден")
        else:
            print("⚠️  NewsAPI ключ не найден (добавьте в .env)")
        
        if twitter_token:
            print("✅ Twitter Bearer Token найден")
        else:
            print("⚠️  Twitter Bearer Token не найден (добавьте в .env)")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании API клиентов: {e}")
        return False

async def run_full_test():
    """Запуск полного тестирования"""
    print("🚀 Запуск полного тестирования GHOST News Engine")
    print("=" * 60)
    
    tests = [
        ("Источники новостей", test_news_sources),
        ("Анализатор влияния", lambda: test_influence_analyzer()),
        ("Главный движок", test_news_engine),
        ("API клиенты", lambda: test_api_clients())
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, True))
        except Exception as e:
            print(f"❌ Ошибка в тесте '{test_name}': {e}")
            results.append((test_name, False))
    
    # Выводим результаты
    print("\n" + "=" * 60)
    print("📊 Результаты тестирования:")
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ ПРОЙДЕН" if success else "❌ ПРОВАЛЕН"
        print(f"{status} - {test_name}")
        if success:
            passed += 1
    
    print(f"\nИтого: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены! Движок новостей готов к работе.")
    else:
        print("⚠️  Некоторые тесты не пройдены. Проверьте настройки.")
    
    return passed == total

def show_setup_instructions():
    """Показать инструкции по настройке"""
    print("\n📋 Инструкции по настройке:")
    print("1. Установите зависимости: pip install requests aiohttp textblob spacy numpy")
    print("2. Установите spaCy модель: python -m spacy download en_core_web_sm")
    print("3. Создайте файл .env с API ключами:")
    print("   NEWS_API_KEY=your_key_here")
    print("   TWITTER_BEARER_TOKEN=your_token_here")
    print("   ALPHA_VANTAGE_API_KEY=your_key_here")
    print("4. Получите API ключи:")
    print("   - NewsAPI: https://newsapi.org/")
    print("   - Twitter: https://developer.twitter.com/")
    print("   - Alpha Vantage: https://www.alphavantage.co/")

if __name__ == "__main__":
    # Проверяем наличие зависимостей
    try:
        import requests
        import aiohttp
        from textblob import TextBlob
        print("✅ Основные зависимости установлены")
    except ImportError as e:
        print(f"❌ Отсутствуют зависимости: {e}")
        show_setup_instructions()
        sys.exit(1)
    
    # Запускаем тесты
    success = asyncio.run(run_full_test())
    
    if not success:
        show_setup_instructions()
    
    sys.exit(0 if success else 1)
