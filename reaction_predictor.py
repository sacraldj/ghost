#!/usr/bin/env python3
"""
GHOST | Reaction Predictor
Предсказание реакции на новость с учётом контекста (rule-based или через GPT)
"""

import json
import sqlite3
import time
from datetime import datetime
from context_enricher import get_context_for_prediction, analyze_context_pattern
from reaction_logger import get_reaction_stats

DB_PATH = "data/predictions.db"

def init_predictions_database():
    """Инициализация базы данных для предсказаний"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            news_id TEXT UNIQUE,
            cluster TEXT,
            context_summary TEXT,
            predicted_reaction TEXT, -- 'pump', 'dump', 'neutral', 'short_pump_then_fade'
            predicted_change_percent REAL,
            confidence_score REAL, -- 0.0 до 1.0
            reasoning TEXT,
            patterns_detected TEXT, -- JSON array
            similar_cases_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Индексы
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_id ON news_predictions(news_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cluster ON news_predictions(cluster)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_predicted_reaction ON news_predictions(predicted_reaction)")
    
    conn.commit()
    conn.close()

def find_similar_cases(cluster, context_patterns, days=90):
    """Поиск похожих случаев в истории"""
    conn = sqlite3.connect("data/reactions.db")
    cursor = conn.cursor()
    
    try:
        # Ищем случаи с тем же кластером
        cursor.execute("""
            SELECT reaction_type, price_change_1h, COUNT(*) as count
            FROM news_reactions 
            WHERE cluster = ? AND created_at >= datetime('now', '-{} days')
            GROUP BY reaction_type, price_change_1h
        """.format(days), (cluster,))
        
        results = cursor.fetchall()
        similar_cases = []
        
        for reaction_type, price_change, count in results:
            if price_change is not None:
                similar_cases.append({
                    "reaction_type": reaction_type,
                    "price_change": price_change,
                    "count": count
                })
        
        return similar_cases
        
    except Exception as e:
        print(f"❌ Ошибка поиска похожих случаев: {e}")
        return []
    finally:
        conn.close()

def rule_based_prediction(cluster, context_data, patterns):
    """Rule-based предсказание на основе контекста"""
    
    # Базовые правила
    prediction = {
        "reaction_type": "neutral",
        "predicted_change": 0.0,
        "confidence": 0.5,
        "reasoning": []
    }
    
    # Анализ тренда
    trend = context_data.get("trend", "sideways")
    rsi = context_data.get("rsi_14", 50)
    position_skew = context_data.get("position_skew", "neutral")
    market_phase = context_data.get("market_phase", "accumulation")
    
    # Правило 1: Перекупленность + позитивные новости = sell-the-news
    if rsi > 70 and "overbought" in patterns:
        if cluster in ["ETF_approval", "ETF_rumor", "positive_news"]:
            prediction["reaction_type"] = "short_pump_then_fade"
            prediction["predicted_change"] = -1.5
            prediction["confidence"] = 0.7
            prediction["reasoning"].append("RSI > 70 (перекуплен) + позитивная новость = sell-the-news")
    
    # Правило 2: Перепроданность + негативные новости = buy-the-dip
    elif rsi < 30 and "oversold" in patterns:
        if cluster in ["FOMC_hawkish", "negative_news", "regulation"]:
            prediction["reaction_type"] = "pump"
            prediction["predicted_change"] = 2.0
            prediction["confidence"] = 0.6
            prediction["reasoning"].append("RSI < 30 (перепродан) + негативная новость = buy-the-dip")
    
    # Правило 3: Crowded longs + любая новость = потенциальный dump
    elif position_skew == "crowded_longs":
        prediction["reaction_type"] = "dump"
        prediction["predicted_change"] = -1.0
        prediction["confidence"] = 0.6
        prediction["reasoning"].append("Crowded longs = риск ликвидации")
    
    # Правило 4: Crowded shorts + позитивные новости = squeeze
    elif position_skew == "crowded_shorts":
        if cluster in ["ETF_approval", "positive_news"]:
            prediction["reaction_type"] = "pump"
            prediction["predicted_change"] = 2.5
            prediction["confidence"] = 0.7
            prediction["reasoning"].append("Crowded shorts + позитивная новость = squeeze")
    
    # Правило 5: Distribution phase + любая новость = dump
    elif market_phase == "distribution":
        prediction["reaction_type"] = "dump"
        prediction["predicted_change"] = -1.5
        prediction["confidence"] = 0.6
        prediction["reasoning"].append("Distribution phase = продажи")
    
    # Правило 6: Accumulation phase + позитивные новости = pump
    elif market_phase == "accumulation":
        if cluster in ["ETF_approval", "positive_news"]:
            prediction["reaction_type"] = "pump"
            prediction["predicted_change"] = 1.5
            prediction["confidence"] = 0.6
            prediction["reasoning"].append("Accumulation phase + позитивная новость = pump")
    
    # Правило 7: Высокая волатильность = усиление движений
    if "high_volatility" in patterns:
        prediction["predicted_change"] *= 1.5
        prediction["reasoning"].append("Высокая волатильность усиливает движения")
    
    return prediction

def gpt_style_prediction(cluster, context_data, patterns):
    """GPT-стиль предсказание с объяснением"""
    
    # Получаем статистику по кластеру
    stats = get_reaction_stats(cluster, days=30)
    
    # Анализируем контекст
    trend = context_data.get("trend", "sideways")
    rsi = context_data.get("rsi_14", 50)
    position_skew = context_data.get("position_skew", "neutral")
    market_phase = context_data.get("market_phase", "accumulation")
    
    # Формируем объяснение
    explanation = f"Анализ новости типа '{cluster}' в контексте:\n"
    explanation += f"• Тренд: {trend}\n"
    explanation += f"• RSI: {rsi:.1f}\n"
    explanation += f"• Позиционирование: {position_skew}\n"
    explanation += f"• Фаза рынка: {market_phase}\n"
    explanation += f"• Паттерны: {', '.join(patterns)}\n"
    
    # Анализ исторической статистики
    if stats:
        explanation += f"\nИсторическая статистика по '{cluster}':\n"
        for reaction_type, count in stats.items():
            explanation += f"• {reaction_type}: {count} случаев\n"
    
    # Логика предсказания
    if "overbought" in patterns and cluster in ["ETF_approval", "positive_news"]:
        prediction = {
            "reaction_type": "short_pump_then_fade",
            "predicted_change": -1.8,
            "confidence": 0.75,
            "reasoning": explanation + "\nВывод: Рынок перекуплен + позитивная новость = sell-the-news эффект"
        }
    elif "oversold" in patterns and cluster in ["FOMC_hawkish", "negative_news"]:
        prediction = {
            "reaction_type": "pump",
            "predicted_change": 2.2,
            "confidence": 0.65,
            "reasoning": explanation + "\nВывод: Рынок перепродан + негативная новость = buy-the-dip"
        }
    elif position_skew == "crowded_longs":
        prediction = {
            "reaction_type": "dump",
            "predicted_change": -1.2,
            "confidence": 0.6,
            "reasoning": explanation + "\nВывод: Crowded longs = риск ликвидации"
        }
    else:
        prediction = {
            "reaction_type": "neutral",
            "predicted_change": 0.3,
            "confidence": 0.4,
            "reasoning": explanation + "\nВывод: Нейтральная реакция ожидается"
        }
    
    return prediction

def predict_news_reaction(news_id, cluster, use_gpt_style=True):
    """Основная функция предсказания реакции на новость"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Получаем контекст
        context_data = get_context_for_prediction(news_id)
        if not context_data:
            print(f"❌ Контекст не найден для {news_id}")
            return None
        
        # Анализируем паттерны
        patterns = analyze_context_pattern(news_id)
        
        # Ищем похожие случаи
        similar_cases = find_similar_cases(cluster, patterns)
        
        # Делаем предсказание
        if use_gpt_style:
            prediction = gpt_style_prediction(cluster, context_data, patterns)
        else:
            prediction = rule_based_prediction(cluster, context_data, patterns)
        
        # Корректируем на основе похожих случаев
        if similar_cases:
            avg_change = sum(case["price_change"] for case in similar_cases) / len(similar_cases)
            prediction["predicted_change"] = (prediction["predicted_change"] + avg_change) / 2
            prediction["confidence"] = min(prediction["confidence"] + 0.1, 0.9)
            prediction["reasoning"] += f"\nСкорректировано на основе {len(similar_cases)} похожих случаев"
        
        # Сохраняем предсказание
        cursor.execute("""
            INSERT OR REPLACE INTO news_predictions 
            (news_id, cluster, context_summary, predicted_reaction, predicted_change_percent,
             confidence_score, reasoning, patterns_detected, similar_cases_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            news_id,
            cluster,
            f"{context_data.get('trend', 'unknown')} | RSI: {context_data.get('rsi_14', 0):.1f}",
            prediction["reaction_type"],
            prediction["predicted_change"],
            prediction["confidence"],
            prediction["reasoning"],
            json.dumps(patterns),
            len(similar_cases)
        ))
        
        conn.commit()
        print(f"✅ Предсказание для {news_id}: {prediction['reaction_type']} ({prediction['predicted_change']:.1f}%)")
        
        return prediction
        
    except Exception as e:
        print(f"❌ Ошибка предсказания: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def get_prediction_summary(news_id):
    """Получение краткого описания предсказания"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT predicted_reaction, predicted_change_percent, confidence_score, reasoning
            FROM news_predictions WHERE news_id = ?
        """, (news_id,))
        
        result = cursor.fetchone()
        if not result:
            return None
            
        reaction, change, confidence, reasoning = result
        
        summary = f"Предсказание: {reaction.upper()} | Изменение: {change:.1f}% | Уверенность: {confidence:.1%}"
        
        return summary
        
    except Exception as e:
        print(f"❌ Ошибка получения предсказания: {e}")
        return None
    finally:
        conn.close()

def get_prediction_accuracy(news_id):
    """Получение точности предсказания (после того как реакция произошла)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Получаем предсказание
        cursor.execute("""
            SELECT predicted_reaction, predicted_change_percent
            FROM news_predictions WHERE news_id = ?
        """, (news_id,))
        
        pred_result = cursor.fetchone()
        if not pred_result:
            return None
            
        predicted_reaction, predicted_change = pred_result
        
        # Получаем фактическую реакцию
        cursor.execute("""
            SELECT reaction_type, price_change_1h
            FROM news_reactions WHERE news_id = ?
        """, (news_id,))
        
        actual_result = cursor.fetchone()
        if not actual_result:
            return None
            
        actual_reaction, actual_change = actual_result
        
        # Вычисляем точность
        if actual_change is None:
            return None
            
        direction_correct = (
            (predicted_change > 0 and actual_change > 0) or
            (predicted_change < 0 and actual_change < 0) or
            (abs(predicted_change) < 0.5 and abs(actual_change) < 0.5)
        )
        
        magnitude_error = abs(abs(predicted_change) - abs(actual_change))
        
        accuracy = {
            "direction_correct": direction_correct,
            "magnitude_error": magnitude_error,
            "predicted": predicted_change,
            "actual": actual_change,
            "reaction_type_match": predicted_reaction == actual_reaction
        }
        
        return accuracy
        
    except Exception as e:
        print(f"❌ Ошибка вычисления точности: {e}")
        return None
    finally:
        conn.close()

if __name__ == "__main__":
    # Инициализация БД
    init_predictions_database()
    
    # Тест предсказания
    test_news_id = "test_001"
    test_cluster = "ETF_approval"
    
    prediction = predict_news_reaction(test_news_id, test_cluster, use_gpt_style=True)
    
    if prediction:
        print(f"✅ Предсказание: {prediction}")
        
        summary = get_prediction_summary(test_news_id)
        print(f"📊 Краткое описание: {summary}") 