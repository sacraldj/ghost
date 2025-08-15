#!/usr/bin/env python3
"""
GHOST News Signal Enhancer
Опциональный модуль для обогащения сигналов новостным контекстом
НЕ ИЗМЕНЯЕТ основную логику - только добавляет дополнительную информацию
"""

import os
import sys
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import json

# Добавляем путь к корневой директории
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импортируем существующие модули новостей (если доступны)
try:
    from ai_news_analyzer import analyze_news_with_ai, filter_and_cluster_news
    from context_enricher import enrich_news_context, get_market_data
    from reaction_predictor import predict_news_reaction
    NEWS_MODULES_AVAILABLE = True
except ImportError as e:
    logging.warning(f"News modules not available: {e}")
    NEWS_MODULES_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class NewsContext:
    """Новостной контекст для сигнала"""
    has_recent_news: bool = False
    news_count: int = 0
    sentiment_score: float = 0.0  # -1 to 1
    urgency_score: float = 0.0    # 0 to 1
    market_impact: float = 0.0    # 0 to 1
    key_events: List[str] = None
    confidence_modifier: float = 1.0  # Множитель для confidence
    entry_modifier: float = 1.0      # Множитель для entry timing
    risk_modifier: float = 1.0       # Множитель для risk management

    def __post_init__(self):
        if self.key_events is None:
            self.key_events = []

class NewsSignalEnhancer:
    """
    Опциональный обогатитель сигналов новостным контекстом
    Не изменяет основную логику, только добавляет дополнительную информацию
    """
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.news_available = NEWS_MODULES_AVAILABLE
        
        if not self.news_available:
            logger.warning("⚠️ News modules not available - enhancer will work in minimal mode")
        
        logger.info(f"📰 News Signal Enhancer initialized (enabled: {enabled}, news_modules: {self.news_available})")
    
    async def enhance_signal_context(self, signal_data: Dict, source_config: Dict) -> NewsContext:
        """
        Обогащает сигнал новостным контекстом
        НЕ ИЗМЕНЯЕТ исходный сигнал - только возвращает дополнительную информацию
        """
        if not self.enabled:
            return NewsContext()
        
        try:
            symbol = signal_data.get('symbol', 'BTCUSDT')
            logger.info(f"📰 Enhancing signal context for {symbol}")
            
            # Получаем новостной контекст
            news_context = await self._get_news_context(symbol)
            
            # Анализируем влияние на торговлю
            trading_impact = self._analyze_trading_impact(news_context, signal_data)
            
            # Создаём итоговый контекст
            context = NewsContext(
                has_recent_news=news_context.get('has_news', False),
                news_count=news_context.get('count', 0),
                sentiment_score=news_context.get('sentiment', 0.0),
                urgency_score=news_context.get('urgency', 0.0),
                market_impact=news_context.get('market_impact', 0.0),
                key_events=news_context.get('key_events', []),
                confidence_modifier=trading_impact.get('confidence_modifier', 1.0),
                entry_modifier=trading_impact.get('entry_modifier', 1.0),
                risk_modifier=trading_impact.get('risk_modifier', 1.0)
            )
            
            logger.info(f"✅ News context enhanced: sentiment={context.sentiment_score:.2f}, impact={context.market_impact:.2f}")
            return context
            
        except Exception as e:
            logger.error(f"❌ Error enhancing signal context: {e}")
            return NewsContext()
    
    async def _get_news_context(self, symbol: str) -> Dict:
        """Получение новостного контекста"""
        if not self.news_available:
            return {'has_news': False, 'count': 0}
        
        try:
            # Ищем новости за последние 4 часа
            recent_news = await self._fetch_recent_news(symbol, hours=4)
            
            if not recent_news:
                return {'has_news': False, 'count': 0}
            
            # Анализируем новости
            sentiment_scores = []
            urgency_scores = []
            impact_scores = []
            key_events = []
            
            for news in recent_news:
                # Базовый анализ если AI недоступен
                analysis = self._basic_news_analysis(news)
                
                sentiment_scores.append(analysis['sentiment'])
                urgency_scores.append(analysis['urgency'])
                impact_scores.append(analysis['impact'])
                
                if analysis['is_important']:
                    key_events.append(news.get('title', '')[:100])
            
            return {
                'has_news': True,
                'count': len(recent_news),
                'sentiment': sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0,
                'urgency': max(urgency_scores) if urgency_scores else 0.0,
                'market_impact': max(impact_scores) if impact_scores else 0.0,
                'key_events': key_events[:3]  # Топ 3 события
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting news context: {e}")
            return {'has_news': False, 'count': 0}
    
    async def _fetch_recent_news(self, symbol: str, hours: int = 4) -> List[Dict]:
        """Получение недавних новостей (заглушка)"""
        # Здесь можно подключить реальный источник новостей
        # Пока возвращаем пустой список
        return []
    
    def _basic_news_analysis(self, news: Dict) -> Dict:
        """Базовый анализ новости без AI"""
        title = news.get('title', '').lower()
        content = news.get('content', '').lower()
        text = f"{title} {content}"
        
        # Простые правила для определения sentiment
        bullish_keywords = ['рост', 'покупка', 'инвестиции', 'одобрение', 'партнерство', 'листинг']
        bearish_keywords = ['падение', 'продажа', 'запрет', 'регулирование', 'взлом', 'скам']
        urgent_keywords = ['срочно', 'breaking', 'сейчас', 'немедленно', 'критично']
        
        # Подсчёт sentiment
        bullish_count = sum(1 for word in bullish_keywords if word in text)
        bearish_count = sum(1 for word in bearish_keywords if word in text)
        
        if bullish_count > bearish_count:
            sentiment = 0.3 + (bullish_count * 0.2)
        elif bearish_count > bullish_count:
            sentiment = -0.3 - (bearish_count * 0.2)
        else:
            sentiment = 0.0
        
        # Ограничиваем диапазон
        sentiment = max(-1.0, min(1.0, sentiment))
        
        # Urgency
        urgency = min(1.0, sum(1 for word in urgent_keywords if word in text) * 0.3)
        
        # Impact (базовый)
        impact = min(1.0, (abs(sentiment) + urgency) / 2)
        
        return {
            'sentiment': sentiment,
            'urgency': urgency,
            'impact': impact,
            'is_important': impact > 0.5
        }
    
    def _analyze_trading_impact(self, news_context: Dict, signal_data: Dict) -> Dict:
        """Анализ влияния новостей на торговлю"""
        if not news_context.get('has_news'):
            return {'confidence_modifier': 1.0, 'entry_modifier': 1.0, 'risk_modifier': 1.0}
        
        sentiment = news_context.get('sentiment', 0.0)
        urgency = news_context.get('urgency', 0.0)
        impact = news_context.get('market_impact', 0.0)
        signal_side = signal_data.get('side', 'LONG')
        
        # Модификатор confidence
        confidence_modifier = 1.0
        if signal_side == 'LONG' and sentiment > 0.3:
            confidence_modifier = 1.0 + (sentiment * 0.2)  # Увеличиваем confidence для LONG при позитивных новостях
        elif signal_side == 'SHORT' and sentiment < -0.3:
            confidence_modifier = 1.0 + (abs(sentiment) * 0.2)  # Увеличиваем confidence для SHORT при негативных новостях
        elif (signal_side == 'LONG' and sentiment < -0.3) or (signal_side == 'SHORT' and sentiment > 0.3):
            confidence_modifier = 1.0 - (abs(sentiment) * 0.1)  # Снижаем confidence при противоречащих новостях
        
        # Модификатор entry timing
        entry_modifier = 1.0
        if urgency > 0.7:
            entry_modifier = 0.7  # Ускоряем вход при срочных новостях
        elif impact > 0.8:
            entry_modifier = 0.8  # Ускоряем вход при высоком влиянии
        
        # Модификатор risk
        risk_modifier = 1.0
        if impact > 0.7:
            risk_modifier = 1.2  # Увеличиваем осторожность при высоком влиянии новостей
        
        return {
            'confidence_modifier': max(0.5, min(1.5, confidence_modifier)),
            'entry_modifier': max(0.5, min(1.5, entry_modifier)),
            'risk_modifier': max(0.8, min(1.5, risk_modifier))
        }
    
    def get_enhancement_summary(self, context: NewsContext) -> str:
        """Получение краткого описания обогащения"""
        if not context.has_recent_news:
            return "📰 Новостей нет"
        
        sentiment_emoji = "📈" if context.sentiment_score > 0.1 else "📉" if context.sentiment_score < -0.1 else "➡️"
        urgency_emoji = "🚨" if context.urgency_score > 0.7 else "⏰" if context.urgency_score > 0.3 else "🕐"
        
        return f"{sentiment_emoji} Новости: {context.news_count} | Sentiment: {context.sentiment_score:.2f} | {urgency_emoji} Urgency: {context.urgency_score:.2f}"

# Глобальный экземпляр (опциональный)
_news_enhancer: Optional[NewsSignalEnhancer] = None

def get_news_enhancer() -> NewsSignalEnhancer:
    """Получение глобального экземпляра news enhancer"""
    global _news_enhancer
    if _news_enhancer is None:
        # Проверяем настройки из переменных окружения
        enabled = os.getenv('NEWS_ENHANCEMENT_ENABLED', 'true').lower() == 'true'
        _news_enhancer = NewsSignalEnhancer(enabled=enabled)
    return _news_enhancer

# Utility функции для интеграции
async def enhance_signal_with_news(signal_data: Dict, source_config: Dict) -> Dict:
    """
    Утилита для обогащения сигнала новостным контекстом
    Возвращает исходный сигнал + news_context
    """
    enhancer = get_news_enhancer()
    news_context = await enhancer.enhance_signal_context(signal_data, source_config)
    
    # НЕ ИЗМЕНЯЕМ исходный сигнал, только добавляем новый ключ
    enhanced_signal = signal_data.copy()
    enhanced_signal['news_context'] = asdict(news_context)
    enhanced_signal['news_enhancement_summary'] = enhancer.get_enhancement_summary(news_context)
    
    return enhanced_signal

if __name__ == "__main__":
    # Тест модуля
    async def test():
        enhancer = NewsSignalEnhancer(enabled=True)
        
        test_signal = {
            'symbol': 'BTCUSDT',
            'side': 'LONG',
            'entry': 45000,
            'targets': [46000, 47000],
            'stop_loss': 44000
        }
        
        context = await enhancer.enhance_signal_context(test_signal, {})
        print(f"News context: {context}")
        print(f"Summary: {enhancer.get_enhancement_summary(context)}")
    
    asyncio.run(test())
