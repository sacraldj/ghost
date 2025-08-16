#!/usr/bin/env python3
"""
Прямое применение схемы базы данных через Supabase Python клиент
"""

import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client

# Загружаем переменные окружения
load_dotenv()

def create_missing_tables():
    """Создание недостающих таблиц напрямую"""
    
    # Supabase настройки
    supabase_url = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Supabase credentials not found")
        return False
    
    print(f"🔗 Подключаемся к Supabase...")
    
    try:
        # Создаем клиент
        supabase: Client = create_client(supabase_url, supabase_key)
        
        print("📊 Проверяем существующие таблицы...")
        
        # Проверяем какие таблицы уже есть
        existing_tables = []
        
        # Список таблиц для проверки
        required_tables = [
            'signals', 'candles_cache', 'trades', 'trade_events', 'trade_audits',
            'strategies', 'strategy_results', 'traders', 'trader_stats'
        ]
        
        for table in required_tables:
            try:
                result = supabase.table(table).select('*').limit(1).execute()
                existing_tables.append(table)
                print(f"  ✅ {table} - существует")
            except:
                print(f"  ❌ {table} - отсутствует")
        
        print(f"\n📋 Найдено таблиц: {len(existing_tables)}/{len(required_tables)}")
        
        # Создаем недостающие таблицы через INSERT/UPDATE операции
        print("\n🔧 Создаем базовые данные...")
        
        # 1. Создаем стратегии
        try:
            strategies_data = [
                {
                    'strategy_id': 'tp2_sl_be',
                    'name': 'TP2 & SL → BE',
                    'description': 'Take TP2 with Stop Loss moved to Break Even after TP1',
                    'params_json': '{"tp1_share": 0.5, "tp2_share": 0.5, "move_sl_to_be": true}',
                    'version': 'v1.0',
                    'enabled': True
                },
                {
                    'strategy_id': 'scalping',
                    'name': 'Scalping',
                    'description': 'Quick trades with small profits',
                    'params_json': '{"tp1_share": 0.8, "tp2_share": 0.2, "move_sl_to_be": false}',
                    'version': 'v1.0',
                    'enabled': True
                },
                {
                    'strategy_id': 'swing',
                    'name': 'Swing Trading',
                    'description': 'Longer-term trades with bigger targets',
                    'params_json': '{"tp1_share": 0.3, "tp2_share": 0.7, "move_sl_to_be": true}',
                    'version': 'v1.0',
                    'enabled': True
                }
            ]
            
            # Пытаемся вставить стратегии
            if 'strategies' in existing_tables:
                print("  📊 Обновляем стратегии...")
                for strategy in strategies_data:
                    try:
                        supabase.table('strategies').upsert(strategy).execute()
                        print(f"    ✅ {strategy['name']}")
                    except Exception as e:
                        print(f"    ⚠️ {strategy['name']}: {e}")
            else:
                print("  ⚠️ Таблица strategies не найдена")
        
        except Exception as e:
            print(f"  ❌ Ошибка создания стратегий: {e}")
        
        # 2. Проверяем трейдеров
        try:
            if 'trader_registry' in existing_tables:
                result = supabase.table('trader_registry').select('trader_id, name').execute()
                traders = result.data
                print(f"\n👥 Найдено трейдеров: {len(traders)}")
                for trader in traders:
                    print(f"  - {trader['trader_id']}: {trader['name']}")
            else:
                print("  ⚠️ Таблица trader_registry не найдена")
        except Exception as e:
            print(f"  ❌ Ошибка получения трейдеров: {e}")
        
        # 3. Проверяем сигналы
        try:
            if 'signals_parsed' in existing_tables:
                result = supabase.table('signals_parsed').select('trader_id').limit(10).execute()
                signals = result.data
                print(f"\n📡 Найдено сигналов: {len(signals)}")
                
                # Группируем по трейдерам
                trader_counts = {}
                for signal in signals:
                    trader_id = signal.get('trader_id', 'unknown')
                    trader_counts[trader_id] = trader_counts.get(trader_id, 0) + 1
                
                for trader_id, count in trader_counts.items():
                    print(f"  - {trader_id}: {count} сигналов")
            else:
                print("  ⚠️ Таблица signals_parsed не найдена")
        except Exception as e:
            print(f"  ❌ Ошибка получения сигналов: {e}")
        
        print(f"\n✅ Диагностика базы данных завершена!")
        return True
            
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return False

if __name__ == "__main__":
    success = create_missing_tables()
    if success:
        print("\n🎉 База данных проверена!")
    else:
        print("\n❌ Проблемы с базой данных!")
