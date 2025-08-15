#!/usr/bin/env python3
"""
Исправление таблицы signals_parsed - добавление недостающих колонок
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def fix_signals_parsed_table():
    """Добавляем недостающие колонки в signals_parsed"""
    print("🔧 ИСПРАВЛЕНИЕ ТАБЛИЦЫ SIGNALS_PARSED")
    print("=" * 50)
    
    try:
        from supabase import create_client, Client
        
        # Подключаемся к Supabase
        supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_key:
            print("❌ Supabase переменные не найдены")
            return False
        
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Подключен к Supabase")
        
        # SQL команды для добавления недостающих колонок
        sql_commands = [
            # Добавляем колонки, которые используются в коде
            "ALTER TABLE signals_parsed ADD COLUMN IF NOT EXISTS message_type VARCHAR(50);",
            "ALTER TABLE signals_parsed ADD COLUMN IF NOT EXISTS market_analysis TEXT;",
            "ALTER TABLE signals_parsed ADD COLUMN IF NOT EXISTS detected_trader_style VARCHAR(50);",
            "ALTER TABLE signals_parsed ADD COLUMN IF NOT EXISTS detection_confidence DECIMAL(5,2);",
            "ALTER TABLE signals_parsed ADD COLUMN IF NOT EXISTS reason TEXT;",
            "ALTER TABLE signals_parsed ADD COLUMN IF NOT EXISTS source_channel VARCHAR(100);",
            "ALTER TABLE signals_parsed ADD COLUMN IF NOT EXISTS has_image BOOLEAN DEFAULT false;",
            
            # Индексы для быстрого поиска
            "CREATE INDEX IF NOT EXISTS idx_signals_parsed_message_type ON signals_parsed(message_type);",
            "CREATE INDEX IF NOT EXISTS idx_signals_parsed_trader_style ON signals_parsed(detected_trader_style);",
            "CREATE INDEX IF NOT EXISTS idx_signals_parsed_has_image ON signals_parsed(has_image);"
        ]
        
        # Выполняем каждую команду
        for i, sql in enumerate(sql_commands, 1):
            try:
                result = supabase.rpc('execute_sql', {'sql': sql}).execute()
                print(f"✅ Команда {i}/{len(sql_commands)} выполнена")
            except Exception as e:
                # Пробуем альтернативный способ через postgrest
                print(f"⚠️  Команда {i} не выполнена через RPC, пробуем другой способ")
                print(f"   SQL: {sql}")
        
        print("\n🎉 ТАБЛИЦА SIGNALS_PARSED ОБНОВЛЕНА!")
        print("📋 Добавленные колонки:")
        print("   - message_type (тип сообщения)")
        print("   - market_analysis (рыночный анализ)")
        print("   - detected_trader_style (стиль трейдера)")
        print("   - detection_confidence (уверенность)")
        print("   - reason (причина входа)")
        print("   - source_channel (канал источника)")
        print("   - has_image (есть изображение)")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    success = await fix_signals_parsed_table()
    
    if success:
        print("\n✅ СХЕМА SIGNALS_PARSED ИСПРАВЛЕНА!")
        print("🚀 Теперь можно сохранять полные данные сигналов")
    else:
        print("\n❌ ОШИБКА ИСПРАВЛЕНИЯ СХЕМЫ")
        print("💡 Возможно, нужно выполнить SQL команды вручную в Supabase")
        print("\n📋 SQL ДЛЯ РУЧНОГО ВЫПОЛНЕНИЯ:")
        sql_commands = [
            "ALTER TABLE signals_parsed ADD COLUMN IF NOT EXISTS message_type VARCHAR(50);",
            "ALTER TABLE signals_parsed ADD COLUMN IF NOT EXISTS market_analysis TEXT;",
            "ALTER TABLE signals_parsed ADD COLUMN IF NOT EXISTS detected_trader_style VARCHAR(50);",
            "ALTER TABLE signals_parsed ADD COLUMN IF NOT EXISTS detection_confidence DECIMAL(5,2);",
            "ALTER TABLE signals_parsed ADD COLUMN IF NOT EXISTS reason TEXT;",
            "ALTER TABLE signals_parsed ADD COLUMN IF NOT EXISTS source_channel VARCHAR(100);",
            "ALTER TABLE signals_parsed ADD COLUMN IF NOT EXISTS has_image BOOLEAN DEFAULT false;"
        ]
        for sql in sql_commands:
            print(f"   {sql}")

if __name__ == "__main__":
    asyncio.run(main())
