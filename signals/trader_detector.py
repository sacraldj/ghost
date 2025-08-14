"""
GHOST Trader Detector
Автоматическое определение трейдеров по стилю сигналов
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class TraderStyle(Enum):
    """Стили трейдеров"""
    WHALES_STANDARD = "whales_standard"
    WHALES_PRECISION = "whales_precision" 
    SPOT_TRADER = "spot_trader"
    UNKNOWN = "unknown"

@dataclass
class DetectionPattern:
    """Паттерн для определения трейдера"""
    keywords: List[str]
    required_patterns: List[str]
    optional_patterns: List[str]
    exclusion_patterns: List[str]
    min_confidence: float

class TraderDetector:
    """Класс для автоматического определения трейдеров"""
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
        logger.info("Trader Detector initialized with patterns for different trading styles")
    
    def _initialize_patterns(self) -> Dict[TraderStyle, DetectionPattern]:
        """Инициализация паттернов для каждого стиля трейдера"""
        
        return {
            TraderStyle.WHALES_STANDARD: DetectionPattern(
                keywords=[
                    "longing", "here", "chart looks bullish", "worth buying",
                    "short-mid term", "quick profits", "resistance zone",
                    "cup and handle", "broke out"
                ],
                required_patterns=[
                    r"Longing #[A-Z]+ Here",
                    r"Long \([0-9x\s\-]+\)",
                    r"Entry: \$[0-9\.]+ - \$[0-9\.]+",
                    r"Targets: .*\$[0-9\.,\s]+",
                    r"Stoploss: \$[0-9\.]+"
                ],
                optional_patterns=[
                    r"Reason: Chart looks bullish.*",
                    r"Worth buying for.*",
                    r"broke out.*pattern",
                    r"resistance.*zone"
                ],
                exclusion_patterns=[
                    r"in spot",
                    r"You can long",
                    r"demanding zone"
                ],
                min_confidence=0.7
            ),
            
            TraderStyle.SPOT_TRADER: DetectionPattern(
                keywords=[
                    "buying", "in spot", "you can long", "leverage", 
                    "demanding zone", "volume growing", "short term"
                ],
                required_patterns=[
                    r"Buying #[A-Z]+ Here in spot",
                    r"You can long in [0-9x]+ leverage",
                    r"Entry: [0-9\.]+-[0-9\.]+\$"
                ],
                optional_patterns=[
                    r"demanding zone",
                    r"Volume growing",
                    r"Worth buy for short term"
                ],
                exclusion_patterns=[
                    r"Longing #[A-Z]+ Here",
                    r"Long \([0-9x\s\-]+\)"
                ],
                min_confidence=0.8
            ),
            
            TraderStyle.WHALES_PRECISION: DetectionPattern(
                keywords=[
                    "longing", "here", "precision", "systematic", "detailed"
                ],
                required_patterns=[
                    r"Longing #[A-Z]+ Here",
                    r"Long \([0-9x\s\-]+\)",
                    r"Entry: \$[0-9\.]+ - \$[0-9\.]+",
                    r"Targets: .*\$[0-9]+\.[0-9]{4}.*"  # 4-decimal precision
                ],
                optional_patterns=[
                    r"Stoploss: \$[0-9]+\.[0-9]{4}",  # 4-decimal SL
                    r"Chart looks bullish"
                ],
                exclusion_patterns=[
                    r"in spot",
                    r"demanding zone"
                ],
                min_confidence=0.6
            )
        }
    
    def detect_trader(self, text: str) -> Tuple[TraderStyle, float, Dict]:
        """
        Определяет трейдера по тексту сигнала
        
        Returns:
            Tuple[TraderStyle, confidence, details]
        """
        text_clean = self._clean_text(text)
        
        best_match = TraderStyle.UNKNOWN
        best_confidence = 0.0
        best_details = {}
        
        # Проверяем каждый стиль
        for style, pattern in self.patterns.items():
            confidence, details = self._calculate_confidence(text_clean, pattern)
            
            if confidence > best_confidence and confidence >= pattern.min_confidence:
                best_match = style
                best_confidence = confidence
                best_details = details
        
        logger.debug(f"Detected trader: {best_match.value} (confidence: {best_confidence:.2f})")
        
        return best_match, best_confidence, best_details
    
    def _clean_text(self, text: str) -> str:
        """Очистка и нормализация текста"""
        # Убираем лишние пробелы и переносы
        text = re.sub(r'\s+', ' ', text.strip())
        return text
    
    def _calculate_confidence(self, text: str, pattern: DetectionPattern) -> Tuple[float, Dict]:
        """Расчет уверенности для конкретного паттерна"""
        text_lower = text.lower()
        details = {
            'matched_keywords': [],
            'matched_required': [],
            'matched_optional': [],
            'exclusions_found': []
        }
        
        # Проверяем ключевые слова
        keyword_score = 0
        for keyword in pattern.keywords:
            if keyword.lower() in text_lower:
                details['matched_keywords'].append(keyword)
                keyword_score += 1
        
        keyword_confidence = min(1.0, keyword_score / len(pattern.keywords))
        
        # Проверяем обязательные паттерны
        required_score = 0
        for req_pattern in pattern.required_patterns:
            if re.search(req_pattern, text, re.IGNORECASE):
                details['matched_required'].append(req_pattern)
                required_score += 1
        
        required_confidence = required_score / len(pattern.required_patterns) if pattern.required_patterns else 1.0
        
        # Проверяем опциональные паттерны
        optional_score = 0
        for opt_pattern in pattern.optional_patterns:
            if re.search(opt_pattern, text, re.IGNORECASE):
                details['matched_optional'].append(opt_pattern)
                optional_score += 1
        
        optional_confidence = optional_score / len(pattern.optional_patterns) if pattern.optional_patterns else 0.0
        
        # Проверяем исключающие паттерны
        exclusion_penalty = 0
        for excl_pattern in pattern.exclusion_patterns:
            if re.search(excl_pattern, text, re.IGNORECASE):
                details['exclusions_found'].append(excl_pattern)
                exclusion_penalty += 0.3  # Штраф за каждое исключение
        
        # Итоговая уверенность
        base_confidence = (
            required_confidence * 0.6 +  # 60% - обязательные паттерны
            keyword_confidence * 0.3 +   # 30% - ключевые слова
            optional_confidence * 0.1    # 10% - опциональные паттерны
        )
        
        final_confidence = max(0.0, base_confidence - exclusion_penalty)
        
        details['scores'] = {
            'keywords': keyword_confidence,
            'required': required_confidence,
            'optional': optional_confidence,
            'exclusion_penalty': exclusion_penalty,
            'final': final_confidence
        }
        
        return final_confidence, details
    
    def get_trader_name(self, style: TraderStyle) -> str:
        """Получить человеко-читаемое имя трейдера"""
        names = {
            TraderStyle.WHALES_STANDARD: "Whales Standard",
            TraderStyle.WHALES_PRECISION: "Whales Precision",
            TraderStyle.SPOT_TRADER: "Spot Trader",
            TraderStyle.UNKNOWN: "Unknown Trader"
        }
        return names.get(style, "Unknown")
    
    def get_trader_id(self, style: TraderStyle, channel_source: str = "whalesguide") -> str:
        """Генерирует trader_id для базы данных"""
        if style == TraderStyle.UNKNOWN:
            return f"{channel_source}_unknown"
        
        style_mapping = {
            TraderStyle.WHALES_STANDARD: "whales_standard",
            TraderStyle.WHALES_PRECISION: "whales_precision", 
            TraderStyle.SPOT_TRADER: "spot_trader"
        }
        
        return f"{channel_source}_{style_mapping.get(style, 'unknown')}"

# Функция для тестирования детектора
def test_trader_detector():
    """Тестирование системы определения трейдеров"""
    print("🧪 ТЕСТИРОВАНИЕ TRADER DETECTOR")
    print("=" * 60)
    
    detector = TraderDetector()
    
    # Тестовые сигналы от разных трейдеров
    test_signals = [
        {
            "name": "Whales Standard (YGG)",
            "text": """Longing #YGG Here

Long (5x - 10x)

Entry: $0.1800 - $0.1760

Reason: Chart looks bullish for it. Worth buying for short-mid term quick profits too. Already broke out of the cup and handle pattern and resistance zone also.

Targets: $0.1840, $0.1880, $0.1920, $0.1960, $0.2080, $0.2200

Stoploss: $0.1720""",
            "expected": TraderStyle.WHALES_STANDARD
        },
        
        {
            "name": "Spot Trader (TAC)",
            "text": """Buying #TAC Here in spot

You can long in 4x leverage, too.

Entry: 0.01380-0.01330$

Reason: Currently in demanding zone.Volume growing up.Chart looks bullish for it. Worth buy for short term quick profits.

Targets: 0.01520$, 0.01740$

Stoploss: 0.01149$""",
            "expected": TraderStyle.SPOT_TRADER
        },
        
        {
            "name": "Whales Precision (SUI)",
            "text": """Longing #SUI Here

Long (5x - 10x)

Entry: $3.89 - $3.70

Reason: Chart looks bullish for it. Worth buying for short-mid term quick profits too.

Targets: $4.0500, $4.2000, $4.3000, $4.4000, $4.6000, $4.8000, $5.0690

Stoploss: $3.4997""",
            "expected": TraderStyle.WHALES_PRECISION
        }
    ]
    
    # Тестируем каждый сигнал
    for i, signal in enumerate(test_signals, 1):
        print(f"\n{i}️⃣ ТЕСТ: {signal['name']}")
        print("-" * 50)
        
        detected_style, confidence, details = detector.detect_trader(signal['text'])
        trader_name = detector.get_trader_name(detected_style)
        trader_id = detector.get_trader_id(detected_style)
        
        expected = signal['expected']
        is_correct = detected_style == expected
        
        print(f"📊 Результат:")
        print(f"   • Detected: {trader_name} ({detected_style.value})")
        print(f"   • Expected: {detector.get_trader_name(expected)} ({expected.value})")
        print(f"   • Confidence: {confidence:.2f}")
        print(f"   • Trader ID: {trader_id}")
        print(f"   • Correct: {'✅' if is_correct else '❌'}")
        
        if confidence > 0:
            print(f"   • Matched keywords: {len(details['matched_keywords'])}")
            print(f"   • Required patterns: {len(details['matched_required'])}")
            print(f"   • Optional patterns: {len(details['matched_optional'])}")
            if details['exclusions_found']:
                print(f"   • Exclusions found: {details['exclusions_found']}")
    
    print(f"\n🎯 СИСТЕМА ДЕТЕКЦИИ ГОТОВА К РАБОТЕ!")

if __name__ == "__main__":
    test_trader_detector()
