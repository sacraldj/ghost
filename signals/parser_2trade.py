"""
GHOST 2Trade Parser
Специализированный парсер для канала 2Trade (@slivaeminfo)
"""

import re
import logging
from datetime import datetime
from typing import Optional, List
from signals.signal_parser_base import SignalParserBase, ParsedSignal, SignalDirection, calculate_confidence

logger = logging.getLogger(__name__)

class TwoTradeParser(SignalParserBase):
    """Специализированный парсер для канала 2Trade"""
    
    def __init__(self):
        super().__init__("2trade_slivaeminfo")
        
        # Паттерны для распознавания формата 2Trade
        self.format_patterns = [
            r'[A-Z]+USDT\s+(LONG|SHORT)',  # BTCUSDT LONG
            r'PAIR:\s*[A-Z]+',             # PAIR: BTC
            r'DIRECTION:\s*(LONG|SHORT)',   # DIRECTION: LONG
            r'ВХОД:\s*[0-9\-\s]+',         # ВХОД: 45000
            r'ЦЕЛИ:\s*[0-9\s]+',           # ЦЕЛИ:
            r'СТОП:\s*[0-9\.]+',           # СТОП: 43000
        ]
        
        # Ключевые слова для дополнительного распознавания
        self.trade2_keywords = [
            'вход:', 'цели:', 'стоп:',
            'pair:', 'direction:', 'entry:', 'tp1:', 'sl:',
            'leverage:', 'плечо:'
        ]
    
    def can_parse(self, text: str) -> bool:
        """Проверка, подходит ли текст для этого парсера"""
        text_clean = self.clean_text(text).lower()
        
        # Проверяем основные паттерны
        matched_patterns = 0
        for pattern in self.format_patterns:
            if re.search(pattern, text_clean, re.IGNORECASE):
                matched_patterns += 1
        
        # Проверяем ключевые слова
        keyword_matches = sum(1 for keyword in self.trade2_keywords if keyword in text_clean)
        
        # Если найдено 3+ паттернов или 2+ ключевых слов
        return matched_patterns >= 3 or keyword_matches >= 2
    
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
                signal.tp1 = signal.targets[0] if len(signal.targets) > 0 else None
                signal.tp2 = signal.targets[1] if len(signal.targets) > 1 else None
                signal.tp3 = signal.targets[2] if len(signal.targets) > 2 else None
                signal.tp4 = signal.targets[3] if len(signal.targets) > 3 else None
            
            # Рассчитываем уверенность
            signal.confidence = self.calculate_confidence_2trade(signal, text_clean)
            
            # Валидация
            signal.is_valid = self.validate_2trade_signal(signal)
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error parsing 2Trade signal: {e}")
            return None
    
    def extract_symbol_2trade(self, text: str) -> Optional[str]:
        """Извлечение символа из формата 2Trade"""
        # Паттерны для 2Trade формата
        patterns = [
            r'([A-Z]{2,10})USDT\s+(LONG|SHORT)',  # BTCUSDT LONG
            r'PAIR:\s*([A-Z]{2,10})',             # PAIR: BTC
            r'([A-Z]{2,10})/USDT',                # BTC/USDT
            r'#([A-Z]{2,10})',                    # #BTC
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
    
    def extract_direction_2trade(self, text: str) -> Optional[SignalDirection]:
        """Извлечение направления из формата 2Trade"""
        text_lower = text.lower()
        
        # 2Trade специфичные паттерны
        if any(word in text_lower for word in ['long', 'лонг', 'direction: long']):
            return SignalDirection.BUY
        elif any(word in text_lower for word in ['short', 'шорт', 'direction: short']):
            return SignalDirection.SELL
        
        return None
    
    def extract_entry_zone_2trade(self, text: str) -> List[float]:
        """Извлечение зоны входа из формата 2Trade"""
        entry_zone = []
        
        # Паттерны для входа 2Trade
        patterns = [
            r'ВХОД:\s*([0-9\-\s\.]+)',      # ВХОД: 45000
            r'ENTRY:\s*([0-9\-\s\.]+)',     # ENTRY: 43000-43500
            r'Entry:\s*\$?([0-9\-\s\.]+)',  # Entry: $43000
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entry_text = match.group(1)
                
                # Ищем диапазон или одиночную цену
                if '-' in entry_text:
                    # Диапазон
                    parts = entry_text.split('-')
                    if len(parts) == 2:
                        try:
                            entry_zone.extend([float(parts[0].strip()), float(parts[1].strip())])
                        except ValueError:
                            continue
                else:
                    # Одиночная цена
                    try:
                        price = float(entry_text.strip())
                        entry_zone.append(price)
                    except ValueError:
                        continue
                break
        
        return entry_zone
    
    def extract_targets_2trade(self, text: str) -> List[float]:
        """Извлечение целей из формата 2Trade"""
        targets = []
        
        # Ищем блок с целями после "ЦЕЛИ:" или "TP"
        lines = text.split('\n')
        in_targets_section = False
        
        for line in lines:
            line = line.strip()
            
            # Начало секции целей
            if re.match(r'(ЦЕЛИ|TP|Targets?):', line, re.IGNORECASE):
                in_targets_section = True
                # Проверяем, есть ли цены в той же строке
                numbers = re.findall(r'([0-9]+\.?[0-9]*)', line)
                for num_str in numbers:
                    try:
                        targets.append(float(num_str))
                    except ValueError:
                        continue
                continue
            
            # Если мы в секции целей и строка содержит только числа
            if in_targets_section:
                # Проверяем, не начинается ли новая секция
                if re.match(r'(СТОП|SL|Stop)', line, re.IGNORECASE):
                    break
                
                # Извлекаем числа из строки
                numbers = re.findall(r'([0-9]+\.?[0-9]*)', line)
                for num_str in numbers:
                    try:
                        price = float(num_str)
                        # Фильтруем слишком маленькие числа (вероятно, не цены)
                        if price > 0.0001:
                            targets.append(price)
                    except ValueError:
                        continue
                
                # Если строка пустая или не содержит чисел, возможно конец секции
                if not numbers and line:
                    break
        
        return targets
    
    def extract_stop_loss_2trade(self, text: str) -> Optional[float]:
        """Извлечение стоп-лосса из формата 2Trade"""
        patterns = [
            r'СТОП:\s*([0-9\.]+)',        # СТОП: 43000
            r'SL:\s*([0-9\.]+)',          # SL: 41500
            r'Stop\s*Loss:\s*([0-9\.]+)', # Stop Loss: 41500
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1))
        
        return None
    
    def extract_leverage_2trade(self, text: str) -> Optional[str]:
        """Извлечение плеча из формата 2Trade"""
        patterns = [
            r'LEVERAGE:\s*([0-9]+)X?',    # LEVERAGE: 10X
            r'ПЛЕЧО:\s*([0-9]+)X?',       # ПЛЕЧО: 10
            r'([0-9]+)x\s*leverage',      # 10x leverage
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                leverage_num = match.group(1)
                return f"{leverage_num}x"
        
        return None
    
    def extract_reason_2trade(self, text: str) -> Optional[str]:
        """Извлечение обоснования из формата 2Trade"""
        # 2Trade обычно не предоставляет подробных обоснований
        # Но можем попробовать найти комментарии
        reason_patterns = [
            r'(?:Причина|Reason|Note):\s*(.+)',
            r'(?:Комментарий|Comment):\s*(.+)',
        ]
        
        for pattern in reason_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def calculate_confidence_2trade(self, signal: ParsedSignal, text: str) -> float:
        """Расчет уверенности для 2Trade сигнала"""
        confidence = 0.6  # Базовая уверенность (2Trade обычно структурирован)
        
        # Бонусы за наличие компонентов
        if signal.entry_zone:
            confidence += 0.2
        if signal.targets and len(signal.targets) >= 2:
            confidence += 0.15
        if signal.stop_loss:
            confidence += 0.15
        if signal.leverage:
            confidence += 0.05
        
        # Проверка структурированности
        if 'ВХОД:' in text and 'СТОП:' in text:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def validate_2trade_signal(self, signal: ParsedSignal) -> bool:
        """Валидация 2Trade сигнала"""
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
