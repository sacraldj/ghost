#!/usr/bin/env python3
"""
Скрипт для заполнения базы данных реальными сигналами
Создает тестовые сигналы для всех трейдеров для демонстрации
"""

import os
import sys
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Добавляем путь к core модулям
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from supabase import create_client, Client
except ImportError:
    print("❌ Supabase client not installed. Run: pip install supabase")
    sys.exit(1)

# Конфигурация
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_ANON_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Supabase credentials not found. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
    sys.exit(1)

# Инициализация Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Список популярных криптовалютных пар
CRYPTO_SYMBOLS = [
    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOTUSDT', 'XRPUSDT',
    'LTCUSDT', 'LINKUSDT', 'BCHUSDT', 'XLMUSDT', 'UNIUSDT', 'VETUSDT',
    'FILUSDT', 'TRXUSDT', 'EOSUSDT', 'XMRUSDT', 'AAVEUSDT', 'ATOMUSDT',
    'MKRUSDT', 'COMPUSDT', 'YFIUSDT', 'SUSHIUSDT', 'SNXUSDT', 'CRVUSDT',
    'ALPINEUSDT', 'DOGEUSDT', 'SHIBUSDT', 'AVAXUSDT', 'MATICUSDT', 'SOLUSDT'
]

# Конфигурация трейдеров
TRADERS = [
    {
        'trader_id': 'cryptoattack24',
        'name': 'КриптоАтака 24',
        'source_handle': '@cryptoattack24',
        'style': 'news_based',  # Основан на новостях
        'accuracy': 0.72,
        'avg_confidence': 0.85
    },
    {
        'trader_id': 'whales_guide_main',
        'name': 'Whales Crypto Guide',
        'source_handle': '@Whalesguide',
        'style': 'technical',
        'accuracy': 0.68,
        'avg_confidence': 0.78
    },
    {
        'trader_id': 'crypto_hub_vip',
        'name': 'Crypto Hub VIP',
        'source_handle': '@crypto_hub_vip',
        'style': 'scalping',
        'accuracy': 0.75,
        'avg_confidence': 0.82
    },
    {
        'trader_id': '2trade_slivaem',
        'name': '2Trade - slivaeminfo',
        'source_handle': '@2trade_slivaem',
        'style': 'swing',
        'accuracy': 0.65,
        'avg_confidence': 0.70
    }
]

def generate_signal_text(symbol: str, side: str, trader_style: str) -> str:
    """Генерирует реалистичный текст сигнала"""
    
    if trader_style == 'news_based':
        templates = [
            f"🚀🔥 #{symbol.replace('USDT', '')} запампили на +{random.randint(15, 80)}% со вчерашнего вечера. Закрепился в топе по покупкам на Binance.",
            f"📈 {symbol.replace('USDT', '')} показывает сильный рост после новостей о партнерстве. Рекомендуем к покупке.",
            f"⚡ Авиакомпании начали принимать {symbol.replace('USDT', '')} для оплаты билетов. Ожидаем дальнейший рост."
        ]
    elif trader_style == 'technical':
        templates = [
            f"📊 {symbol} LONG\nEntry: {random.uniform(0.1, 100):.4f}\nTP1: {random.uniform(0.1, 100):.4f}\nTP2: {random.uniform(0.1, 100):.4f}\nSL: {random.uniform(0.1, 100):.4f}",
            f"🎯 Сигнал на {symbol}\nНаправление: {'LONG' if side == 'Buy' else 'SHORT'}\nВход: {random.uniform(0.1, 100):.4f}\nЦели: {random.uniform(0.1, 100):.4f}, {random.uniform(0.1, 100):.4f}",
        ]
    elif trader_style == 'scalping':
        templates = [
            f"⚡ СКАЛЬПИНГ {symbol}\n🟢 LONG от {random.uniform(0.1, 100):.4f}\n🎯 TP: {random.uniform(0.1, 100):.4f}\n🛑 SL: {random.uniform(0.1, 100):.4f}",
            f"💨 Быстрый сигнал {symbol}\nВход: {random.uniform(0.1, 100):.4f}\nВыход: {random.uniform(0.1, 100):.4f}",
        ]
    else:  # swing
        templates = [
            f"📈 СВИНГ {symbol}\nВход: {random.uniform(0.1, 100):.4f}\nЦель 1: {random.uniform(0.1, 100):.4f}\nЦель 2: {random.uniform(0.1, 100):.4f}\nСтоп: {random.uniform(0.1, 100):.4f}",
            f"🎯 Среднесрочный сигнал {symbol}\nПокупка от {random.uniform(0.1, 100):.4f}\nХолд до {random.uniform(0.1, 100):.4f}",
        ]
    
    return random.choice(templates)

def generate_realistic_signals(trader: Dict, days_back: int = 30, signals_per_day: float = 2.5) -> List[Dict]:
    """Генерирует реалистичные сигналы для трейдера"""
    
    signals = []
    total_signals = int(days_back * signals_per_day * random.uniform(0.7, 1.3))
    
    for i in range(total_signals):
        # Случайное время в последние N дней
        random_time = datetime.now() - timedelta(
            days=random.uniform(0, days_back),
            hours=random.uniform(0, 24),
            minutes=random.uniform(0, 60)
        )
        
        symbol = random.choice(CRYPTO_SYMBOLS)
        side = random.choice(['Buy', 'Sell'])
        
        # Генерируем цены
        entry_price = random.uniform(0.1, 1000)
        tp1_price = entry_price * (1.02 if side == 'Buy' else 0.98)
        tp2_price = entry_price * (1.05 if side == 'Buy' else 0.95)
        sl_price = entry_price * (0.98 if side == 'Buy' else 1.02)
        
        signal_text = generate_signal_text(symbol, side, trader['style'])
        
        signal = {
            'id': f"{trader['trader_id']}_{int(random_time.timestamp() * 1000)}_{i}",
            'received_at': int(random_time.timestamp() * 1000),
            'source_name': trader['trader_id'],
            'raw_text': signal_text,
            'symbol_raw': symbol,
            'symbol': symbol,
            'side': side,
            'entry_low': entry_price * 0.99,
            'entry_high': entry_price * 1.01,
            'targets_json': json.dumps([tp1_price, tp2_price]),
            'stoploss': sl_price,
            'parse_version': '1.0',
            'parsed_ok': 1 if random.random() < trader['accuracy'] else 0
        }
        
        signals.append(signal)
    
    return signals

def generate_signal_outcomes(signals: List[Dict], trader: Dict) -> List[Dict]:
    """Генерирует исходы для сигналов"""
    
    outcomes = []
    
    for signal in signals:
        if signal['parsed_ok'] == 0:
            continue  # Пропускаем невалидные сигналы
        
        # Определяем исход на основе точности трейдера
        success_rate = trader['accuracy']
        
        if random.random() < success_rate:
            # Успешный сигнал
            if random.random() < 0.6:  # 60% TP1
                final_result = 'TP1_ONLY'
                pnl_sim = random.uniform(50, 150)
            else:  # 40% TP2
                final_result = 'TP2_FULL'
                pnl_sim = random.uniform(100, 300)
        else:
            # Неуспешный сигнал
            final_result = 'SL_HIT'
            pnl_sim = random.uniform(-120, -50)
        
        outcome = {
            'signal_id': signal['id'],
            'trader_id': signal['source_name'],
            'final_result': final_result,
            'pnl_sim': pnl_sim,
            'roi_sim': (pnl_sim / 100) * 100,  # ROI в процентах
            'duration_to_tp1_min': random.randint(5, 120) if 'TP' in final_result else None,
            'duration_to_tp2_min': random.randint(30, 300) if final_result == 'TP2_FULL' else None,
            'max_favorable': random.uniform(0, 200),
            'max_adverse': random.uniform(-100, 0),
            'calculated_at': datetime.now().isoformat()
        }
        
        outcomes.append(outcome)
    
    return outcomes

def main():
    """Основная функция"""
    print("🚀 Начинаем заполнение базы данных реальными сигналами...")
    
    try:
        # 1. Добавляем/обновляем трейдеров
        print("\n📊 Добавляем трейдеров...")
        for trader in TRADERS:
            try:
                result = supabase.table('trader_registry').upsert({
                    'trader_id': trader['trader_id'],
                    'name': trader['name'],
                    'source_type': 'telegram',
                    'source_handle': trader['source_handle'],
                    'mode': 'observe',
                    'is_active': True,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }).execute()
                
                print(f"✅ Добавлен трейдер: {trader['name']}")
                
            except Exception as e:
                print(f"⚠️ Ошибка добавления трейдера {trader['name']}: {e}")
        
        # 2. Генерируем и добавляем сигналы
        print("\n📈 Генерируем сигналы...")
        all_signals = []
        all_outcomes = []
        
        for trader in TRADERS:
            print(f"🔄 Генерируем сигналы для {trader['name']}...")
            
            signals = generate_realistic_signals(trader, days_back=30)
            outcomes = generate_signal_outcomes(signals, trader)
            
            all_signals.extend(signals)
            all_outcomes.extend(outcomes)
            
            print(f"✅ Сгенерировано {len(signals)} сигналов, {len(outcomes)} исходов")
        
        # 3. Добавляем сигналы в базу данных
        print(f"\n💾 Сохраняем {len(all_signals)} сигналов в базу...")
        
        # Добавляем сырые сигналы
        try:
            # Разбиваем на батчи по 100
            batch_size = 100
            for i in range(0, len(all_signals), batch_size):
                batch = all_signals[i:i + batch_size]
                
                # Пытаемся добавить в signals (новая схема)
                try:
                    result = supabase.table('signals').upsert(batch).execute()
                    print(f"✅ Добавлен батч {i//batch_size + 1} в таблицу signals")
                except Exception as e:
                    print(f"⚠️ Ошибка добавления в signals: {e}")
                    
                    # Fallback: добавляем в signals_raw (старая схема)
                    try:
                        raw_signals = []
                        for signal in batch:
                            raw_signals.append({
                                'signal_id': signal['id'],
                                'trader_id': signal['source_name'],
                                'raw_text': signal['raw_text'],
                                'posted_at': datetime.fromtimestamp(signal['received_at'] / 1000).isoformat(),
                                'source_type': 'telegram',
                                'channel_id': f"@{signal['source_name']}"
                            })
                        
                        result = supabase.table('signals_raw').upsert(raw_signals).execute()
                        print(f"✅ Добавлен батч {i//batch_size + 1} в таблицу signals_raw")
                    except Exception as e2:
                        print(f"❌ Ошибка добавления в signals_raw: {e2}")
        
        except Exception as e:
            print(f"❌ Ошибка сохранения сигналов: {e}")
        
        # 4. Добавляем исходы
        print(f"\n🎯 Сохраняем {len(all_outcomes)} исходов...")
        try:
            batch_size = 100
            for i in range(0, len(all_outcomes), batch_size):
                batch = all_outcomes[i:i + batch_size]
                result = supabase.table('signal_outcomes').upsert(batch).execute()
                print(f"✅ Добавлен батч исходов {i//batch_size + 1}")
        
        except Exception as e:
            print(f"❌ Ошибка сохранения исходов: {e}")
        
        print(f"\n🎉 Готово! Добавлено:")
        print(f"   👥 Трейдеров: {len(TRADERS)}")
        print(f"   📊 Сигналов: {len(all_signals)}")
        print(f"   🎯 Исходов: {len(all_outcomes)}")
        print(f"\n🔗 Теперь проверьте дашборд: http://localhost:3000")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
