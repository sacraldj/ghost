#!/usr/bin/env python3
"""
Проверяем работу дедупликации
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def check_deduplication():
    from signals.signal_orchestrator_with_supabase import orchestrator_with_supabase
    
    print("🔍 ПРОВЕРКА ДЕДУПЛИКАЦИИ")
    print("=" * 40)
    
    # Получаем статистику системы
    stats = await orchestrator_with_supabase.get_stats()
    
    print(f"📊 СТАТИСТИКА СИСТЕМЫ:")
    print(f"  • Обработано сигналов: {stats.get('signals_processed', 0)}")
    print(f"  • Сохранено в базу: {stats.get('signals_saved', 0)}")  
    print(f"  • Сырых сохранено: {stats.get('raw_signals_saved', 0)}")
    print(f"  • Дубликатов пропущено: {stats.get('duplicates_skipped', 0)}")
    print(f"  • Ошибок Supabase: {stats.get('supabase_errors', 0)}")
    print(f"  • Время работы: {stats.get('uptime_human', '0:00:00')}")
    
    # Проверяем последние сообщения
    if orchestrator_with_supabase.supabase:
        # Последние 5 минут
        five_min_ago = (datetime.now() - timedelta(minutes=5)).isoformat()
        recent = orchestrator_with_supabase.supabase.table('signals_raw').select('*').gte('created_at', five_min_ago).order('created_at', desc=True).limit(10).execute()
        
        print(f"\n📥 ПОСЛЕДНИЕ СООБЩЕНИЯ (5 мин):")
        print(f"  Всего: {len(recent.data)}")
        
        for i, msg in enumerate(recent.data[:5], 1):
            time = msg.get('created_at', '')[:19].replace('T', ' ')
            trader = msg.get('trader_id', 'N/A')[:15]
            text = msg.get('text', '')[:40].replace('\n', ' ')
            print(f"  {i}. [{time}] {trader}: {text}...")
    
    print(f"\n✅ ДЕДУПЛИКАЦИЯ: {'РАБОТАЕТ' if stats.get('duplicates_skipped', 0) > 0 else 'ОЖИДАНИЕ ДУБЛИКАТОВ'}")

if __name__ == "__main__":
    asyncio.run(check_deduplication())
