"""
GHOST Parser Factory
Автоматический выбор и создание парсеров для различных источников сигналов
"""

import logging
from typing import Dict, Type, Optional, Any, List
from abc import ABC, abstractmethod

from signals.whales_crypto_parser import WhalesCryptoParser
from signals.trader_detector import TraderDetector, TraderStyle

logger = logging.getLogger(__name__)

class SignalParserInterface(ABC):
    """Интерфейс для всех парсеров сигналов"""
    
    @abstractmethod
    def can_parse(self, text: str) -> bool:
        """Проверка, может ли парсер обработать этот текст"""
        pass
    
    @abstractmethod
    def parse_signal(self, text: str, trader_id: str) -> Optional[Any]:
        """Парсинг сигнала из текста"""
        pass

class UniversalWhalesParser(SignalParserInterface):
    """Универсальный парсер для всех типов трейдеров в @Whalesguide"""
    
    def __init__(self):
        self.detector = TraderDetector()
        self.whales_parser = WhalesCryptoParser()
        logger.info("Universal Whales Parser initialized")
    
    def can_parse(self, text: str) -> bool:
        """Проверяет через детектор трейдеров и базовый парсер"""
        # Сначала проверяем через детектор
        style, confidence, _ = self.detector.detect_trader(text)
        
        if style != TraderStyle.UNKNOWN and confidence > 0.5:
            return True
        
        # Fallback на базовый парсер
        return self.whales_parser.can_parse(text)
    
    def parse_signal(self, text: str, trader_id: str = None) -> Optional[Any]:
        """Парсинг с автоматическим определением трейдера"""
        # Определяем трейдера автоматически
        style, confidence, details = self.detector.detect_trader(text)
        
        if not trader_id:
            trader_id = self.detector.get_trader_id(style, "whalesguide")
        
        # Парсим через соответствующий метод
        signal = self.whales_parser.parse_signal(text, trader_id)
        
        if signal:
            # Добавляем информацию о детекции
            signal.detected_trader_style = style.value
            signal.detection_confidence = confidence
            signal.detection_details = details
            
            logger.info(f"Parsed signal from {style.value} (confidence: {confidence:.2f})")
        
        return signal

class Trade2Parser(SignalParserInterface):
    """Парсер для канала 2Trade"""
    
    def __init__(self):
        self.keywords = ["🎯", "ENTRY", "TARGET", "STOP", "LONG", "SHORT"]
        logger.info("2Trade Parser initialized")
    
    def can_parse(self, text: str) -> bool:
        """Проверка формата 2Trade"""
        text_upper = text.upper()
        keyword_count = sum(1 for keyword in self.keywords if keyword in text_upper)
        return keyword_count >= 3
    
    def parse_signal(self, text: str, trader_id: str) -> Optional[Any]:
        """Парсинг сигналов 2Trade"""
        # Заглушка для будущей реализации
        logger.info(f"2Trade parsing for {trader_id} - not implemented yet")
        return None

class VIPSignalsParser(SignalParserInterface):
    """Парсер для VIP каналов"""
    
    def __init__(self):
        self.vip_indicators = ["🔥", "💎", "VIP", "PREMIUM", "⭐"]
        logger.info("VIP Signals Parser initialized")
    
    def can_parse(self, text: str) -> bool:
        """Проверка VIP формата"""
        return any(indicator in text for indicator in self.vip_indicators)
    
    def parse_signal(self, text: str, trader_id: str) -> Optional[Any]:
        """Парсинг VIP сигналов"""
        # Заглушка для будущей реализации
        logger.info(f"VIP parsing for {trader_id} - not implemented yet")
        return None

class DiscordParser(SignalParserInterface):
    """Парсер для Discord каналов"""
    
    def can_parse(self, text: str) -> bool:
        """Проверка Discord формата"""
        # Discord часто использует embed-ы и специальное форматирование
        discord_indicators = ["**", "__", "```", "> "]
        return any(indicator in text for indicator in discord_indicators)
    
    def parse_signal(self, text: str, trader_id: str) -> Optional[Any]:
        """Парсинг Discord сигналов"""
        logger.info(f"Discord parsing for {trader_id} - not implemented yet")
        return None

class ParserFactory:
    """Фабрика для создания и выбора парсеров"""
    
    def __init__(self):
        self.parsers: Dict[str, Type[SignalParserInterface]] = {}
        self.instances: Dict[str, SignalParserInterface] = {}
        
        # Регистрируем стандартные парсеры
        self._register_default_parsers()
        
        logger.info("Parser Factory initialized")
    
    def _register_default_parsers(self):
        """Регистрация стандартных парсеров"""
        self.register_parser("whales_universal", UniversalWhalesParser)
        self.register_parser("whales_crypto_parser", UniversalWhalesParser)  # Алиас
        self.register_parser("2trade_parser", Trade2Parser)
        self.register_parser("vip_signals_parser", VIPSignalsParser)
        self.register_parser("discord_parser", DiscordParser)
    
    def register_parser(self, parser_type: str, parser_class: Type[SignalParserInterface]):
        """Регистрация нового типа парсера"""
        self.parsers[parser_type] = parser_class
        logger.info(f"Registered parser type: {parser_type}")
    
    def get_parser(self, parser_type: str) -> Optional[SignalParserInterface]:
        """Получение экземпляра парсера по типу"""
        if parser_type not in self.parsers:
            logger.error(f"Unknown parser type: {parser_type}")
            return None
        
        # Используем singleton pattern для парсеров
        if parser_type not in self.instances:
            try:
                parser_class = self.parsers[parser_type]
                self.instances[parser_type] = parser_class()
                logger.debug(f"Created parser instance: {parser_type}")
            except Exception as e:
                logger.error(f"Error creating parser {parser_type}: {e}")
                return None
        
        return self.instances[parser_type]
    
    def auto_select_parser(self, text: str, 
                          preferred_parsers: List[str] = None) -> Optional[SignalParserInterface]:
        """Автоматический выбор парсера по тексту"""
        
        # Если указаны предпочтительные парсеры, проверяем их первыми
        if preferred_parsers:
            for parser_type in preferred_parsers:
                parser = self.get_parser(parser_type)
                if parser and parser.can_parse(text):
                    logger.debug(f"Selected preferred parser: {parser_type}")
                    return parser
        
        # Проверяем все доступные парсеры
        for parser_type, parser_class in self.parsers.items():
            parser = self.get_parser(parser_type)
            if parser and parser.can_parse(text):
                logger.debug(f"Auto-selected parser: {parser_type}")
                return parser
        
        logger.warning("No suitable parser found for the text")
        return None
    
    def parse_with_fallback(self, text: str, 
                           preferred_parsers: List[str] = None,
                           trader_id: str = None) -> Optional[Any]:
        """Парсинг с автоматическим выбором и fallback"""
        
        # Пробуем автоматический выбор
        parser = self.auto_select_parser(text, preferred_parsers)
        
        if parser:
            try:
                result = parser.parse_signal(text, trader_id)
                if result:
                    return result
            except Exception as e:
                logger.error(f"Error parsing with selected parser: {e}")
        
        # Fallback на универсальный парсер
        fallback_parser = self.get_parser("whales_universal")
        if fallback_parser and fallback_parser.can_parse(text):
            try:
                logger.info("Using fallback universal parser")
                return fallback_parser.parse_signal(text, trader_id)
            except Exception as e:
                logger.error(f"Error with fallback parser: {e}")
        
        return None
    
    def get_available_parsers(self) -> List[str]:
        """Получение списка доступных парсеров"""
        return list(self.parsers.keys())
    
    def get_parser_info(self) -> Dict[str, Dict[str, Any]]:
        """Получение информации о всех парсерах"""
        info = {}
        
        for parser_type, parser_class in self.parsers.items():
            info[parser_type] = {
                "class_name": parser_class.__name__,
                "module": parser_class.__module__,
                "description": parser_class.__doc__ or "No description",
                "is_instantiated": parser_type in self.instances
            }
        
        return info

# Глобальный экземпляр фабрики
parser_factory = ParserFactory()

def get_parser_factory() -> ParserFactory:
    """Получение глобального экземпляра фабрики"""
    return parser_factory

# Функция для тестирования фабрики
def test_parser_factory():
    """Тестирование фабрики парсеров"""
    print("🧪 ТЕСТИРОВАНИЕ PARSER FACTORY")
    print("=" * 60)
    
    factory = get_parser_factory()
    
    # Показываем доступные парсеры
    print("📋 ДОСТУПНЫЕ ПАРСЕРЫ:")
    for parser_type in factory.get_available_parsers():
        print(f"   • {parser_type}")
    
    # Тестовые сигналы
    test_signals = [
        {
            "name": "Whales Standard",
            "text": """Longing #BTCUSDT Here

Long (5x - 10x)

Entry: $45000 - $44500

Targets: $46000, $47000, $48000

Stoploss: $43000""",
            "expected_parser": "whales_universal"
        },
        {
            "name": "Spot Trader", 
            "text": """Buying #ETH Here in spot

You can long in 4x leverage, too.

Entry: 2800-2850$

Targets: 2900$, 3000$

Stoploss: 2750$""",
            "expected_parser": "whales_universal"
        },
        {
            "name": "VIP Signal",
            "text": """🔥 VIP PREMIUM SIGNAL 💎

LONG #SOLUSDT
Entry: 180-185
Targets: 200, 220, 250
SL: 170""",
            "expected_parser": "vip_signals_parser"
        },
        {
            "name": "Discord Format",
            "text": """**LONG SIGNAL**
```
Symbol: ADAUSDT
Entry: 0.45
TP: 0.50
SL: 0.40
```""",
            "expected_parser": "discord_parser"
        }
    ]
    
    print(f"\n🎯 ТЕСТИРОВАНИЕ АВТОВЫБОРА:")
    
    for i, signal in enumerate(test_signals, 1):
        print(f"\n{i}️⃣ {signal['name']}:")
        
        # Автоматический выбор парсера
        parser = factory.auto_select_parser(signal['text'])
        
        if parser:
            parser_type = None
            for pt, pc in factory.parsers.items():
                if isinstance(parser, pc):
                    parser_type = pt
                    break
            
            print(f"   Selected: {parser_type}")
            print(f"   Expected: {signal['expected_parser']}")
            
            # Пробуем парсить
            result = factory.parse_with_fallback(signal['text'])
            if result:
                print(f"   Parsing: ✅ Success")
                if hasattr(result, 'symbol'):
                    print(f"   Symbol: {result.symbol}")
            else:
                print(f"   Parsing: ❌ Failed")
        else:
            print(f"   Selected: None")
            print(f"   Status: ❌ No suitable parser")
    
    print(f"\n🎉 FACTORY ГОТОВА К РАБОТЕ!")

if __name__ == "__main__":
    test_parser_factory()
