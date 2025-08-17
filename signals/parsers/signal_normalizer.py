"""
GHOST Signal Normalizer
Унифицированный нормализатор сигналов (fallback парсер)
"""

import re
import logging
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class Side(Enum):
    BUY = "BUY"
    SELL = "SELL"
    LONG = "LONG"
    SHORT = "SHORT"

class EntryType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    RANGE = "range"

@dataclass
class NormalizedSignal:
    """Нормализованный сигнал"""
    trader_id: str
    symbol: str
    side: Side
    entry: Optional[float] = None
    range_low: Optional[float] = None
    range_high: Optional[float] = None
    tp1: Optional[float] = None
    tp2: Optional[float] = None
    tp3: Optional[float] = None
    tp4: Optional[float] = None
    sl: Optional[float] = None
    leverage_hint: Optional[int] = None
    timeframe_hint: Optional[str] = None
    confidence: float = 0.0
    entry_type: Optional[EntryType] = None
    is_valid: bool = True
    validation_errors: List[str] = None
    
    def __post_init__(self):
        if self.validation_errors is None:
            self.validation_errors = []

class SignalNormalizer:
    """Fallback нормализатор сигналов"""
    
    def __init__(self):
        # Ключевые слова для определения направления
        self.long_keywords = ['long', 'buy', 'longing', 'покупка', 'лонг']
        self.short_keywords = ['short', 'sell', 'shorting', 'продажа', 'шорт']
        
        # Паттерны для извлечения данных
        self.symbol_patterns = [
            r'#([A-Z]{2,10})',           # #BTC, #ETH
            r'([A-Z]{2,10})USDT?',       # BTCUSDT, ETHUSDT
            r'([A-Z]{2,10})/USDT?',      # BTC/USDT
            r'PAIR:\s*([A-Z]{2,10})',    # PAIR: BTC
        ]
        
        self.price_patterns = [
            r'\$?([0-9]+\.?[0-9]*)',     # $1234.56, 1234.56
        ]
    
    def normalize(self, trader_id: str, raw_text: str, profile: str = 'standard_v1') -> Optional[NormalizedSignal]:
        """Главная функция нормализации"""
        try:
            signal = NormalizedSignal(trader_id=trader_id, symbol="", side=Side.BUY)
            
            # Очистка текста
            clean_text = self._clean_text(raw_text)
            
            # Извлечение символа
            symbol = self._extract_symbol(clean_text)
            if not symbol:
                signal.validation_errors.append("Symbol not found")
                signal.is_valid = False
                return signal
            
            signal.symbol = symbol
            
            # Извлечение направления
            side = self._extract_side(clean_text)
            if not side:
                signal.validation_errors.append("Direction not found")
                signal.is_valid = False
                return signal
            
            signal.side = side
            
            # Извлечение цен
            self._extract_prices(clean_text, signal)
            
            # Извлечение плеча
            signal.leverage_hint = self._extract_leverage(clean_text)
            
            # Определение типа входа
            signal.entry_type = self._determine_entry_type(signal)
            
            # Валидация
            self._validate_signal(signal)
            
            # Расчет уверенности
            signal.confidence = self._calculate_confidence(signal, clean_text)
            
            return signal
            
        except Exception as e:
            logger.error(f"Error normalizing signal: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """Очистка текста"""
        # Убираем лишние символы
        text = re.sub(r'[^\w\s\.\-\+\:\$\#\/\(\)]', ' ', text)
        # Нормализуем пробелы
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _extract_symbol(self, text: str) -> Optional[str]:
        """Извлечение символа"""
        for pattern in self.symbol_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                symbol = match.group(1).upper()
                # Убираем суффиксы
                if symbol.endswith('USDT'):
                    symbol = symbol[:-4]
                elif symbol.endswith('USD'):
                    symbol = symbol[:-3]
                return symbol
        return None
    
    def _extract_side(self, text: str) -> Optional[Side]:
        """Извлечение направления"""
        text_lower = text.lower()
        
        # Проверяем ключевые слова
        for keyword in self.long_keywords:
            if keyword in text_lower:
                return Side.LONG
        
        for keyword in self.short_keywords:
            if keyword in text_lower:
                return Side.SHORT
        
        return None
    
    def _extract_prices(self, text: str, signal: NormalizedSignal):
        """Извлечение цен"""
        # Ищем entry
        entry_match = re.search(r'entry:?\s*\$?([0-9]+\.?[0-9]*)', text, re.IGNORECASE)
        if entry_match:
            signal.entry = float(entry_match.group(1))
        
        # Ищем диапазон
        range_match = re.search(r'\$?([0-9]+\.?[0-9]*)\s*-\s*\$?([0-9]+\.?[0-9]*)', text)
        if range_match:
            price1 = float(range_match.group(1))
            price2 = float(range_match.group(2))
            signal.range_low = min(price1, price2)
            signal.range_high = max(price1, price2)
            
            if not signal.entry:
                signal.entry = (signal.range_low + signal.range_high) / 2
        
        # Ищем TP
        tp_patterns = [
            (r'tp1:?\s*\$?([0-9]+\.?[0-9]*)', 'tp1'),
            (r'tp2:?\s*\$?([0-9]+\.?[0-9]*)', 'tp2'),
            (r'tp3:?\s*\$?([0-9]+\.?[0-9]*)', 'tp3'),
            (r'tp4:?\s*\$?([0-9]+\.?[0-9]*)', 'tp4'),
        ]
        
        for pattern, field in tp_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                setattr(signal, field, float(match.group(1)))
        
        # Ищем SL
        sl_match = re.search(r'(?:sl|stop|stoploss):?\s*\$?([0-9]+\.?[0-9]*)', text, re.IGNORECASE)
        if sl_match:
            signal.sl = float(sl_match.group(1))
    
    def _extract_leverage(self, text: str) -> Optional[int]:
        """Извлечение плеча"""
        leverage_match = re.search(r'(?:leverage|лечо):?\s*(\d+)x?', text, re.IGNORECASE)
        if leverage_match:
            return int(leverage_match.group(1))
        
        # Ищем в скобках (5x - 10x)
        bracket_match = re.search(r'\((\d+)x\s*-\s*(\d+)x\)', text, re.IGNORECASE)
        if bracket_match:
            return int(bracket_match.group(1))  # Берем минимальное
        
        return None
    
    def _determine_entry_type(self, signal: NormalizedSignal) -> EntryType:
        """Определение типа входа"""
        if signal.range_low and signal.range_high and signal.range_low != signal.range_high:
            return EntryType.RANGE
        elif signal.entry:
            return EntryType.LIMIT
        else:
            return EntryType.MARKET
    
    def _validate_signal(self, signal: NormalizedSignal):
        """Валидация сигнала"""
        errors = []
        
        # Проверяем обязательные поля
        if not signal.symbol:
            errors.append("Missing symbol")
        
        if not signal.side:
            errors.append("Missing side")
        
        if not signal.entry and not (signal.range_low and signal.range_high):
            errors.append("Missing entry price")
        
        # Логическая проверка цен для LONG
        if signal.side in [Side.LONG, Side.BUY]:
            entry_price = signal.entry or signal.range_high or 0
            
            if signal.tp1 and entry_price > 0 and signal.tp1 <= entry_price:
                errors.append("TP1 must be higher than entry for LONG")
            
            if signal.sl and entry_price > 0 and signal.sl >= entry_price:
                errors.append("Stop loss must be lower than entry for LONG")
        
        # Логическая проверка цен для SHORT
        if signal.side in [Side.SHORT, Side.SELL]:
            entry_price = signal.entry or signal.range_low or 0
            
            if signal.tp1 and entry_price > 0 and signal.tp1 >= entry_price:
                errors.append("TP1 must be lower than entry for SHORT")
            
            if signal.sl and entry_price > 0 and signal.sl <= entry_price:
                errors.append("Stop loss must be higher than entry for SHORT")
        
        signal.validation_errors.extend(errors)
        signal.is_valid = len(errors) == 0
    
    def _calculate_confidence(self, signal: NormalizedSignal, text: str) -> float:
        """Расчет уверенности"""
        confidence = 0.0
        
        # Базовые компоненты
        if signal.symbol:
            confidence += 20.0
        
        if signal.side:
            confidence += 15.0
        
        if signal.entry or (signal.range_low and signal.range_high):
            confidence += 25.0
        
        if signal.tp1:
            confidence += 20.0
        
        if signal.tp2:
            confidence += 10.0
        
        if signal.sl:
            confidence += 15.0
        
        if signal.leverage_hint:
            confidence += 5.0
        
        # Штрафы
        confidence -= len(signal.validation_errors) * 10.0
        
        return max(0.0, min(100.0, confidence))

# Convenience функция
def normalize_signal(trader_id: str, raw_text: str, profile: str = 'standard_v1') -> Optional[NormalizedSignal]:
    """Нормализация сигнала (внешний интерфейс)"""
    normalizer = SignalNormalizer()
    return normalizer.normalize(trader_id, raw_text, profile)

# Тест
def test_normalizer():
    """Тестирование нормализатора"""
    test_signals = [
        "Longing #SUI Entry: $3.89 TP1: $4.05 SL: $3.50",
        "PAIR: BTC DIRECTION: LONG ENTRY: $43000 TP1: $45000 SL: $41000",
        "Short #ETH at $2650 Target: $2580 Stop: $2720"
    ]
    
    normalizer = SignalNormalizer()
    
    for i, signal_text in enumerate(test_signals):
        print(f"\n🧪 Test {i+1}: {signal_text}")
        
        result = normalizer.normalize(f"test_trader_{i}", signal_text)
        
        if result:
            print(f"✅ Symbol: {result.symbol}")
            print(f"   Side: {result.side.value}")
            print(f"   Entry: {result.entry}")
            print(f"   TP1: {result.tp1}")
            print(f"   SL: {result.sl}")
            print(f"   Valid: {result.is_valid}")
            print(f"   Confidence: {result.confidence:.1f}%")
            if result.validation_errors:
                print(f"   Errors: {result.validation_errors}")
        else:
            print("❌ Failed to normalize")

if __name__ == "__main__":
    test_normalizer()