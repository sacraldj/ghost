#!/usr/bin/env python3
"""
Показать все сообщения за сегодня из Supabase
"""

import asyncio
import os
import sys
from datetime import datetime
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def show_all_data():
    """Показываем все данные за сегодня"""
    
    from signals.signal_orchestrator_with_supabase import orchestrator_with_supabase
    
    print("📊 ДАННЫЕ ЗА СЕГОДНЯ В SUPABASE")
    print("=" * 60)
    
    if not orchestrator_with_supabase.supabase:
        print("❌ Нет подключения к Supabase")
        return
    
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"📅 Дата: {today}")
    print()
    
    try:
        # 1. СЫРЫЕ СИГНАЛЫ (signals_raw)
        print("1️⃣ СЫРЫЕ СООБЩЕНИЯ (signals_raw):")
        print("-" * 40)
        
        raw_result = orchestrator_with_supabase.supabase.table('signals_raw').select('*').gte('created_at', f'{today}T00:00:00').order('created_at').execute()
        
        print(f"📊 Всего сообщений: {len(raw_result.data)}")
        
        if raw_result.data:
            for i, signal in enumerate(raw_result.data, 1):
                time = signal.get('created_at', '')[:19].replace('T', ' ')
                trader = signal.get('trader_id', 'N/A')
                text = signal.get('raw_text', '')[:100].replace('\n', ' ')
                print(f"  {i:2d}. [{time}] {trader:15s}: {text}...")
        
        print()
        
        # 2. ОБРАБОТАННЫЕ СИГНАЛЫ (signals_parsed)  
        print("2️⃣ ОБРАБОТАННЫЕ СИГНАЛЫ (signals_parsed):")
        print("-" * 40)
        
        parsed_result = orchestrator_with_supabase.supabase.table('signals_parsed').select('*').gte('created_at', f'{today}T00:00:00').order('created_at').execute()
        
        print(f"📊 Всего обработано: {len(parsed_result.data)}")
        
        if parsed_result.data:
            for i, signal in enumerate(parsed_result.data, 1):
                time = signal.get('created_at', '')[:19].replace('T', ' ')
                trader = signal.get('trader_id', 'N/A')
                symbol = signal.get('symbol', 'N/A')
                side = signal.get('side', 'N/A')
                tp1 = signal.get('tp1', 'N/A')
                sl = signal.get('sl', 'N/A')
                confidence = signal.get('confidence', 0)
                print(f"  {i:2d}. [{time}] {trader:15s}: {symbol:8s} {side:5s} TP1:{tp1} SL:{sl} ({confidence:.2f})")
        
        print()
        
        # 3. ВИРТУАЛЬНЫЕ СДЕЛКИ (v_trades)
        print("3️⃣ ВИРТУАЛЬНЫЕ СДЕЛКИ (v_trades):")
        print("-" * 40)
        
        try:
            trades_result = orchestrator_with_supabase.supabase.table('v_trades').select('*').gte('created_at', f'{today}T00:00:00').order('created_at').execute()
            
            print(f"📊 Всего сделок: {len(trades_result.data)}")
            
            if trades_result.data:
                for i, trade in enumerate(trades_result.data, 1):
                    time = trade.get('created_at', '')[:19].replace('T', ' ')
                    symbol = trade.get('symbol', 'N/A')
                    side = trade.get('side', 'N/A')
                    status = trade.get('status', 'N/A')
                    print(f"  {i:2d}. [{time}] {symbol:8s} {side:5s} {status}")
            
        except Exception as e:
            print(f"  ⚠️ v_trades недоступно: {e}")
        
        print()
        
        # 4. СТАТИСТИКА
        print("4️⃣ СТАТИСТИКА:")
        print("-" * 40)
        print(f"📥 Сырых сообщений:     {len(raw_result.data):3d}")
        print(f"🎯 Обработанных сигналов: {len(parsed_result.data):3d}")
        if 'trades_result' in locals():
            print(f"💰 Виртуальных сделок:   {len(trades_result.data):3d}")
        
        # Подсчет по трейдерам
        traders = {}
        for signal in raw_result.data:
            trader = signal.get('trader_id', 'unknown')
            traders[trader] = traders.get(trader, 0) + 1
        
        print(f"\n📊 ПО ТРЕЙДЕРАМ:")
        for trader, count in sorted(traders.items()):
            print(f"  • {trader:20s}: {count:2d} сообщений")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(show_all_data())
