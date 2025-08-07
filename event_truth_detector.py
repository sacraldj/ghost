#!/usr/bin/env python3
"""
GHOST | Event Truth Detector
Детектор истины событий - анализирует аномалии и выявляет реальные причины движений
"""

import json
import sqlite3
import time
from datetime import datetime, timedelta
from price_feed_logger import get_price_at
from reaction_logger import get_reaction_stats

DB_PATH = "data/event_truth.db"

def init_truth_database():
    """Инициализация БД для детектора истины"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS event_anomalies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE,
            event_type TEXT, -- 'news_without_reaction', 'reaction_without_news', 'unexpected_movement'
            news_id TEXT,
            timestamp INTEGER,
            price_before REAL,
            price_after REAL,
            price_change REAL,
            volume_change REAL,
            news_cluster TEXT,
            market_context TEXT,
            anomaly_score REAL, -- 0.0 до 1.0
            possible_causes TEXT, -- JSON array
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_manipulations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER,
            symbol TEXT,
            manipulation_type TEXT, -- 'pump', 'dump', 'squeeze', 'liquidation'
            price_before REAL,
            price_after REAL,
            volume_spike REAL,
            funding_rate_change REAL,
            open_interest_change REAL,
            confidence_score REAL,
            evidence TEXT, -- JSON с доказательствами
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def detect_news_without_reaction():
    """Детектирует новости без реакции рынка"""
    conn = sqlite3.connect("data/reactions.db")
    cursor = conn.cursor()
    
    try:
        # Ищем новости с низкой реакцией
        cursor.execute("""
            SELECT news_id, title, cluster, price_change_1h, price_change_4h
            FROM news_reactions
            WHERE created_at >= datetime('now', '-7 days')
            AND (abs(price_change_1h) < 0.5 OR price_change_1h IS NULL)
            AND cluster IN ('ETF_approval', 'FOMC_meeting', 'CPI_report')
        """)
        
        anomalies = []
        for news_id, title, cluster, change_1h, change_4h in cursor.fetchall():
            if abs(change_1h or 0) < 0.5:  # Реакция менее 0.5%
                anomalies.append({
                    "event_id": f"no_reaction_{news_id}",
                    "event_type": "news_without_reaction",
                    "news_id": news_id,
                    "title": title,
                    "cluster": cluster,
                    "price_change": change_1h or 0,
                    "anomaly_score": 0.8,
                    "possible_causes": [
                        "Новость уже была заложена в цене",
                        "Рынок не поверил новости",
                        "Контр-сигналы перевесили",
                        "Технические факторы подавили"
                    ]
                })
        
        return anomalies
        
    except Exception as e:
        print(f"❌ Ошибка детекции новостей без реакции: {e}")
        return []
    finally:
        conn.close()

def detect_reaction_without_news():
    """Детектирует движения без видимых новостей"""
    conn = sqlite3.connect("data/reactions.db")
    cursor = conn.cursor()
    
    try:
        # Ищем большие движения без новостей
        cursor.execute("""
            SELECT timestamp, price_change_1h, price_change_4h
            FROM price_feed
            WHERE created_at >= datetime('now', '-7 days')
            AND abs(price_change_1h) > 2.0
            AND NOT EXISTS (
                SELECT 1 FROM news_reactions 
                WHERE news_reactions.event_timestamp BETWEEN 
                    price_feed.timestamp - 3600000 AND 
                    price_feed.timestamp + 3600000
            )
        """)
        
        anomalies = []
        for timestamp, change_1h, change_4h in cursor.fetchall():
            if abs(change_1h) > 2.0:  # Движение более 2%
                anomalies.append({
                    "event_id": f"no_news_{timestamp}",
                    "event_type": "reaction_without_news",
                    "timestamp": timestamp,
                    "price_change": change_1h,
                    "anomaly_score": 0.9,
                    "possible_causes": [
                        "Крупный ордер/ликвидация",
                        "Скрытая новость/инсайд",
                        "Технический пробой",
                        "Манипуляция рынка"
                    ]
                })
        
        return anomalies
        
    except Exception as e:
        print(f"❌ Ошибка детекции движений без новостей: {e}")
        return []
    finally:
        conn.close()

def detect_market_manipulation(symbol="BTCUSDT"):
    """Детектирует возможные манипуляции рынка"""
    
    try:
        # Получаем данные о движении цены и объема
        conn = sqlite3.connect("data/price_feed.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT timestamp, close_price, volume
            FROM price_feed
            WHERE symbol = ? AND created_at >= datetime('now', '-24 hours')
            ORDER BY timestamp DESC
            LIMIT 60
        """, (symbol,))
        
        price_data = cursor.fetchall()
        conn.close()
        
        if len(price_data) < 10:
            return []
        
        manipulations = []
        
        # Анализируем всплески объема
        for i in range(5, len(price_data) - 5):
            current_price = price_data[i][1]
            current_volume = price_data[i][2]
            
            # Средний объем за последние 5 свечей
            avg_volume = sum(price_data[j][2] for j in range(i-5, i)) / 5
            
            # Если объем в 3+ раза больше среднего
            if current_volume > avg_volume * 3:
                price_change = ((current_price - price_data[i-1][1]) / price_data[i-1][1]) * 100
                
                if abs(price_change) > 1.0:  # Движение более 1%
                    manipulation_type = "pump" if price_change > 0 else "dump"
                    
                    manipulations.append({
                        "timestamp": price_data[i][0],
                        "symbol": symbol,
                        "manipulation_type": manipulation_type,
                        "price_before": price_data[i-1][1],
                        "price_after": current_price,
                        "volume_spike": current_volume / avg_volume,
                        "confidence_score": min(current_volume / avg_volume / 5, 0.9),
                        "evidence": {
                            "volume_multiplier": current_volume / avg_volume,
                            "price_change": price_change,
                            "timeframe": "1m"
                        }
                    })
        
        return manipulations
        
    except Exception as e:
        print(f"❌ Ошибка детекции манипуляций: {e}")
        return []

def analyze_expectation_vs_reality(news_id):
    """Анализирует ожидание vs реальность для новости"""
    
    try:
        # Получаем данные о новости
        conn = sqlite3.connect("data/reactions.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT cluster, price_change_1h, price_change_4h, price_change_24h
            FROM news_reactions WHERE news_id = ?
        """, (news_id,))
        
        result = cursor.fetchone()
        if not result:
            return None
            
        cluster, change_1h, change_4h, change_24h = result
        
        # Определяем ожидаемую реакцию по кластеру
        expected_reactions = {
            "ETF_approval": {"direction": "positive", "magnitude": 2.0},
            "FOMC_hawkish": {"direction": "negative", "magnitude": 1.5},
            "FOMC_dovish": {"direction": "positive", "magnitude": 1.5},
            "CPI_higher": {"direction": "negative", "magnitude": 1.0},
            "CPI_lower": {"direction": "positive", "magnitude": 1.0}
        }
        
        expected = expected_reactions.get(cluster, {"direction": "neutral", "magnitude": 0.5})
        actual_change = change_1h or 0
        
        # Анализируем соответствие
        if expected["direction"] == "positive" and actual_change < 0:
            expectation_gap = "Ожидался рост, но был спад"
        elif expected["direction"] == "negative" and actual_change > 0:
            expectation_gap = "Ожидался спад, но был рост"
        elif abs(actual_change) < expected["magnitude"] * 0.5:
            expectation_gap = "Реакция слабее ожидаемой"
        elif abs(actual_change) > expected["magnitude"] * 2:
            expectation_gap = "Реакция сильнее ожидаемой"
        else:
            expectation_gap = "Реакция соответствует ожиданиям"
        
        return {
            "news_id": news_id,
            "cluster": cluster,
            "expected": expected,
            "actual_change": actual_change,
            "expectation_gap": expectation_gap,
            "surprise_factor": abs(actual_change - expected["magnitude"]) / expected["magnitude"]
        }
        
    except Exception as e:
        print(f"❌ Ошибка анализа ожиданий: {e}")
        return None
    finally:
        conn.close()

def save_anomalies(anomalies):
    """Сохраняет аномалии в БД"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        for anomaly in anomalies:
            cursor.execute("""
                INSERT OR REPLACE INTO event_anomalies
                (event_id, event_type, news_id, timestamp, price_change,
                 news_cluster, anomaly_score, possible_causes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                anomaly["event_id"],
                anomaly["event_type"],
                anomaly.get("news_id"),
                anomaly.get("timestamp"),
                anomaly.get("price_change", 0),
                anomaly.get("cluster"),
                anomaly["anomaly_score"],
                json.dumps(anomaly["possible_causes"])
            ))
        
        conn.commit()
        print(f"✅ Сохранено {len(anomalies)} аномалий")
        
    except Exception as e:
        print(f"❌ Ошибка сохранения аномалий: {e}")
        conn.rollback()
    finally:
        conn.close()

def generate_truth_report():
    """Генерирует отчет о детекции истины"""
    print("🔍 ОТЧЕТ О ДЕТЕКЦИИ ИСТИНЫ GHOST")
    print("=" * 50)
    
    # Новости без реакции
    no_reaction = detect_news_without_reaction()
    print(f"📰 Новости без реакции: {len(no_reaction)}")
    for anomaly in no_reaction[:3]:
        print(f"• {anomaly['title'][:50]}... → {anomaly['price_change']:.2f}%")
    
    # Движения без новостей
    no_news = detect_reaction_without_news()
    print(f"📈 Движения без новостей: {len(no_news)}")
    for anomaly in no_news[:3]:
        print(f"• {anomaly['timestamp']} → {anomaly['price_change']:.2f}%")
    
    # Манипуляции рынка
    manipulations = detect_market_manipulation()
    print(f"🎭 Возможные манипуляции: {len(manipulations)}")
    for manip in manipulations[:3]:
        print(f"• {manip['manipulation_type']} → {manip['volume_spike']:.1f}x объем")
    
    print("\n" + "=" * 50)
    print("💡 ВЫВОДЫ:")
    print("• Система выявляет аномалии в реальном времени")
    print("• Помогает понять истинные причины движений")
    print("• Фильтрует шум от реальных сигналов")
    print("• Улучшает качество прогнозов")

if __name__ == "__main__":
    # Инициализация БД
    init_truth_database()
    
    # Детекция аномалий
    anomalies = detect_news_without_reaction() + detect_reaction_without_news()
    save_anomalies(anomalies)
    
    # Детекция манипуляций
    manipulations = detect_market_manipulation()
    
    # Генерация отчета
    generate_truth_report() 