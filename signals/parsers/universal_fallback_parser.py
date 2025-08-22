#!/usr/bin/env python3
"""
УНИВЕРСАЛЬНЫЙ FALLBACK ПАРСЕР
Парсер для любых трейдеров, когда специализированный парсер не найден
"""

import logging
import re
from datetime import datetime
from typing import Optional

from signals.parsers.signal_parser_base import SignalParserBase, ParsedSignal, SignalDirection

logger = logging.getLogger(__name__)

class UniversalFallbackParser(SignalParserBase):
    """Универсальный fallback парсер для любых торговых сигналов"""
    
    def __init__(self):
        super().__init__()
        self.source_name = "universal_fallback"
        logger.info("✅ Universal Fallback Parser initialized")
    
    def can_parse(self, text: str) -> bool:
        """Проверяет может ли text быть торговым сигналом"""
        if not text or len(text.strip()) < 10:
            return False
            
        text_upper = text.upper()
        
        # Ищем символы торговых пар
        symbol_indicators = ['#', '$', 'USDT', 'USD', 'BTC', 'ETH', 'DOGE', 'ADA', 'SOL']
        has_symbol = any(indicator in text_upper for indicator in symbol_indicators)
        
        # Ищем направления
        direction_indicators = ['LONG', 'SHORT', 'BUY', 'SELL', '🚀', '🔴', 'ЛОНГ', 'ШОРТ']
        has_direction = any(indicator in text_upper for indicator in direction_indicators)
        
        # Ищем цены (числа)
        has_numbers = bool(re.search(r'\d+\.?\d*', text))
        
        # Ищем ключевые слова торговли
        trading_keywords = ['ENTRY', 'TARGET', 'TP', 'STOP', 'SL', 'LEVERAGE', 'ВХОД', 'ЦЕЛЬ', 'СТОП']
        has_trading_words = any(keyword in text_upper for keyword in trading_keywords)
        
        result = has_symbol and (has_direction or has_trading_words) and has_numbers
        
        logger.info(f"🔍 Can parse check: symbol={has_symbol}, direction={has_direction}, "
                   f"numbers={has_numbers}, trading_words={has_trading_words} -> {result}")
        
        return result
    
    def parse_signal(self, text: str, trader_id: str) -> Optional[ParsedSignal]:
        """Парсинг торгового сигнала через regex и эвристики"""
        try:
            logger.info(f"🔧 Запуск универсального парсера для {trader_id}")
            
            # Извлекаем символ
            symbol = self._extract_symbol(text)
            if not symbol:
                logger.warning("❌ Не удалось извлечь символ")
                return None
            
            # Извлекаем направление
            direction = self._extract_direction(text)
            if not direction:
                logger.warning("❌ Не удалось определить направление")
                return None
            
            # Извлекаем цены
            prices = self._extract_prices(text)
            if len(prices) < 2:
                logger.warning("❌ Недостаточно цен для анализа")
                return None
            
            # Распределяем цены на entry, targets, stop_loss
            entry_prices, targets, stop_loss = self._distribute_prices(prices, direction)
            
            # Извлекаем leverage
            leverage = self._extract_leverage(text)
            
            # Проверяем валидность
            is_valid, errors = self._validate_signal(direction, entry_prices, targets, stop_loss)
            
            # Создаем сигнал
            signal = ParsedSignal(
                signal_id=f"{trader_id}_{symbol}_{int(datetime.now().timestamp())}",
                source=self.source_name,
                trader_id=trader_id,
                raw_text=text,
                timestamp=datetime.now(),
                symbol=symbol,
                direction=direction,
                leverage=leverage,
                entry_zone=entry_prices if len(entry_prices) > 1 else None,
                entry_single=entry_prices[0] if len(entry_prices) == 1 else None,
                targets=targets,
                tp1=targets[0] if len(targets) > 0 else None,
                tp2=targets[1] if len(targets) > 1 else None,
                tp3=targets[2] if len(targets) > 2 else None,
                stop_loss=stop_loss,
                confidence=0.8 if is_valid else 0.3,
                is_valid=is_valid,
                parse_errors=errors
            )
            
            status = "✅ VALID" if is_valid else "❌ INVALID"
            logger.info(f"{status} Универсальный парсер: {symbol} {direction.value}")
            
            return signal
            
        except Exception as e:
            logger.error(f"❌ Ошибка в универсальном парсере: {e}")
            return None
    
    def _extract_symbol(self, text: str) -> Optional[str]:
        """Извлечение торгового символа"""
        # Паттерны для поиска символов
        patterns = [
            r'#(\w+USDT?)',      # #BTCUSDT, #ETHUSDT
            r'#(\w+USD)',        # #BTCUSD, #ETHUSD  
            r'#(\w+)',           # #BTC, #ETH
            r'\$(\w+)',          # $BTC, $ETH
            r'(\w+USDT?)\b',     # BTCUSDT, ETHUSDT
            r'(\w+)/USDT?',      # BTC/USDT, ETH/USDT
            r'(\w+)-USDT?',      # BTC-USDT, ETH-USDT
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                symbol = match.group(1).upper()
                
                # Нормализация символа
                if not symbol.endswith(('USDT', 'USD', 'USDC', 'BUSD')):
                    # Проверяем популярные базовые валюты
                    if symbol in ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'DOGE', 'MATIC', 'DOT', 'LINK', 'UNI']:
                        symbol += 'USDT'
                
                logger.info(f"✅ Символ найден: {symbol}")
                return symbol
        
        logger.warning("❌ Символ не найден")
        return None
    
    def _extract_direction(self, text: str) -> Optional[SignalDirection]:
        """Извлечение направления сделки"""
        text_upper = text.upper()
        
        # Ключевые слова для LONG
        long_patterns = [
            r'\bLONG\b', r'\bBUY\b', r'\bLONGING\b', r'\bЛОНГ\b', r'\bКУПИТЬ\b',
            r'🚀', r'📈', r'⬆️', r'💚', r'🟢'
        ]
        
        # Ключевые слова для SHORT  
        short_patterns = [
            r'\bSHORT\b', r'\bSELL\b', r'\bSHORTING\b', r'\bШОРТ\b', r'\bПРОДАТЬ\b',
            r'🔴', r'📉', r'⬇️', r'❤️', r'🔻'
        ]
        
        # Проверяем LONG
        for pattern in long_patterns:
            if re.search(pattern, text_upper):
                logger.info("✅ Направление: LONG")
                return SignalDirection.LONG
        
        # Проверяем SHORT
        for pattern in short_patterns:
            if re.search(pattern, text_upper):
                logger.info("✅ Направление: SHORT")
                return SignalDirection.SHORT
        
        logger.warning("❌ Направление не определено")
        return None
    
    def _extract_prices(self, text: str) -> list:
        """Извлечение всех цен из текста"""
        # Паттерн для цен с запятыми и точками
        price_patterns = [
            r'\$?[\d,]+\.?\d*',     # $45,000.50, 45000, 45,000
            r'[\d,]+\.?\d*\$?',     # 45000$, 45,000.50
        ]
        
        prices = []
        for pattern in price_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # Очищаем от символов и конвертируем
                clean_price = re.sub(r'[,$]', '', match)
                try:
                    price = float(clean_price)
                    if 0.00001 < price < 1000000:  # разумные пределы цен
                        prices.append(price)
                except ValueError:
                    continue
        
        # Удаляем дубликаты и сортируем
        prices = sorted(list(set(prices)))
        
        logger.info(f"✅ Найдено цен: {len(prices)} - {prices}")
        return prices
    
    def _distribute_prices(self, prices: list, direction: SignalDirection) -> tuple:
        """Распределение цен на entry, targets, stop_loss"""
        if len(prices) < 2:
            return [], [], None
        
        # Простая эвристика распределения
        entry_prices = []
        targets = []
        stop_loss = None
        
        if len(prices) == 2:
            # 2 цены: entry + target ИЛИ entry + stop
            entry_prices = [prices[0]]
            
            if direction == SignalDirection.LONG:
                if prices[1] > prices[0]:
                    targets = [prices[1]]  # выше = target
                else:
                    stop_loss = prices[1]  # ниже = stop
            else:  # SHORT
                if prices[1] < prices[0]:
                    targets = [prices[1]]  # ниже = target
                else:
                    stop_loss = prices[1]  # выше = stop
                    
        elif len(prices) == 3:
            # 3 цены: entry + target + stop
            entry_prices = [prices[0]]
            
            if direction == SignalDirection.LONG:
                # Для LONG: entry < target, entry > stop
                higher = [p for p in prices[1:] if p > prices[0]]
                lower = [p for p in prices[1:] if p < prices[0]]
                targets = higher
                stop_loss = lower[0] if lower else None
            else:  # SHORT
                # Для SHORT: entry > target, entry < stop
                lower = [p for p in prices[1:] if p < prices[0]]
                higher = [p for p in prices[1:] if p > prices[0]]
                targets = lower
                stop_loss = higher[0] if higher else None
                
        else:  # 4+ цены
            # Много цен: первые = entry zone, средние = targets, последняя = stop
            
            # Проверяем есть ли entry zone (близкие цены)
            if len(prices) >= 4 and abs(prices[1] - prices[0]) / prices[0] < 0.1:
                entry_prices = [prices[0], prices[1]]
                remaining = prices[2:]
            else:
                entry_prices = [prices[0]]
                remaining = prices[1:]
            
            # Последняя цена часто stop_loss
            potential_stop = remaining[-1]
            potential_targets = remaining[:-1]
            
            avg_entry = sum(entry_prices) / len(entry_prices)
            
            if direction == SignalDirection.LONG:
                targets = [p for p in potential_targets if p > avg_entry]
                if potential_stop < avg_entry:
                    stop_loss = potential_stop
            else:  # SHORT
                targets = [p for p in potential_targets if p < avg_entry]
                if potential_stop > avg_entry:
                    stop_loss = potential_stop
        
        return entry_prices, targets, stop_loss
    
    def _extract_leverage(self, text: str) -> str:
        """Извлечение плеча"""
        leverage_match = re.search(r'(\d+)x', text, re.IGNORECASE)
        
        if leverage_match:
            leverage = f"{leverage_match.group(1)}x"
            logger.info(f"✅ Leverage найден: {leverage}")
            return leverage
        
        logger.info("ℹ️ Leverage не найден, используем 15x по умолчанию")
        return "15x"
    
    def _validate_signal(self, direction: SignalDirection, entry_prices: list, 
                        targets: list, stop_loss: float) -> tuple:
        """Проверка логической корректности сигнала"""
        errors = []
        
        if not entry_prices:
            errors.append("Нет entry цен")
            
        if not targets:
            errors.append("Нет targets")
        
        if entry_prices and targets:
            avg_entry = sum(entry_prices) / len(entry_prices)
            
            if direction == SignalDirection.LONG:
                # Для LONG: targets должны быть выше entry
                invalid_targets = [t for t in targets if t <= avg_entry]
                if invalid_targets:
                    errors.append(f"Targets {invalid_targets} не выше entry {avg_entry:.2f} для LONG")
                
                # Stop loss должен быть ниже entry
                if stop_loss and stop_loss >= avg_entry:
                    errors.append(f"Stop loss {stop_loss} не ниже entry {avg_entry:.2f} для LONG")
                    
            else:  # SHORT
                # Для SHORT: targets должны быть ниже entry
                invalid_targets = [t for t in targets if t >= avg_entry]
                if invalid_targets:
                    errors.append(f"Targets {invalid_targets} не ниже entry {avg_entry:.2f} для SHORT")
                
                # Stop loss должен быть выше entry
                if stop_loss and stop_loss <= avg_entry:
                    errors.append(f"Stop loss {stop_loss} не выше entry {avg_entry:.2f} для SHORT")
        
        is_valid = len(errors) == 0
        
        if errors:
            logger.warning(f"⚠️ Ошибки валидации: {'; '.join(errors)}")
        
        return is_valid, errors
