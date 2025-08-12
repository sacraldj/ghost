#!/usr/bin/env python3
"""
Создание тестовых данных для проверки дашборда
"""

import json
import os
from datetime import datetime, timedelta
import random

# Создаем директории
os.makedirs("news_engine/output", exist_ok=True)

# Тестовые Telegram сигналы
test_signals = []
test_raw_messages = []

# Генерируем тестовые данные
symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT", "DOTUSDT"]
channels = ["Crypto Signals VIP", "Trading Alerts", "News Channel", "Market Analysis"]

for i in range(20):
    timestamp = (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat()
    
    symbol = random.choice(symbols)
    side = random.choice(["LONG", "SHORT"])
    entry = round(random.uniform(50, 3000), 4)
    tp1 = round(entry * random.uniform(1.02, 1.1), 4)
    tp2 = round(entry * random.uniform(1.1, 1.2), 4)
    sl = round(entry * random.uniform(0.95, 0.98), 4)
    
    signal_text = f"""
{symbol} - {side}

Вход: {entry}

{tp1}
{tp2}

Стоп: {sl}
    """.strip()
    
    # Сигнал
    signal = {
        "timestamp": timestamp,
        "source": random.choice(channels),
        "chat_id": -1001000000000 - random.randint(1, 999999999),
        "text": signal_text,
        "type": "trade",
        "trigger": side
    }
    test_signals.append(signal)
    
    # Сырое сообщение
    raw_message = {
        "timestamp": timestamp,
        "chat_id": signal["chat_id"],
        "channel_name": signal["source"],
        "message_id": random.randint(1000, 9999),
        "text": signal_text,
        "from_user": f"trader_{random.randint(1, 100)}"
    }
    test_raw_messages.append(raw_message)

# Добавляем новостные сигналы
news_texts = [
    "🔥 BREAKING: Bitcoin ETF approval expected this week!",
    "📈 Ethereum upgrade successful, price rallying",
    "⚠️ SEC investigating major crypto exchange",
    "🚀 Tesla announces $2B Bitcoin purchase",
    "📊 CPI data shows inflation cooling, crypto pumping"
]

for i, news in enumerate(news_texts):
    timestamp = (datetime.now() - timedelta(hours=i)).isoformat()
    
    signal = {
        "timestamp": timestamp,
        "source": "Crypto News Fast",
        "chat_id": -1001111111111,
        "text": news,
        "type": "news",
        "trigger": "BREAKING"
    }
    test_signals.append(signal)
    
    raw_message = {
        "timestamp": timestamp,
        "chat_id": -1001111111111,
        "channel_name": "Crypto News Fast",
        "message_id": random.randint(1000, 9999),
        "text": news,
        "from_user": "news_bot"
    }
    test_raw_messages.append(raw_message)

# Сортируем по времени (новые сначала)
test_signals.sort(key=lambda x: x["timestamp"], reverse=True)
test_raw_messages.sort(key=lambda x: x["timestamp"], reverse=True)

# Сохраняем файлы
with open("news_engine/output/signals.json", "w", encoding="utf-8") as f:
    json.dump(test_signals, f, ensure_ascii=False, indent=2)

with open("news_engine/output/raw_logbook.json", "w", encoding="utf-8") as f:
    json.dump(test_raw_messages, f, ensure_ascii=False, indent=2)

print(f"✅ Создано {len(test_signals)} тестовых сигналов")
print(f"✅ Создано {len(test_raw_messages)} тестовых сообщений")
print("📁 Файлы сохранены в news_engine/output/")
print("\n🚀 Теперь можно тестировать API:")
print("   curl http://localhost:3000/api/telegram-signals")
