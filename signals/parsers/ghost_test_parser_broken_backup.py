"""
GHOST Test Signal Parser
Специализированный парсер для тестового канала @ghostsignaltest
Парсит сигналы и сохраняет их в таблицу v_trades
"""

import re
import logging
from datetime import datetime
from typing import Optional, List
from .signal_parser_base import SignalParserBase, ParsedSignal, SignalDirection, calculate_confidence
import sys
import os

# Добавляем путь для импорта config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.crypto_symbols_database import get_crypto_symbols_db

logger = logging.getLogger(__name__)

class GhostTestParser(SignalParserBase):
    """Специализированный парсер для тестового канала Ghost Signal Test"""
    
    def __init__(self):
        super().__init__("ghost_signal_test")
        
        # Инициализируем базу символов
        self.crypto_db = get_crypto_symbols_db()
        
        # Паттерны для распознавания тестовых сигналов (на основе реального формата)
        self.format_patterns = [
            r'(LONG|SHORT|BUY|SELL|Longing|Shorting)',  # Направление сделки
            r'(Entry|ENTRY):\s*[\$]?([0-9,]+\.?[0-9]*)',  # Entry: $50000
            r'(Target|TARGET|TP|tp)s?:?\s*[\$]?([0-9,]+\.?[0-9]*)',  # Targets
            r'(Stop|STOP|SL|sl|Stop-loss):?\s*[\$]?([0-9,]+\.?[0-9]*)',  # Stop-loss
            r'([A-Z]{2,10})(USDT?|USD|USDC)?',  # BTCUSDT, APT и т.д.
            r'#([A-Z]{2,10})',  # #BTC, #APT и т.д.
            r'([0-9]+)x',  # Leverage: 10x, 15x и т.д.
            r'TEST.*SIGNAL',  # TEST - SIGNAL
            r'Forwarded from',  # Forwarded from канал
            r'(Short|Long)\s*\([0-9x\-\s]+\)',  # Short (5x-10x)
        ]
        
        # Ключевые слова для дополнительного распознавания
        self.ghost_keywords = [
            'test', 'signal', 'forwarded from', 'shorting', 'longing',
            'entry', 'targets', 'stop-loss', 'short (', 'long (',
            'leverage', 'whales crypto guide', 'here', 'reason',
            'testing', 'now', 'crypto'
        ]
    
    def can_parse(self, text: str) -> bool:
        """Проверка, подходит ли текст для этого парсера (СТРОГАЯ фильтрация)"""
        if not text or len(text.strip()) < 10:
            return False
            
        text_clean = self.clean_text(text).upper()
        
        # ОБЯЗАТЕЛЬНЫЕ критерии для сигнала
        has_direction = bool(re.search(r'\b(LONG|SHORT|BUY|SELL|LONGING|SHORTING)\b', text_clean))
        
        # Проверяем наличие символа через новую систему
        detected_symbol = self.extract_symbol_ghost(text_clean)
        has_symbol = detected_symbol is not None
        
        has_price = bool(re.search(r'(ENTRY|TARGET|TP|STOP|SL).*\$?[0-9,]+\.?[0-9]*', text_clean, re.IGNORECASE))
        
        # ИСКЛЮЧАЕМ очевидно НЕ сигналы
        exclude_phrases = [
            'ОК', 'ХОРОШО', 'ПОНЯТНО', 'СПАСИБО', 'ДА', 'НЕТ', 
            'ПРИВЕТ', 'ПОКА', 'КАК ДЕЛА', 'ЧТО ТАМ',
            'ВСЕ ЛИ ВЕРНО', 'ВНЕСЛОСЬ ЛИ', 'СМОТРИМ ТАБЛИЦУ',
            'ТЕСТ', 'ПРОВЕРКА', 'АДМИН', 'СЮДА ПИСАТЬ'
        ]
        
        for phrase in exclude_phrases:
            if phrase in text_clean and len(text_clean) < 50:
                return False
        
        # Сигнал должен иметь ВСЕ обязательные элементы
        is_signal = has_direction and has_symbol and has_price
        
        # Дополнительная проверка на минимальную длину для сигналов
        if is_signal and len(text_clean) < 30:
            return False
            
        return is_signal
    
    def parse_signal(self, text: str, trader_id: str) -> Optional[ParsedSignal]:
        """Основная функция парсинга тестового сигнала"""
        try:
            text_clean = self.clean_text(text)
            timestamp = datetime.now()
            
            # Извлекаем основные компоненты
            symbol = self.extract_symbol_ghost(text_clean)
            if not symbol:
                logger.warning("Could not extract symbol from Ghost test text")
                return None
            
            direction = self.extract_direction_ghost(text_clean)
            if not direction:
                logger.warning("Could not extract direction from Ghost test text")
                return None
            
            # Извлекаем цены
            entry_prices = self.extract_entry_prices_ghost(text_clean)
            targets = self.extract_targets_ghost(text_clean)
            stop_loss = self.extract_stop_loss_ghost(text_clean)
            leverage = self.extract_leverage_ghost(text_clean)
            
            # Проверяем логику сигнала перед созданием
            is_valid, validation_errors = self._validate_signal_logic(direction, entry_prices, targets, stop_loss)
            
            # Создаем объект сигнала
            signal = ParsedSignal(
                signal_id=self.generate_signal_id(trader_id, symbol, timestamp),
                source=self.source_name,
                trader_id=trader_id,
                raw_text=text,
                timestamp=timestamp,
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
                confidence=0.1 if not is_valid else self.calculate_confidence_ghost(text_clean, symbol, direction, entry_prices, targets, stop_loss)
            )
            
            # Добавляем информацию о валидности в сигнал
            signal.is_valid = is_valid
            signal.validation_errors = validation_errors
            
            if not is_valid:
                logger.error(f"❌ INVALID_SIGNAL | {symbol} {direction.value} | {'; '.join(validation_errors)}")
                logger.warning(f"📊 Entry: {entry_prices}, Targets: {targets}, Stop: {stop_loss}")
            else:
                logger.info(f"✅ VALID_SIGNAL | {symbol} {direction.value}")
            
            logger.info(f"✅ Ghost test signal parsed: {symbol} {direction.value}")
            return signal
            
        except Exception as e:
            logger.error(f"❌ Error parsing Ghost test signal: {e}")
            return None
    
    def extract_symbol_ghost(self, text: str) -> Optional[str]:
        """Извлекает торговую пару из текста с исправлением опечаток"""
        if not text:
            return None
            
        text_upper = text.upper()
        
        # Паттерны для поиска символов
        symbol_patterns = [
            r'#([A-Z0-9]{2,15})',  # #BTC, #ETHH, #BITCOIN
            r'\$([A-Z0-9]{2,15})',  # $BTC, $ETHH
            r'([A-Z]{2,15})(USDT|USD|USDC|BTC|ETH)\b',  # BTCUSDT, ETHUSDT
            r'([A-Z]{2,15})[/\-\s](USDT|USD|USDC)\b',  # BTC/USDT, ETH-USDT
            r'\b([A-Z]{2,15})\s+(LONG|SHORT|BUY|SELL)',  # BTC LONG
            r'(LONG|SHORT|BUY|SELL)\s+([A-Z]{2,15})',  # LONG BTC
            r'\b([A-Z]{2,15})\s+signal',  # BTC signal
            r'signal\s+([A-Z]{2,15})',  # signal BTC
            r'([A-Z]{2,15})\s+now\b',  # BTC now
            r'Testing\s+#?([A-Z]{2,15})',  # Testing #BTC
        ]
        
        found_symbols = []
        
        # Ищем все потенциальные символы
        for pattern in symbol_patterns:
            matches = re.finditer(pattern, text_upper)
            for match in matches:
                # Берем либо первую, либо вторую группу в зависимости от паттерна
                if len(match.groups()) >= 2:
                    # Для паттернов с двумя группами берем правильную
                    if match.group(1) in ['LONG', 'SHORT', 'BUY', 'SELL']:
                        candidate = match.group(2)
                    else:
                        candidate = match.group(1)
                else:
                    candidate = match.group(1)
                
                if candidate and len(candidate) >= 2:
                    found_symbols.append(candidate)
        
        # Также ищем известные названия криптовалют в тексте
        words = text_upper.split()
        for word in words:
            # Очищаем от знаков препинания
            clean_word = ''.join(c for c in word if c.isalnum())
            if len(clean_word) >= 2:
                found_symbols.append(clean_word)
        
        # Обрабатываем найденные символы
        for raw_symbol in found_symbols:
            # Пробуем нормализовать через базу символов
            normalized = self.crypto_db.normalize_symbol(raw_symbol)
            if normalized:
                logger.info(f"💡 Symbol normalized: '{raw_symbol}' → '{normalized}'")
                return normalized
        
        # Если ничего не найдено, пробуем с более агрессивным поиском
        for raw_symbol in found_symbols:
            suggestions = self.crypto_db.get_suggestions(raw_symbol, limit=1)
            if suggestions:
                suggestion = suggestions[0]
                logger.info(f"🔧 Symbol suggestion: '{raw_symbol}' → '{suggestion}' (auto-corrected)")
                return suggestion
        
        return None
    
    def extract_direction_ghost(self, text: str) -> Optional[SignalDirection]:
        """Извлекает направление сделки"""
        text_upper = text.upper()
        
        # Проверяем разные варианты формата
        if re.search(r'\b(LONGING|LONG|BUY)\b', text_upper):
            return SignalDirection.LONG
        elif re.search(r'\b(SHORTING|SHORT|SELL)\b', text_upper):
            return SignalDirection.SHORT
        
        return None
    
    def extract_entry_prices_ghost(self, text: str) -> List[float]:
        """Извлекает цены входа с сохранением точности записи"""
        prices = []
        entry_patterns = [
            r'(?:ENTRY|Entry|entry):\s*\$?([0-9,]+\.?[0-9]*)',
            r'(?:ENTRY|Entry|entry)\s*@\s*\$?([0-9,]+\.?[0-9]*)',
            r'(?:ENTRY|Entry|entry)\s*\$?([0-9,]+\.?[0-9]*)',
        ]
        
        for pattern in entry_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    for price_str in match:
                        if price_str:
                            try:
                                clean_price_str = price_str.replace(',', '')
                                price = float(clean_price_str)
                                if price > 0:
                                    prices.append(price)
                            except (ValueError, TypeError):
                                continue
                        except (ValueError, TypeError):
                            continue
                else:
                    try:
                        clean_price_str = match.replace(',', '')
                        price = float(clean_price_str)
                        if price > 0:
                            prices.append(price)
                    except (ValueError, TypeError):
                        continue
        
        return sorted(set(prices))
    
    def extract_targets_ghost(self, text: str) -> List[float]:
        """Извлекает целевые цены с сохранением точности записи"""
        targets = []
        
        # Паттерны для целей с поддержкой запятых как разделителей тысяч
        target_patterns = [
            r'(?:TARGET|Target|target)\s*[12345]?:?\s*\$?([0-9,]+\.?[0-9]*)',
            r'(?:TP|tp)\s*[12345]?:?\s*\$?([0-9,]+\.?[0-9]*)',
            r'(?:Targets?|TARGETS?):\s*(.+?)(?=\n|Stop|$)',  # Захватываем всю строку с целями до Stop или конца
        ]
        
        for pattern in target_patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
            for match in matches:
                # Ищем все цены в найденной строке с поддержкой запятых
                price_parts = re.findall(r'\$?([0-9,]+\.?[0-9]*)', match)
                for price_str in price_parts:
                    try:
                        # Убираем запятые для конвертации в float
                        clean_price_str = price_str.strip().replace(',', '')
                        price = float(clean_price_str)
                        if price > 0:
                            targets.append(price)
                    except (ValueError, TypeError):
                        continue
        
        return sorted(set(targets))
    
    def extract_stop_loss_ghost(self, text: str) -> Optional[float]:
        """Извлекает стоп-лосс с сохранением точности записи"""
        stop_patterns = [
            r'(?:STOP|Stop|stop|SL|sl):\s*\$?([0-9,]+\.?[0-9]*)',
            r'(?:STOP|Stop|stop|SL|sl)\s*@\s*\$?([0-9,]+\.?[0-9]*)',
            r'(?:STOP|Stop|stop|SL|sl)\s*LOSS:?\s*\$?([0-9,]+\.?[0-9]*)',
            r'(?:Stop-loss|STOP-LOSS|stop-loss):\s*\$?([0-9,]+\.?[0-9]*)',  # Для формата "Stop-loss: $110,500"
        ]
        
        for pattern in stop_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    # Убираем запятые для конвертации в float
                    clean_price_str = match.group(1).replace(',', '')
                    return float(clean_price_str)
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def extract_entry_prices_exact(self, text: str) -> List[str]:
        """Извлекает точные строковые представления цен входа"""
        prices = []
        
        # Паттерны для цен входа с сохранением точного формата
        entry_patterns = [
            r'(?:ENTRY|Entry|entry):\s*\$?([0-9,]+\.?[0-9]*)',
            r'(?:ENTRY|Entry|entry)\s*@\s*\$?([0-9,]+\.?[0-9]*)',
            r'(?:ENTRY|Entry|entry)\s*\$?([0-9,]+\.?[0-9]*)',
            r'(?:ENTRY|Entry|entry):\s*\$?([0-9,]+\.?[0-9]*)\s*-\s*\$?([0-9,]+\.?[0-9]*)',
        ]
        
        for pattern in entry_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    for price_str in match:
                        if price_str and price_str.strip():  # Проверяем, что строка не пустая
                            prices.append(price_str.strip())
                else:
                    if match and match.strip():
                        prices.append(match.strip())
        
        return list(dict.fromkeys(prices))  # Убираем дубликаты, сохраняя порядок
    
    def extract_targets_exact(self, text: str) -> List[str]:
        """Извлекает точные строковые представления целевых цен"""
        targets = []
        
        # Паттерны для целей с сохранением точного формата
        target_patterns = [
            r'(?:TARGET|Target|target)\s*[12345]?:?\s*\$?([0-9,]+\.?[0-9]*)',
            r'(?:TP|tp)\s*[12345]?:?\s*\$?([0-9,]+\.?[0-9]*)',
            r'(?:Targets?|TARGETS?):\s*(.+?)(?=\n|Stop|$)',  # Захватываем всю строку с целями
        ]
        
        for pattern in target_patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
            for match in matches:
                # Ищем все цены в найденной строке (цифры с точкой, но без запятых-разделителей)
                price_parts = re.findall(r'\$?([0-9]+\.?[0-9]*)', match)
                for price_str in price_parts:
                    clean_str = price_str.strip()
                    # Проверяем, что строка содержит только цифры и точку
                    if clean_str and len(clean_str) > 0 and re.match(r'^[0-9]+\.?[0-9]*$', clean_str):
                        targets.append(clean_str)
        
        return list(dict.fromkeys(targets))  # Убираем дубликаты, сохраняя порядок
    
    def extract_stop_loss_exact(self, text: str) -> Optional[str]:
        """Извлекает точное строковое представление стоп-лосса"""
        stop_patterns = [
            r'(?:STOP|Stop|stop|SL|sl):\s*\$?([0-9,]+\.?[0-9]*)',
            r'(?:STOP|Stop|stop|SL|sl)\s*@\s*\$?([0-9,]+\.?[0-9]*)',
            r'(?:STOP|Stop|stop|SL|sl)\s*LOSS:?\s*\$?([0-9,]+\.?[0-9]*)',
            r'(?:Stop-loss|STOP-LOSS|stop-loss):\s*\$?([0-9,]+\.?[0-9]*)',
        ]
        
        for pattern in stop_patterns:
            match = re.search(pattern, text)
            if match:
                clean_str = match.group(1).strip()
                if clean_str:
                    return clean_str
        
        return None
    
    def extract_leverage_ghost(self, text: str) -> Optional[str]:
        """Извлекает плечо"""
        leverage_patterns = [
            r'([0-9]{1,2})x',
            r'(?:LEVERAGE|Leverage|leverage):\s*([0-9]{1,2})x?',
        ]
        
        for pattern in leverage_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return f"{match.group(1)}x"
        
        return "15x"  # По умолчанию
    
    def calculate_confidence_ghost(self, text: str, symbol: str, direction: SignalDirection, 
                                 entry_prices: List[float], targets: List[float], 
                                 stop_loss: Optional[float]) -> float:
        """Рассчитывает уверенность в парсинге"""
        confidence = 0.0
        
        # Базовая уверенность
        if symbol:
            confidence += 0.3
        if direction:
            confidence += 0.2
        if entry_prices:
            confidence += 0.2
        if targets:
            confidence += 0.2
        if stop_loss:
            confidence += 0.1
        
        # Бонус за качество данных
        if len(targets) >= 2:
            confidence += 0.1
        if len(entry_prices) >= 1:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _validate_signal_logic(self, direction: SignalDirection, entry_prices: List[float], targets: List[float], stop_loss: Optional[float]) -> tuple[bool, List[str]]:
        """Проверяет логическую корректность сигнала согласно чек-листу"""
        validation_errors = []
        
        # === 1. ТЕХНИЧЕСКИЕ ОШИБКИ ===
        
        # Проверка наличия обязательных данных
        if not entry_prices:
            validation_errors.append("TECH_ERROR: Отсутствует Entry")
            
        if not targets:
            validation_errors.append("TECH_ERROR: Отсутствуют Targets")
            
        if not stop_loss:
            validation_errors.append("TECH_ERROR: Отсутствует Stop-loss")
            
        # Если критичных данных нет, возвращаем ошибки
        if not entry_prices or not targets:
            return False, validation_errors
            
        # Берем среднюю и минимальную/максимальную цены входа
        avg_entry = sum(entry_prices) / len(entry_prices)
        min_entry = min(entry_prices)
        max_entry = max(entry_prices)
        
        # === 2. ЛОГИЧЕСКИЕ ОШИБКИ ===
        
        if direction == SignalDirection.LONG:
            # Для LONG: все TP должны быть выше Entry
            for i, target in enumerate(targets, 1):
                if target <= avg_entry:
                    validation_errors.append(f"LOGIC_ERROR: Target {i} ({target}) ниже или равен Entry ({avg_entry:.4f}) в LONG")
                    
            # Для LONG: SL должен быть ниже Entry
            if stop_loss and stop_loss >= avg_entry:
                validation_errors.append(f"LOGIC_ERROR: Stop-loss ({stop_loss}) выше или равен Entry ({avg_entry:.4f}) в LONG")
                
            # Проверка пересечения диапазона Entry со SL
            if stop_loss and stop_loss >= min_entry:
                validation_errors.append(f"LOGIC_ERROR: Stop-loss ({stop_loss}) пересекается с диапазоном Entry ({min_entry}-{max_entry})")
                
        elif direction == SignalDirection.SHORT:
            # Для SHORT: все TP должны быть ниже Entry  
            for i, target in enumerate(targets, 1):
                if target >= avg_entry:
                    validation_errors.append(f"LOGIC_ERROR: Target {i} ({target}) выше или равен Entry ({avg_entry:.4f}) в SHORT")
            
            # Для SHORT: SL должен быть выше Entry
            if stop_loss and stop_loss <= avg_entry:
                validation_errors.append(f"LOGIC_ERROR: Stop-loss ({stop_loss}) ниже или равен Entry ({avg_entry:.4f}) в SHORT")
                
            # Проверка пересечения диапазона Entry со SL
            if stop_loss and stop_loss <= max_entry:
                validation_errors.append(f"LOGIC_ERROR: Stop-loss ({stop_loss}) пересекается с диапазоном Entry ({min_entry}-{max_entry})")
        
        # Проверка на TP/SL равные Entry (движение = 0)
        for i, target in enumerate(targets, 1):
            if target == avg_entry:
                validation_errors.append(f"LOGIC_ERROR: Target {i} ({target}) равен Entry - движение = 0")
                
        if stop_loss and stop_loss == avg_entry:
            validation_errors.append(f"LOGIC_ERROR: Stop-loss ({stop_loss}) равен Entry - движение = 0")
        
        # Проверка дубликатов TP
        unique_targets = set(targets)
        if len(unique_targets) < len(targets):
            validation_errors.append("LOGIC_ERROR: Обнаружены дублирующиеся Targets")
        
        # === 3. РЫНОЧНЫЕ ОШИБКИ ===
        
        # Проверка слишком узкого диапазона (меньше 0.1% движения)
        min_movement_percent = 0.001  # 0.1%
        
        for i, target in enumerate(targets, 1):
            movement = abs(target - avg_entry) / avg_entry
            if movement < min_movement_percent:
                validation_errors.append(f"MARKET_ERROR: Target {i} слишком близко к Entry (движение {movement*100:.2f}% < 0.1%)")
                
        if stop_loss:
            sl_movement = abs(stop_loss - avg_entry) / avg_entry
            if sl_movement < min_movement_percent:
                validation_errors.append(f"MARKET_ERROR: Stop-loss слишком близко к Entry (движение {sl_movement*100:.2f}% < 0.1%)")
        
        # === 4. ПРОВЕРКА НА РАЗУМНОСТЬ ЦЕН ===
        
        # Проверка что цены положительные и разумные
        all_prices = entry_prices + targets + ([stop_loss] if stop_loss else [])
        for price in all_prices:
            if price <= 0:
                validation_errors.append(f"TECH_ERROR: Некорректная цена: {price}")
            elif price > 1000000:  # Слишком высокая цена
                validation_errors.append(f"MARKET_ERROR: Подозрительно высокая цена: {price}")
            elif price < 0.000001:  # Слишком низкая цена
                validation_errors.append(f"MARKET_ERROR: Подозрительно низкая цена: {price}")
        
        is_valid = len(validation_errors) == 0
        return is_valid, validation_errors

# Тестирование парсера
if __name__ == "__main__":
    sample_signals = [
        """
        🚀 GHOST TEST SIGNAL
        
        Symbol: BTCUSDT
        Direction: LONG
        Entry: $50000 - $49500
        Target 1: $52000
        Target 2: $54000
        Stop Loss: $48000
        Leverage: 10x
        """,
        """
        #BTC LONG 15x
        Entry: 49800
        TP1: 51500
        TP2: 53000
        SL: 48200
        """,
        """
        ETH/USDT
        BUY @ $3200
        Targets: 3350, 3500
        Stop: 3100
        """
    ]
    
    parser = GhostTestParser()
    
    print("🧪 Testing Ghost Test Parser")
    for i, signal in enumerate(sample_signals, 1):
        print(f"\n--- Test Signal {i} ---")
        print(f"Can parse: {parser.can_parse(signal)}")
        
        if parser.can_parse(signal):
            result = parser.parse_signal(signal, "ghost_test_channel")
            if result:
                print(f"✅ Parsed: {result.symbol} {result.direction.value}")
                print(f"Entry: {result.entry_zone or result.entry_single}")
                print(f"Targets: {result.targets}")
                print(f"Stop Loss: {result.stop_loss}")
                print(f"Confidence: {result.confidence:.2f}")
            else:
                print("❌ Failed to parse")
