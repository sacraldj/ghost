"""
GHOST Test Signal Parser
Специализированный парсер для тестового канала @ghostsignaltest
Парсит сигналы и сохраняет их в таблицу v_trades
"""

import re
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from .signal_parser_base import SignalParserBase, ParsedSignal, SignalDirection, calculate_confidence
import sys
import os

# Добавляем путь для импорта config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.crypto_symbols_database import get_crypto_symbols_db

# Импортируем image parser если доступен
try:
    from .image_parser import ImageSignalParser
    IMAGE_PARSER_AVAILABLE = True
except ImportError:
    IMAGE_PARSER_AVAILABLE = False

logger = logging.getLogger(__name__)

class GhostTestParser(SignalParserBase):
    """Специализированный парсер для тестового канала Ghost Signal Test"""
    
    def __init__(self):
        super().__init__("ghost_signal_test")
        
        # Инициализируем базу символов
        self.crypto_db = get_crypto_symbols_db()
        
        # Инициализируем image parser если доступен
        self.image_parser = None
        if IMAGE_PARSER_AVAILABLE:
            try:
                self.image_parser = ImageSignalParser()
                logger.info("✅ Image parser initialized for Ghost Test")
            except Exception as e:
                logger.warning(f"⚠️ Image parser initialization failed: {e}")
        else:
            logger.info("ℹ️ Image parser not available for Ghost Test")
        
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
    
    def can_parse(self, text: str, has_image: bool = False) -> bool:
        """Проверка, подходит ли текст/изображение для этого парсера"""
        
        # Для изображений - принимаем ВСЕ если есть хоть какой-то текст
        if has_image:
            logger.info("🖼️ Ghost Test: Detected image with text, accepting for parsing")
            return True
            
        # Для текста - используем обычную логику
        if not text or len(text.strip()) < 5:  # Понизили минимум с 10 до 5
            return False
            
        text_clean = self.clean_text(text).upper()
        
        # РАСШИРЕННЫЕ критерии для сигнала (более гибкие)
        has_direction = bool(re.search(r'\b(LONG|SHORT|BUY|SELL|LONGING|SHORTING)\b', text_clean))
        
        # Проверяем наличие символа через новую систему
        detected_symbol = self.extract_symbol_ghost(text_clean)
        has_symbol = detected_symbol is not None
        
        has_price = bool(re.search(r'(ENTRY|TARGET|TP|STOP|SL).*\$?[0-9,]+\.?[0-9]*', text_clean, re.IGNORECASE))
        
        # Дополнительные паттерны для более гибкого парсинга
        has_crypto_mention = bool(re.search(r'(ЗАПАМПИЛИ|РОСТ|ПАМП|DUMP|MOON|BREAKOUT)', text_clean))
        has_percentage = bool(re.search(r'\+?\d+%', text_clean))
        
        # ИСКЛЮЧАЕМ очевидно НЕ сигналы
        exclude_phrases = [
            'ОК', 'ХОРОШО', 'ПОНЯТНО', 'СПАСИБО', 'ДА', 'НЕТ', 
            'ПРИВЕТ', 'ПОКА', 'КАК ДЕЛА', 'ЧТО ТАМ'
        ]
        
        for phrase in exclude_phrases:
            if phrase in text_clean and len(text_clean) < 30:  # Уменьшили с 50 до 30
                return False
        
        # ГИБКАЯ логика: сигнал если есть ХОТЯ БЫ 2 из критериев
        criteria_met = sum([
            has_direction,
            has_symbol, 
            has_price,
            has_crypto_mention,
            has_percentage
        ])
        
        is_signal = criteria_met >= 2 or (has_direction and has_symbol)
        
        # Минимальная длина для сигналов
        if is_signal and len(text_clean) < 15:  # Понизили с 30 до 15
            return False
            
        return is_signal
    
    def parse_signal(self, text: str, trader_id: str, image_data: Optional[bytes] = None, image_format: str = "PNG") -> Optional[ParsedSignal]:
        """Основная функция парсинга тестового сигнала (текст + изображения)"""
        try:
            timestamp = datetime.now()
            
            # Сначала пробуем парсить изображение если есть
            image_signal_data = None
            if image_data and self.image_parser:
                try:
                    logger.info("🖼️ Attempting to parse image signal...")
                    # Для совместимости пока делаем синхронно - создаем простую заглушку
                    image_signal_data = self._parse_image_signal_sync(image_data, image_format, text)
                    if image_signal_data:
                        logger.info("✅ Image signal data extracted successfully")
                except Exception as e:
                    logger.warning(f"⚠️ Image parsing failed: {e}")
            
            # Парсим текстовую часть
            text_clean = self.clean_text(text)
            
            # Извлекаем основные компоненты из текста
            symbol = self.extract_symbol_ghost(text_clean)
            direction = self.extract_direction_ghost(text_clean)
            entry_prices = self.extract_entry_prices_ghost(text_clean)
            targets = self.extract_targets_ghost(text_clean)
            stop_loss = self.extract_stop_loss_ghost(text_clean)
            leverage = self.extract_leverage_ghost(text_clean)
            
            # Если из текста ничего не извлекли - пробуем взять из изображения
            if image_signal_data:
                symbol = symbol or image_signal_data.get('symbol')
                if not direction and image_signal_data.get('direction'):
                    direction_str = image_signal_data.get('direction', '').upper()
                    if 'LONG' in direction_str or 'BUY' in direction_str:
                        direction = SignalDirection.LONG
                    elif 'SHORT' in direction_str or 'SELL' in direction_str:
                        direction = SignalDirection.SHORT
                
                entry_prices = entry_prices or image_signal_data.get('entry_prices', [])
                targets = targets or image_signal_data.get('targets', [])
                stop_loss = stop_loss or image_signal_data.get('stop_loss')
                leverage = leverage or image_signal_data.get('leverage', '10x')
            
            # Если все еще нет символа или направления - создаем "универсальный" сигнал
            if not symbol:
                # Пробуем найти любое упоминание криптовалюты
                crypto_mentions = re.findall(r'#?([A-Z]{2,10})', text_clean.upper())
                symbol = crypto_mentions[0] if crypto_mentions else "TEST"
                if symbol != "TEST":
                    symbol = self.crypto_db.normalize_symbol(symbol) or f"{symbol}USDT"
                    
            if not direction:
                # Определяем направление по ключевым словам
                if re.search(r'(ЗАПАМПИЛИ|РОСТ|UP|\+\d+%|PUMP|MOON)', text_clean.upper()):
                    direction = SignalDirection.LONG
                elif re.search(r'(DUMP|DOWN|FALL|SHORT)', text_clean.upper()):
                    direction = SignalDirection.SHORT
                else:
                    direction = SignalDirection.LONG  # По умолчанию
            
            # Если нет цен - создаем тестовые
            if not entry_prices and not targets and not stop_loss:
                logger.info("📝 Creating test signal with mock prices for Ghost Test")
                entry_prices = [100.0]  # Тестовая цена входа
                targets = [110.0, 120.0]  # Тестовые цели
                stop_loss = 90.0  # Тестовый стоп-лосс
                
                # Корректируем для SHORT
                if direction == SignalDirection.SHORT:
                    targets = [90.0, 80.0]
                    stop_loss = 110.0
            
            # Проверяем логику сигнала
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
            
            # Помечаем если был использован image parser
            if image_signal_data:
                signal.parse_method = "text_image_hybrid"
            
            signal_type = "IMAGE+TEXT" if image_data else "TEXT"
            if not is_valid:
                logger.error(f"❌ INVALID_SIGNAL ({signal_type}) | {symbol} {direction.value} | {'; '.join(validation_errors)}")
            else:
                logger.info(f"✅ VALID_SIGNAL ({signal_type}) | {symbol} {direction.value}")
            
            logger.info(f"✅ Ghost test signal parsed: {symbol} {direction.value} ({signal_type})")
            return signal
            
        except Exception as e:
            logger.error(f"❌ Error parsing Ghost test signal: {e}")
            return None
    
    def _parse_image_signal_sync(self, image_data: bytes, image_format: str, caption: str = "") -> Optional[Dict[str, Any]]:
        """Синхронный парсинг изображения (базовая версия)"""
        if not self.image_parser:
            return None
            
        try:
            # Простая заглушка для изображений - извлекаем базовую информацию
            # В будущем можно добавить OCR или другие методы
            result = {
                'symbol': None,
                'direction': None,  
                'entry_prices': [],
                'targets': [],
                'stop_loss': None,
                'leverage': None,
                'confidence': 0.5,
                'parse_method': 'image_basic',
                'has_image': True
            }
            
            # Если есть caption (подпись к изображению) - пробуем извлечь из неё данные
            if caption and len(caption) > 10:
                caption_upper = caption.upper()
                
                # Ищем символ в подписи
                crypto_mentions = re.findall(r'#?([A-Z]{2,10})', caption_upper)
                if crypto_mentions:
                    result['symbol'] = crypto_mentions[0]
                
                # Ищем направление в подписи
                if re.search(r'\b(LONG|BUY|LONGING)\b', caption_upper):
                    result['direction'] = 'LONG'
                elif re.search(r'\b(SHORT|SELL|SHORTING)\b', caption_upper):
                    result['direction'] = 'SHORT'
                
                logger.info(f"📝 Extracted from image caption: symbol={result.get('symbol')}, direction={result.get('direction')}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in sync image parsing: {e}")
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
            # Для LONG: все TP должны быть выше Entry (для Ghost Test - только предупреждение)
            for i, target in enumerate(targets, 1):
                if target <= avg_entry:
                    logger.warning(f"⚠️ LOGIC_WARNING: Target {i} ({target}) ниже Entry ({avg_entry:.4f}) в LONG - разрешено для тестирования")
                    
            # Для LONG: SL должен быть ниже Entry (для Ghost Test - только предупреждение)
            if stop_loss and stop_loss >= avg_entry:
                logger.warning(f"⚠️ LOGIC_WARNING: Stop-loss ({stop_loss}) выше Entry ({avg_entry:.4f}) в LONG - разрешено для тестирования")
                
            # Проверка пересечения диапазона Entry со SL (для Ghost Test - только предупреждение)
            if stop_loss and stop_loss >= min_entry:
                logger.warning(f"⚠️ LOGIC_WARNING: Stop-loss ({stop_loss}) пересекается с Entry ({min_entry}-{max_entry}) - разрешено для тестирования")
                
        elif direction == SignalDirection.SHORT:
            # Для SHORT: все TP должны быть ниже Entry (для Ghost Test - только предупреждение)
            for i, target in enumerate(targets, 1):
                if target >= avg_entry:
                    logger.warning(f"⚠️ LOGIC_WARNING: Target {i} ({target}) выше Entry ({avg_entry:.4f}) в SHORT - разрешено для тестирования")
            
            # Для SHORT: SL должен быть выше Entry (для Ghost Test - только предупреждение)
            if stop_loss and stop_loss <= avg_entry:
                logger.warning(f"⚠️ LOGIC_WARNING: Stop-loss ({stop_loss}) ниже Entry ({avg_entry:.4f}) в SHORT - разрешено для тестирования")
                
            # Проверка пересечения диапазона Entry со SL (для Ghost Test - только предупреждение)
            if stop_loss and stop_loss <= max_entry:
                logger.warning(f"⚠️ LOGIC_WARNING: Stop-loss ({stop_loss}) пересекается с Entry ({min_entry}-{max_entry}) - разрешено для тестирования")
        
        # Проверка на TP/SL равные Entry (для Ghost Test - только предупреждение)
        for i, target in enumerate(targets, 1):
            if target == avg_entry:
                logger.warning(f"⚠️ LOGIC_WARNING: Target {i} ({target}) равен Entry - разрешено для тестирования")
                
        if stop_loss and stop_loss == avg_entry:
            logger.warning(f"⚠️ LOGIC_WARNING: Stop-loss ({stop_loss}) равен Entry - разрешено для тестирования")
        
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