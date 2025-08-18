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

logger = logging.getLogger(__name__)

class GhostTestParser(SignalParserBase):
    """Специализированный парсер для тестового канала Ghost Signal Test"""
    
    def __init__(self):
        super().__init__("ghost_signal_test")
        
        # Паттерны для распознавания тестовых сигналов (на основе реального формата)
        self.format_patterns = [
            r'(LONG|SHORT|BUY|SELL|Longing|Shorting)',  # Направление сделки
            r'(Entry|ENTRY):\s*[\$]?([0-9]+\.?[0-9]*)',  # Entry: $50000
            r'(Target|TARGET|TP|tp)s?:?\s*[\$]?([0-9]+\.?[0-9]*)',  # Targets
            r'(Stop|STOP|SL|sl|Stop-loss):?\s*[\$]?([0-9]+\.?[0-9]*)',  # Stop-loss
            r'([A-Z]{3,10})(USDT?|USD)?',  # BTCUSDT, APT и т.д.
            r'#[A-Z]{3,10}',  # #BTC, #APT и т.д.
            r'([0-9]+)x',  # Leverage: 10x, 15x и т.д.
            r'TEST.*SIGNAL',  # TEST - SIGNAL
            r'Forwarded from',  # Forwarded from канал
            r'(Short|Long)\s*\([0-9x\-\s]+\)',  # Short (5x-10x)
        ]
        
        # Ключевые слова для дополнительного распознавания
        self.ghost_keywords = [
            'test',
            'signal', 
            'forwarded from',
            'shorting',
            'longing',
            'entry',
            'targets',
            'stop-loss',
            'short (',
            'long (',
            'leverage',
            'whales crypto guide',
            'apt',
            'btc',
            'eth',
            'here',
            'reason'
        ]
        
        # Список популярных торговых пар
        self.common_symbols = [
            'BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT',
            'BNBUSDT', 'XRPUSDT', 'LTCUSDT', 'BCHUSDT', 'EOSUSDT',
            'TRXUSDT', 'XLMUSDT', 'ATOMUSDT', 'VETUSDT', 'FILUSDT',
            'UNIUSDT', 'AVAXUSDT', 'MATICUSDT', 'ALGOUSDT', 'DOGEUSDT',
            'APTUSDT', 'SOLUSDT', 'NEARUSDT', 'FTMUSDT', 'SANDUSDT',
            'MANAUSDT', 'AXSUSDT', 'ICPUSDT', 'THETAUSDT', 'MKRUSDT'
        ]
    
    def can_parse(self, text: str) -> bool:
        """Проверка, подходит ли текст для этого парсера (СТРОГАЯ фильтрация)"""
        if not text or len(text.strip()) < 10:
            return False
            
        text_clean = self.clean_text(text).upper()
        
        # ОБЯЗАТЕЛЬНЫЕ критерии для сигнала
        has_direction = bool(re.search(r'\b(LONG|SHORT|BUY|SELL|LONGING|SHORTING)\b', text_clean))
        has_symbol = any(symbol in text_clean for symbol in self.common_symbols) or bool(re.search(r'#[A-Z]{3,10}', text_clean))
        has_price = bool(re.search(r'(ENTRY|TARGET|TP|STOP|SL).*\$?[0-9]+\.?[0-9]*', text_clean, re.IGNORECASE))
        
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
                confidence=self.calculate_confidence_ghost(text_clean, symbol, direction, entry_prices, targets, stop_loss)
            )
            
            logger.info(f"✅ Ghost test signal parsed: {symbol} {direction.value}")
            return signal
            
        except Exception as e:
            logger.error(f"❌ Error parsing Ghost test signal: {e}")
            return None
    
    def extract_symbol_ghost(self, text: str) -> Optional[str]:
        """Извлекает торговую пару из текста"""
        text_upper = text.upper()
        
        # Ищем популярные торговые пары
        for symbol in self.common_symbols:
            if symbol in text_upper:
                return symbol
        
        # Ищем паттерны вида XXXUSDT и просто символы
        symbol_patterns = [
            r'([A-Z]{3,10})(USDT|USD)',
            r'#([A-Z]{3,10})',
            r'([A-Z]{3,10})\s*/',
            r'\$([A-Z]{3,10})',
            r'\b(BTC|ETH|ADA|DOT|LINK|BNB|XRP|LTC|BCH|EOS|TRX|XLM|ATOM|VET|FIL|UNI|AVAX|MATIC|ALGO|DOGE)\b'
        ]
        
        for pattern in symbol_patterns:
            match = re.search(pattern, text_upper)
            if match:
                base = match.group(1)
                if base in ['BTC', 'ETH', 'ADA', 'DOT', 'LINK', 'BNB', 'XRP', 'LTC', 'BCH', 'EOS', 'TRX', 'XLM', 'ATOM', 'VET', 'FIL', 'UNI', 'AVAX', 'MATIC', 'ALGO', 'DOGE', 'APT', 'SOL', 'NEAR', 'FTM', 'SAND', 'MANA', 'AXS', 'ICP', 'THETA', 'MKR']:
                    return f"{base}USDT"
        
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
        """Извлекает цены входа"""
        prices = []
        
        # Паттерны для цен входа
        entry_patterns = [
            r'(?:ENTRY|Entry|entry):\s*\$?([0-9]+\.?[0-9]*)',
            r'(?:ENTRY|Entry|entry)\s*@\s*\$?([0-9]+\.?[0-9]*)',
            r'(?:ENTRY|Entry|entry)\s*\$?([0-9]+\.?[0-9]*)',
            r'(?:ENTRY|Entry|entry):\s*\$?([0-9]+\.?[0-9]*)\s*-\s*\$?([0-9]+\.?[0-9]*)',
        ]
        
        for pattern in entry_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    for price_str in match:
                        try:
                            price = float(price_str)
                            if price > 0:
                                prices.append(price)
                        except (ValueError, TypeError):
                            continue
                else:
                    try:
                        price = float(match)
                        if price > 0:
                            prices.append(price)
                    except (ValueError, TypeError):
                        continue
        
        return sorted(set(prices))
    
    def extract_targets_ghost(self, text: str) -> List[float]:
        """Извлекает целевые цены"""
        targets = []
        
        # Паттерны для целей (специально для формата со скриншота)
        target_patterns = [
            r'(?:TARGET|Target|target)\s*[12345]?:?\s*\$?([0-9]+\.?[0-9]*)',
            r'(?:TP|tp)\s*[12345]?:?\s*\$?([0-9]+\.?[0-9]*)',
            r'(?:Targets?|TARGETS?):\s*(.+?)(?=\n|Stop|$)',  # Захватываем всю строку с целями до Stop или конца
        ]
        
        for pattern in target_patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
            for match in matches:
                # Ищем все цены в найденной строке
                price_parts = re.findall(r'\$?([0-9]+\.?[0-9]*)', match)
                for price_str in price_parts:
                    try:
                        price = float(price_str.strip())
                        if price > 0:
                            targets.append(price)
                    except (ValueError, TypeError):
                        continue
        
        return sorted(set(targets))
    
    def extract_stop_loss_ghost(self, text: str) -> Optional[float]:
        """Извлекает стоп-лосс"""
        stop_patterns = [
            r'(?:STOP|Stop|stop|SL|sl):\s*\$?([0-9]+\.?[0-9]*)',
            r'(?:STOP|Stop|stop|SL|sl)\s*@\s*\$?([0-9]+\.?[0-9]*)',
            r'(?:STOP|Stop|stop|SL|sl)\s*LOSS:?\s*\$?([0-9]+\.?[0-9]*)',
            r'(?:Stop-loss|STOP-LOSS|stop-loss):\s*\$?([0-9]+\.?[0-9]*)',  # Для формата "Stop-loss: $4.75"
        ]
        
        for pattern in stop_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return float(match.group(1))
                except (ValueError, TypeError):
                    continue
        
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
