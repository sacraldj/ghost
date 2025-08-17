"""
GHOST Crypto Hub VIP Parser
Парсер для сигналов формата Crypto Hub VIP (англоязычные сигналы)
На основе примера:

Longing #SUI Here
Long (5x - 10x)
Entry: $3.89 - $3.70
Reason: Chart looks bullish for it. Worth buying for short-mid term quick profits too.
Targets: $4.0500, $4.2000, $4.3000, $4.4000, $4.6000, $4.8000, $5.0690
Stoploss: $3.4997
"""

import re
import logging
from datetime import datetime
from typing import Optional, List
from .signal_parser_base import SignalParserBase, ParsedSignal, SignalDirection, calculate_confidence

logger = logging.getLogger(__name__)

class CryptoHubParser(SignalParserBase):
    """Парсер для сигналов Crypto Hub VIP формата"""
    
    def __init__(self):
        super().__init__("crypto_hub_vip")
        
        # Паттерны для распознавания формата Crypto Hub
        self.format_patterns = [
            r'Longing\s+#[A-Z]+',  # Longing #SUI Here
            r'Long\s*\([0-9x\s\-]+\)',  # Long (5x - 10x)
            r'Entry:\s*\$[0-9\.]+\s*-\s*\$[0-9\.]+',  # Entry: $3.89 - $3.70
            r'Targets:\s*\$[0-9\.,\s]+',  # Targets: $4.05, $4.20, ...
            r'Stoploss:\s*\$[0-9\.]+',  # Stoploss: $3.4997
        ]
    
    def can_parse(self, text: str) -> bool:
        """Проверка, подходит ли текст для этого парсера"""
        text_clean = self.clean_text(text)
        
        # Должно быть минимум 2 паттерна из 5
        matched_patterns = 0
        for pattern in self.format_patterns:
            if re.search(pattern, text_clean, re.IGNORECASE):
                matched_patterns += 1
        
        return matched_patterns >= 2
    
    def parse_signal(self, text: str, trader_id: str) -> Optional[ParsedSignal]:
        """Основная функция парсинга сигнала Crypto Hub"""
        try:
            text_clean = self.clean_text(text)
            timestamp = datetime.now()
            
            # Извлекаем основные компоненты
            symbol = self.extract_symbol(text_clean)
            if not symbol:
                self.logger.warning("Could not extract symbol from text")
                return None
            
            direction = self.extract_direction_crypto_hub(text_clean)
            if not direction:
                self.logger.warning("Could not extract direction from text")
                return None
            
            # Создаем объект сигнала
            signal = ParsedSignal(
                signal_id=self.generate_signal_id(trader_id, symbol, timestamp),
                source=self.source_name,
                trader_id=trader_id,
                raw_text=text,
                timestamp=timestamp,
                symbol=symbol,
                direction=direction
            )
            
            # Извлекаем детали
            signal.leverage = self.extract_leverage_crypto_hub(text_clean)
            signal.entry_zone = self.extract_entry_zone_crypto_hub(text_clean)
            signal.targets = self.extract_targets_crypto_hub(text_clean)
            signal.stop_loss = self.extract_stop_loss_crypto_hub(text_clean)
            signal.reason = self.extract_reason_crypto_hub(text_clean)
            
            # Заполняем отдельные TP поля
            if signal.targets:
                if len(signal.targets) >= 1:
                    signal.tp1 = signal.targets[0]
                if len(signal.targets) >= 2:
                    signal.tp2 = signal.targets[1]
                if len(signal.targets) >= 3:
                    signal.tp3 = signal.targets[2]
                if len(signal.targets) >= 4:
                    signal.tp4 = signal.targets[3]
            
            # Устанавливаем single entry как среднюю зоны входа
            if signal.entry_zone:
                signal.entry_single = sum(signal.entry_zone) / len(signal.entry_zone)
            
            # Валидация
            self.validate_signal(signal)
            
            # Расчет уверенности
            signal.confidence = calculate_confidence(signal)
            
            self.logger.info(f"Parsed Crypto Hub signal: {symbol} {direction.value} (confidence: {signal.confidence:.1f}%)")
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error parsing Crypto Hub signal: {e}")
            return None
    
    def extract_direction_crypto_hub(self, text: str) -> Optional[SignalDirection]:
        """Извлечение направления специфично для Crypto Hub"""
        text_lower = text.lower()
        
        # Специфичные паттерны Crypto Hub
        if 'longing' in text_lower or 'long (' in text_lower:
            return SignalDirection.LONG
        elif 'shorting' in text_lower or 'short (' in text_lower:
            return SignalDirection.SHORT
        
        # Fallback на базовый метод
        return self.extract_direction(text)
    
    def extract_leverage_crypto_hub(self, text: str) -> Optional[str]:
        """Извлечение плеча для формата Crypto Hub"""
        # Ищем паттерн "Long (5x - 10x)"
        pattern = r'(?:Long|Short)\s*\(([^)]+)\)'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            leverage_text = match.group(1).strip()
            return leverage_text
        
        return self.extract_leverage(text)
    
    def extract_entry_zone_crypto_hub(self, text: str) -> List[float]:
        """Извлечение зоны входа для Crypto Hub"""
        # Ищем "Entry: $3.89 - $3.70"
        pattern = r'Entry:\s*\$?([0-9]+\.?[0-9]*)\s*-\s*\$?([0-9]+\.?[0-9]*)'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            try:
                price1 = float(match.group(1))
                price2 = float(match.group(2))
                return sorted([price1, price2])
            except ValueError:
                pass
        
        # Fallback на базовый метод
        return self.extract_entry_zone(text)
    
    def extract_targets_crypto_hub(self, text: str) -> List[float]:
        """Извлечение целей для Crypto Hub"""
        targets = []
        
        # Ищем "Targets: $4.0500, $4.2000, $4.3000, ..."
        pattern = r'Targets:\s*((?:\$?[0-9]+\.?[0-9]*[,\s]*)+)'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            targets_text = match.group(1)
            # Извлекаем все числа
            price_matches = re.findall(r'\$?([0-9]+\.?[0-9]*)', targets_text)
            
            for price_str in price_matches:
                try:
                    price = float(price_str)
                    if price > 0:
                        targets.append(price)
                except ValueError:
                    continue
        
        # Если не нашли через Targets:, ищем отдельные TP
        if not targets:
            targets = self.extract_targets(text)
        
        return targets
    
    def extract_stop_loss_crypto_hub(self, text: str) -> Optional[float]:
        """Извлечение стоп-лосса для Crypto Hub"""
        # Ищем "Stoploss: $3.4997"
        pattern = r'Stoploss:\s*\$?([0-9]+\.?[0-9]*)'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        
        # Fallback на базовый метод
        return self.extract_stop_loss(text)
    
    def extract_reason_crypto_hub(self, text: str) -> Optional[str]:
        """Извлечение обоснования для Crypto Hub"""
        # Ищем "Reason: ..."
        pattern = r'Reason:\s*(.+?)(?:\n|Targets|Target|Entry|Stoploss|$)'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        
        if match:
            reason = match.group(1).strip()
            # Очищаем от лишних символов
            reason = re.sub(r'\s+', ' ', reason)
            return reason
        
        # Fallback на базовый метод
        return self.extract_reason(text)

# Функция для тестирования парсера
def test_crypto_hub_parser():
    """Тестирование парсера на примере сигнала SUI"""
    sample_signal = """
    Longing #SUI Here

    Long (5x - 10x)

    Entry: $3.89 - $3.70

    Reason: Chart looks bullish for it. Worth buying for short-mid term quick profits too.

    Targets: $4.0500, $4.2000, $4.3000, $4.4000, $4.6000, $4.8000, $5.0690

    Stoploss: $3.4997
    """
    
    parser = CryptoHubParser()
    
    print("🧪 Testing Crypto Hub Parser")
    print(f"Can parse: {parser.can_parse(sample_signal)}")
    
    if parser.can_parse(sample_signal):
        signal = parser.parse_signal(sample_signal, "crypto_hub_test")
        
        if signal:
            print(f"✅ Parsed successfully!")
            print(f"Symbol: {signal.symbol}")
            print(f"Direction: {signal.direction.value}")
            print(f"Leverage: {signal.leverage}")
            print(f"Entry Zone: {signal.entry_zone}")
            print(f"Targets: {signal.targets}")
            print(f"Stop Loss: {signal.stop_loss}")
            print(f"Reason: {signal.reason}")
            print(f"Confidence: {signal.confidence:.1f}%")
            print(f"Valid: {signal.is_valid}")
            if signal.parse_errors:
                print(f"Errors: {signal.parse_errors}")
        else:
            print("❌ Failed to parse")
    
    return parser

if __name__ == "__main__":
    test_crypto_hub_parser()
