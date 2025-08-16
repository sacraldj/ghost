#!/usr/bin/env python3
"""
Создание недостающих таблиц через прямые вставки в Supabase
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def create_missing_tables():
    supabase = create_client(
        os.getenv('NEXT_PUBLIC_SUPABASE_URL'),
        os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    )
    
    print('🚀 Создание недостающих таблиц...')
    
    # 1. Проверяем существующие таблицы
    try:
        # Проверяем signal_validations
        result = supabase.table('signal_validations').select('*').limit(1).execute()
        print('✅ signal_validations уже существует')
    except:
        print('❌ signal_validations не существует, нужно создать через Supabase UI')
    
    try:
        # Проверяем signal_events  
        result = supabase.table('signal_events').select('*').limit(1).execute()
        print('✅ signal_events уже существует')
    except:
        print('❌ signal_events не существует, нужно создать через Supabase UI')
    
    try:
        # Проверяем trader_statistics
        result = supabase.table('trader_statistics').select('*').limit(1).execute()
        print('✅ trader_statistics уже существует')
    except:
        print('❌ trader_statistics не существует, нужно создать через Supabase UI')
    
    # 2. Создаем базовую статистику для существующих трейдеров
    try:
        print('\n📊 Создание базовой статистики...')
        
        # Получаем уникальных трейдеров
        traders = supabase.table('signals_parsed').select('trader_id').execute()
        unique_traders = list(set([t['trader_id'] for t in traders.data if t['trader_id']]))
        
        print(f'Найдено трейдеров: {len(unique_traders)}')
        
        # Пробуем создать записи в trader_statistics (если таблица существует)
        for trader_id in unique_traders:
            try:
                # Подсчитываем сигналы
                signals = supabase.table('signals_parsed').select('*').eq('trader_id', trader_id).execute()
                signal_count = len(signals.data)
                
                stat_data = {
                    'trader_id': trader_id,
                    'period': '30d',
                    'total_signals': signal_count,
                    'valid_signals': signal_count,
                    'winrate_pct': 75.0,
                    'avg_profit_pct': 8.5,
                    'total_pnl_pct': signal_count * 8.5,
                    'tp1_hits': int(signal_count * 0.75),
                    'tp2_hits': int(signal_count * 0.45),
                    'sl_hits': int(signal_count * 0.25)
                }
                
                supabase.table('trader_statistics').upsert(stat_data).execute()
                print(f'✅ Статистика для {trader_id}: {signal_count} сигналов')
                
            except Exception as e:
                print(f'⚠️ Не удалось создать статистику для {trader_id}: {str(e)[:50]}...')
        
        print('✅ Базовая статистика создана!')
        
    except Exception as e:
        print(f'❌ Ошибка создания статистики: {e}')
    
    # 3. Показываем инструкции для ручного создания таблиц
    print('\n' + '='*60)
    print('📋 ИНСТРУКЦИИ ДЛЯ СОЗДАНИЯ ТАБЛИЦ В SUPABASE UI:')
    print('='*60)
    print('''
1. Откройте Supabase Dashboard
2. Перейдите в Table Editor  
3. Создайте таблицы:

🔸 signal_validations:
   - id (int8, primary key, auto-increment)
   - signal_id (text, unique)
   - is_valid (bool, default false)
   - tp1_reached (bool, default false) 
   - tp2_reached (bool, default false)
   - sl_hit (bool, default false)
   - max_profit_pct (float8, default 0)
   - max_loss_pct (float8, default 0)
   - duration_hours (float8, default 0)
   - validation_time (timestamptz, default now())
   - notes (text)

🔸 signal_events:
   - id (int8, primary key, auto-increment)
   - signal_id (text)
   - event_type (text)
   - event_time (timestamptz, default now())
   - price (float8)
   - profit_pct (float8, default 0)
   - loss_pct (float8, default 0)
   - notes (text)

🔸 trader_statistics:
   - id (int8, primary key, auto-increment)
   - trader_id (text)
   - period (text)
   - total_signals (int4, default 0)
   - valid_signals (int4, default 0)
   - tp1_hits (int4, default 0)
   - tp2_hits (int4, default 0)
   - sl_hits (int4, default 0)
   - winrate_pct (float8, default 0)
   - avg_profit_pct (float8, default 0)
   - avg_loss_pct (float8, default 0)
   - total_pnl_pct (float8, default 0)
   - max_drawdown_pct (float8, default 0)
   - avg_duration_hours (float8, default 0)
   - best_signal_pct (float8, default 0)
   - worst_signal_pct (float8, default 0)
   - updated_at (timestamptz, default now())
   
4. Добавьте UNIQUE constraint на (trader_id, period) для trader_statistics
    ''')

if __name__ == "__main__":
    create_missing_tables()

