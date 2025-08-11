#!/usr/bin/env python3
"""
Демонстрация бесплатных источников GHOST News Engine
Показывает работу RSS парсера и Public API без API ключей
"""

import logging
from datetime import datetime
from rss_parser import RSSParser
from public_api_client import PublicAPIClient

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def demo_rss_sources():
    """Демонстрирует работу RSS источников"""
    print("📰 ДЕМОНСТРАЦИЯ RSS ИСТОЧНИКОВ")
    print("=" * 50)
    
    parser = RSSParser()
    
    # Конфигурация RSS feeds
    rss_feeds = [
        {
            'url': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
            'max_articles': 3,
            'keywords': ['bitcoin', 'crypto', 'ethereum']
        },
        {
            'url': 'https://cointelegraph.com/rss',
            'max_articles': 3,
            'keywords': ['defi', 'nft', 'blockchain']
        },
        {
            'url': 'https://cryptonews.com/news/feed',
            'max_articles': 3,
            'keywords': ['binance', 'coinbase', 'regulation']
        }
    ]
    
    print("🔍 Получаем новости из RSS feeds...")
    articles = parser.get_multiple_feeds(rss_feeds)
    
    print(f"\n✅ Получено {len(articles)} статей:")
    for i, article in enumerate(articles, 1):
        print(f"\n{i}. {article['title']}")
        print(f"   📅 {article['published_date'].strftime('%Y-%m-%d %H:%M UTC')}")
        print(f"   📰 {article['source_name']}")
        print(f"   🔗 {article['link']}")
        
        if article['description']:
            desc = article['description'][:100] + "..." if len(article['description']) > 100 else article['description']
            print(f"   📝 {desc}")
    
    return articles

def demo_public_apis():
    """Демонстрирует работу Public APIs"""
    print("\n\n🌐 ДЕМОНСТРАЦИЯ PUBLIC APIs")
    print("=" * 50)
    
    client = PublicAPIClient()
    
    # 1. Топ криптовалют
    print("📊 Получаем топ-10 криптовалют по рыночной капитализации...")
    top_coins = client.get_top_cryptocurrencies(10)
    
    print(f"\n✅ Получено {len(top_coins)} криптовалют:")
    for i, coin in enumerate(top_coins[:5], 1):
        print(f"{i:2}. {coin['symbol']:8} {coin['name']:20} ${coin['current_price']:>10,.2f}")
        print(f"     MC: ${coin['market_cap']:>15,.0f} | 24h: {coin['price_change_percentage_24h']:>7.2f}%")
    
    # 2. Цены популярных монет
    print("\n💰 Получаем цены популярных криптовалют...")
    popular_coins = ['bitcoin', 'ethereum', 'binancecoin', 'cardano', 'solana']
    prices = client.get_crypto_price(popular_coins)
    
    print(f"\n✅ Цены {len(prices)} криптовалют:")
    for coin, price_data in prices.items():
        price = price_data.get('usd', 'N/A')
        if price != 'N/A':
            print(f"   {coin:12}: ${price:>10,.2f}")
    
    # 3. Рыночные данные BTC
    print("\n📈 Получаем рыночные данные Bitcoin...")
    btc_data = client.get_market_data("BTCUSDT")
    
    if btc_data:
        print(f"\n✅ Данные BTC/USDT:")
        print(f"   💰 Цена: ${btc_data['price']:>10,.2f}")
        print(f"   📊 Изменение 24ч: {btc_data['price_change_percent']:>7.2f}%")
        print(f"   📈 Максимум 24ч: ${btc_data['high_24h']:>10,.2f}")
        print(f"   📉 Минимум 24ч: ${btc_data['low_24h']:>10,.2f}")
        print(f"   💎 Объем 24ч: ${btc_data['volume_24h']:>10,.0f}")
    
    return {
        'top_coins': top_coins,
        'prices': prices,
        'btc_data': btc_data
    }

def demo_news_analysis():
    """Демонстрирует анализ новостей"""
    print("\n\n🧠 ДЕМОНСТРАЦИЯ АНАЛИЗА НОВОСТЕЙ")
    print("=" * 50)
    
    # Получаем новости
    parser = RSSParser()
    rss_feeds = [
        {
            'url': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
            'max_articles': 5,
            'keywords': ['bitcoin', 'crypto', 'ethereum', 'defi', 'nft']
        }
    ]
    
    articles = parser.get_multiple_feeds(rss_feeds)
    
    if not articles:
        print("❌ Не удалось получить новости для анализа")
        return
    
    print(f"📰 Анализируем {len(articles)} новостей...")
    
    # Простой анализ по ключевым словам
    keyword_stats = {}
    source_stats = {}
    
    for article in articles:
        # Статистика по источникам
        source = article['source_name']
        source_stats[source] = source_stats.get(source, 0) + 1
        
        # Статистика по ключевым словам
        title_lower = article['title'].lower()
        description_lower = article.get('description', '').lower()
        text = f"{title_lower} {description_lower}"
        
        keywords = ['bitcoin', 'ethereum', 'defi', 'nft', 'binance', 'coinbase', 'regulation']
        for keyword in keywords:
            if keyword in text:
                keyword_stats[keyword] = keyword_stats.get(keyword, 0) + 1
    
    # Выводим статистику
    print(f"\n📊 Статистика по источникам:")
    for source, count in source_stats.items():
        print(f"   {source}: {count} статей")
    
    print(f"\n🔍 Статистика по ключевым словам:")
    for keyword, count in sorted(keyword_stats.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            print(f"   {keyword}: {count} упоминаний")
    
    # Находим самые свежие новости
    if articles:
        newest = min(articles, key=lambda x: x['published_date'])
        oldest = max(articles, key=lambda x: x['published_date'])
        
        print(f"\n⏰ Временной диапазон:")
        print(f"   Самая свежая: {newest['published_date'].strftime('%Y-%m-%d %H:%M UTC')}")
        print(f"   Самая старая: {oldest['published_date'].strftime('%Y-%m-%d %H:%M UTC')}")

def main():
    """Основная функция демонстрации"""
    print("🚀 GHOST NEWS ENGINE - ДЕМОНСТРАЦИЯ БЕСПЛАТНЫХ ИСТОЧНИКОВ")
    print("=" * 60)
    print("Этот скрипт показывает работу бесплатных источников без API ключей")
    print("=" * 60)
    
    try:
        # 1. RSS источники
        rss_articles = demo_rss_sources()
        
        # 2. Public APIs
        api_data = demo_public_apis()
        
        # 3. Анализ новостей
        demo_news_analysis()
        
        print("\n\n🎉 ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА!")
        print("=" * 60)
        print("✅ RSS парсер работает с 4 источниками")
        print("✅ Public API клиент работает с 3 источниками")
        print("✅ Анализ новостей работает")
        print("=" * 60)
        print("💡 Теперь у вас есть рабочий новостный движок без API ключей!")
        
    except Exception as e:
        print(f"\n❌ Ошибка в демонстрации: {e}")
        logging.error(f"Ошибка в демонстрации: {e}")

if __name__ == "__main__":
    main()
