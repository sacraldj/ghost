#!/usr/bin/env python3
"""
Диагностика записи сигналов в Supabase
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def diagnose_supabase_write():
    """Диагностика записи в Supabase"""
    print("🔍 ДИАГНОСТИКА ЗАПИСИ СИГНАЛОВ В SUPABASE")
    print("=" * 60)
    
    try:
        # Импортируем компоненты
        sys.path.append('.')
        from core.live_signal_processor import LiveSignalProcessor
        from core.telegram_listener import TelegramListener
        from signals.unified_signal_system import UnifiedSignalParser, SignalSource
        from core.channel_manager import ChannelManager
        
        # Проверяем Supabase переменные
        supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_key:
            print("❌ Supabase переменные не найдены")
            print(f"SUPABASE_URL: {'✅' if supabase_url else '❌'}")
            print(f"SUPABASE_KEY: {'✅' if supabase_key else '❌'}")
            return False
        
        print("✅ Supabase переменные найдены")
        
        # Создаем процессор
        processor = LiveSignalProcessor()
        print("✅ LiveSignalProcessor создан")
        
        # Получаем источники
        sources = processor.channel_manager.get_active_sources()
        whales_source = None
        for source in sources:
            if source.source_id == "whales_guide_main":
                whales_source = source
                break
        
        if not whales_source:
            print("❌ Источник whales_guide_main не найден")
            return False
        
        print(f"✅ Источник найден: {whales_source.name}")
        
        # Тестируем запись тестового RAW сигнала
        print("\n📝 ТЕСТ ЗАПИСИ RAW СИГНАЛА...")
        test_raw_data = {
            "chat_id": "-1001288385100",
            "message_id": "test_raw_1",
            "text": "🚀 #BTC LONG Entry: $45000-$45500 Targets: $46000, $47000 SL: $44000 Leverage: 10X",
            "timestamp": datetime.now(),
            "has_image": False,
            "channel_name": "Whales Crypto Guide",
            "trader_id": "whales_guide_main"
        }
        
        await processor._save_raw_signal(test_raw_data["text"], whales_source, test_raw_data)
        print("✅ RAW сигнал записан в signals_raw")
        
        # Тестируем парсинг и запись PARSED сигнала
        print("\n🧠 ТЕСТ ПАРСИНГА И ЗАПИСИ PARSED СИГНАЛА...")
        parsed_signal = await processor.unified_parser.parse_signal(
            test_raw_data["text"],
            SignalSource.TELEGRAM_WHALESGUIDE,
            whales_source.parser_type
        )
        
        if parsed_signal:
            await processor._save_parsed_signal(parsed_signal, whales_source)
            print("✅ PARSED сигнал записан в signals_parsed")
            print(f"   Symbol: {parsed_signal.symbol}")
            print(f"   Side: {parsed_signal.side}")
            print(f"   Entry: {parsed_signal.entry_zone}")
            print(f"   Targets: {parsed_signal.targets}")
        else:
            print("❌ Парсинг не удался")
        
        # Тестируем реальное подключение к Telegram
        print("\n📱 ТЕСТ ПОДКЛЮЧЕНИЯ К TELEGRAM...")
        api_id = os.getenv('TELEGRAM_API_ID')
        api_hash = os.getenv('TELEGRAM_API_HASH')
        phone = os.getenv('TELEGRAM_PHONE')
        
        if not all([api_id, api_hash, phone]):
            print("❌ Telegram переменные не найдены")
            print(f"API_ID: {'✅' if api_id else '❌'}")
            print(f"API_HASH: {'✅' if api_hash else '❌'}")
            print(f"PHONE: {'✅' if phone else '❌'}")
            return False
        
        listener = TelegramListener(api_id, api_hash, phone)
        if not await listener.initialize():
            print("❌ Подключение к Telegram не удалось")
            return False
        
        print("✅ Подключен к Telegram")
        
        # Проверяем авторизацию
        if listener.client and await listener.client.is_user_authorized():
            print("✅ Telegram авторизация активна")
        else:
            print("⚠️ Telegram требует авторизации")
        
        # Закрываем соединение
        if listener.client:
            await listener.client.disconnect()
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка диагностики: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    success = await diagnose_supabase_write()
    
    if success:
        print("\n🎉 ДИАГНОСТИКА УСПЕШНА!")
        print("✅ Система может записывать сигналы в Supabase")
        print("💡 Проверьте таблицы signals_raw и signals_parsed в Supabase")
        print("🔄 После деплоя на Render система начнет получать реальные сигналы")
    else:
        print("\n❌ ПРОБЛЕМА С ЗАПИСЬЮ")
        print("💡 Исправьте ошибки выше и повторите тест")

if __name__ == "__main__":
    asyncio.run(main())
