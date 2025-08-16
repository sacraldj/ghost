#!/usr/bin/env python3
"""
Применение полной схемы базы данных GHOST
"""

import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client

# Загружаем переменные окружения
load_dotenv()

def apply_database_schema():
    """Применение схемы базы данных"""
    
    # Supabase настройки
    supabase_url = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Supabase credentials not found. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
        return False
    
    print(f"🔗 Подключаемся к Supabase...")
    print(f"URL: {supabase_url}")
    
    try:
        # Создаем клиент
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Читаем SQL файл
        with open('db/safe_add_new_tables.sql', 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        print("📄 Читаем SQL схему...")
        
        # Разбиваем на отдельные команды
        sql_commands = [cmd.strip() for cmd in sql_content.split(';') if cmd.strip() and not cmd.strip().startswith('--')]
        
        print(f"🔧 Выполняем {len(sql_commands)} команд...")
        
        success_count = 0
        error_count = 0
        
        for i, command in enumerate(sql_commands, 1):
            if not command:
                continue
                
            try:
                print(f"  {i}/{len(sql_commands)}: {command[:50]}...")
                
                # Выполняем команду через RPC
                result = supabase.rpc('exec_sql', {'sql': command}).execute()
                
                if result.data:
                    print(f"    ✅ Успешно")
                    success_count += 1
                else:
                    print(f"    ⚠️ Нет данных в ответе")
                    
            except Exception as e:
                print(f"    ❌ Ошибка: {e}")
                error_count += 1
                
                # Продолжаем выполнение остальных команд
                continue
        
        print(f"\n📊 Результат:")
        print(f"  ✅ Успешно: {success_count}")
        print(f"  ❌ Ошибок: {error_count}")
        
        if error_count == 0:
            print("🎉 Схема базы данных успешно применена!")
            return True
        else:
            print("⚠️ Схема применена частично. Проверьте ошибки выше.")
            return False
            
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return False

if __name__ == "__main__":
    success = apply_database_schema()
    if success:
        print("\n✅ База данных готова!")
    else:
        print("\n❌ Проблемы с базой данных!")
