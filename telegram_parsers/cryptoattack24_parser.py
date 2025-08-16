"""
Супер точный парсер для канала КриптоАтака 24 (t.me/cryptoattack24)
Специализированный парсер для анализа сообщений о криптовалютных движениях
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CryptoAttack24Signal:
    """Структура сигнала от CryptoAttack24"""
    symbol: str
    action: str  # "pump", "growth", "breakout", "consolidation"
    confidence: float
    context: str  # Контекст сообщения
    price_movement: Optional[str] = None  # "+57%", "рост", etc.
    exchange: Optional[str] = None  # "Binance", "CEX", etc.
    timeframe: Optional[str] = None
    sector: Optional[str] = None  # "авиакомпании", "туризм", etc.
    raw_text: str = ""
    timestamp: Optional[datetime] = None

class CryptoAttack24Parser:
    """Супер точный парсер для КриптоАтака 24"""
    
    def __init__(self):
        self.name = "CryptoAttack24 Super Parser"
        self.version = "1.0.0"
        self.min_confidence = 0.6
        
        # Паттерны для извлечения информации
        self.patterns = {
            # Символы криптовалют
            'symbol': [
                r'#([A-Z]{2,10})\s+запампили',
                r'([A-Z]{2,10})\s+запампили',
                r'([A-Z]{2,10})\s+закрепился',
                r'([A-Z]{2,10})\s+в\s+топе',
                r'#([A-Z]{2,10})',
                r'\b([A-Z]{2,10})\b(?=\s+(?:запампили|закрепился|в топе|рост))',
            ],
            
            # Движения цены
            'price_movement': [
                r'запампили на \+(\d+)%',
                r'рост на (\d+)%',
                r'выросли на (\d+)%',
                r'\+(\d+)%',
                r'на (\d+)% вверх',
            ],
            
            # Биржи
            'exchange': [
                r'на (Binance)',
                r'на (CEX)',
                r'на всех (CEX)',
                r'(Binance)',
                r'по (спотовым покупкам)',
                r'в топе (лидеров)',
            ],
            
            # Временные метки
            'time': [
                r'в (\d{2}:\d{2})',
                r'со вчерашнего вечера',
                r'с утра',
                r'в течение дня',
            ],
            
            # Сектора и контекст
            'sector': [
                r'(авиакомпании|туристические агентства)',
                r'(Emirates|Air Arabia|Travala|Alternative Airlines)',
                r'(бронирований|криптовалют|оплаты)',
            ],
            
            # Действия
            'action': [
                r'(запампили)',
                r'(закрепился)',
                r'(занял первое место)',
                r'(поддерживают использование)',
                r'(обновили категорию)',
            ]
        }
        
        # Ключевые слова для определения типа сигнала
        self.signal_keywords = {
            'pump': ['запампили', 'рост', 'выросли', 'вверх'],
            'consolidation': ['закрепился', 'в топе', 'первое место'],
            'adoption': ['поддерживают', 'использование', 'оплаты', 'бронирований'],
            'news': ['обновили', 'категорию', 'авиакомпании', 'агентства'],
        }
        
        # Исключающие фразы (шум)
        self.noise_patterns = [
            r'примечательно, что .* не покидает',
            r'до сих пор',
            r'тестовое сообщение',
            r'демо',
        ]

    def parse_message(self, message_text: str, timestamp: Optional[datetime] = None) -> Optional[CryptoAttack24Signal]:
        """
        Основной метод парсинга сообщения
        """
        try:
            if not message_text or len(message_text.strip()) < 10:
                return None
            
            # Проверяем на шум
            if self._is_noise(message_text):
                logger.debug(f"Message filtered as noise: {message_text[:50]}...")
                return None
            
            # Извлекаем компоненты
            symbol = self._extract_symbol(message_text)
            action = self._extract_action(message_text)
            price_movement = self._extract_price_movement(message_text)
            exchange = self._extract_exchange(message_text)
            sector = self._extract_sector(message_text)
            
            # Определяем тип сигнала и уверенность
            signal_type, confidence = self._classify_signal(message_text, symbol, action)
            
            if confidence < self.min_confidence:
                logger.debug(f"Low confidence signal: {confidence:.2f}")
                return None
            
            # Создаем сигнал
            signal = CryptoAttack24Signal(
                symbol=symbol or "UNKNOWN",
                action=signal_type,
                confidence=confidence,
                context=self._extract_context(message_text),
                price_movement=price_movement,
                exchange=exchange,
                sector=sector,
                raw_text=message_text,
                timestamp=timestamp or datetime.now()
            )
            
            logger.info(f"Parsed signal: {signal.symbol} {signal.action} (confidence: {confidence:.2f})")
            return signal
            
        except Exception as e:
            logger.error(f"Error parsing message: {e}")
            return None

    def _extract_symbol(self, text: str) -> Optional[str]:
        """Извлечение символа криптовалюты"""
        for pattern in self.patterns['symbol']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                symbol = match.group(1).upper()
                # Проверяем, что это реальный символ
                if 2 <= len(symbol) <= 10 and symbol.isalpha():
                    return symbol
        return None

    def _extract_action(self, text: str) -> Optional[str]:
        """Извлечение действия"""
        for pattern in self.patterns['action']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).lower()
        return None

    def _extract_price_movement(self, text: str) -> Optional[str]:
        """Извлечение движения цены"""
        for pattern in self.patterns['price_movement']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None

    def _extract_exchange(self, text: str) -> Optional[str]:
        """Извлечение биржи"""
        for pattern in self.patterns['exchange']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1) if match.groups() else match.group(0)
        return None

    def _extract_sector(self, text: str) -> Optional[str]:
        """Извлечение сектора"""
        for pattern in self.patterns['sector']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1) if match.groups() else match.group(0)
        return None

    def _classify_signal(self, text: str, symbol: Optional[str], action: Optional[str]) -> Tuple[str, float]:
        """Классификация типа сигнала и определение уверенности"""
        text_lower = text.lower()
        confidence = 0.0
        signal_type = "news"
        
        # Проверяем каждый тип сигнала
        for sig_type, keywords in self.signal_keywords.items():
            type_confidence = 0.0
            for keyword in keywords:
                if keyword in text_lower:
                    type_confidence += 0.2
            
            if type_confidence > confidence:
                confidence = type_confidence
                signal_type = sig_type
        
        # Бонусы за наличие символа и действия
        if symbol:
            confidence += 0.3
        if action:
            confidence += 0.2
        
        # Бонус за процентное движение
        if re.search(r'\+?\d+%', text):
            confidence += 0.3
        
        # Бонус за упоминание биржи
        if any(exchange in text_lower for exchange in ['binance', 'cex']):
            confidence += 0.2
        
        # Максимальная уверенность 1.0
        confidence = min(confidence, 1.0)
        
        return signal_type, confidence

    def _extract_context(self, text: str) -> str:
        """Извлечение контекста сообщения"""
        # Берем первые 100 символов как контекст
        return text[:100].strip()

    def _is_noise(self, text: str) -> bool:
        """Проверка на шумовые сообщения"""
        text_lower = text.lower()
        
        for pattern in self.noise_patterns:
            if re.search(pattern, text_lower):
                return True
        
        # Дополнительные проверки на шум
        if len(text.strip()) < 20:
            return True
            
        if text.count('http') > 2:  # Слишком много ссылок
            return True
            
        return False

    def get_parser_stats(self) -> Dict:
        """Статистика парсера"""
        return {
            'name': self.name,
            'version': self.version,
            'min_confidence': self.min_confidence,
            'supported_signals': list(self.signal_keywords.keys()),
            'pattern_count': sum(len(patterns) for patterns in self.patterns.values())
        }

# Функция для тестирования парсера
def test_cryptoattack24_parser():
    """Тестирование парсера с примерами сообщений"""
    parser = CryptoAttack24Parser()
    
    test_messages = [
        "🚀🔥 #ALPINE запампили на +57% со вчерашнего вечера. В 18:30 по мск он закрепился в топе по спотовым покупкам на Binance, а затем на всех CEX. В 19:35 также закрепился в топе по фьючерсным покупкам на всех CEX, в 20:06 занял первое место в топе лидеров по росту OI Binance.",
        
        "🏢✈️ Авиакомпании и туристические агентства, включая Emirates, Air Arabia, Travala и Alternative Airlines, теперь поддерживают использование криптовалют для оплаты бронирований.",
        
        "Примечательно, что ALPINE не покидает топы по покупкам до сих пор.",
        
        "📊 Обновили категорию Swaps в разделе Smart Money в сети Solana."
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n--- Тест {i} ---")
        print(f"Сообщение: {message}")
        
        result = parser.parse_message(message)
        if result:
            print(f"Результат: {result.symbol} | {result.action} | Уверенность: {result.confidence:.2f}")
            print(f"Движение: {result.price_movement}")
            print(f"Биржа: {result.exchange}")
            print(f"Сектор: {result.sector}")
        else:
            print("Сигнал не распознан или отфильтрован")

if __name__ == "__main__":
    test_cryptoattack24_parser()
