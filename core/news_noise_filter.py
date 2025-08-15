#!/usr/bin/env python3
"""
GHOST News Noise Filter
Агрессивная фильтрация шума в новостях (как просил Дарэн)
"Надо фильтровать очень сильно их, потому что очень много шума которые вообще ничего не дают"
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FilterResult:
    """Результат фильтрации новости"""
    is_important: bool
    importance_score: float  # 0.0 - 1.0
    filter_reason: str
    detected_categories: List[str]
    spam_indicators: List[str]

class NewsNoiseFilter:
    """
    Агрессивный фильтр шума для новостей
    Отсеивает 90%+ мусора, оставляет только действительно важные новости
    """
    
    def __init__(self):
        self.importance_threshold = 0.6  # Порог важности (можно настроить)
        
        # Критически важные ключевые слова (как в примере Дарэна)
        self.critical_keywords = {
            'fed_monetary': [
                'фрс', 'fed', 'федеральная резервная система', 'процентная ставка', 'ставка фрс',
                'пауэлл', 'powell', 'fomc', 'снижение ставки', 'повышение ставки', 
                'монетарная политика', 'денежная политика', 'базовая ставка'
            ],
            'regulatory_critical': [
                'sec', 'cftc', 'одобрение etf', 'etf одобрен', 'биткоин etf', 'ethereum etf',
                'регулирование крипто', 'запрет крипто', 'легализация', 'лицензия'
            ],
            'whale_activity': [
                'артур хейс', 'arthur hayes', 'майкл сэйлор', 'michael saylor', 'илон маск', 'elon musk',
                'покупает', 'продает', 'купил', 'продал', 'инвестировал', 'вложил',
                'microstrategy', 'tesla', 'grayscale', 'blackrock'
            ],
            'market_structure': [
                'листинг', 'listing', 'делистинг', 'delisting', 'халвинг', 'halving',
                'разлок', 'unlock', 'airdrop', 'токеномика', 'tokenomics',
                'мейннет', 'mainnet', 'хардфорк', 'hardfork'
            ],
            'macro_events': [
                'инфляция', 'inflation', 'cpi', 'ppi', 'безработица', 'unemployment',
                'gdp', 'ввп', 'рецессия', 'recession', 'кризис', 'crisis'
            ]
        }
        
        # Спам-индикаторы (автоматически отсеиваем)
        self.spam_indicators = {
            'promotional': [
                'реклама', 'промо', 'promo', 'скидка', 'discount', 'бонус', 'bonus',
                'акция', 'конкурс', 'розыгрыш', 'giveaway', 'airdrop бесплатно'
            ],
            'clickbait': [
                'шокирующая правда', 'невероятно', 'секрет', 'тайна', 'exclusive',
                'breaking: цена', 'срочно: курс', 'сенсация', 'разоблачение'
            ],
            'generic_price': [
                'цена растет', 'цена падает', 'курс вырос', 'курс упал',
                'технический анализ показывает', 'аналитики прогнозируют',
                'возможный рост до', 'может упасть до'
            ],
            'social_noise': [
                'мем', 'meme', 'шутка', 'joke', 'троллинг', 'trolling',
                'хайп', 'hype', 'фомо', 'fomo', 'к луне', 'to the moon'
            ],
            'low_quality': [
                'слухи', 'rumors', 'неподтвержденная информация', 'возможно',
                'по неофициальным данным', 'источники утверждают', 'инсайдеры говорят'
            ]
        }
        
        # Источники с высоким доверием
        self.trusted_sources = {
            'tier1': [  # Максимальное доверие
                'reuters', 'bloomberg', 'wall street journal', 'financial times',
                'coindesk', 'cointelegraph', 'the block', 'decrypt'
            ],
            'tier2': [  # Высокое доверие
                'cnbc', 'cnn business', 'forbes', 'yahoo finance',
                'binance news', 'coinbase blog', 'kraken blog'
            ],
            'tier3': [  # Среднее доверие
                'crypto news', 'bitcoin magazine', 'ethereum world news',
                'ambcrypto', 'u.today', 'cryptoslate'
            ]
        }
        
        # Источники-спам (автоматически отсеиваем)
        self.spam_sources = [
            'cryptopotato', 'newsbtc низкого качества', 'clickbait crypto',
            'pump news', 'moon news', 'crypto hype'
        ]
        
        logger.info("🔍 News Noise Filter initialized with aggressive filtering")
    
    def filter_news(self, news_data: Dict) -> FilterResult:
        """
        Основная функция фильтрации новости
        Возвращает результат с оценкой важности
        """
        title = news_data.get('title', '').lower()
        content = news_data.get('content', '').lower()
        source = news_data.get('source', '').lower()
        
        # Объединяем текст для анализа
        full_text = f"{title} {content}"
        
        # 1. Проверяем на спам-источники (мгновенное отсеивание)
        if self._is_spam_source(source):
            return FilterResult(
                is_important=False,
                importance_score=0.0,
                filter_reason="Spam source detected",
                detected_categories=[],
                spam_indicators=['spam_source']
            )
        
        # 2. Ищем спам-индикаторы
        spam_indicators = self._detect_spam_indicators(full_text)
        if len(spam_indicators) >= 2:  # Если 2+ спам-индикатора = отсеиваем
            return FilterResult(
                is_important=False,
                importance_score=0.1,
                filter_reason=f"Multiple spam indicators: {', '.join(spam_indicators)}",
                detected_categories=[],
                spam_indicators=spam_indicators
            )
        
        # 3. Анализируем важность по категориям
        importance_score, detected_categories = self._calculate_importance(full_text)
        
        # 4. Корректируем на основе источника
        source_multiplier = self._get_source_trust_multiplier(source)
        final_score = min(1.0, importance_score * source_multiplier)
        
        # 5. Применяем временные фильтры
        time_penalty = self._apply_time_filters(news_data)
        final_score *= time_penalty
        
        # 6. Финальное решение
        is_important = final_score >= self.importance_threshold
        
        # Логируем решение
        if is_important:
            logger.info(f"✅ IMPORTANT NEWS: {title[:50]}... (score: {final_score:.2f})")
        else:
            logger.debug(f"❌ Filtered out: {title[:30]}... (score: {final_score:.2f}, reason: {detected_categories})")
        
        return FilterResult(
            is_important=is_important,
            importance_score=final_score,
            filter_reason=f"Score {final_score:.2f}, categories: {detected_categories}" if is_important else "Below threshold",
            detected_categories=detected_categories,
            spam_indicators=spam_indicators
        )
    
    def _is_spam_source(self, source: str) -> bool:
        """Проверка на спам-источник"""
        return any(spam_source in source for spam_source in self.spam_sources)
    
    def _detect_spam_indicators(self, text: str) -> List[str]:
        """Обнаружение спам-индикаторов"""
        detected = []
        
        for category, indicators in self.spam_indicators.items():
            for indicator in indicators:
                if indicator in text:
                    detected.append(category)
                    break  # Один индикатор на категорию
        
        return detected
    
    def _calculate_importance(self, text: str) -> Tuple[float, List[str]]:
        """Расчёт важности новости по категориям"""
        importance_score = 0.0
        detected_categories = []
        
        # Веса категорий (как в примере Дарэна)
        category_weights = {
            'fed_monetary': 1.0,      # ФРС = максимальный вес
            'regulatory_critical': 0.9,  # Регулирование
            'whale_activity': 0.8,    # Активность китов
            'market_structure': 0.7,  # Структурные изменения
            'macro_events': 0.6       # Макро события
        }
        
        for category, keywords in self.critical_keywords.items():
            category_score = 0.0
            matches = 0
            
            for keyword in keywords:
                if keyword in text:
                    matches += 1
                    # Больше совпадений = выше важность
                    category_score = min(1.0, matches * 0.3)
            
            if category_score > 0:
                detected_categories.append(category)
                weighted_score = category_score * category_weights[category]
                importance_score = max(importance_score, weighted_score)  # Берём максимум
        
        return importance_score, detected_categories
    
    def _get_source_trust_multiplier(self, source: str) -> float:
        """Получение множителя доверия к источнику"""
        for tier_sources in self.trusted_sources['tier1']:
            if tier_sources in source:
                return 1.2  # Повышаем важность для tier1
        
        for tier_sources in self.trusted_sources['tier2']:
            if tier_sources in source:
                return 1.1  # Повышаем для tier2
        
        for tier_sources in self.trusted_sources['tier3']:
            if tier_sources in source:
                return 1.0  # Нейтрально для tier3
        
        return 0.8  # Снижаем для неизвестных источников
    
    def _apply_time_filters(self, news_data: Dict) -> float:
        """Применение временных фильтров"""
        published_at = news_data.get('published_at')
        if not published_at:
            return 1.0
        
        try:
            if isinstance(published_at, str):
                # Пытаемся парсить дату
                try:
                    pub_time = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                except:
                    pub_time = datetime.now()  # Fallback
            else:
                pub_time = published_at
            
            # Снижаем важность старых новостей
            age_hours = (datetime.now() - pub_time.replace(tzinfo=None)).total_seconds() / 3600
            
            if age_hours > 24:
                return 0.5  # Старые новости менее важны
            elif age_hours > 6:
                return 0.8  # Немного снижаем
            else:
                return 1.0  # Свежие новости
                
        except Exception:
            return 1.0  # В случае ошибки не применяем штраф
    
    def get_filter_statistics(self) -> Dict:
        """Получение статистики фильтрации"""
        return {
            'importance_threshold': self.importance_threshold,
            'critical_categories': len(self.critical_keywords),
            'spam_categories': len(self.spam_indicators),
            'trusted_sources': sum(len(sources) for sources in self.trusted_sources.values()),
            'spam_sources': len(self.spam_sources)
        }
    
    def update_threshold(self, new_threshold: float):
        """Обновление порога важности"""
        old_threshold = self.importance_threshold
        self.importance_threshold = max(0.0, min(1.0, new_threshold))
        logger.info(f"🎯 Importance threshold updated: {old_threshold:.2f} → {self.importance_threshold:.2f}")

# Utility функции
def filter_news_batch(news_list: List[Dict]) -> List[Dict]:
    """Фильтрация батча новостей"""
    filter_instance = NewsNoiseFilter()
    filtered_news = []
    
    for news in news_list:
        result = filter_instance.filter_news(news)
        if result.is_important:
            # Добавляем информацию о фильтрации к новости
            news['filter_result'] = {
                'importance_score': result.importance_score,
                'detected_categories': result.detected_categories,
                'filter_reason': result.filter_reason
            }
            filtered_news.append(news)
    
    logger.info(f"🔍 Filtered {len(news_list)} → {len(filtered_news)} important news ({len(filtered_news)/len(news_list)*100:.1f}% kept)")
    return filtered_news

def is_news_important(news_data: Dict) -> bool:
    """Быстрая проверка важности новости"""
    filter_instance = NewsNoiseFilter()
    result = filter_instance.filter_news(news_data)
    return result.is_important

if __name__ == "__main__":
    # Тест фильтра с примерами из сообщения Дарэна
    filter_instance = NewsNoiseFilter()
    
    # Пример 1: Важная новость (министр финансов США)
    important_news = {
        'title': 'Министр финансов США: Мы не собираемся покупать криптовалюту в наши резервы',
        'content': 'Возможно, мы начнем со снижения ставки ФРС на 25 б.п., а затем ускорим процесс',
        'source': 'reuters',
        'published_at': datetime.now().isoformat()
    }
    
    # Пример 2: Спам-новость
    spam_news = {
        'title': 'Шокирующая правда о биткоине! Цена может вырасти до 1 миллиона!',
        'content': 'Эксклюзивный анализ показывает невероятные возможности роста. Не упустите шанс!',
        'source': 'cryptopotato',
        'published_at': datetime.now().isoformat()
    }
    
    # Пример 3: Важная новость (активность кита)
    whale_news = {
        'title': 'Артур Хейс заявил, что закупает ETH и обещает больше не фиксировать прибыль',
        'content': 'Артур Хейс приобрел ETH и другие токены на 6,85 млн $',
        'source': 'coindesk',
        'published_at': datetime.now().isoformat()
    }
    
    print("🧪 TESTING NEWS NOISE FILTER")
    print("=" * 50)
    
    for i, (name, news) in enumerate([
        ("Important (Fed)", important_news),
        ("Spam", spam_news), 
        ("Whale Activity", whale_news)
    ], 1):
        result = filter_instance.filter_news(news)
        print(f"\n{i}. {name}:")
        print(f"   Important: {'✅' if result.is_important else '❌'}")
        print(f"   Score: {result.importance_score:.2f}")
        print(f"   Categories: {result.detected_categories}")
        if result.spam_indicators:
            print(f"   Spam indicators: {result.spam_indicators}")
    
    print(f"\n📊 Filter Statistics:")
    stats = filter_instance.get_filter_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")
