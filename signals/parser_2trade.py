"""
GHOST 2Trade Parser
Парсер для сигналов формата канала 2Trade
На основе архитектуры системы Дарена
"""

import re
import logging
from datetime import datetime
from typing import Optional, List
from signals.signal_parser_base import SignalParserBase, ParsedSignal, SignalDirection, calculate_confidence

logger = logging.getLogger(__name__)

class TwoTradeParser(SignalParserBase):
    """Парсер для сигналов канала 2Trade"""
    
    def __init__(self):
        super().__init__("2trade")
        
        # Паттерны для распознавания формата 2Trade
        self.format_patterns = [
            r'PAIR:\s*[A-Z]+',  # PAIR: SUI
            r'DIRECTION:\s*(?:LONG|SHORT)',  # DIRECTION: LONG
            r'ENTRY:\s*[0-9\.\$\-\s]+',  # ENTRY: $3.80 - $3.90
            r'TP\d+:\s*\$?[0-9\.]+',  # TP1: $4.05
            r'SL:\s*\$?[0-9\.]+',  # SL: $3.50
            r'LEVERAGE:\s*\d+X',  # LEVERAGE: 10X
        ]
    
    def can_parse(self, text: str) -> bool:
        """Проверка, подходит ли текст для парсера 2Trade"""
        text_clean = self.clean_text(text)
        
        # Должно быть минимум 3 паттерна из 6
        matched_patterns = 0
        for pattern in self.format_patterns:
            if re.search(pattern, text_clean, re.IGNORECASE):
                matched_patterns += 1
        
        return matched_patterns >= 3
    
    def parse_signal(self, text: str, trader_id: str) -> Optional[ParsedSignal]:
        """Основная функция парсинга сигнала 2Trade"""
        try:
            text_clean = self.clean_text(text)
            timestamp = datetime.now()
            
            # Извлекаем основные компоненты
            symbol = self.extract_symbol_2trade(text_clean)
            if not symbol:
                self.logger.warning("Could not extract symbol from 2Trade text")
                return None
            
            direction = self.extract_direction_2trade(text_clean)
            if not direction:
                self.logger.warning("Could not extract direction from 2Trade text")
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
            
            # Извлекаем детали специфично для 2Trade
            signal.leverage = self.extract_leverage_2trade(text_clean)
            signal.entry_zone = self.extract_entry_zone_2trade(text_clean)
            signal.targets = self.extract_targets_2trade(text_clean)
            signal.stop_loss = self.extract_stop_loss_2trade(text_clean)
            signal.reason = self.extract_reason_2trade(text_clean)
            
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
            
            # Устанавливаем single entry
            if signal.entry_zone:
                signal.entry_single = sum(signal.entry_zone) / len(signal.entry_zone)
            
            # Валидация
            self.validate_signal(signal)
            
            # Расчет уверенности
            signal.confidence = calculate_confidence(signal)
            
            self.logger.info(f"Parsed 2Trade signal: {symbol} {direction.value} (confidence: {signal.confidence:.1f}%)")
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error parsing 2Trade signal: {e}")
            return None
    
    def extract_symbol_2trade(self, text: str) -> Optional[str]:
        """Извлечение символа для формата 2Trade"""
        # Ищем "PAIR: SUI"
        pattern = r'PAIR:\s*([A-Z]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            return match.group(1).upper()
        
        # Fallback на базовый метод
        return self.extract_symbol(text)
    
    def extract_direction_2trade(self, text: str) -> Optional[SignalDirection]:
        """Извлечение направления для 2Trade"""
        # Ищем "DIRECTION: LONG"
        pattern = r'DIRECTION:\s*(LONG|SHORT)'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            direction_str = match.group(1).upper()
            if direction_str == 'LONG':
                return SignalDirection.LONG
            elif direction_str == 'SHORT':
                return SignalDirection.SHORT
        
        # Fallback на базовый метод
        return self.extract_direction(text)
    
    def extract_leverage_2trade(self, text: str) -> Optional[str]:
        """Извлечение плеча для 2Trade"""
        # Ищем "LEVERAGE: 10X"
        pattern = r'LEVERAGE:\s*(\d+X?)'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            leverage = match.group(1).upper()
            if not leverage.endswith('X'):
                leverage += 'X'
            return leverage
        
        return self.extract_leverage(text)
    
    def extract_entry_zone_2trade(self, text: str) -> List[float]:
        """Извлечение зоны входа для 2Trade"""
        # Ищем "ENTRY: $3.80 - $3.90" или "ENTRY: $3.85"
        pattern = r'ENTRY:\s*\$?([0-9]+\.?[0-9]*)\s*(?:-\s*\$?([0-9]+\.?[0-9]*))?'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            try:
                price1 = float(match.group(1))
                prices = [price1]
                
                if match.group(2):  # Есть второя цена (диапазон)
                    price2 = float(match.group(2))
                    prices.append(price2)
                
                return sorted(prices)
            except ValueError:
                pass
        
        # Fallback на базовый метод
        return self.extract_entry_zone(text)
    
    def extract_targets_2trade(self, text: str) -> List[float]:
        """Извлечение целей для 2Trade"""
        targets = []
        
        # Ищем "TP1: $4.05", "TP2: $4.20", etc.
        tp_pattern = r'TP(\d+):\s*\$?([0-9]+\.?[0-9]*)'
        matches = re.findall(tp_pattern, text, re.IGNORECASE)
        
        # Сортируем по номеру TP
        sorted_matches = sorted(matches, key=lambda x: int(x[0]))
        
        for tp_num, price_str in sorted_matches:
            try:
                price = float(price_str)
                if price > 0:
                    targets.append(price)
            except ValueError:
                continue
        
        # Если не нашли через TP паттерн, fallback на базовый
        if not targets:
            targets = self.extract_targets(text)
        
        return targets
    
    def extract_stop_loss_2trade(self, text: str) -> Optional[float]:
        """Извлечение стоп-лосса для 2Trade"""
        # Ищем "SL: $3.50"
        pattern = r'SL:\s*\$?([0-9]+\.?[0-9]*)'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        
        # Fallback на базовый метод
        return self.extract_stop_loss(text)
    
    def extract_reason_2trade(self, text: str) -> Optional[str]:
        """Извлечение обоснования для 2Trade"""
        # Ищем строки после основных параметров
        # Может быть "REASON:" или просто текст в конце
        
        # Сначала пробуем найти явное REASON:
        pattern = r'REASON:\s*(.+?)(?:\n|$)'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        
        if match:
            reason = match.group(1).strip()
            return re.sub(r'\s+', ' ', reason)
        
        # Ищем текст после всех основных полей
        # Удаляем все известные поля и смотрим, что осталось
        clean_text = text
        
        fields_to_remove = [
            r'PAIR:\s*[A-Z]+',
            r'DIRECTION:\s*(?:LONG|SHORT)',
            r'ENTRY:\s*[0-9\.\$\-\s]+',
            r'TP\d+:\s*\$?[0-9\.]+',
            r'SL:\s*\$?[0-9\.]+',
            r'LEVERAGE:\s*\d+X?',
        ]
        
        for pattern in fields_to_remove:
            clean_text = re.sub(pattern, '', clean_text, flags=re.IGNORECASE)
        
        # Очищаем оставшийся текст
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        if clean_text and len(clean_text) > 10:  # Минимальная длина для разумного обоснования
            return clean_text
        
        return None

# Функция для тестирования парсера
def test_2trade_parser():
    """Тестирование парсера 2Trade"""
    sample_signal = """
    PAIR: SUI
    DIRECTION: LONG
    ENTRY: $3.80 - $3.90
    TP1: $4.05
    TP2: $4.20
    TP3: $4.35
    SL: $3.50
    LEVERAGE: 10X
    
    Strong bullish momentum, expecting breakout above resistance.
    """
    
    parser = TwoTradeParser()
    
    print("🧪 Testing 2Trade Parser")
    print(f"Can parse: {parser.can_parse(sample_signal)}")
    
    if parser.can_parse(sample_signal):
        signal = parser.parse_signal(sample_signal, "2trade_test")
        
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
    test_2trade_parser()
