#!/usr/bin/env python3
"""
Простой скрипт для добавления тестовых сигналов в существующие таблицы
"""

import os
import sys
import json
import random
from datetime import datetime, timedelta

try:
    from supabase import create_client, Client
except ImportError:
    print("❌ Supabase client not installed. Run: pip install supabase")
    sys.exit(1)

# Конфигурация
SUPABASE_URL = os.getenv('SUPABASE_URL', "https://qjdpckwqozsbpskwplfl.supabase.co")
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFqZHBja3dxb3pzYnBza3dwbGZsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NDUwNTI1NSwiZXhwIjoyMDcwMDgxMjU1fQ.At9S4Jb1maeGrh3GfFtj1ItcOSDBn0Qj1dJ7aWZD97g")

# Инициализация Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Список трейдеров
TRADERS = [
    'cryptoattack24',
    'whales_guide_main', 
    'crypto_hub_vip',
    '2trade_slivaem'
]

# Криптовалютные пары
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'ALPINEUSDT', 'DOGEUSDT', 'SOLUSDT']

def add_signals_parsed():
    """Добавляем сигналы в signals_parsed"""
    print("📊 Добавляем сигналы в signals_parsed...")
    
    signals = []
    for trader_id in TRADERS:
        for i in range(random.randint(5, 15)):  # 5-15 сигналов на трейдера
            signal_time = datetime.now() - timedelta(days=random.randint(0, 30))
            
            signal = {
                'signal_id': f"{trader_id}_{int(signal_time.timestamp())}_{i}",
                'trader_id': trader_id,
                'symbol': random.choice(SYMBOLS),
                'side': random.choice(['BUY', 'SELL']),
                'entry_price': round(random.uniform(0.1, 1000), 4),
                'tp1': round(random.uniform(0.1, 1000), 4),
                'tp2': round(random.uniform(0.1, 1000), 4),
                'sl': round(random.uniform(0.1, 1000), 4),
                'confidence': random.randint(70, 95),
                'is_valid': True,
                'posted_at': signal_time.isoformat(),
                'raw_text': f"Test signal for {random.choice(SYMBOLS)} from {trader_id}"
            }
            signals.append(signal)
    
    try:
        # Добавляем батчами
        batch_size = 50
        for i in range(0, len(signals), batch_size):
            batch = signals[i:i + batch_size]
            result = supabase.table('signals_parsed').upsert(batch).execute()
            print(f"✅ Добавлен батч {i//batch_size + 1} в signals_parsed")
        
        print(f"✅ Добавлено {len(signals)} сигналов в signals_parsed")
        return len(signals)
        
    except Exception as e:
        print(f"❌ Ошибка добавления в signals_parsed: {e}")
        return 0

def add_signal_outcomes(signals_count):
    """Добавляем исходы сигналов"""
    print("🎯 Добавляем исходы сигналов...")
    
    outcomes = []
    outcome_id = 1
    
    for trader_id in TRADERS:
        trader_signals = signals_count // len(TRADERS)  # Примерно равное количество
        
        for i in range(trader_signals):
            # Генерируем реалистичные исходы
            if random.random() < 0.65:  # 65% успешных сигналов
                final_result = random.choice(['TP1_ONLY', 'TP2_FULL'])
                pnl_sim = random.uniform(50, 200) if final_result == 'TP1_ONLY' else random.uniform(100, 400)
            else:
                final_result = 'SL_HIT'
                pnl_sim = random.uniform(-150, -50)
            
            outcome = {
                'outcome_id': outcome_id,
                'signal_id': f"{trader_id}_outcome_{outcome_id}",
                'trader_id': trader_id,
                'final_result': final_result,
                'pnl_sim': round(pnl_sim, 2),
                'roi_sim': round((pnl_sim / 100) * 100, 2),
                'duration_to_tp1_min': random.randint(5, 120) if 'TP' in final_result else None,
                'calculated_at': datetime.now().isoformat()
            }
            outcomes.append(outcome)
            outcome_id += 1
    
    try:
        batch_size = 50
        for i in range(0, len(outcomes), batch_size):
            batch = outcomes[i:i + batch_size]
            result = supabase.table('signal_outcomes').upsert(batch).execute()
            print(f"✅ Добавлен батч исходов {i//batch_size + 1}")
        
        print(f"✅ Добавлено {len(outcomes)} исходов")
        
    except Exception as e:
        print(f"❌ Ошибка добавления исходов: {e}")

def main():
    print("🚀 Добавляем тестовые сигналы в существующие таблицы...")
    
    try:
        # 1. Добавляем сигналы
        signals_count = add_signals_parsed()
        
        # 2. Добавляем исходы
        if signals_count > 0:
            add_signal_outcomes(signals_count)
        
        print(f"\n🎉 Готово! Проверьте дашборд: http://localhost:3000")
        print(f"Трейдеры теперь должны показывать реальные данные:")
        for trader in TRADERS:
            print(f"  - {trader}")
            
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()
