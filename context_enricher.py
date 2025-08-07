#!/usr/bin/env python3
"""
GHOST | Context Enricher
Сопровождает каждую новость рыночным состоянием: тренд, RSI, funding rate, sentiment и т.д.
"""

import json
import sqlite3
import time
import requests
from datetime import datetime
from price_feed_logger import get_price_at
import yaml

# === API Подключение ===
with open("config/api_keys.yaml") as f:
    keys = yaml.safe_load(f)["bybit"]

from pybit.unified_trading import HTTP
session = HTTP(api_key=keys["api_key"], api_secret=keys["api_secret"])

DB_PATH = "data/context.db"

def init_context_database():
    """Инициализация базы данных для контекста"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_context (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            news_id TEXT UNIQUE,
            timestamp INTEGER,
            symbol TEXT DEFAULT 'BTCUSDT',
            price REAL,
            rsi_14 REAL,
            rsi_1h REAL,
            trend TEXT, -- 'bullish', 'bearish', 'sideways'
            funding_rate REAL,
            fear_greed_index INTEGER,
            volatility_regime TEXT, -- 'low', 'medium', 'high'
            position_skew TEXT, -- 'crowded_longs', 'crowded_shorts', 'neutral'
            day_of_week TEXT,
            hour_of_day INTEGER,
            market_phase TEXT, -- 'accumulation', 'markup', 'distribution', 'markdown'
            volume_24h REAL,
            volume_change_1h REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Индексы
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_id ON market_context(news_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON market_context(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trend ON market_context(trend)")
    
    conn.commit()
    conn.close()

def calculate_rsi(prices, period=14):
    """Расчет RSI"""
    if len(prices) < period + 1:
        return None
    
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def get_market_data(symbol='BTCUSDT'):
    """Получение рыночных данных"""
    try:
        # Получаем свечи для расчета RSI
        response = session.get_kline(
            category="linear",
            symbol=symbol,
            interval="1",
            limit=50
        )
        
        if response["retCode"] != 0:
            return None
            
        klines = response["result"]["list"]
        prices = [float(kline[4]) for kline in klines]  # close prices
        
        # Текущая цена
        current_price = prices[-1]
        
        # RSI
        rsi_14 = calculate_rsi(prices, 14)
        rsi_1h = calculate_rsi(prices[-60:], 14) if len(prices) >= 60 else rsi_14
        
        # Тренд (простая логика)
        if len(prices) >= 20:
            sma_20 = sum(prices[-20:]) / 20
            trend = "bullish" if current_price > sma_20 else "bearish"
        else:
            trend = "sideways"
        
        # Funding Rate
        try:
            funding_response = session.get_funding_rate(
                category="linear",
                symbol=symbol
            )
            funding_rate = float(funding_response["result"]["list"][0]["fundingRate"]) if funding_response["retCode"] == 0 else 0
        except:
            funding_rate = 0
        
        # Fear & Greed Index (упрощенная версия)
        if rsi_14:
            if rsi_14 > 70:
                fear_greed = 80  # Greed
            elif rsi_14 < 30:
                fear_greed = 20  # Fear
            else:
                fear_greed = 50  # Neutral
        else:
            fear_greed = 50
        
        # Volatility Regime
        if len(prices) >= 20:
            returns = [(prices[i] - prices[i-1])/prices[i-1] for i in range(1, len(prices))]
            volatility = (sum([r*r for r in returns[-20:]]) / 20) ** 0.5 * 100
            
            if volatility > 5:
                volatility_regime = "high"
            elif volatility > 2:
                volatility_regime = "medium"
            else:
                volatility_regime = "low"
        else:
            volatility_regime = "medium"
        
        # Position Skew (упрощенная логика)
        if funding_rate > 0.01:
            position_skew = "crowded_longs"
        elif funding_rate < -0.01:
            position_skew = "crowded_shorts"
        else:
            position_skew = "neutral"
        
        # Market Phase
        if trend == "bullish" and rsi_14 and rsi_14 < 70:
            market_phase = "markup"
        elif trend == "bullish" and rsi_14 and rsi_14 > 70:
            market_phase = "distribution"
        elif trend == "bearish" and rsi_14 and rsi_14 > 30:
            market_phase = "markdown"
        else:
            market_phase = "accumulation"
        
        # Volume
        volumes = [float(kline[5]) for kline in klines]
        volume_24h = sum(volumes[-24:]) if len(volumes) >= 24 else sum(volumes)
        volume_change_1h = ((volumes[-1] - volumes[-2]) / volumes[-2] * 100) if len(volumes) >= 2 else 0
        
        return {
            "price": current_price,
            "rsi_14": rsi_14,
            "rsi_1h": rsi_1h,
            "trend": trend,
            "funding_rate": funding_rate,
            "fear_greed_index": fear_greed,
            "volatility_regime": volatility_regime,
            "position_skew": position_skew,
            "market_phase": market_phase,
            "volume_24h": volume_24h,
            "volume_change_1h": volume_change_1h
        }
        
    except Exception as e:
        print(f"❌ Ошибка получения рыночных данных: {e}")
        return None

def enrich_news_context(news_id, symbol='BTCUSDT'):
    """Обогащение новости рыночным контекстом"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Получаем рыночные данные
        market_data = get_market_data(symbol)
        
        if not market_data:
            print(f"❌ Не удалось получить рыночные данные для {news_id}")
            return None
        
        # Текущее время
        current_time = int(time.time() * 1000)
        dt = datetime.now()
        
        cursor.execute("""
            INSERT OR REPLACE INTO market_context 
            (news_id, timestamp, symbol, price, rsi_14, rsi_1h, trend, 
             funding_rate, fear_greed_index, volatility_regime, position_skew,
             day_of_week, hour_of_day, market_phase, volume_24h, volume_change_1h)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            news_id,
            current_time,
            symbol,
            market_data["price"],
            market_data["rsi_14"],
            market_data["rsi_1h"],
            market_data["trend"],
            market_data["funding_rate"],
            market_data["fear_greed_index"],
            market_data["volatility_regime"],
            market_data["position_skew"],
            dt.strftime("%A"),
            dt.hour,
            market_data["market_phase"],
            market_data["volume_24h"],
            market_data["volume_change_1h"]
        ))
        
        conn.commit()
        print(f"✅ Обогащен контекст для {news_id}: {market_data['trend']} | RSI: {market_data['rsi_14']:.1f}")
        
        return market_data
        
    except Exception as e:
        print(f"❌ Ошибка обогащения контекста: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def get_context_summary(news_id):
    """Получение краткого описания контекста"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT trend, rsi_14, funding_rate, fear_greed_index, 
                   volatility_regime, position_skew, market_phase
            FROM market_context WHERE news_id = ?
        """, (news_id,))
        
        result = cursor.fetchone()
        if not result:
            return None
            
        trend, rsi, funding, fear_greed, volatility, position, phase = result
        
        summary = f"{trend.upper()} | RSI: {rsi:.1f} | Funding: {funding:.4f} | "
        summary += f"Fear/Greed: {fear_greed} | Vol: {volatility} | "
        summary += f"Position: {position} | Phase: {phase}"
        
        return summary
        
    except Exception as e:
        print(f"❌ Ошибка получения контекста: {e}")
        return None
    finally:
        conn.close()

def analyze_context_pattern(news_id):
    """Анализ паттернов контекста"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT trend, rsi_14, funding_rate, fear_greed_index, 
                   volatility_regime, position_skew, market_phase
            FROM market_context WHERE news_id = ?
        """, (news_id,))
        
        result = cursor.fetchone()
        if not result:
            return None
            
        trend, rsi, funding, fear_greed, volatility, position, phase = result
        
        patterns = []
        
        # Анализ перекупленности/перепроданности
        if rsi and rsi > 70:
            patterns.append("overbought")
        elif rsi and rsi < 30:
            patterns.append("oversold")
        
        # Анализ позиционирования
        if position == "crowded_longs":
            patterns.append("crowded_longs")
        elif position == "crowded_shorts":
            patterns.append("crowded_shorts")
        
        # Анализ фазы рынка
        if phase == "distribution":
            patterns.append("distribution_phase")
        elif phase == "accumulation":
            patterns.append("accumulation_phase")
        
        # Анализ волатильности
        if volatility == "high":
            patterns.append("high_volatility")
        
        return patterns
        
    except Exception as e:
        print(f"❌ Ошибка анализа паттернов: {e}")
        return []
    finally:
        conn.close()

def get_context_for_prediction(news_id):
    """Получение контекста для предсказания"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT * FROM market_context WHERE news_id = ?
        """, (news_id,))
        
        result = cursor.fetchone()
        if not result:
            return None
            
        # Преобразуем в словарь
        columns = [desc[0] for desc in cursor.description]
        context_data = dict(zip(columns, result))
        
        return context_data
        
    except Exception as e:
        print(f"❌ Ошибка получения контекста для предсказания: {e}")
        return None
    finally:
        conn.close()

if __name__ == "__main__":
    # Инициализация БД
    init_context_database()
    
    # Тест обогащения контекста
    test_news_id = "test_001"
    context = enrich_news_context(test_news_id)
    
    if context:
        print(f"✅ Контекст обогащен: {context}")
        
        summary = get_context_summary(test_news_id)
        print(f"📊 Краткое описание: {summary}")
        
        patterns = analyze_context_pattern(test_news_id)
        print(f"🔍 Паттерны: {patterns}") 