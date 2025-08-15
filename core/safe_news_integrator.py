#!/usr/bin/env python3
"""
GHOST Safe News Integrator
Безопасная интеграция новостного анализа с существующей системой сигналов
НЕ ИЗМЕНЯЕТ основную логику - работает как опциональные hooks
"""

import os
import sys
import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import json

# Импортируем наши новые модули
try:
    from .news_signal_enhancer import get_news_enhancer, NewsContext
    from .news_statistics_tracker import get_news_stats_tracker
    from .news_noise_filter import NewsNoiseFilter, is_news_important
except ImportError:
    # Fallback для прямого запуска
    from news_signal_enhancer import get_news_enhancer, NewsContext
    from news_statistics_tracker import get_news_stats_tracker
    from news_noise_filter import NewsNoiseFilter, is_news_important

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SafeNewsIntegrator:
    """
    Безопасный интегратор новостного анализа
    Работает как middleware - НЕ НАРУШАЕТ существующую логику
    """
    
    def __init__(self):
        self.enabled = self._check_if_enabled()
        self.hooks_registered = []
        
        # Инициализируем компоненты только если включено
        if self.enabled:
            self.news_enhancer = get_news_enhancer()
            self.stats_tracker = get_news_stats_tracker()
            self.noise_filter = NewsNoiseFilter()
            logger.info("✅ Safe News Integrator initialized and ENABLED")
        else:
            logger.info("⚪ Safe News Integrator initialized but DISABLED")
    
    def _check_if_enabled(self) -> bool:
        """Проверка включена ли новостная интеграция"""
        # Можно включить/выключить через переменную окружения
        return os.getenv('GHOST_NEWS_INTEGRATION_ENABLED', 'false').lower() == 'true'
    
    def register_signal_hook(self, hook_name: str, callback: Callable):
        """Регистрация hook'а для сигналов"""
        if self.enabled:
            self.hooks_registered.append(hook_name)
            logger.info(f"🔗 Registered news hook: {hook_name}")
    
    async def enhance_signal_safely(self, signal_data: Dict, source_config: Dict) -> Dict:
        """
        Безопасное обогащение сигнала новостным контекстом
        Возвращает исходный сигнал + дополнительную информацию
        НЕ ИЗМЕНЯЕТ основные поля сигнала
        """
        if not self.enabled:
            return signal_data
        
        try:
            # Создаём копию чтобы не изменить оригинал
            enhanced_signal = signal_data.copy()
            
            # Добавляем новостной контекст
            news_context = await self.news_enhancer.enhance_signal_context(signal_data, source_config)
            
            # Добавляем дополнительные поля (НЕ ИЗМЕНЯЕМ основные!)
            enhanced_signal['news_enhancement'] = {
                'enabled': True,
                'context': news_context.__dict__,
                'summary': self.news_enhancer.get_enhancement_summary(news_context),
                'confidence_suggestion': news_context.confidence_modifier,
                'entry_timing_suggestion': news_context.entry_modifier,
                'risk_suggestion': news_context.risk_modifier,
                'enhanced_at': datetime.now().isoformat()
            }
            
            # Логируем для статистики (не влияет на торговлю)
            self._log_enhancement_stats(signal_data, news_context)
            
            return enhanced_signal
            
        except Exception as e:
            logger.error(f"❌ Error in safe news enhancement: {e}")
            # В случае ошибки возвращаем исходный сигнал
            return signal_data
    
    def _log_enhancement_stats(self, signal_data: Dict, news_context: NewsContext):
        """Логирование статистики обогащения"""
        if not self.enabled:
            return
        
        try:
            # Записываем в статистику
            if news_context.has_recent_news:
                news_event = {
                    'symbol': signal_data.get('symbol', 'UNKNOWN'),
                    'sentiment': news_context.sentiment_score,
                    'market_impact': news_context.market_impact,
                    'urgency': news_context.urgency_score,
                    'is_critical': news_context.urgency_score > 0.7
                }
                self.stats_tracker.record_news_event(news_event)
                
        except Exception as e:
            logger.error(f"❌ Error logging enhancement stats: {e}")
    
    def filter_news_safely(self, news_data: Dict) -> Optional[Dict]:
        """
        Безопасная фильтрация новостей
        Возвращает новость только если она важна
        """
        if not self.enabled:
            return news_data  # Пропускаем всё если отключено
        
        try:
            filter_result = self.noise_filter.filter_news(news_data)
            
            if filter_result.is_important:
                # Добавляем информацию о фильтрации
                filtered_news = news_data.copy()
                filtered_news['filter_info'] = {
                    'importance_score': filter_result.importance_score,
                    'detected_categories': filter_result.detected_categories,
                    'filter_reason': filter_result.filter_reason,
                    'filtered_at': datetime.now().isoformat()
                }
                return filtered_news
            else:
                # Логируем отфильтрованную новость
                logger.debug(f"🔍 News filtered out: {news_data.get('title', '')[:50]}... (reason: {filter_result.filter_reason})")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error in safe news filtering: {e}")
            # В случае ошибки пропускаем новость
            return news_data
    
    def get_daily_news_report(self) -> Dict:
        """Получение ежедневного отчёта по новостям"""
        if not self.enabled:
            return {'enabled': False, 'message': 'News integration disabled'}
        
        try:
            return self.stats_tracker.generate_daily_report()
        except Exception as e:
            logger.error(f"❌ Error generating daily news report: {e}")
            return {'error': str(e)}
    
    def print_news_statistics(self):
        """Печать статистики новостей"""
        if not self.enabled:
            print("📰 News integration is DISABLED")
            return
        
        try:
            self.stats_tracker.print_daily_report()
        except Exception as e:
            logger.error(f"❌ Error printing news statistics: {e}")
    
    def update_news_settings(self, settings: Dict):
        """Обновление настроек новостной интеграции"""
        if not self.enabled:
            logger.warning("⚠️ Cannot update settings - news integration disabled")
            return
        
        try:
            if 'importance_threshold' in settings:
                self.noise_filter.update_threshold(settings['importance_threshold'])
                logger.info(f"🎯 Updated importance threshold: {settings['importance_threshold']}")
            
            if 'enhancement_enabled' in settings:
                self.news_enhancer.enabled = settings['enhancement_enabled']
                logger.info(f"🔧 Updated enhancement enabled: {settings['enhancement_enabled']}")
                
        except Exception as e:
            logger.error(f"❌ Error updating news settings: {e}")
    
    def get_integration_status(self) -> Dict:
        """Получение статуса интеграции"""
        return {
            'enabled': self.enabled,
            'components': {
                'news_enhancer': self.enabled and hasattr(self, 'news_enhancer'),
                'stats_tracker': self.enabled and hasattr(self, 'stats_tracker'),
                'noise_filter': self.enabled and hasattr(self, 'noise_filter')
            },
            'hooks_registered': len(self.hooks_registered),
            'environment_var': os.getenv('GHOST_NEWS_INTEGRATION_ENABLED', 'false'),
            'timestamp': datetime.now().isoformat()
        }

# Глобальный экземпляр
_safe_integrator: Optional[SafeNewsIntegrator] = None

def get_safe_news_integrator() -> SafeNewsIntegrator:
    """Получение глобального экземпляра безопасного интегратора"""
    global _safe_integrator
    if _safe_integrator is None:
        _safe_integrator = SafeNewsIntegrator()
    return _safe_integrator

# Utility функции для простой интеграции
async def safe_enhance_signal(signal_data: Dict, source_config: Dict = None) -> Dict:
    """Утилита для безопасного обогащения сигнала"""
    integrator = get_safe_news_integrator()
    return await integrator.enhance_signal_safely(signal_data, source_config or {})

def safe_filter_news(news_data: Dict) -> Optional[Dict]:
    """Утилита для безопасной фильтрации новостей"""
    integrator = get_safe_news_integrator()
    return integrator.filter_news_safely(news_data)

def get_news_integration_status() -> Dict:
    """Утилита для получения статуса интеграции"""
    integrator = get_safe_news_integrator()
    return integrator.get_integration_status()

# Декоратор для безопасного добавления новостного контекста
def with_news_context(func):
    """
    Декоратор для автоматического добавления новостного контекста
    Использование:
    
    @with_news_context
    def process_signal(signal_data, source_config):
        # signal_data теперь может содержать news_enhancement
        return processed_signal
    """
    async def wrapper(*args, **kwargs):
        # Ищем signal_data в аргументах
        signal_data = None
        source_config = None
        
        if len(args) >= 1 and isinstance(args[0], dict):
            signal_data = args[0]
        if len(args) >= 2 and isinstance(args[1], dict):
            source_config = args[1]
        
        # Обогащаем если нашли signal_data
        if signal_data:
            enhanced_signal = await safe_enhance_signal(signal_data, source_config)
            # Заменяем первый аргумент на обогащённый сигнал
            args = (enhanced_signal,) + args[1:]
        
        # Вызываем оригинальную функцию
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    
    return wrapper

if __name__ == "__main__":
    # Тест интегратора
    async def test_integrator():
        print("🧪 TESTING SAFE NEWS INTEGRATOR")
        print("=" * 50)
        
        # Включаем интеграцию для теста
        os.environ['GHOST_NEWS_INTEGRATION_ENABLED'] = 'true'
        
        integrator = SafeNewsIntegrator()
        
        # Тестовый сигнал
        test_signal = {
            'symbol': 'BTCUSDT',
            'side': 'LONG',
            'entry': 45000,
            'targets': [46000, 47000],
            'stop_loss': 44000,
            'confidence': 0.8
        }
        
        # Тестируем обогащение
        enhanced = await integrator.enhance_signal_safely(test_signal, {})
        
        print(f"Original signal keys: {list(test_signal.keys())}")
        print(f"Enhanced signal keys: {list(enhanced.keys())}")
        
        if 'news_enhancement' in enhanced:
            print(f"News enhancement added: ✅")
            print(f"Enhancement summary: {enhanced['news_enhancement']['summary']}")
        else:
            print(f"News enhancement: ❌")
        
        # Тестируем фильтрацию
        test_news = {
            'title': 'ФРС снижает ставку на 25 базисных пунктов',
            'content': 'Федеральная резервная система объявила о снижении процентной ставки',
            'source': 'reuters'
        }
        
        filtered = integrator.filter_news_safely(test_news)
        print(f"News filtering result: {'✅ Important' if filtered else '❌ Filtered out'}")
        
        # Статус интеграции
        status = integrator.get_integration_status()
        print(f"Integration status: {status}")
    
    # Запускаем тест
    asyncio.run(test_integrator())
