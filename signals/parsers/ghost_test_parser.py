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
        
        # Паттерны для распознавания тестовых сигналов
        self.format_patterns = [
            r'(LONG|SHORT|BUY|SELL)',  # Направление сделки
            r'(Entry|ENTRY):\s*[\$]?([0-9]+\.?[0-9]*)',  # Entry: $50000 или Entry: 50000
            r'(Target|TARGET|TP|tp)s?:?\s*[\$]?([0-9]+\.?[0-9]*)',  # Target: $55000
            r'(Stop|STOP|SL|sl):?\s*[\$]?([0-9]+\.?[0-9]*)',  # Stop: $48000
            r'([A-Z]{3,10})(USDT?|USD)',  # BTCUSDT, ETHUSDT и т.д.
            r'#[A-Z]{3,10}',  # #BTC, #ETH и т.д.
            r'([0-9]+)x',  # Leverage: 10x, 15x и т.д.
        ]
        
        # Ключевые слова для дополнительного распознавания
        self.ghost_keywords = [
            'ghost',
            'test',
            'signal',
            'entry',
            'target',
            'stop',
            'long',
            'short',
            'leverage',
            'btc',
            'eth',
            'usdt'
        ]
        
        # Список популярных торговых пар
        self.common_symbols = [
            'BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT',
            'BNBUSDT', 'XRPUSDT', 'LTCUSDT', 'BCHUSDT', 'EOSUSDT',
            'TRXUSDT', 'XLMUSDT', 'ATOMUSDT', 'VETUSDT', 'FILUSDT',
            'UNIUSDT', 'AVAXUSDT', 'MATICUSDT', 'ALGOUSDT', 'DOGEUSDT'
        ]
    
    def can_parse(self, text: str) -> bool:
        """Проверка, подходит ли текст для этого парсера"""
        if not text:
            return False
            
        text_clean = self.clean_text(text).upper()
        
        # Проверяем основные паттерны
        matched_patterns = 0
        for pattern in self.format_patterns:
            if re.search(pattern, text_clean, re.IGNORECASE):
                matched_patterns += 1
        
        # Проверяем ключевые слова
        keyword_matches = sum(1 for keyword in self.ghost_keywords 
                             if keyword.upper() in text_clean)
        
        # Проверяем наличие торговых пар
        symbol_matches = sum(1 for symbol in self.common_symbols 
                           if symbol in text_clean)
        
        # Если найдено достаточно совпадений
        return (matched_patterns >= 2 or 
                keyword_matches >= 2 or 
                symbol_matches >= 1)
    
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
                if base in ['BTC', 'ETH', 'ADA', 'DOT', 'LINK', 'BNB', 'XRP', 'LTC', 'BCH', 'EOS', 'TRX', 'XLM', 'ATOM', 'VET', 'FIL', 'UNI', 'AVAX', 'MATIC', 'ALGO', 'DOGE']:
                    return f"{base}USDT"
        
        return None
    
    def extract_direction_ghost(self, text: str) -> Optional[SignalDirection]:
        """Извлекает направление сделки"""
        text_upper = text.upper()
        
        if re.search(r'\b(LONG|BUY)\b', text_upper):
            return SignalDirection.LONG
        elif re.search(r'\b(SHORT|SELL)\b', text_upper):
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
        
        # Паттерны для целей
        target_patterns = [
            r'(?:TARGET|Target|target)\s*[12345]?:?\s*\$?([0-9]+\.?[0-9]*)',
            r'(?:TP|tp)\s*[12345]?:?\s*\$?([0-9]+\.?[0-9]*)',
            r'(?:Targets?|TARGETS?):\s*([0-9,.\s\$]+)',  # Targets: 52000, 54000
        ]
        
        for pattern in target_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if ',' in match:  # Несколько целей через запятую
                    for price_str in match.split(','):
                        try:
                            price = float(price_str.strip().replace('$', ''))
                            if price > 0:
                                targets.append(price)
                        except (ValueError, TypeError):
                            continue
                else:
                    try:
                        price = float(match.strip().replace('$', ''))
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
