"""
GHOST Whales Crypto Guide Parser
Специализированный парсер для канала @Whalesguide
"""

import re
import logging
from datetime import datetime
from typing import Optional, List
from .signal_parser_base import SignalParserBase, ParsedSignal, SignalDirection, calculate_confidence

logger = logging.getLogger(__name__)

class WhalesCryptoParser(SignalParserBase):
    """Специализированный парсер для канала Whales Crypto Guide"""
    
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
        keyword_matches = sum(1 for keyword in self.whales_keywords if keyword in text_clean)
        
        # Если найдено 2+ паттернов или 1+ ключевых слов
        return matched_patterns >= 2 or keyword_matches >= 1
    
    def parse_signal(self, text: str, trader_id: str) -> Optional[ParsedSignal]:
        """Основная функция парсинга сигнала Whales Crypto"""
        try:
            text_clean = self.clean_text(text)
            timestamp = datetime.now()
            
            # Извлекаем основные компоненты
            symbol = self.extract_symbol_whales(text_clean)
            if not symbol:
                self.logger.warning("Could not extract symbol from Whales text")
                return None
            
            direction = self.extract_direction_whales(text_clean)
            if not direction:
                self.logger.warning("Could not extract direction from Whales text")
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
                signal.tp1 = signal.targets[0] if len(signal.targets) > 0 else None
                signal.tp2 = signal.targets[1] if len(signal.targets) > 1 else None
                signal.tp3 = signal.targets[2] if len(signal.targets) > 2 else None
                signal.tp4 = signal.targets[3] if len(signal.targets) > 3 else None
            
            # Рассчитываем уверенность
            signal.confidence = self.calculate_confidence_whales(signal, text_clean)
            
            # Валидация
            signal.is_valid = self.validate_whales_signal(signal)
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error parsing Whales signal: {e}")
            return None
    
    def extract_symbol_whales(self, text: str) -> Optional[str]:
        """Извлечение символа из формата Whales"""
        # Паттерны для Whales формата
        patterns = [
            r'Longing\s+#([A-Z]{2,10})',  # Longing #SWARMS
            r'Buying\s+#([A-Z]{2,10})',   # Buying #ETH
            r'#([A-Z]{2,10})\s+Here',     # #SUI Here
            r'#([A-Z]{2,10}USDT?)',       # #BTCUSDT
            r'([A-Z]{2,10})/USDT',        # BTC/USDT
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                symbol = match.group(1).upper()
                # Нормализуем символ
                if symbol.endswith('USDT'):
                    symbol = symbol[:-4]
                elif symbol.endswith('USD'):
                    symbol = symbol[:-3]
                return symbol
        
        return None
    
    def extract_direction_whales(self, text: str) -> Optional[SignalDirection]:
        """Извлечение направления из формата Whales"""
        text_lower = text.lower()
        
        # Whales специфичные паттерны
        if any(word in text_lower for word in ['longing', 'long', 'buying', 'buy']):
            return SignalDirection.BUY
        elif any(word in text_lower for word in ['shorting', 'short', 'selling', 'sell']):
            return SignalDirection.SELL
        
        return None
    
    def extract_entry_zone_whales(self, text: str) -> List[float]:
        """Извлечение зоны входа из формата Whales"""
        entry_zone = []
        
        # Паттерны для входа Whales
        patterns = [
            r'Entry:\s*\$([0-9\.]+)\s*-\s*\$([0-9\.]+)',  # Entry: $0.02569 - $0.02400
            r'Entry:\s*([0-9\.]+)\s*-\s*([0-9\.]+)',      # Entry: 2800-2850
            r'Entry:\s*\$?([0-9\.]+)',                    # Entry: $45000
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:  # Диапазон
                    entry_zone.extend([float(match.group(1)), float(match.group(2))])
                else:  # Одиночная цена
                    entry_zone.append(float(match.group(1)))
                break
        
        return entry_zone
    
    def extract_targets_whales(self, text: str) -> List[float]:
        """Извлечение целей из формата Whales"""
        targets = []
        
        # Паттерн для целей Whales
        targets_match = re.search(r'Targets:\s*(.+)', text, re.IGNORECASE)
        if targets_match:
            targets_text = targets_match.group(1)
            
            # Извлекаем все числа из строки целей
            price_matches = re.findall(r'\$?([0-9]+\.?[0-9]*)', targets_text)
            for price_str in price_matches:
                try:
                    price = float(price_str)
                    targets.append(price)
                except ValueError:
                    continue
        
        return targets
    
    def extract_stop_loss_whales(self, text: str) -> Optional[float]:
        """Извлечение стоп-лосса из формата Whales"""
        patterns = [
            r'Stoploss:\s*\$([0-9\.]+)',  # Stoploss: $0.02260
            r'Stop\s*Loss:\s*\$?([0-9\.]+)',  # Stop Loss: 43000
            r'SL:\s*\$?([0-9\.]+)',       # SL: 2750
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1))
        
        return None
    
    def extract_leverage_whales(self, text: str) -> Optional[str]:
        """Извлечение плеча из формата Whales"""
        patterns = [
            r'Long\s*\(([0-9x\s\-]+)\)',  # Long (5x - 10x)
            r'([0-9]+)x\s+leverage',      # 4x leverage
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                leverage_text = match.group(1)
                # Извлекаем максимальное значение плеча
                numbers = re.findall(r'([0-9]+)', leverage_text)
                if numbers:
                    max_leverage = max(int(num) for num in numbers)
                    return f"{max_leverage}x"
        
        return None
    
    def extract_reason_whales(self, text: str) -> Optional[str]:
        """Извлечение обоснования из формата Whales"""
        reason_match = re.search(r'Reason:\s*(.+)', text, re.IGNORECASE)
        if reason_match:
            return reason_match.group(1).strip()
        
        return None
    
    def calculate_confidence_whales(self, signal: ParsedSignal, text: str) -> float:
        """Расчет уверенности для Whales сигнала"""
        confidence = 0.5  # Базовая уверенность
        
        # Бонусы за наличие компонентов
        if signal.entry_zone:
            confidence += 0.2
        if signal.targets and len(signal.targets) >= 2:
            confidence += 0.2
        if signal.stop_loss:
            confidence += 0.15
        if signal.leverage:
            confidence += 0.1
        if signal.reason:
            confidence += 0.1
        
        # Проверка логичности цен
        if signal.entry_zone and signal.targets:
            avg_entry = sum(signal.entry_zone) / len(signal.entry_zone)
            if signal.direction == SignalDirection.BUY:
                if all(target > avg_entry for target in signal.targets):
                    confidence += 0.1
            else:
                if all(target < avg_entry for target in signal.targets):
                    confidence += 0.1
        
        return min(confidence, 1.0)
    
    def validate_whales_signal(self, signal: ParsedSignal) -> bool:
        """Валидация Whales сигнала"""
        # Обязательные поля
        if not all([signal.symbol, signal.direction]):
            return False
        
        # Должна быть хотя бы цена входа или цели
        if not signal.entry_zone and not signal.targets:
            return False
        
        # Проверка логичности цен
        if signal.entry_zone and signal.stop_loss:
            avg_entry = sum(signal.entry_zone) / len(signal.entry_zone)
            if signal.direction == SignalDirection.BUY:
                if signal.stop_loss >= avg_entry:  # SL должен быть ниже входа для LONG
                    return False
            else:
                if signal.stop_loss <= avg_entry:  # SL должен быть выше входа для SHORT
                    return False
        
        return True
