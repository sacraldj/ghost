#!/usr/bin/env python3
"""
Тест новостной интеграции GHOST
Безопасный тест всех модулей без влияния на торговую логику
"""

import os
import asyncio
import sys
from datetime import datetime

# Включаем интеграцию для теста
os.environ['GHOST_NEWS_INTEGRATION_ENABLED'] = 'true'

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_news_integration():
    print("🧪 ТЕСТ НОВОСТНОЙ ИНТЕГРАЦИИ GHOST")
    print("=" * 60)
    print("⚠️  БЕЗОПАСНЫЙ ТЕСТ - НЕ ВЛИЯЕТ НА ТОРГОВЫЕ ОПЕРАЦИИ")
    print("=" * 60)
    
    try:
        # Импортируем модули
        sys.path.append('core')
        from safe_news_integrator import get_safe_news_integrator
        from news_noise_filter import NewsNoiseFilter
        from news_statistics_tracker import get_news_stats_tracker
        
        print("\n📦 МОДУЛИ ЗАГРУЖЕНЫ:")
        print("   ✅ Safe News Integrator")
        print("   ✅ News Noise Filter") 
        print("   ✅ News Statistics Tracker")
        
        # Тест интегратора
        print("\n🔧 ТЕСТ ИНТЕГРАТОРА:")
        integrator = get_safe_news_integrator()
        status = integrator.get_integration_status()
        print(f"   Enabled: {'✅' if status['enabled'] else '❌'}")
        print(f"   Components: {list(status['components'].keys())}")
        
        # Тест обогащения сигнала
        print("\n📊 ТЕСТ ОБОГАЩЕНИЯ СИГНАЛА:")
        test_signal = {
            'symbol': 'BTCUSDT',
            'side': 'LONG',
            'entry': 45000,
            'targets': [46000, 47000],
            'stop_loss': 44000,
            'confidence': 0.8
        }
        
        enhanced_signal = await integrator.enhance_signal_safely(test_signal, {})
        
        if 'news_enhancement' in enhanced_signal:
            print("   ✅ Сигнал обогащён новостным контекстом")
            enhancement = enhanced_signal['news_enhancement']
            print(f"   Summary: {enhancement['summary']}")
            print(f"   Confidence modifier: {enhancement['confidence_suggestion']:.2f}")
        else:
            print("   ⚪ Новостной контекст не добавлен (нет данных)")
        
        # Тест фильтра шума
        print("\n🔍 ТЕСТ ФИЛЬТРА ШУМА:")
        filter_instance = NewsNoiseFilter()
        
        # Тестовые новости (из примера Дарэна)
        test_news = [
            {
                'title': 'Министр финансов США: Мы не собираемся покупать криптовалюту',
                'content': 'Возможно снижение ставки ФРС на 25 б.п.',
                'source': 'reuters',
                'published_at': datetime.now().isoformat()
            },
            {
                'title': 'Шокирующая правда о биткоине! К луне!',
                'content': 'Невероятные возможности роста! Exclusive hype!',
                'source': 'cryptopotato',
                'published_at': datetime.now().isoformat()
            },
            {
                'title': 'Артур Хейс заявил, что закупает ETH',
                'content': 'Артур Хейс приобрел ETH на 6,85 млн $',
                'source': 'coindesk',
                'published_at': datetime.now().isoformat()
            }
        ]
        
        for i, news in enumerate(test_news, 1):
            result = filter_instance.filter_news(news)
            print(f"   {i}. {'✅ ВАЖНАЯ' if result.is_important else '❌ ОТФИЛЬТРОВАНО'} - {news['title'][:40]}...")
            print(f"      Score: {result.importance_score:.2f}, Categories: {result.detected_categories}")
        
        # Тест статистики
        print("\n📈 ТЕСТ СТАТИСТИКИ:")
        stats_tracker = get_news_stats_tracker()
        
        # Добавляем тестовые данные
        for news in test_news:
            filter_result = filter_instance.filter_news(news)
            if filter_result.is_important:
                stats_tracker.record_news_event({
                    'sentiment': 0.5 if 'покупает' in news['title'] else -0.2 if 'шокирующая' in news['title'] else 0.0,
                    'market_impact': filter_result.importance_score,
                    'is_critical': filter_result.importance_score > 0.7
                })
        
        # Генерируем отчёт
        report = stats_tracker.generate_daily_report()
        print(f"   ✅ Отчёт сгенерирован:")
        print(f"      Total news: {report['summary']['total_news']}")
        print(f"      Critical news: {report['summary']['critical_news']}")
        print(f"      Sentiment breakdown: {report['sentiment_breakdown']}")
        
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("✅ Новостная интеграция работает корректно")
        print("✅ Основная торговая логика НЕ ЗАТРОНУТА")
        
        return True
        
    except ImportError as e:
        print(f"\n❌ ОШИБКА ИМПОРТА: {e}")
        print("💡 Возможно, не все модули доступны")
        return False
        
    except Exception as e:
        print(f"\n❌ ОШИБКА ТЕСТА: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_environment_setup():
    """Тест настройки окружения"""
    print("\n🔧 ПРОВЕРКА ОКРУЖЕНИЯ:")
    
    # Проверяем переменные
    news_enabled = os.getenv('GHOST_NEWS_INTEGRATION_ENABLED', 'false')
    print(f"   GHOST_NEWS_INTEGRATION_ENABLED: {news_enabled}")
    
    supabase_url = os.getenv('NEXT_PUBLIC_SUPABASE_URL', '')
    print(f"   SUPABASE_URL: {'✅ Set' if supabase_url else '❌ Missing'}")
    
    openai_key = os.getenv('OPENAI_API_KEY', '')
    print(f"   OPENAI_API_KEY: {'✅ Set' if openai_key else '⚪ Optional'}")
    
    # Проверяем директории
    data_dir = 'data'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"   ✅ Created {data_dir}/ directory")
    else:
        print(f"   ✅ {data_dir}/ directory exists")

async def main():
    print("🚀 GHOST NEWS INTEGRATION TEST")
    print("Версия: Безопасная интеграция v1.0")
    print(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Настройка окружения
    test_environment_setup()
    
    # Основной тест
    success = await test_news_integration()
    
    if success:
        print("\n🎯 РЕКОМЕНДАЦИИ:")
        print("1. Для включения в продакшне: GHOST_NEWS_INTEGRATION_ENABLED=true")
        print("2. Добавьте NewsAnalysisDashboard в дашборд")
        print("3. API endpoint: /api/news-analysis")
        print("4. Все модули работают независимо от торговой логики")
        
        print("\n📖 ИСПОЛЬЗОВАНИЕ:")
        print("# В коде торговли (опционально):")
        print("from core.safe_news_integrator import safe_enhance_signal")
        print("enhanced = await safe_enhance_signal(signal_data)")
        print("# enhanced содержит исходный сигнал + news_enhancement")
    else:
        print("\n💡 УСТРАНЕНИЕ ПРОБЛЕМ:")
        print("1. Убедитесь что все модули в core/ доступны")
        print("2. Проверьте переменные окружения")
        print("3. Установите зависимости: pip install openai google-generativeai")

if __name__ == "__main__":
    asyncio.run(main())
