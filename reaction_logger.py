#!/usr/bin/env python3
"""
GHOST | Reaction Logger
Логирует: что за новость пришла, во сколько, и что произошло потом (через 1ч, 4ч, 24ч)
"""

import json
import sqlite3
import time
from datetime import datetime, timedelta
from price_feed_logger import get_price_at

DB_PATH = "data/reactions.db"

def init_reactions_database():
    """Инициализация базы данных для реакций"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news_reactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            news_id TEXT UNIQUE,
            cluster TEXT NOT NULL,
            title TEXT,
            content TEXT,
            source TEXT,
            published_at TIMESTAMP,
            event_timestamp INTEGER,
            symbol TEXT DEFAULT 'BTCUSDT',
            price_at_event REAL,
            price_1h REAL,
            price_4h REAL,
            price_24h REAL,
            reaction_type TEXT, -- 'pump', 'dump', 'neutral', 'short_pump_then_fade'
            price_change_1h REAL,
            price_change_4h REAL,
            price_change_24h REAL,
            volume_change_1h REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Индексы
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cluster ON news_reactions(cluster)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON news_reactions(event_timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reaction_type ON news_reactions(reaction_type)")
    
    conn.commit()
    conn.close()

def log_news_event(news_data):
    """Логирование нового события новости"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Получаем цену на момент события
        event_timestamp = int(time.time() * 1000)  # в миллисекундах
        price_data = get_price_at(news_data.get('symbol', 'BTCUSDT'), event_timestamp)
        
        cursor.execute("""
            INSERT OR REPLACE INTO news_reactions 
            (news_id, cluster, title, content, source, published_at, event_timestamp, 
             symbol, price_at_event)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            news_data.get('news_id'),
            news_data.get('cluster'),
            news_data.get('title'),
            news_data.get('content'),
            news_data.get('source'),
            news_data.get('published_at'),
            event_timestamp,
            news_data.get('symbol', 'BTCUSDT'),
            price_data['price'] if price_data else None
        ))
        
        conn.commit()
        print(f"✅ Логировано событие: {news_data.get('cluster')} | {news_data.get('title')[:50]}...")
        
    except Exception as e:
        print(f"❌ Ошибка логирования события: {e}")
        conn.rollback()
    finally:
        conn.close()

def update_reaction_prices(news_id, hours_later=1):
    """Обновление цен через указанное время"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Получаем время события
        cursor.execute("SELECT event_timestamp, symbol FROM news_reactions WHERE news_id = ?", (news_id,))
        result = cursor.fetchone()
        
        if not result:
            print(f"❌ Событие {news_id} не найдено")
            return
            
        event_timestamp, symbol = result
        event_time = event_timestamp / 1000  # конвертируем в секунды
        
        # Вычисляем время для проверки
        check_time = event_time + (hours_later * 3600)
        check_timestamp = int(check_time * 1000)
        
        # Получаем цену через указанное время
        price_data = get_price_at(symbol, check_timestamp)
        
        if price_data:
            # Получаем цену на момент события
            cursor.execute("SELECT price_at_event FROM news_reactions WHERE news_id = ?", (news_id,))
            event_price = cursor.fetchone()[0]
            
            if event_price:
                price_change = ((price_data['price'] - event_price) / event_price) * 100
                
                # Обновляем данные
                if hours_later == 1:
                    cursor.execute("""
                        UPDATE news_reactions 
                        SET price_1h = ?, price_change_1h = ?
                        WHERE news_id = ?
                    """, (price_data['price'], price_change, news_id))
                elif hours_later == 4:
                    cursor.execute("""
                        UPDATE news_reactions 
                        SET price_4h = ?, price_change_4h = ?
                        WHERE news_id = ?
                    """, (price_data['price'], price_change, news_id))
                elif hours_later == 24:
                    cursor.execute("""
                        UPDATE news_reactions 
                        SET price_24h = ?, price_change_24h = ?
                        WHERE news_id = ?
                    """, (price_data['price'], price_change, news_id))
                
                conn.commit()
                print(f"✅ Обновлена цена через {hours_later}ч: {price_change:.2f}%")
                
    except Exception as e:
        print(f"❌ Ошибка обновления цен: {e}")
        conn.rollback()
    finally:
        conn.close()

def classify_reaction(news_id):
    """Классификация типа реакции"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT price_change_1h, price_change_4h, price_change_24h
            FROM news_reactions WHERE news_id = ?
        """, (news_id,))
        
        result = cursor.fetchone()
        if not result:
            return None
            
        change_1h, change_4h, change_24h = result
        
        if not change_1h:
            return None
            
        # Классификация реакции
        if change_1h > 2.0:
            if change_4h and change_4h < change_1h * 0.5:
                reaction_type = "short_pump_then_fade"
            else:
                reaction_type = "pump"
        elif change_1h < -2.0:
            reaction_type = "dump"
        elif abs(change_1h) < 0.5:
            reaction_type = "neutral"
        else:
            reaction_type = "moderate_move"
        
        # Обновляем тип реакции
        cursor.execute("""
            UPDATE news_reactions 
            SET reaction_type = ?
            WHERE news_id = ?
        """, (reaction_type, news_id))
        
        conn.commit()
        print(f"✅ Классифицирована реакция: {reaction_type}")
        return reaction_type
        
    except Exception as e:
        print(f"❌ Ошибка классификации: {e}")
        return None
    finally:
        conn.close()

def get_reaction_stats(cluster=None, days=30):
    """Получение статистики реакций"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        if cluster:
            cursor.execute("""
                SELECT reaction_type, COUNT(*) as count
                FROM news_reactions 
                WHERE cluster = ? AND created_at >= datetime('now', '-{} days')
                GROUP BY reaction_type
            """.format(days), (cluster,))
        else:
            cursor.execute("""
                SELECT reaction_type, COUNT(*) as count
                FROM news_reactions 
                WHERE created_at >= datetime('now', '-{} days')
                GROUP BY reaction_type
            """.format(days))
        
        results = cursor.fetchall()
        stats = {row[0]: row[1] for row in results}
        
        return stats
        
    except Exception as e:
        print(f"❌ Ошибка получения статистики: {e}")
        return {}
    finally:
        conn.close()

def schedule_reaction_updates():
    """Планировщик обновления реакций"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Находим события, которые нужно обновить
        current_time = int(time.time())
        
        # События через 1 час
        cursor.execute("""
            SELECT news_id FROM news_reactions 
            WHERE price_1h IS NULL 
            AND event_timestamp <= ?
        """, ((current_time - 3600) * 1000,))
        
        for (news_id,) in cursor.fetchall():
            update_reaction_prices(news_id, 1)
            classify_reaction(news_id)
        
        # События через 4 часа
        cursor.execute("""
            SELECT news_id FROM news_reactions 
            WHERE price_4h IS NULL 
            AND event_timestamp <= ?
        """, ((current_time - 14400) * 1000,))
        
        for (news_id,) in cursor.fetchall():
            update_reaction_prices(news_id, 4)
        
        # События через 24 часа
        cursor.execute("""
            SELECT news_id FROM news_reactions 
            WHERE price_24h IS NULL 
            AND event_timestamp <= ?
        """, ((current_time - 86400) * 1000,))
        
        for (news_id,) in cursor.fetchall():
            update_reaction_prices(news_id, 24)
            
    except Exception as e:
        print(f"❌ Ошибка планировщика: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # Инициализация БД
    init_reactions_database()
    
    # Тестовое событие
    test_news = {
        "news_id": "test_001",
        "cluster": "ETF_approval",
        "title": "SEC Approves Bitcoin ETF",
        "content": "The SEC has approved the first Bitcoin ETF...",
        "source": "Reuters",
        "published_at": datetime.now().isoformat(),
        "symbol": "BTCUSDT"
    }
    
    log_news_event(test_news)
    print("✅ Тестовое событие залогировано") 