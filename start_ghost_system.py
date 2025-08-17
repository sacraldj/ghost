#!/usr/bin/env python3
"""
GHOST System Launcher
Простой запуск основных компонентов системы Ghost
"""

import asyncio
import os
import sys
import logging
from datetime import datetime

# Добавляем текущую директорию в путь
sys.path.insert(0, os.getcwd())

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_supabase_connection():
    """Тестирование подключения к Supabase"""
    try:
        from signals.signal_orchestrator_with_supabase import SignalOrchestratorWithSupabase
        
        logger.info("🔍 Проверка подключения к Supabase...")
        orchestrator = SignalOrchestratorWithSupabase()
        
        # Тестируем подключение
        connected = await orchestrator.test_supabase_connection()
        
        if connected:
            logger.info("✅ Supabase подключение успешно!")
            
            # Получаем статистику
            stats = await orchestrator.get_stats()
            logger.info(f"📊 Доступно парсеров: {len(stats['parsers_available'])}")
            logger.info(f"🎯 Парсеры: {', '.join(stats['parsers_available'])}")
            
            return orchestrator
        else:
            logger.error("❌ Supabase подключение не удалось")
            return None
            
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации: {e}")
        return None

async def test_signal_processing(orchestrator):
    """Тестирование обработки сигналов"""
    if not orchestrator:
        return
    
    logger.info("🧪 Тестирование обработки сигналов...")
    
    # Тестовые сигналы для каждого парсера
    test_signals = [
        {
            'text': '''
            Longing #BTC Here
            
            Long (5x - 10x)
            
            Entry: $45000 - $44000
            
            Targets: $46000, $47000, $48000
            
            Stoploss: $43000
            ''',
            'trader_id': 'whales_crypto_guide',
            'name': 'Whales Crypto Test'
        },
        {
            'text': '''
            BTCUSDT LONG
            
            PAIR: BTC
            DIRECTION: LONG
            
            ВХОД: 45000-46000
            
            ЦЕЛИ:
            47000
            48000
            49000
            
            СТОП: 43000
            ''',
            'trader_id': '2trade_premium',
            'name': '2Trade Test'
        },
        {
            'text': '''
            🚀🔥 #ALPINE запампили на +57% со вчерашнего вечера. 
            В 18:30 по мск он закрепился в топе по спотовым покупкам на Binance.
            ''',
            'trader_id': 'cryptoattack24',
            'name': 'CryptoAttack24 Test'
        }
    ]
    
    successful_tests = 0
    
    for test in test_signals:
        try:
            logger.info(f"   🔄 Тестируем {test['name']}...")
            
            result = await orchestrator.process_raw_signal(
                test['text'], 
                test['trader_id'], 
                test['trader_id']
            )
            
            if result:
                logger.info(f"   ✅ {test['name']}: {result.symbol} {result.direction}")
                successful_tests += 1
            else:
                logger.warning(f"   ⚠️ {test['name']}: Не удалось обработать")
                
        except Exception as e:
            logger.error(f"   ❌ {test['name']}: Ошибка - {e}")
    
    logger.info(f"📊 Тестирование завершено: {successful_tests}/{len(test_signals)} успешно")
    return successful_tests

async def start_telegram_listener():
    """Запуск Telegram слушателя"""
    try:
        logger.info("📱 Попытка запуска Telegram Listener...")
        
        # Проверяем переменные окружения
        api_id = os.getenv('TELEGRAM_API_ID')
        api_hash = os.getenv('TELEGRAM_API_HASH')
        
        if not api_id or not api_hash:
            logger.warning("⚠️ TELEGRAM_API_ID и TELEGRAM_API_HASH не настроены")
            logger.info("   Для полной работы системы нужно настроить Telegram API")
            return False
        
        from core.telegram_listener import TelegramListener
        
        listener = TelegramListener(api_id, api_hash)
        
        # Инициализируем (но не запускаем полностью)
        initialized = await listener.initialize()
        
        if initialized:
            logger.info("✅ Telegram Listener готов к работе")
            return True
        else:
            logger.warning("⚠️ Telegram Listener не удалось инициализировать")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка Telegram Listener: {e}")
        return False

async def main():
    """Главная функция запуска системы"""
    logger.info("🚀 Запуск GHOST Trading System")
    logger.info("=" * 50)
    logger.info(f"📅 Время запуска: {datetime.now()}")
    
    # 1. Тестируем Supabase
    orchestrator = await test_supabase_connection()
    
    if not orchestrator:
        logger.error("💥 Критическая ошибка: Supabase не доступен")
        logger.info("🔧 Проверьте переменные окружения:")
        logger.info("   - NEXT_PUBLIC_SUPABASE_URL")
        logger.info("   - SUPABASE_SERVICE_ROLE_KEY")
        return
    
    # 2. Тестируем обработку сигналов
    successful_signals = await test_signal_processing(orchestrator)
    
    if successful_signals == 0:
        logger.warning("⚠️ Ни один сигнал не был обработан успешно")
    
    # 3. Тестируем Telegram
    telegram_ready = await start_telegram_listener()
    
    # 4. Итоговый отчет
    logger.info("\n" + "=" * 50)
    logger.info("📊 ИТОГОВЫЙ СТАТУС СИСТЕМЫ")
    logger.info("=" * 50)
    
    logger.info(f"✅ Supabase подключение: {'ОК' if orchestrator else 'ОШИБКА'}")
    logger.info(f"✅ Обработка сигналов: {successful_signals}/3 парсеров работают")
    logger.info(f"✅ Telegram готовность: {'ОК' if telegram_ready else 'ТРЕБУЕТ НАСТРОЙКИ'}")
    
    if orchestrator and successful_signals > 0:
        logger.info("🎉 Основные компоненты системы работают!")
        logger.info("🌐 Dashboard доступен по адресу:")
        logger.info("   https://ghost-6nu0rvupx-sacralpros-projects.vercel.app")
        
        if not telegram_ready:
            logger.info("\n🔧 Для полной работы настройте:")
            logger.info("   1. TELEGRAM_API_ID и TELEGRAM_API_HASH в .env")
            logger.info("   2. Запустите: python core/telegram_listener.py")
    else:
        logger.error("💥 Система требует исправлений")
    
    logger.info("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
