#!/usr/bin/env python3
"""
GHOST News Statistics Tracker
Отдельный модуль для сбора "полной статистики" по новостям (как просил Дарэн)
НЕ ВЛИЯЕТ на основную торговую логику
"""

import os
import sys
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class NewsStatistics:
    """Статистика по новостям"""
    total_news_processed: int = 0
    critical_news_count: int = 0
    prediction_accuracy: float = 0.0
    avg_market_impact: float = 0.0
    sentiment_distribution: Dict[str, int] = None
    source_reliability: Dict[str, float] = None
    cluster_performance: Dict[str, Dict] = None
    time_impact_analysis: Dict[str, float] = None
    false_signals_count: int = 0
    
    def __post_init__(self):
        if self.sentiment_distribution is None:
            self.sentiment_distribution = {'bullish': 0, 'bearish': 0, 'neutral': 0}
        if self.source_reliability is None:
            self.source_reliability = {}
        if self.cluster_performance is None:
            self.cluster_performance = {}
        if self.time_impact_analysis is None:
            self.time_impact_analysis = {'1h': 0.0, '4h': 0.0, '24h': 0.0}

class NewsStatisticsTracker:
    """
    Трекер статистики новостей
    Работает независимо от основной системы торговли
    """
    
    def __init__(self, db_path: str = "data/news_statistics.db"):
        self.db_path = db_path
        self._init_database()
        logger.info(f"📊 News Statistics Tracker initialized with DB: {db_path}")
    
    def _init_database(self):
        """Инициализация базы данных для статистики"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица общей статистики
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_stats_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE UNIQUE,
                total_news INTEGER DEFAULT 0,
                critical_news INTEGER DEFAULT 0,
                prediction_accuracy REAL DEFAULT 0.0,
                avg_market_impact REAL DEFAULT 0.0,
                bullish_count INTEGER DEFAULT 0,
                bearish_count INTEGER DEFAULT 0,
                neutral_count INTEGER DEFAULT 0,
                false_signals INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица надёжности источников
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS source_reliability (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_name TEXT,
                date DATE,
                total_predictions INTEGER DEFAULT 0,
                correct_predictions INTEGER DEFAULT 0,
                accuracy_rate REAL DEFAULT 0.0,
                avg_impact_score REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source_name, date)
            )
        """)
        
        # Таблица производительности кластеров
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cluster_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cluster_name TEXT,
                date DATE,
                news_count INTEGER DEFAULT 0,
                avg_sentiment REAL DEFAULT 0.0,
                avg_accuracy REAL DEFAULT 0.0,
                market_impact_1h REAL DEFAULT 0.0,
                market_impact_4h REAL DEFAULT 0.0,
                market_impact_24h REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(cluster_name, date)
            )
        """)
        
        # Таблица влияния по времени
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS time_impact_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                news_id TEXT,
                cluster TEXT,
                sentiment REAL,
                predicted_impact REAL,
                actual_impact_1h REAL,
                actual_impact_4h REAL,
                actual_impact_24h REAL,
                accuracy_1h REAL,
                accuracy_4h REAL,
                accuracy_24h REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def record_news_event(self, news_data: Dict):
        """Записать новостное событие для статистики"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            today = datetime.now().date()
            
            # Определяем sentiment
            sentiment_score = news_data.get('sentiment', 0.0)
            if sentiment_score > 0.1:
                sentiment_category = 'bullish'
            elif sentiment_score < -0.1:
                sentiment_category = 'bearish'
            else:
                sentiment_category = 'neutral'
            
            # Обновляем общую статистику
            cursor.execute("""
                INSERT OR IGNORE INTO news_stats_summary (date) VALUES (?)
            """, (today,))
            
            cursor.execute(f"""
                UPDATE news_stats_summary 
                SET total_news = total_news + 1,
                    {sentiment_category}_count = {sentiment_category}_count + 1,
                    avg_market_impact = (avg_market_impact * (total_news - 1) + ?) / total_news
                WHERE date = ?
            """, (news_data.get('market_impact', 0.0), today))
            
            # Отмечаем критические новости
            if news_data.get('is_critical', False) or news_data.get('urgency', 0.0) > 0.7:
                cursor.execute("""
                    UPDATE news_stats_summary 
                    SET critical_news = critical_news + 1
                    WHERE date = ?
                """, (today,))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"📊 Recorded news event: {sentiment_category}, impact: {news_data.get('market_impact', 0.0):.2f}")
            
        except Exception as e:
            logger.error(f"❌ Error recording news event: {e}")
    
    def record_prediction_accuracy(self, news_id: str, predicted: float, actual: float, timeframe: str):
        """Записать точность предсказания"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Вычисляем точность (обратная к ошибке)
            error = abs(predicted - actual)
            max_error = max(abs(predicted), abs(actual), 1.0)  # Избегаем деления на 0
            accuracy = max(0.0, 1.0 - (error / max_error))
            
            # Записываем в таблицу временного анализа
            cursor.execute(f"""
                UPDATE time_impact_analysis 
                SET actual_impact_{timeframe} = ?, accuracy_{timeframe} = ?
                WHERE news_id = ?
            """, (actual, accuracy, news_id))
            
            # Обновляем общую точность за сегодня
            today = datetime.now().date()
            cursor.execute("""
                UPDATE news_stats_summary 
                SET prediction_accuracy = (
                    SELECT AVG(accuracy_1h) FROM time_impact_analysis 
                    WHERE date(timestamp) = ?
                )
                WHERE date = ?
            """, (today, today))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"📊 Recorded prediction accuracy: {accuracy:.2f} for {timeframe}")
            
        except Exception as e:
            logger.error(f"❌ Error recording prediction accuracy: {e}")
    
    def record_source_reliability(self, source_name: str, was_accurate: bool, impact_score: float):
        """Записать надёжность источника"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            today = datetime.now().date()
            
            # Обновляем статистику источника
            cursor.execute("""
                INSERT OR REPLACE INTO source_reliability 
                (source_name, date, total_predictions, correct_predictions, accuracy_rate, avg_impact_score)
                VALUES (
                    ?, ?, 
                    COALESCE((SELECT total_predictions FROM source_reliability WHERE source_name = ? AND date = ?), 0) + 1,
                    COALESCE((SELECT correct_predictions FROM source_reliability WHERE source_name = ? AND date = ?), 0) + ?,
                    CASE WHEN (COALESCE((SELECT total_predictions FROM source_reliability WHERE source_name = ? AND date = ?), 0) + 1) > 0 
                         THEN (COALESCE((SELECT correct_predictions FROM source_reliability WHERE source_name = ? AND date = ?), 0) + ?) * 1.0 / (COALESCE((SELECT total_predictions FROM source_reliability WHERE source_name = ? AND date = ?), 0) + 1)
                         ELSE 0.0 END,
                    (COALESCE((SELECT avg_impact_score FROM source_reliability WHERE source_name = ? AND date = ?), 0) * COALESCE((SELECT total_predictions FROM source_reliability WHERE source_name = ? AND date = ?), 0) + ?) / (COALESCE((SELECT total_predictions FROM source_reliability WHERE source_name = ? AND date = ?), 0) + 1)
                )
            """, (
                source_name, today,  # INSERT values
                source_name, today,  # total_predictions SELECT
                source_name, today, 1 if was_accurate else 0,  # correct_predictions SELECT + increment
                source_name, today,  # accuracy_rate calculation - total_predictions
                source_name, today, 1 if was_accurate else 0,  # accuracy_rate calculation - correct_predictions
                source_name, today,  # accuracy_rate calculation - total_predictions (denominator)
                source_name, today,  # avg_impact_score calculation - existing avg
                source_name, today,  # avg_impact_score calculation - existing total
                impact_score,  # avg_impact_score calculation - new impact
                source_name, today   # avg_impact_score calculation - total for denominator
            ))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"📊 Recorded source reliability: {source_name}, accurate: {was_accurate}")
            
        except Exception as e:
            logger.error(f"❌ Error recording source reliability: {e}")
    
    def get_full_statistics(self, days: int = 30) -> NewsStatistics:
        """Получить полную статистику за период"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            start_date = (datetime.now() - timedelta(days=days)).date()
            
            # Общая статистика
            cursor.execute("""
                SELECT 
                    SUM(total_news) as total_news,
                    SUM(critical_news) as critical_news,
                    AVG(prediction_accuracy) as avg_accuracy,
                    AVG(avg_market_impact) as avg_impact,
                    SUM(bullish_count) as bullish,
                    SUM(bearish_count) as bearish,
                    SUM(neutral_count) as neutral,
                    SUM(false_signals) as false_signals
                FROM news_stats_summary 
                WHERE date >= ?
            """, (start_date,))
            
            row = cursor.fetchone()
            if row and row[0]:  # Проверяем что есть данные
                total_news, critical_news, avg_accuracy, avg_impact, bullish, bearish, neutral, false_signals = row
            else:
                total_news = critical_news = bullish = bearish = neutral = false_signals = 0
                avg_accuracy = avg_impact = 0.0
            
            # Надёжность источников
            cursor.execute("""
                SELECT source_name, AVG(accuracy_rate) as avg_accuracy
                FROM source_reliability 
                WHERE date >= ?
                GROUP BY source_name
                ORDER BY avg_accuracy DESC
            """, (start_date,))
            
            source_reliability = dict(cursor.fetchall())
            
            # Производительность кластеров
            cursor.execute("""
                SELECT 
                    cluster_name,
                    AVG(avg_accuracy) as accuracy,
                    AVG(market_impact_1h) as impact_1h,
                    AVG(market_impact_4h) as impact_4h,
                    AVG(market_impact_24h) as impact_24h,
                    COUNT(*) as count
                FROM cluster_performance 
                WHERE date >= ?
                GROUP BY cluster_name
            """, (start_date,))
            
            cluster_performance = {}
            for row in cursor.fetchall():
                cluster_name, accuracy, impact_1h, impact_4h, impact_24h, count = row
                cluster_performance[cluster_name] = {
                    'accuracy': accuracy or 0.0,
                    'impact_1h': impact_1h or 0.0,
                    'impact_4h': impact_4h or 0.0,
                    'impact_24h': impact_24h or 0.0,
                    'count': count or 0
                }
            
            # Временной анализ
            cursor.execute("""
                SELECT 
                    AVG(accuracy_1h) as avg_1h,
                    AVG(accuracy_4h) as avg_4h,
                    AVG(accuracy_24h) as avg_24h
                FROM time_impact_analysis 
                WHERE timestamp >= ?
            """, (start_date,))
            
            time_row = cursor.fetchone()
            time_impact_analysis = {
                '1h': time_row[0] or 0.0 if time_row else 0.0,
                '4h': time_row[1] or 0.0 if time_row else 0.0,
                '24h': time_row[2] or 0.0 if time_row else 0.0
            }
            
            conn.close()
            
            return NewsStatistics(
                total_news_processed=total_news or 0,
                critical_news_count=critical_news or 0,
                prediction_accuracy=avg_accuracy or 0.0,
                avg_market_impact=avg_impact or 0.0,
                sentiment_distribution={
                    'bullish': bullish or 0,
                    'bearish': bearish or 0,
                    'neutral': neutral or 0
                },
                source_reliability=source_reliability,
                cluster_performance=cluster_performance,
                time_impact_analysis=time_impact_analysis,
                false_signals_count=false_signals or 0
            )
            
        except Exception as e:
            logger.error(f"❌ Error getting full statistics: {e}")
            return NewsStatistics()
    
    def generate_daily_report(self) -> Dict:
        """Генерация ежедневного отчёта"""
        stats = self.get_full_statistics(days=1)
        
        report = {
            'date': datetime.now().date().isoformat(),
            'summary': {
                'total_news': stats.total_news_processed,
                'critical_news': stats.critical_news_count,
                'prediction_accuracy': f"{stats.prediction_accuracy:.2%}",
                'avg_market_impact': f"{stats.avg_market_impact:.3f}"
            },
            'sentiment_breakdown': stats.sentiment_distribution,
            'top_sources': dict(list(sorted(stats.source_reliability.items(), key=lambda x: x[1], reverse=True))[:5]),
            'best_performing_clusters': dict(list(sorted(stats.cluster_performance.items(), key=lambda x: x[1]['accuracy'], reverse=True))[:3]),
            'time_accuracy': {
                '1h_accuracy': f"{stats.time_impact_analysis['1h']:.2%}",
                '4h_accuracy': f"{stats.time_impact_analysis['4h']:.2%}",
                '24h_accuracy': f"{stats.time_impact_analysis['24h']:.2%}"
            },
            'issues': {
                'false_signals': stats.false_signals_count
            }
        }
        
        return report
    
    def print_daily_report(self):
        """Печать ежедневного отчёта"""
        report = self.generate_daily_report()
        
        print(f"\n📊 GHOST NEWS STATISTICS REPORT - {report['date']}")
        print("=" * 60)
        
        print(f"📈 SUMMARY:")
        print(f"   Total News: {report['summary']['total_news']}")
        print(f"   Critical News: {report['summary']['critical_news']}")
        print(f"   Prediction Accuracy: {report['summary']['prediction_accuracy']}")
        print(f"   Avg Market Impact: {report['summary']['avg_market_impact']}")
        
        print(f"\n💭 SENTIMENT BREAKDOWN:")
        for sentiment, count in report['sentiment_breakdown'].items():
            print(f"   {sentiment.title()}: {count}")
        
        print(f"\n🏆 TOP SOURCES:")
        for source, accuracy in report['top_sources'].items():
            print(f"   {source}: {accuracy:.2%}")
        
        print(f"\n⏰ TIME ACCURACY:")
        for timeframe, accuracy in report['time_accuracy'].items():
            print(f"   {timeframe}: {accuracy}")
        
        if report['issues']['false_signals'] > 0:
            print(f"\n⚠️  ISSUES:")
            print(f"   False Signals: {report['issues']['false_signals']}")

# Глобальный экземпляр
_news_stats_tracker: Optional[NewsStatisticsTracker] = None

def get_news_stats_tracker() -> NewsStatisticsTracker:
    """Получение глобального экземпляра трекера статистики"""
    global _news_stats_tracker
    if _news_stats_tracker is None:
        _news_stats_tracker = NewsStatisticsTracker()
    return _news_stats_tracker

if __name__ == "__main__":
    # Тест модуля
    tracker = NewsStatisticsTracker()
    
    # Тестовые данные
    test_news = {
        'sentiment': 0.5,
        'market_impact': 0.7,
        'is_critical': True,
        'source': 'test_source'
    }
    
    tracker.record_news_event(test_news)
    tracker.record_source_reliability('test_source', True, 0.7)
    
    # Генерируем отчёт
    tracker.print_daily_report()
