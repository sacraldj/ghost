#!/usr/bin/env python3
"""
Тест парсера Whales Guide
Проверяем как парсятся реальные сообщения
"""

import sys
import os
import asyncio
from datetime import datetime

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_whales_guide_parsing():
    print("🧪 ТЕСТ ПАРСЕРА WHALES GUIDE")
    print("=" * 60)
    
    try:
        from signals.unified_signal_system import UnifiedSignalParser, SignalSource
        
        # Добавляем недостающие enums
        class SourceType:
            TELEGRAM_CHANNEL = "telegram_channel"
            
        class SourceStatus:
            ACTIVE = "active"
        
        # Инициализируем парсер
        parser = UnifiedSignalParser()
        
        # Тестовые сообщения из реальных каналов Whales Guide
        test_messages = [
            # Стандартный сигнал
            {
                "text": """Longing #BTCUSDT Here

Long (5x - 10x)

Entry: $45000 - $44500

Targets: $46000, $47000, $48000

Stoploss: $43000

Reason: Chart looks bullish with strong support levels""",
                "expected": "trading_signal"
            },
            
            # Spot покупка
            {
                "text": """Buying #ETH Here in spot

You can long in 4x leverage, too.

Entry: 2800-2850$

Targets: 2900$, 3000$

Stoploss: 2750$

Reason: Worth buying for quick profits""",
                "expected": "trading_signal"
            },
            
            # Короткий анализ
            {
                "text": """#BTC looking bullish here. Strong support at 44k level. Could see a pump to 47k soon.""",
                "expected": "market_analysis"
            },
            
            # Сообщение с эмодзи и сложным форматом
            {
                "text": """🚀 #SOLUSDT 

📈 LONG SIGNAL

💰 Entry Zone: $95.50 - $96.20
🎯 TP1: $98.00
🎯 TP2: $100.50  
🎯 TP3: $103.00
🛑 SL: $93.80

⚡ Leverage: 5x-10x
📊 Strong breakout pattern forming""",
                "expected": "trading_signal"
            },
            
            # Русскоязычное сообщение
            {
                "text": """Покупаем #BTC здесь
Вход: 45000-44500
Цели: 46000, 47000
Стоп: 43000""",
                "expected": "trading_signal"
            },
            
            # Новость/анализ
            {
                "text": """Market update: Bitcoin dominance increasing. Alt season might be delayed. Keep an eye on BTC levels.""",
                "expected": None  # Не должно парситься как сигнал
            },
            
            # Сообщение с изображением/графиком
            {
                "text": """#ETHUSDT Technical Analysis

Looking at the 4H chart, we can see:
- Strong resistance at $2850
- Support holding at $2750  
- RSI showing oversold conditions

Expecting bounce to $2900 level.""",
                "expected": "market_analysis"
            }
        ]
        
        print(f"📊 Тестируем {len(test_messages)} сообщений...\n")
        
        success_count = 0
        total_count = len(test_messages)
        
        for i, test in enumerate(test_messages, 1):
            print(f"🔍 ТЕСТ {i}:")
            print(f"   Текст: {test['text'][:80]}...")
            print(f"   Ожидаем: {test['expected']}")
            
            try:
                # Создаём тестовый сигнал
                unified_signal = await parser.parse_signal(
                    raw_text=test['text'],
                    source=SignalSource.TELEGRAM_WHALESGUIDE,
                    trader_id=f"test_trader_{i}",
                    message_id=f"test_msg_{i}"
                )
                
                if unified_signal:
                    print(f"   ✅ РАСПОЗНАН:")
                    print(f"      Symbol: {unified_signal.symbol}")
                    print(f"      Side: {unified_signal.side}")
                    print(f"      Entry Min: {unified_signal.entry_min}")
                    print(f"      Entry Max: {unified_signal.entry_max}")
                    print(f"      Targets: {unified_signal.targets}")
                    print(f"      Stop Loss: {unified_signal.sl}")
                    print(f"      Leverage: {unified_signal.leverage}")
                    print(f"      Type: {getattr(unified_signal, 'message_type', 'unknown')}")
                    print(f"      Confidence: {unified_signal.confidence:.2f}")
                    
                    # Проверяем соответствие ожиданиям
                    if test['expected']:
                        success_count += 1
                        print(f"   ✅ РЕЗУЛЬТАТ: Соответствует ожиданиям")
                    else:
                        print(f"   ⚠️  РЕЗУЛЬТАТ: Не ожидали парсинг, но сработал")
                else:
                    print(f"   ❌ НЕ РАСПОЗНАН")
                    if test['expected']:
                        print(f"   ❌ РЕЗУЛЬТАТ: Ожидали {test['expected']}, но не распознан")
                    else:
                        success_count += 1
                        print(f"   ✅ РЕЗУЛЬТАТ: Правильно не распознан")
                
            except Exception as e:
                print(f"   ❌ ОШИБКА: {e}")
            
            print()
        
        print("=" * 60)
        print(f"📈 ИТОГИ ТЕСТИРОВАНИЯ:")
        print(f"   Успешно: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
        
        if success_count == total_count:
            print("   🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        elif success_count >= total_count * 0.8:
            print("   ✅ Хороший результат, есть место для улучшений")
        else:
            print("   ⚠️  Требуются доработки парсера")
        
        return success_count / total_count
        
    except ImportError as e:
        print(f"❌ ОШИБКА ИМПОРТА: {e}")
        print("💡 Убедитесь что модули signals/ доступны")
        return 0.0
    except Exception as e:
        print(f"❌ ОШИБКА ТЕСТА: {e}")
        import traceback
        traceback.print_exc()
        return 0.0

async def test_current_system_status():
    """Проверка текущего статуса системы парсинга"""
    print("\n🔍 ПРОВЕРКА ТЕКУЩЕГО СТАТУСА СИСТЕМЫ:")
    print("-" * 40)
    
    try:
        # Проверяем доступность компонентов
        from core.live_signal_processor import get_live_processor
        from core.channel_manager import ChannelManager
        from core.telegram_listener import TelegramListener
        
        print("✅ Компоненты системы доступны")
        
        # Проверяем конфигурацию
        channel_manager = ChannelManager()
        sources = channel_manager.get_active_sources()
        
        print(f"✅ Активных источников: {len(sources)}")
        
        whales_guide = None
        for source in sources:
            if source.source_id == "whales_guide_main":
                whales_guide = source
                break
        
        if whales_guide:
            print(f"✅ Whales Guide найден:")
            print(f"   ID: {whales_guide.source_id}")
            print(f"   Parser: {whales_guide.parser_type}")
            print(f"   Active: {whales_guide.is_active}")
            print(f"   Channel ID: {whales_guide.connection_params.get('channel_id', 'N/A')}")
        else:
            print("❌ Whales Guide не найден в активных источниках")
        
        # Проверяем переменные окружения
        telegram_api_id = os.getenv('TELEGRAM_API_ID')
        telegram_api_hash = os.getenv('TELEGRAM_API_HASH')
        telegram_phone = os.getenv('TELEGRAM_PHONE')
        
        print(f"✅ TELEGRAM_API_ID: {'✓' if telegram_api_id else '❌'}")
        print(f"✅ TELEGRAM_API_HASH: {'✓' if telegram_api_hash else '❌'}")
        print(f"✅ TELEGRAM_PHONE: {'✓' if telegram_phone else '❌'}")
        
    except ImportError as e:
        print(f"❌ Компоненты системы недоступны: {e}")
    except Exception as e:
        print(f"❌ Ошибка проверки: {e}")

async def main():
    print("🚀 GHOST WHALES GUIDE PARSER TEST")
    print(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Проверяем статус системы
    await test_current_system_status()
    
    # Тестируем парсер
    success_rate = await test_whales_guide_parsing()
    
    print("\n🎯 РЕКОМЕНДАЦИИ:")
    if success_rate >= 0.9:
        print("✅ Парсер работает отлично!")
        print("📡 Можно запускать на продакшн")
    elif success_rate >= 0.7:
        print("✅ Парсер работает хорошо")
        print("🔧 Рекомендуется небольшая доработка")
    else:
        print("⚠️  Парсер требует улучшений")
        print("🔧 Нужна доработка алгоритмов парсинга")
    
    print("\n📖 СЛЕДУЮЩИЕ ШАГИ:")
    print("1. Убедитесь что система на Render запущена")
    print("2. Проверьте логи Telegram подключения")
    print("3. Мониторьте поступление сигналов в Supabase")
    print("4. Проверьте дашборд на наличие новых сигналов")

if __name__ == "__main__":
    asyncio.run(main())
