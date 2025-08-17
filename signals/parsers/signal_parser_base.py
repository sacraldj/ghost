"""
GHOST Signal Parser Base
Базовый класс для парсеров сигналов разных источников
На основе архитектуры системы Дарена
"""

import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class SignalDirection(Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    BUY = "BUY"
    SELL = "SELL"

@dataclass
class ParsedSignal:
    """Стандартная структура распарсенного сигнала"""
    # Базовые поля
    signal_id: str
    source: str
    trader_id: str
    raw_text: str
    timestamp: datetime
    
    # Торговые данные
    symbol: str
    direction: SignalDirection
    leverage: Optional[str] = None
    
    # Цены входа
    entry_zone: Optional[List[float]] = None
    entry_single: Optional[float] = None
    
    # Цели (TP)
    targets: List[float] = None
    tp1: Optional[float] = None
    tp2: Optional[float] = None
    tp3: Optional[float] = None
    tp4: Optional[float] = None
    
    # Стоп-лосс
    stop_loss: Optional[float] = None
    
    # Дополнительные поля
    reason: Optional[str] = None
    confidence: float = 0.0
    is_valid: bool = True
    parse_errors: List[str] = None
    
    def __post_init__(self):
        if self.targets is None:
            self.targets = []
        if self.parse_errors is None:
            self.parse_errors = []
        if self.entry_zone is None:
            self.entry_zone = []

class SignalParserBase(ABC):
    """Базовый класс для всех парсеров сигналов"""
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.logger = logging.getLogger(f"{__name__}.{source_name}")
    
    @abstractmethod
    def can_parse(self, text: str) -> bool:
        """Проверка, может ли парсер обработать данный текст"""
        pass
    
    @abstractmethod
    def parse_signal(self, text: str, trader_id: str) -> Optional[ParsedSignal]:
        """Основная функция парсинга сигнала"""
        pass
    
    def clean_text(self, text: str) -> str:
        """Очистка текста от лишних символов"""
        # Удаляем emoji и специальные символы
        text = re.sub(r'[^\w\s\.\-\+\:\$\#\/\(\)]', ' ', text)
        # Нормализуем пробелы
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def extract_symbol(self, text: str) -> Optional[str]:
        """Извлечение символа торговой пары"""
        # Паттерны для поиска символов
        patterns = [
            r'#([A-Z]{2,10})',  # #SUI, #BTC
            r'([A-Z]{2,10}USDT?)',  # SUIUSDT, BTCUSDT
            r'([A-Z]{2,10})/USDT?',  # SUI/USDT
            r'Longing\s+#([A-Z]{2,10})',  # Longing #SUI
            r'PAIR:\s*([A-Z]{2,10})',  # PAIR: SUI
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                symbol = match.group(1).upper()
                # Нормализуем к формату SYMBOL
                if symbol.endswith('USDT'):
                    symbol = symbol[:-4]
                elif symbol.endswith('USD'):
                    symbol = symbol[:-3]
                return symbol
        
        return None
    
    def extract_direction(self, text: str) -> Optional[SignalDirection]:
        """Извлечение направления сделки"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['long', 'longing', 'buy']):
            return SignalDirection.LONG
        elif any(word in text_lower for word in ['short', 'shorting', 'sell']):
            return SignalDirection.SHORT
        
        return None
    
    def extract_leverage(self, text: str) -> Optional[str]:
        """Извлечение плеча"""
        patterns = [
            r'(\d+x)\s*-\s*(\d+x)',  # 5x - 10x
            r'(\d+x)',  # 10x
            r'leverage:?\s*(\d+)',  # leverage: 10
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    def extract_prices(self, text: str, keywords: List[str]) -> List[float]:
        """Извлечение цен по ключевым словам"""
        prices = []
        
        for keyword in keywords:
            # Ищем паттерн: keyword: $price или keyword $price
            pattern = f'{keyword}:?\\s*\\$?([0-9]+\\.?[0-9]*)'
            matches = re.findall(pattern, text, re.IGNORECASE)
            
            for match in matches:
                try:
                    price = float(match)
                    if price > 0:
                        prices.append(price)
                except ValueError:
                    continue
        
        return prices
    
    def extract_entry_zone(self, text: str) -> List[float]:
        """Извлечение зоны входа"""
        keywords = ['entry', 'вход']
        prices = self.extract_prices(text, keywords)
        
        # Также ищем диапазоны: $3.89 - $3.70
        range_pattern = r'\$?([0-9]+\.?[0-9]*)\s*-\s*\$?([0-9]+\.?[0-9]*)'
        ranges = re.findall(range_pattern, text)
        
        for range_match in ranges:
            try:
                price1 = float(range_match[0])
                price2 = float(range_match[1])
                if price1 > 0 and price2 > 0:
                    prices.extend([price1, price2])
            except ValueError:
                continue
        
        return sorted(set(prices))  # Убираем дубликаты и сортируем
    
    def extract_targets(self, text: str) -> List[float]:
        """Извлечение целей (TP)"""
        targets = []
        
        # Ищем отдельные цели
        tp_patterns = [
            r'(?:tp|target|цель)\s*(\d+)?:?\s*\$?([0-9]+\.?[0-9]*)',
            r'targets?:?\s*((?:\$?[0-9]+\.?[0-9]*,?\s*)+)',
        ]
        
        for pattern in tp_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) == 2:  # tp1: $4.05
                    try:
                        price = float(match[1])
                        if price > 0:
                            targets.append(price)
                    except ValueError:
                        continue
                elif len(match) == 1:  # targets: $4.05, $4.20, $4.30
                    prices_text = match[0] if isinstance(match, tuple) else match
                    price_matches = re.findall(r'\$?([0-9]+\.?[0-9]*)', prices_text)
                    for price_str in price_matches:
                        try:
                            price = float(price_str)
                            if price > 0:
                                targets.append(price)
                        except ValueError:
                            continue
        
        return targets
    
    def extract_stop_loss(self, text: str) -> Optional[float]:
        """Извлечение стоп-лосса"""
        keywords = ['stoploss', 'stop loss', 'sl', 'стоп']
        prices = self.extract_prices(text, keywords)
        
        return prices[0] if prices else None
    
    def extract_reason(self, text: str) -> Optional[str]:
        """Извлечение причины/обоснования сигнала"""
        reason_patterns = [
            r'reason:?\s*(.+?)(?:\n|target|stop|$)',
            r'обоснование:?\s*(.+?)(?:\n|цель|стоп|$)',
        ]
        
        for pattern in reason_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return None
    
    def validate_signal(self, signal: ParsedSignal) -> bool:
        """Валидация распарсенного сигнала"""
        errors = []
        
        # Проверяем обязательные поля
        if not signal.symbol:
            errors.append("Missing symbol")
        
        if not signal.direction:
            errors.append("Missing direction")
        
        if not signal.entry_zone and not signal.entry_single:
            errors.append("Missing entry price")
        
        if not signal.targets:
            errors.append("Missing targets")
        
        # Проверяем логику цен для LONG
        if signal.direction in [SignalDirection.LONG, SignalDirection.BUY]:
            entry_price = signal.entry_single or (max(signal.entry_zone) if signal.entry_zone else 0)
            
            if signal.targets and entry_price > 0:
                if signal.targets[0] <= entry_price:
                    errors.append("TP1 must be higher than entry for LONG")
            
            if signal.stop_loss and entry_price > 0:
                if signal.stop_loss >= entry_price:
                    errors.append("Stop loss must be lower than entry for LONG")
        
        # Проверяем логику цен для SHORT
        if signal.direction in [SignalDirection.SHORT, SignalDirection.SELL]:
            entry_price = signal.entry_single or (min(signal.entry_zone) if signal.entry_zone else 0)
            
            if signal.targets and entry_price > 0:
                if signal.targets[0] >= entry_price:
                    errors.append("TP1 must be lower than entry for SHORT")
            
            if signal.stop_loss and entry_price > 0:
                if signal.stop_loss <= entry_price:
                    errors.append("Stop loss must be higher than entry for SHORT")
        
        signal.parse_errors.extend(errors)
        signal.is_valid = len(errors) == 0
        
        return signal.is_valid
    
    def generate_signal_id(self, trader_id: str, symbol: str, timestamp: datetime) -> str:
        """Генерация уникального ID сигнала"""
        ts_str = timestamp.strftime("%Y%m%d_%H%M%S")
        return f"{trader_id}_{symbol}_{ts_str}"

# Вспомогательные функции
def normalize_symbol(symbol: str) -> str:
    """Нормализация символа к стандартному формату"""
    if not symbol:
        return ""
    
    symbol = symbol.upper().strip()
    
    # Убираем лишние суффиксы
    if symbol.endswith('USDT'):
        symbol = symbol[:-4]
    elif symbol.endswith('USD'):
        symbol = symbol[:-3]
    
    return symbol

def calculate_confidence(signal: ParsedSignal) -> float:
    """Расчет уверенности в парсинге"""
    confidence = 0.0
    
    # Базовые компоненты
    if signal.symbol:
        confidence += 20.0
    
    if signal.direction:
        confidence += 15.0
    
    if signal.entry_zone or signal.entry_single:
        confidence += 25.0
    
    if signal.targets:
        confidence += 20.0 + min(len(signal.targets) * 5.0, 15.0)  # Бонус за количество целей
    
    if signal.stop_loss:
        confidence += 15.0
    
    if signal.leverage:
        confidence += 5.0
    
    if signal.reason:
        confidence += 5.0
    
    # Штрафы за ошибки
    confidence -= len(signal.parse_errors) * 10.0
    
    return max(0.0, min(100.0, confidence))
