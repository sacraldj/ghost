#!/usr/bin/env python3
"""
Простая проверка Supabase - что есть в базе данных
"""

import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

try:
    from supabase import create_client
except ImportError:
    print("❌ Установите: pip install supabase")
    exit(1)

# Подключаемся
supabase_url = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not supabase_url or not supabase_key:
    print("❌ Нет переменных NEXT_PUBLIC_SUPABASE_URL и SUPABASE_SERVICE_ROLE_KEY")
    exit(1)

supabase = create_client(supabase_url, supabase_key)

print("🔍 ПРОВЕРКА БАЗЫ ДАННЫХ SUPABASE")
print("=" * 50)
print(f"URL: {supabase_url}")

# Список таблиц для проверки
tables_to_check = [
    'trader_registry',
    'signals_raw', 
    'signals_parsed',
    'unified_signals',
    'trades',
    'news_events',
    'profiles'
]

print("\n📊 ПРОВЕРКА ТАБЛИЦ:")

for table_name in tables_to_check:
    try:
        result = supabase.table(table_name).select('*', count='exact').limit(0).execute()
        count = result.count or 0
        print(f"✅ {table_name}: {count} записей")
    except Exception as e:
        print(f"❌ {table_name}: НЕТ ({str(e)[:50]}...)")

print("\n🎯 ДЕТАЛЬНАЯ ПРОВЕРКА КЛЮЧЕВЫХ ТАБЛИЦ:")

# Проверяем трейдеров
try:
    result = supabase.table('trader_registry').select('trader_id, name, is_active').execute()
    if result.data:
        print(f"\n👥 ТРЕЙДЕРЫ ({len(result.data)}):")
        for trader in result.data:
            status = "🟢" if trader.get('is_active') else "🔴"
            print(f"  {status} {trader.get('name')} ({trader.get('trader_id')})")
    else:
        print("\n👥 ТРЕЙДЕРЫ: Пусто")
except Exception as e:
    print(f"\n👥 ТРЕЙДЕРЫ: Ошибка - {e}")

# Проверяем сигналы
try:
    result = supabase.table('signals_raw').select('trader_id, created_at').order('created_at', desc=True).limit(3).execute()
    if result.data:
        print(f"\n📡 ПОСЛЕДНИЕ СЫРЫЕ СИГНАЛЫ ({len(result.data)}):")
        for signal in result.data:
            print(f"  📝 {signal.get('trader_id')} - {signal.get('created_at')}")
    else:
        print("\n📡 СЫРЫЕ СИГНАЛЫ: Пусто")
except Exception as e:
    print(f"\n📡 СЫРЫЕ СИГНАЛЫ: Ошибка - {e}")

try:
    result = supabase.table('signals_parsed').select('trader_id, symbol, side, posted_at').order('posted_at', desc=True).limit(3).execute()
    if result.data:
        print(f"\n💹 ПОСЛЕДНИЕ ОБРАБОТАННЫЕ СИГНАЛЫ ({len(result.data)}):")
        for signal in result.data:
            print(f"  💎 {signal.get('trader_id')}: {signal.get('symbol')} {signal.get('side')} - {signal.get('posted_at')}")
    else:
        print("\n💹 ОБРАБОТАННЫЕ СИГНАЛЫ: Пусто")
except Exception as e:
    print(f"\n💹 ОБРАБОТАННЫЕ СИГНАЛЫ: Ошибка - {e}")

print("\n" + "=" * 50)
print("✅ ПРОВЕРКА ЗАВЕРШЕНА!")
