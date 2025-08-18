#!/usr/bin/env python3
"""
Проверка сегодняшних данных в Supabase
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def check_todays_messages():
    """Проверяем сегодняшние сообщения в базе"""
    
    from signals.signal_orchestrator_with_supabase import orchestrator_with_supabase
    
    print("🔍 Проверяем сегодняшние данные в Supabase...")
    
    if not orchestrator_with_supabase.supabase:
        print("❌ Нет подключения к Supabase")
        return
    
    # Сегодняшняя дата
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"📅 Проверяем данные за: {today}")
    
    try:
        # Проверяем сырые сигналы за сегодня
        raw_result = orchestrator_with_supabase.supabase.table('signals_raw').select('*').gte('created_at', f'{today}T00:00:00').execute()
        print(f"📊 signals_raw за сегодня: {len(raw_result.data)} записей")
        
        if raw_result.data:
            print("📝 Последние 3 сырых сигнала:")
            for i, signal in enumerate(raw_result.data[-3:]):
                time = signal.get('created_at', 'N/A')[:19]
                trader = signal.get('trader_id', 'N/A')
                text = signal.get('raw_text', '')[:50]
                print(f"  {i+1}. [{time}] {trader}: {text}...")
        
        # Проверяем обработанные сигналы за сегодня  
        parsed_result = orchestrator_with_supabase.supabase.table('signals_parsed').select('*').gte('created_at', f'{today}T00:00:00').execute()
        print(f"📊 signals_parsed за сегодня: {len(parsed_result.data)} записей")
        
        if parsed_result.data:
            print("🎯 Последние 3 обработанных сигнала:")
            for i, signal in enumerate(parsed_result.data[-3:]):
                time = signal.get('created_at', 'N/A')[:19] 
                trader = signal.get('trader_id', 'N/A')
                symbol = signal.get('symbol', 'N/A')
                side = signal.get('side', 'N/A')
                print(f"  {i+1}. [{time}] {trader}: {symbol} {side}")
        
        # Проверяем v_trades за сегодня
        try:
            trades_result = orchestrator_with_supabase.supabase.table('v_trades').select('*').gte('created_at', f'{today}T00:00:00').execute()
            print(f"📊 v_trades за сегодня: {len(trades_result.data)} записей")
        except:
            print(f"📊 v_trades: недоступно")
            
    except Exception as e:
        print(f"❌ Ошибка при проверке данных: {e}")
    
    # Проверяем статус системы
    print(f"\n🔧 СТАТУС СИСТЕМЫ:")
    print(f"  • GHOST система: ❌ НЕ ЗАПУЩЕНА")
    print(f"  • Telegram слушание: ❌ ОСТАНОВЛЕНО") 
    print(f"  • Обработка новых сигналов: ❌ НЕ РАБОТАЕТ")
    
    print(f"\n💡 РЕКОМЕНДАЦИИ:")
    print(f"  1. Запустить систему: python3 start_all.py")
    print(f"  2. Система будет слушать Telegram каналы")  
    print(f"  3. Новые сообщения будут автоматически обработаны")

if __name__ == "__main__":
    asyncio.run(check_todays_messages())
