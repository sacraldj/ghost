"""
GHOST Whales Crypto Guide Parser
Парсер для сигналов канала @Whalesguide
"""

import re
import logging
from datetime import datetime
from typing import Optional, List
from signals.signal_parser_base import SignalParserBase, ParsedSignal, SignalDirection, calculate_confidence

logger = logging.getLogger(__name__)

class WhalesCryptoParser(SignalParserBase):
    """Парсер для сигналов канала Whales Crypto Guide"""
    
    def __init__(self):
        super().__init__("whales_crypto_guide")
        
        # Паттерны для распознавания формата Whales Crypto
        self.format_patterns = [
            r'Longing\s+#[A-Z]+',  # Longing #SWARMS Here
            r'Long\s*\([0-9x\s\-]+\)',  # Long (5x - 10x)
            r'Entry:\s*\$[0-9\.]+\s*-\s*\$[0-9\.]+',  # Entry: $0.02569 - $0.02400
            r'Targets:\s*\$[0-9\.,\s]+',  # Targets: $0.027, $0.028, ...
            r'Stoploss:\s*\$[0-9\.]+',  # Stoploss: $0.02260
            r'Reason:\s*.+',  # Reason: Chart looks bullish...
        ]
        
        # Ключевые слова для дополнительного распознавания
        self.whales_keywords = [
            'chart looks bullish',
            'worth buying',
            'quick profits',
            'short-mid term',
            'whales crypto',
            'whalesguide'
        ]
    
    def can_parse(self, text: str) -> bool:
        """Проверка, подходит ли текст для этого парсера"""
        text_clean = self.clean_text(text).lower()
        
        # Проверяем основные паттерны
        matched_patterns = 0
        for pattern in self.format_patterns:
            if re.search(pattern, text_clean, re.IGNORECASE):
                matched_patterns += 1
        
        # Проверяем специфичные ключевые слова
        keyword_matches = 0
        for keyword in self.whales_keywords:
            if keyword.lower() in text_clean:
                keyword_matches += 1
        
        # Должно быть минимум 3 паттерна из 6 ИЛИ 2 паттерна + ключевые слова
        return matched_patterns >= 3 or (matched_patterns >= 2 and keyword_matches >= 1)
    
    def parse_signal(self, text: str, trader_id: str) -> Optional[ParsedSignal]:
        """Основная функция парсинга сигнала Whales Crypto"""
        try:
            text_clean = self.clean_text(text)
            timestamp = datetime.now()
            
            # Извлекаем основные компоненты
            symbol = self.extract_symbol_whales(text_clean)
            if not symbol:
                self.logger.warning("Could not extract symbol from Whales Crypto text")
                return None
            
            direction = self.extract_direction_whales(text_clean)
            if not direction:
                self.logger.warning("Could not extract direction from Whales Crypto text")
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
            
            # Извлекаем детали специфично для Whales Crypto
            signal.leverage = self.extract_leverage_whales(text_clean)
            signal.entry_zone = self.extract_entry_zone_whales(text_clean)
            signal.targets = self.extract_targets_whales(text_clean)
            signal.stop_loss = self.extract_stop_loss_whales(text_clean)
            signal.reason = self.extract_reason_whales(text_clean)
            
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
            
            # Дополнительная уверенность для качественных сигналов Whales Crypto
            if signal.reason and len(signal.reason) > 20:
                signal.confidence += 5.0
            
            if signal.targets and len(signal.targets) >= 4:
                signal.confidence += 5.0
            
            signal.confidence = min(100.0, signal.confidence)
            
            self.logger.info(f"Parsed Whales Crypto signal: {symbol} {direction.value} (confidence: {signal.confidence:.1f}%)")
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error parsing Whales Crypto signal: {e}")
            return None
    
    def extract_symbol_whales(self, text: str) -> Optional[str]:
        """Извлечение символа для Whales Crypto"""
        # Ищем "#SWARMS", "#BTC", etc.
        pattern = r'#([A-Z]{2,15})'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            symbol = match.group(1).upper()
            # Нормализуем некоторые специфичные символы
            symbol_mapping = {
                'SWARMS': 'SWARMS',
                'BTC': 'BTC',
                'ETH': 'ETH',
                'SOL': 'SOL',
                'DOGE': 'DOGE'
            }
            return symbol_mapping.get(symbol, symbol)
        
        # Fallback на базовый метод
        return self.extract_symbol(text)
    
    def extract_direction_whales(self, text: str) -> Optional[SignalDirection]:
        """Извлечение направления для Whales Crypto"""
        text_lower = text.lower()
        
        # Специфичные паттерны Whales Crypto
        if 'longing' in text_lower:
            return SignalDirection.LONG
        elif 'shorting' in text_lower:
            return SignalDirection.SHORT
        elif 'long (' in text_lower:
            return SignalDirection.LONG
        elif 'short (' in text_lower:
            return SignalDirection.SHORT
        
        # Fallback на базовый метод
        return self.extract_direction(text)
    
    def extract_leverage_whales(self, text: str) -> Optional[str]:
        """Извлечение плеча для Whales Crypto"""
        # Ищем паттерн "Long (5x - 10x)"
        pattern = r'(?:Long|Short)\s*\(([^)]+)\)'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            leverage_text = match.group(1).strip()
            return leverage_text
        
        return self.extract_leverage(text)
    
    def extract_entry_zone_whales(self, text: str) -> List[float]:
        """Извлечение зоны входа для Whales Crypto"""
        # Ищем "Entry: $0.02569 - $0.02400"
        pattern = r'Entry:\s*\$?([0-9]*\.?[0-9]+)\s*-\s*\$?([0-9]*\.?[0-9]+)'
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
    
    def extract_targets_whales(self, text: str) -> List[float]:
        """Извлечение целей для Whales Crypto"""
        targets = []
        
        # Ищем "Targets: $0.027, $0.028, $0.029, $0.03050, $0.032, $0.034, $0.036, $0.03859"
        pattern = r'Targets:\s*((?:\$?[0-9]*\.?[0-9]+[,\s]*)+)'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            targets_text = match.group(1)
            # Извлекаем все числа
            price_matches = re.findall(r'\$?([0-9]*\.?[0-9]+)', targets_text)
            
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
    
    def extract_stop_loss_whales(self, text: str) -> Optional[float]:
        """Извлечение стоп-лосса для Whales Crypto"""
        # Ищем "Stoploss: $0.02260"
        pattern = r'Stoploss:\s*\$?([0-9]*\.?[0-9]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        
        # Fallback на базовый метод
        return self.extract_stop_loss(text)
    
    def extract_reason_whales(self, text: str) -> Optional[str]:
        """Извлечение обоснования для Whales Crypto"""
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
def test_whales_crypto_parser():
    """Тестирование парсера на примере сигнала SWARMS"""
    sample_signal = """
    Longing #SWARMS Here

    Long (5x - 10x)

    Entry: $0.02569 - $0.02400

    Reason: Chart looks bullish for it. Worth buying for short-mid term quick profits too.

    Targets: $0.027, $0.028, $0.029, $0.03050, $0.032, $0.034, $0.036, $0.03859

    Stoploss: $0.02260
    """
    
    parser = WhalesCryptoParser()
    
    print("🧪 Testing Whales Crypto Parser")
    print(f"Can parse: {parser.can_parse(sample_signal)}")
    
    if parser.can_parse(sample_signal):
        signal = parser.parse_signal(sample_signal, "whales_crypto_guide")
        
        if signal:
            print(f"✅ Parsed successfully!")
            print(f"Symbol: {signal.symbol}")
            print(f"Direction: {signal.direction.value}")
            print(f"Leverage: {signal.leverage}")
            print(f"Entry Zone: {signal.entry_zone}")
            print(f"Targets ({len(signal.targets)}): {signal.targets}")
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
    test_whales_crypto_parser()
