#!/usr/bin/env python3
"""
GHOST | AI News Analyzer
Многослойная ИИ-система для анализа новостей с GPT-4 и Gemini
"""

import json
import sqlite3
import time
import requests
from datetime import datetime
import openai
import google.generativeai as genai
from context_enricher import get_market_data, enrich_news_context
from reaction_logger import log_news_event

# === API Keys ===
import yaml
with open("config/api_keys.yaml") as f:
    keys = yaml.safe_load(f)

# OpenAI GPT-4
openai.api_key = keys.get("openai", {}).get("api_key")

# Google Gemini
genai.configure(api_key=keys.get("gemini", {}).get("api_key"))
gemini_model = genai.GenerativeModel('gemini-pro')

DB_PATH = "data/ai_analysis.db"

def init_ai_database():
    """Инициализация БД для ИИ-анализа"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_news_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            news_id TEXT UNIQUE,
            cluster TEXT,
            gpt_analysis TEXT,
            gemini_analysis TEXT,
            final_verdict TEXT,
            confidence_score REAL,
            similar_cases_found INTEGER,
            market_context TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news_clusters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            news_id TEXT UNIQUE,
            cluster TEXT,
            significance_score REAL, -- 0.0 до 1.0
            is_important BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def filter_and_cluster_news(news_data):
    """Слой 1: Фильтрация и кластеризация новостей"""
    
    # Определяем кластер новости
    title = news_data.get("title", "").lower()
    content = news_data.get("content", "").lower()
    
    clusters = {
        "ETF_approval": ["etf", "sec", "approval", "bitcoin etf"],
        "FOMC_meeting": ["fomc", "federal reserve", "interest rate", "fed"],
        "CPI_report": ["cpi", "inflation", "consumer price"],
        "regulation": ["regulation", "sec", "cfdc", "legal"],
        "institutional": ["institutional", "blackrock", "fidelity", "adoption"],
        "technical": ["technical", "support", "resistance", "breakout"],
        "macro": ["macro", "economy", "recession", "growth"]
    }
    
    # Определяем кластер
    detected_cluster = "general"
    max_matches = 0
    
    for cluster, keywords in clusters.items():
        matches = sum(1 for keyword in keywords if keyword in title or keyword in content)
        if matches > max_matches:
            max_matches = matches
            detected_cluster = cluster
    
    # Оцениваем значимость
    significance_score = calculate_significance(news_data, detected_cluster)
    
    return {
        "cluster": detected_cluster,
        "significance_score": significance_score,
        "is_important": significance_score > 0.7
    }

def calculate_significance(news_data, cluster):
    """Оценка значимости новости"""
    score = 0.0
    
    # Источник новости
    source = news_data.get("source", "").lower()
    if source in ["reuters", "bloomberg", "cnbc", "wsj"]:
        score += 0.3
    elif source in ["coindesk", "cointelegraph"]:
        score += 0.2
    
    # Ключевые слова
    title = news_data.get("title", "").lower()
    important_keywords = ["approval", "rejection", "announcement", "decision", "official"]
    score += sum(0.1 for keyword in important_keywords if keyword in title)
    
    # Длина контента (более подробные новости важнее)
    content_length = len(news_data.get("content", ""))
    if content_length > 500:
        score += 0.2
    
    # Кластерная важность
    cluster_importance = {
        "ETF_approval": 0.9,
        "FOMC_meeting": 0.8,
        "CPI_report": 0.7,
        "regulation": 0.6,
        "institutional": 0.5,
        "technical": 0.3,
        "macro": 0.4
    }
    
    score += cluster_importance.get(cluster, 0.3)
    
    return min(score, 1.0)

def gpt_context_analysis(news_data, market_context):
    """Слой 2: GPT-4 анализ контекста"""
    
    try:
        prompt = f"""
        Ты профессиональный криптотрейдер с 10+ лет опыта. Проанализируй новость:

        НОВОСТЬ:
        Заголовок: {news_data.get('title', '')}
        Содержание: {news_data.get('content', '')}
        Источник: {news_data.get('source', '')}
        Кластер: {news_data.get('cluster', '')}

        КОНТЕКСТ РЫНКА:
        Тренд: {market_context.get('trend', '')}
        RSI: {market_context.get('rsi_14', 0)}
        Позиционирование: {market_context.get('position_skew', '')}
        Фаза рынка: {market_context.get('market_phase', '')}

        АНАЛИЗ:
        1. Что означает эта новость для рынка?
        2. Как рынок отреагирует в данном контексте?
        3. Какие риски и возможности?
        4. Ожидаемое движение цены (в %)
        5. Уверенность в прогнозе (0-100%)

        Ответь в формате JSON:
        {{
            "analysis": "краткий анализ",
            "expected_reaction": "pump/dump/neutral",
            "price_movement": 1.5,
            "confidence": 75,
            "risks": ["список рисков"],
            "opportunities": ["список возможностей"]
        }}
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        gpt_response = response.choices[0].message.content
        
        # Парсим JSON ответ
        try:
            analysis = json.loads(gpt_response)
            return analysis
        except:
            return {"error": "Failed to parse GPT response"}
            
    except Exception as e:
        print(f"❌ Ошибка GPT анализа: {e}")
        return {"error": str(e)}

def gemini_pattern_analysis(news_id, cluster, market_context):
    """Слой 3: Gemini анализ паттернов"""
    
    try:
        # Получаем исторические данные
        conn = sqlite3.connect("data/reactions.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT title, reaction_type, price_change_1h, created_at
            FROM news_reactions 
            WHERE cluster = ? AND created_at >= datetime('now', '-90 days')
            ORDER BY created_at DESC
            LIMIT 10
        """, (cluster,))
        
        historical_cases = cursor.fetchall()
        conn.close()
        
        # Формируем промпт для Gemini
        historical_text = ""
        for title, reaction, change, date in historical_cases:
            historical_text += f"- {date}: {title} → {reaction} ({change:.1f}%)\n"
        
        prompt = f"""
        Ты эксперт по анализу рыночных паттернов. Проанализируй:

        ТЕКУЩАЯ НОВОСТЬ: {news_id}
        КЛАСТЕР: {cluster}
        РЫНОЧНЫЙ КОНТЕКСТ: {market_context}

        ИСТОРИЧЕСКИЕ СЛУЧАИ:
        {historical_text}

        ЗАДАЧА:
        1. Найди похожие паттерны в истории
        2. Определи повторяющиеся реакции
        3. Спрогнозируй реакцию на текущую новость
        4. Оцени уверенность в прогнозе

        Ответь в формате JSON:
        {{
            "similar_patterns": ["описание паттернов"],
            "expected_reaction": "pump/dump/neutral",
            "confidence": 80,
            "reasoning": "объяснение",
            "similar_cases_count": 5
        }}
        """
        
        response = gemini_model.generate_content(prompt)
        gemini_response = response.text
        
        # Парсим JSON ответ
        try:
            analysis = json.loads(gemini_response)
            return analysis
        except:
            return {"error": "Failed to parse Gemini response"}
            
    except Exception as e:
        print(f"❌ Ошибка Gemini анализа: {e}")
        return {"error": str(e)}

def synthesize_ai_insights(gpt_analysis, gemini_analysis, market_context):
    """Слой 4: Синтез выводов всех ИИ"""
    
    # Если есть ошибки в анализах
    if "error" in gpt_analysis or "error" in gemini_analysis:
        return {
            "final_verdict": "neutral",
            "confidence": 0.3,
            "reasoning": "Ошибка в ИИ-анализе"
        }
    
    # Сравниваем выводы GPT и Gemini
    gpt_reaction = gpt_analysis.get("expected_reaction", "neutral")
    gemini_reaction = gemini_analysis.get("expected_reaction", "neutral")
    
    gpt_confidence = gpt_analysis.get("confidence", 50) / 100
    gemini_confidence = gemini_analysis.get("confidence", 50) / 100
    
    # Если ИИ согласны
    if gpt_reaction == gemini_reaction:
        final_verdict = gpt_reaction
        confidence = (gpt_confidence + gemini_confidence) / 2
        reasoning = f"GPT и Gemini согласны: {gpt_reaction}"
    else:
        # Выбираем более уверенный прогноз
        if gpt_confidence > gemini_confidence:
            final_verdict = gpt_reaction
            confidence = gpt_confidence * 0.8  # Снижаем уверенность при разногласиях
            reasoning = f"GPT более уверен: {gpt_reaction}"
        else:
            final_verdict = gemini_reaction
            confidence = gemini_confidence * 0.8
            reasoning = f"Gemini более уверен: {gemini_reaction}"
    
    return {
        "final_verdict": final_verdict,
        "confidence": confidence,
        "reasoning": reasoning,
        "gpt_analysis": gpt_analysis,
        "gemini_analysis": gemini_analysis
    }

def analyze_news_with_ai(news_data):
    """Основная функция многослойного ИИ-анализа"""
    
    # Слой 1: Фильтрация и кластеризация
    clustering = filter_and_cluster_news(news_data)
    news_data["cluster"] = clustering["cluster"]
    
    # Если новость не важная - пропускаем
    if not clustering["is_important"]:
        print(f"⚠️ Новость {news_data.get('news_id')} не важная, пропускаем")
        return None
    
    # Логируем событие
    log_news_event(news_data)
    
    # Обогащаем контекстом
    market_context = enrich_news_context(news_data["news_id"])
    if not market_context:
        print(f"❌ Не удалось получить контекст для {news_data['news_id']}")
        return None
    
    # Слой 2: GPT анализ
    print(f"🧠 GPT анализирует {news_data['news_id']}...")
    gpt_analysis = gpt_context_analysis(news_data, market_context)
    
    # Слой 3: Gemini анализ
    print(f"🤖 Gemini анализирует {news_data['news_id']}...")
    gemini_analysis = gemini_pattern_analysis(
        news_data["news_id"], 
        clustering["cluster"], 
        market_context
    )
    
    # Слой 4: Синтез
    final_verdict = synthesize_ai_insights(gpt_analysis, gemini_analysis, market_context)
    
    # Сохраняем анализ
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO ai_news_analysis 
            (news_id, cluster, gpt_analysis, gemini_analysis, final_verdict,
             confidence_score, market_context)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            news_data["news_id"],
            clustering["cluster"],
            json.dumps(gpt_analysis),
            json.dumps(gemini_analysis),
            final_verdict["final_verdict"],
            final_verdict["confidence"],
            json.dumps(market_context)
        ))
        
        conn.commit()
        print(f"✅ ИИ-анализ завершен: {final_verdict['final_verdict']} ({final_verdict['confidence']:.1%})")
        
        return {
            "news_id": news_data["news_id"],
            "cluster": clustering["cluster"],
            "final_verdict": final_verdict,
            "gpt_analysis": gpt_analysis,
            "gemini_analysis": gemini_analysis
        }
        
    except Exception as e:
        print(f"❌ Ошибка сохранения анализа: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def get_ai_analysis_summary(news_id):
    """Получение краткого описания ИИ-анализа"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT final_verdict, confidence_score, gpt_analysis, gemini_analysis
            FROM ai_news_analysis WHERE news_id = ?
        """, (news_id,))
        
        result = cursor.fetchone()
        if not result:
            return None
            
        verdict, confidence, gpt_json, gemini_json = result
        
        gpt_analysis = json.loads(gpt_json) if gpt_json else {}
        gemini_analysis = json.loads(gemini_json) if gemini_json else {}
        
        summary = f"ИИ-ВЕРДИКТ: {verdict.upper()} | Уверенность: {confidence:.1%}\n"
        summary += f"GPT: {gpt_analysis.get('expected_reaction', 'N/A')} ({gpt_analysis.get('confidence', 0)}%)\n"
        summary += f"Gemini: {gemini_analysis.get('expected_reaction', 'N/A')} ({gemini_analysis.get('confidence', 0)}%)"
        
        return summary
        
    except Exception as e:
        print(f"❌ Ошибка получения анализа: {e}")
        return None
    finally:
        conn.close()

if __name__ == "__main__":
    # Инициализация БД
    init_ai_database()
    
    # Тест ИИ-анализа
    test_news = {
        "news_id": "ai_test_001",
        "title": "SEC Approves Bitcoin ETF - Major Milestone for Crypto",
        "content": "The Securities and Exchange Commission has officially approved the first Bitcoin ETF, marking a historic moment for cryptocurrency adoption...",
        "source": "Reuters",
        "published_at": datetime.now().isoformat(),
        "symbol": "BTCUSDT"
    }
    
    result = analyze_news_with_ai(test_news)
    
    if result:
        print(f"✅ ИИ-анализ: {result}")
        
        summary = get_ai_analysis_summary("ai_test_001")
        print(f"📊 Краткое описание: {summary}") 