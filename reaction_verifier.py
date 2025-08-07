#!/usr/bin/env python3
"""
GHOST | Reaction Verifier
Сравнивает прогноз с фактом (попал/не попал) и обновляет статистику точности
"""

import json
import sqlite3
import time
from datetime import datetime, timedelta
from reaction_predictor import get_prediction_accuracy
from reaction_logger import get_reaction_stats

DB_PATH = "data/verification.db"

def init_verification_database():
    """Инициализация базы данных для верификации"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prediction_verification (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            news_id TEXT UNIQUE,
            cluster TEXT,
            predicted_reaction TEXT,
            actual_reaction TEXT,
            predicted_change REAL,
            actual_change REAL,
            direction_correct BOOLEAN,
            magnitude_error REAL,
            reaction_type_match BOOLEAN,
            accuracy_score REAL, -- 0.0 до 1.0
            verification_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Индексы
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_id ON prediction_verification(news_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cluster ON prediction_verification(cluster)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_direction_correct ON prediction_verification(direction_correct)")
    
    conn.commit()
    conn.close()

def verify_prediction(news_id):
    """Верификация предсказания для конкретной новости"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Получаем точность предсказания
        accuracy = get_prediction_accuracy(news_id)
        
        if not accuracy:
            print(f"❌ Недостаточно данных для верификации {news_id}")
            return None
        
        # Вычисляем общий score точности
        accuracy_score = 0.0
        if accuracy["direction_correct"]:
            accuracy_score += 0.5
        if accuracy["reaction_type_match"]:
            accuracy_score += 0.3
        if accuracy["magnitude_error"] < 1.0:  # Ошибка менее 1%
            accuracy_score += 0.2
        
        # Получаем дополнительную информацию
        conn_pred = sqlite3.connect("data/predictions.db")
        cursor_pred = conn_pred.cursor()
        
        cursor_pred.execute("""
            SELECT cluster, predicted_reaction, predicted_change_percent
            FROM news_predictions WHERE news_id = ?
        """, (news_id,))
        
        pred_result = cursor_pred.fetchone()
        if not pred_result:
            return None
            
        cluster, predicted_reaction, predicted_change = pred_result
        
        # Сохраняем верификацию
        cursor.execute("""
            INSERT OR REPLACE INTO prediction_verification 
            (news_id, cluster, predicted_reaction, actual_reaction, predicted_change,
             actual_change, direction_correct, magnitude_error, reaction_type_match, accuracy_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            news_id,
            cluster,
            predicted_reaction,
            accuracy.get("actual_reaction", "unknown"),
            predicted_change,
            accuracy["actual"],
            accuracy["direction_correct"],
            accuracy["magnitude_error"],
            accuracy["reaction_type_match"],
            accuracy_score
        ))
        
        conn.commit()
        
        # Формируем результат
        result = {
            "news_id": news_id,
            "cluster": cluster,
            "predicted": {
                "reaction": predicted_reaction,
                "change": predicted_change
            },
            "actual": {
                "reaction": accuracy.get("actual_reaction", "unknown"),
                "change": accuracy["actual"]
            },
            "accuracy": {
                "direction_correct": accuracy["direction_correct"],
                "magnitude_error": accuracy["magnitude_error"],
                "reaction_type_match": accuracy["reaction_type_match"],
                "score": accuracy_score
            }
        }
        
        print(f"✅ Верифицировано {news_id}: {accuracy_score:.1%} точность")
        return result
        
    except Exception as e:
        print(f"❌ Ошибка верификации: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def get_verification_stats(cluster=None, days=30):
    """Получение статистики точности предсказаний"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        if cluster:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_predictions,
                    AVG(accuracy_score) as avg_accuracy,
                    SUM(CASE WHEN direction_correct THEN 1 ELSE 0 END) as correct_directions,
                    SUM(CASE WHEN reaction_type_match THEN 1 ELSE 0 END) as correct_types,
                    AVG(magnitude_error) as avg_magnitude_error
                FROM prediction_verification 
                WHERE cluster = ? AND verification_timestamp >= datetime('now', '-{} days')
            """.format(days), (cluster,))
        else:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_predictions,
                    AVG(accuracy_score) as avg_accuracy,
                    SUM(CASE WHEN direction_correct THEN 1 ELSE 0 END) as correct_directions,
                    SUM(CASE WHEN reaction_type_match THEN 1 ELSE 0 END) as correct_types,
                    AVG(magnitude_error) as avg_magnitude_error
                FROM prediction_verification 
                WHERE verification_timestamp >= datetime('now', '-{} days')
            """.format(days))
        
        result = cursor.fetchone()
        if not result:
            return None
            
        total, avg_acc, correct_dir, correct_types, avg_mag_error = result
        
        if total == 0:
            return None
            
        stats = {
            "total_predictions": total,
            "avg_accuracy": avg_acc,
            "direction_accuracy": correct_dir / total,
            "type_accuracy": correct_types / total,
            "avg_magnitude_error": avg_mag_error
        }
        
        return stats
        
    except Exception as e:
        print(f"❌ Ошибка получения статистики: {e}")
        return None
    finally:
        conn.close()

def get_cluster_performance():
    """Получение производительности по кластерам"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                cluster,
                COUNT(*) as total,
                AVG(accuracy_score) as avg_accuracy,
                SUM(CASE WHEN direction_correct THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as direction_accuracy
            FROM prediction_verification 
            WHERE verification_timestamp >= datetime('now', '-30 days')
            GROUP BY cluster
            ORDER BY avg_accuracy DESC
        """)
        
        results = cursor.fetchall()
        performance = []
        
        for cluster, total, avg_acc, dir_acc in results:
            performance.append({
                "cluster": cluster,
                "total_predictions": total,
                "avg_accuracy": avg_acc,
                "direction_accuracy": dir_acc
            })
        
        return performance
        
    except Exception as e:
        print(f"❌ Ошибка получения производительности: {e}")
        return []
    finally:
        conn.close()

def identify_weak_patterns():
    """Выявление слабых паттернов в предсказаниях"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Анализируем случаи с низкой точностью
        cursor.execute("""
            SELECT 
                cluster,
                predicted_reaction,
                actual_reaction,
                COUNT(*) as count,
                AVG(accuracy_score) as avg_accuracy
            FROM prediction_verification 
            WHERE accuracy_score < 0.5 AND verification_timestamp >= datetime('now', '-30 days')
            GROUP BY cluster, predicted_reaction, actual_reaction
            ORDER BY count DESC
        """)
        
        results = cursor.fetchall()
        weak_patterns = []
        
        for cluster, pred_reaction, actual_reaction, count, avg_acc in results:
            weak_patterns.append({
                "cluster": cluster,
                "predicted": pred_reaction,
                "actual": actual_reaction,
                "frequency": count,
                "avg_accuracy": avg_acc,
                "issue": f"Часто предсказываем '{pred_reaction}', но получаем '{actual_reaction}'"
            })
        
        return weak_patterns
        
    except Exception as e:
        print(f"❌ Ошибка выявления слабых паттернов: {e}")
        return []
    finally:
        conn.close()

def generate_verification_report():
    """Генерация отчета о верификации"""
    print("📊 ОТЧЕТ О ВЕРИФИКАЦИИ GHOST")
    print("=" * 50)
    
    # Общая статистика
    overall_stats = get_verification_stats()
    if overall_stats:
        print(f"📈 Общая точность: {overall_stats['avg_accuracy']:.1%}")
        print(f"🎯 Точность направления: {overall_stats['direction_accuracy']:.1%}")
        print(f"📋 Точность типа реакции: {overall_stats['type_accuracy']:.1%}")
        print(f"📏 Средняя ошибка величины: {overall_stats['avg_magnitude_error']:.2f}%")
        print(f"📊 Всего предсказаний: {overall_stats['total_predictions']}")
    
    print("\n" + "=" * 50)
    
    # Производительность по кластерам
    cluster_performance = get_cluster_performance()
    if cluster_performance:
        print("🏆 ПРОИЗВОДИТЕЛЬНОСТЬ ПО КЛАСТЕРАМ:")
        for perf in cluster_performance[:5]:  # Топ-5
            print(f"• {perf['cluster']}: {perf['avg_accuracy']:.1%} ({perf['total_predictions']} предсказаний)")
    
    print("\n" + "=" * 50)
    
    # Слабые паттерны
    weak_patterns = identify_weak_patterns()
    if weak_patterns:
        print("⚠️ СЛАБЫЕ ПАТТЕРНЫ:")
        for pattern in weak_patterns[:3]:  # Топ-3 проблемных
            print(f"• {pattern['cluster']}: {pattern['issue']}")
            print(f"  Частота: {pattern['frequency']} | Точность: {pattern['avg_accuracy']:.1%}")
    
    print("\n" + "=" * 50)

def auto_verify_predictions():
    """Автоматическая верификация предсказаний"""
    conn = sqlite3.connect("data/reactions.db")
    cursor = conn.cursor()
    
    try:
        # Находим события, которые нужно верифицировать (прошло больше 1 часа)
        current_time = int(time.time())
        one_hour_ago = (current_time - 3600) * 1000  # в миллисекундах
        
        cursor.execute("""
            SELECT news_id FROM news_reactions 
            WHERE price_1h IS NOT NULL 
            AND event_timestamp <= ?
        """, (one_hour_ago,))
        
        news_ids = [row[0] for row in cursor.fetchall()]
        
        verified_count = 0
        for news_id in news_ids:
            result = verify_prediction(news_id)
            if result:
                verified_count += 1
        
        print(f"✅ Автоматически верифицировано {verified_count} предсказаний")
        
    except Exception as e:
        print(f"❌ Ошибка автоматической верификации: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # Инициализация БД
    init_verification_database()
    
    # Тест верификации
    test_news_id = "test_001"
    verification = verify_prediction(test_news_id)
    
    if verification:
        print(f"✅ Верификация: {verification}")
    
    # Генерация отчета
    generate_verification_report()
    
    # Автоматическая верификация
    auto_verify_predictions() 