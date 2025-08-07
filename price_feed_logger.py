#!/usr/bin/env python3
"""
GHOST | Price Feed Logger
Постоянно пишет свечи (1m/5m) по BTC/ETH и другим активам
Используется всеми модулями для сравнения: "что было до и после новости"
"""

import json
import time
import sqlite3
from datetime import datetime
from pybit.unified_trading import HTTP
import yaml

# === API Подключение ===
with open("config/api_keys.yaml") as f:
    keys = yaml.safe_load(f)["bybit"]

session = HTTP(api_key=keys["api_key"], api_secret=keys["api_secret"])

# === Конфигурация ===
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "WIFUSDT"]
INTERVALS = ["1", "5"]  # 1m и 5m свечи
DB_PATH = "data/price_feed.db"

def init_database():
    """Инициализация базы данных для цен"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_feed (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            interval TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            open_price REAL NOT NULL,
            high_price REAL NOT NULL,
            low_price REAL NOT NULL,
            close_price REAL NOT NULL,
            volume REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, interval, timestamp)
        )
    """)
    
    # Индексы для быстрого поиска
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbol_timestamp ON price_feed(symbol, timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_interval ON price_feed(interval)")
    
    conn.commit()
    conn.close()

def get_kline_data(symbol, interval, limit=1):
    """Получение свечей с Bybit"""
    try:
        response = session.get_kline(
            category="linear",
            symbol=symbol,
            interval=interval,
            limit=limit
        )
        
        if response["retCode"] == 0:
            return response["result"]["list"]
        else:
            print(f"❌ Ошибка получения данных {symbol}: {response}")
            return []
            
    except Exception as e:
        print(f"❌ Ошибка API {symbol}: {e}")
        return []

def save_price_data(symbol, interval, kline_data):
    """Сохранение ценовых данных в БД"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        for kline in kline_data:
            # kline: [timestamp, open, high, low, close, volume, ...]
            timestamp = int(kline[0])
            open_price = float(kline[1])
            high_price = float(kline[2])
            low_price = float(kline[3])
            close_price = float(kline[4])
            volume = float(kline[5])
            
            cursor.execute("""
                INSERT OR REPLACE INTO price_feed 
                (symbol, interval, timestamp, open_price, high_price, low_price, close_price, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (symbol, interval, timestamp, open_price, high_price, low_price, close_price, volume))
            
        conn.commit()
        print(f"✅ Сохранено {len(kline_data)} свечей {symbol} {interval}m")
        
    except Exception as e:
        print(f"❌ Ошибка сохранения {symbol}: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_price_at(symbol, target_timestamp):
    """Получение цены на конкретный момент времени"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Ищем ближайшую свечу к целевому времени
        cursor.execute("""
            SELECT close_price, timestamp 
            FROM price_feed 
            WHERE symbol = ? AND timestamp <= ?
            ORDER BY timestamp DESC 
            LIMIT 1
        """, (symbol, target_timestamp))
        
        result = cursor.fetchone()
        if result:
            return {
                "price": result[0],
                "timestamp": result[1],
                "symbol": symbol
            }
        else:
            return None
            
    except Exception as e:
        print(f"❌ Ошибка получения цены {symbol}: {e}")
        return None
    finally:
        conn.close()

def log_price_feed():
    """Основной цикл сбора ценовых данных"""
    print("🔁 GHOST Price Feed Logger запущен...")
    
    while True:
        try:
            current_time = datetime.now()
            
            for symbol in SYMBOLS:
                for interval in INTERVALS:
                    kline_data = get_kline_data(symbol, interval, limit=1)
                    if kline_data:
                        save_price_data(symbol, interval, kline_data)
            
            # Пауза между обновлениями
            time.sleep(30)  # Обновляем каждые 30 секунд
            
        except KeyboardInterrupt:
            print("🛑 Price Feed Logger остановлен")
            break
        except Exception as e:
            print(f"❌ Ошибка в основном цикле: {e}")
            time.sleep(60)

if __name__ == "__main__":
    # Создаем директорию для данных
    import os
    os.makedirs("data", exist_ok=True)
    
    # Инициализируем БД
    init_database()
    
    # Запускаем сбор данных
    log_price_feed() 