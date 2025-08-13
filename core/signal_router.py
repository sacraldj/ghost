"""
GHOST Signal Router
Маршрутизация сигналов по источникам и парсерам
На основе архитектуры core/signal_router.py системы Дарена
"""

import logging
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Type
from dataclasses import asdict

from signals.signal_parser_base import SignalParserBase, ParsedSignal
from signals.crypto_hub_parser import CryptoHubParser
from signals.parser_2trade import TwoTradeParser
from parser.signal_normalizer import SignalNormalizer, normalize_signal

logger = logging.getLogger(__name__)

class SignalRouter:
    """Главный маршрутизатор сигналов"""
    
    def __init__(self, db_connection_string: str = None):
        self.db_connection_string = db_connection_string
        
        # Регистрируем парсеры
        self.parsers: List[SignalParserBase] = [
            CryptoHubParser(),
            TwoTradeParser(),
        ]
        
        # Fallback парсер (наш существующий)
        self.fallback_normalizer = SignalNormalizer()
        
        # Статистика
        self.stats = {
            'total_signals': 0,
            'parsed_signals': 0,
            'failed_signals': 0,
            'by_source': {},
            'by_parser': {}
        }
        
        logger.info(f"Signal Router initialized with {len(self.parsers)} parsers")
    
    async def route_signal(self, raw_text: str, trader_id: str, source_info: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Главная функция маршрутизации сигнала
        
        Args:
            raw_text: Сырой текст сигнала
            trader_id: ID трейдера
            source_info: Дополнительная информация об источнике
            
        Returns:
            Словарь с результатом парсинга или None
        """
        try:
            self.stats['total_signals'] += 1
            
            # Очищаем текст
            clean_text = self._clean_input_text(raw_text)
            if not clean_text:
                logger.warning("Empty signal text after cleaning")
                return None
            
            logger.info(f"Routing signal from trader {trader_id}: {clean_text[:100]}...")
            
            # Пробуем каждый парсер
            for parser in self.parsers:
                try:
                    if parser.can_parse(clean_text):
                        logger.info(f"Using parser: {parser.source_name}")
                        
                        parsed_signal = parser.parse_signal(clean_text, trader_id)
                        
                        if parsed_signal and parsed_signal.is_valid:
                            # Дополняем информацией об источнике
                            if source_info:
                                parsed_signal.raw_text = raw_text  # Сохраняем оригинал
                            
                            # Конвертируем в dict для совместимости
                            result = self._convert_to_dict(parsed_signal)
                            
                            # Обновляем статистику
                            self.stats['parsed_signals'] += 1
                            self._update_parser_stats(parser.source_name, True)
                            
                            # Сохраняем в БД если нужно
                            await self._save_parsed_signal(result)
                            
                            logger.info(f"Successfully parsed signal: {parsed_signal.symbol} {parsed_signal.direction.value}")
                            return result
                        
                        else:
                            logger.warning(f"Parser {parser.source_name} failed validation")
                            
                except Exception as e:
                    logger.error(f"Error in parser {parser.source_name}: {e}")
                    continue
            
            # Если ни один парсер не сработал, пробуем fallback
            logger.info("Trying fallback normalizer...")
            try:
                fallback_result = await self._try_fallback_parser(clean_text, trader_id)
                if fallback_result:
                    self.stats['parsed_signals'] += 1
                    self._update_parser_stats('fallback_normalizer', True)
                    return fallback_result
            except Exception as e:
                logger.error(f"Fallback parser error: {e}")
            
            # Ничего не получилось
            self.stats['failed_signals'] += 1
            logger.warning(f"No parser could handle signal from {trader_id}")
            
            # Сохраняем неудачный сигнал для анализа
            await self._save_failed_signal(raw_text, trader_id, "no_parser_match")
            
            return None
            
        except Exception as e:
            logger.error(f"Error in signal routing: {e}")
            self.stats['failed_signals'] += 1
            return None
    
    def _clean_input_text(self, text: str) -> str:
        """Очистка входящего текста"""
        if not text:
            return ""
        
        # Убираем лишние пробелы и переносы
        text = text.strip()
        
        # Убираем служебные символы Telegram
        text = text.replace('\u200d', '').replace('\u200c', '')
        
        return text
    
    def _convert_to_dict(self, signal: ParsedSignal) -> Dict[str, Any]:
        """Конвертация ParsedSignal в словарь для совместимости"""
        result = asdict(signal)
        
        # Конвертируем enum в строку
        if signal.direction:
            result['direction'] = signal.direction.value
        
        # Конвертируем datetime в ISO string
        if signal.timestamp:
            result['timestamp'] = signal.timestamp.isoformat()
        
        # Добавляем дополнительные поля для совместимости с существующей системой
        result['side'] = signal.direction.value if signal.direction else None
        result['entry'] = signal.entry_single
        result['entry_type'] = 'range' if signal.entry_zone and len(signal.entry_zone) > 1 else 'limit'
        result['sl'] = signal.stop_loss
        result['posted_at'] = signal.timestamp.isoformat() if signal.timestamp else None
        result['checksum'] = self._generate_checksum(signal)
        
        return result
    
    def _generate_checksum(self, signal: ParsedSignal) -> str:
        """Генерация чексуммы для анти-дубликатов"""
        import hashlib
        
        # Создаем уникальную строку из ключевых полей
        unique_string = f"{signal.trader_id}|{signal.symbol}|{signal.direction.value if signal.direction else ''}|{signal.entry_single or 0}|{signal.timestamp.strftime('%Y-%m-%d %H:%M') if signal.timestamp else ''}"
        
        return hashlib.sha256(unique_string.encode()).hexdigest()
    
    async def _try_fallback_parser(self, text: str, trader_id: str) -> Optional[Dict[str, Any]]:
        """Попытка парсинга fallback нормализатором"""
        try:
            # Используем существующий SignalNormalizer
            normalized = normalize_signal(trader_id, text, 'standard_v1')
            
            if normalized and normalized.is_valid:
                # Конвертируем в формат совместимый с нашей системой
                result = {
                    'signal_id': f"{trader_id}_{normalized.symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    'source': 'fallback_normalizer',
                    'trader_id': trader_id,
                    'raw_text': text,
                    'timestamp': datetime.now().isoformat(),
                    'symbol': normalized.symbol,
                    'direction': normalized.side.value,
                    'side': normalized.side.value,
                    'entry': normalized.entry,
                    'entry_type': normalized.entry_type.value if normalized.entry_type else 'limit',
                    'entry_zone': [normalized.range_low, normalized.range_high] if normalized.range_low and normalized.range_high else None,
                    'targets': [tp for tp in [normalized.tp1, normalized.tp2, normalized.tp3, normalized.tp4] if tp],
                    'tp1': normalized.tp1,
                    'tp2': normalized.tp2,
                    'tp3': normalized.tp3,
                    'tp4': normalized.tp4,
                    'sl': normalized.sl,
                    'stop_loss': normalized.sl,
                    'leverage': str(normalized.leverage_hint) + 'X' if normalized.leverage_hint else None,
                    'confidence': normalized.confidence,
                    'is_valid': normalized.is_valid,
                    'parse_errors': normalized.validation_errors,
                    'posted_at': datetime.now().isoformat(),
                    'checksum': self._generate_checksum_fallback(trader_id, normalized.symbol, text)
                }
                
                logger.info(f"Fallback parser succeeded: {normalized.symbol} {normalized.side.value}")
                return result
            
        except Exception as e:
            logger.error(f"Fallback parser error: {e}")
        
        return None
    
    def _generate_checksum_fallback(self, trader_id: str, symbol: str, text: str) -> str:
        """Генерация чексуммы для fallback парсера"""
        import hashlib
        
        normalized_text = text.lower().strip()
        unique_string = f"{trader_id}|{symbol}|{normalized_text}|{datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        return hashlib.sha256(unique_string.encode()).hexdigest()
    
    def _update_parser_stats(self, parser_name: str, success: bool):
        """Обновление статистики парсеров"""
        if parser_name not in self.stats['by_parser']:
            self.stats['by_parser'][parser_name] = {'success': 0, 'failed': 0}
        
        if success:
            self.stats['by_parser'][parser_name]['success'] += 1
        else:
            self.stats['by_parser'][parser_name]['failed'] += 1
    
    async def _save_parsed_signal(self, signal_data: Dict[str, Any]):
        """Сохранение успешно распарсенного сигнала"""
        try:
            # Здесь можно сохранять в нашу БД signals_parsed
            # Пока логируем
            logger.debug(f"Saving parsed signal: {signal_data['signal_id']}")
            
            # TODO: Интеграция с Supabase для сохранения в signals_parsed
            
        except Exception as e:
            logger.error(f"Error saving parsed signal: {e}")
    
    async def _save_failed_signal(self, raw_text: str, trader_id: str, reason: str):
        """Сохранение неудачного сигнала для анализа"""
        try:
            failed_signal = {
                'trader_id': trader_id,
                'raw_text': raw_text,
                'reason': reason,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.debug(f"Saving failed signal from {trader_id}: {reason}")
            
            # TODO: Сохранение в отдельную таблицу failed_signals или логи
            
        except Exception as e:
            logger.error(f"Error saving failed signal: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики работы роутера"""
        return {
            **self.stats,
            'success_rate': (self.stats['parsed_signals'] / max(self.stats['total_signals'], 1)) * 100,
            'parsers_info': [
                {
                    'name': parser.source_name,
                    'class': parser.__class__.__name__
                }
                for parser in self.parsers
            ]
        }
    
    def add_parser(self, parser: SignalParserBase):
        """Добавление нового парсера"""
        self.parsers.append(parser)
        logger.info(f"Added parser: {parser.source_name}")
    
    def remove_parser(self, source_name: str):
        """Удаление парсера по имени"""
        self.parsers = [p for p in self.parsers if p.source_name != source_name]
        logger.info(f"Removed parser: {source_name}")

# Глобальный экземпляр роутера
signal_router: Optional[SignalRouter] = None

def get_signal_router() -> SignalRouter:
    """Получение глобального экземпляра роутера"""
    global signal_router
    if signal_router is None:
        signal_router = SignalRouter()
    return signal_router

# Convenience функция для внешнего использования
async def route_signal(raw_text: str, trader_id: str, source_info: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
    """Функция для маршрутизации сигнала (внешний интерфейс)"""
    router = get_signal_router()
    return await router.route_signal(raw_text, trader_id, source_info)

# Тестирование роутера
async def test_signal_router():
    """Тестирование роутера с разными форматами"""
    router = SignalRouter()
    
    # Тест Crypto Hub формата
    crypto_hub_signal = """
    Longing #SUI Here
    Long (5x - 10x)
    Entry: $3.89 - $3.70
    Reason: Chart looks bullish for it. Worth buying for short-mid term quick profits too.
    Targets: $4.0500, $4.2000, $4.3000, $4.4000, $4.6000, $4.8000, $5.0690
    Stoploss: $3.4997
    """
    
    # Тест 2Trade формата
    two_trade_signal = """
    PAIR: BTC
    DIRECTION: LONG
    ENTRY: $43000 - $43500
    TP1: $45000
    TP2: $46500
    TP3: $48000
    SL: $41500
    LEVERAGE: 10X
    
    Strong bullish momentum expected.
    """
    
    print("🧪 Testing Signal Router")
    
    # Тест 1
    print("\n1. Testing Crypto Hub signal:")
    result1 = await router.route_signal(crypto_hub_signal, "crypto_hub_test")
    if result1:
        print(f"✅ Routed to: {result1['source']}")
        print(f"   Symbol: {result1['symbol']} {result1['direction']}")
    else:
        print("❌ Failed to route")
    
    # Тест 2  
    print("\n2. Testing 2Trade signal:")
    result2 = await router.route_signal(two_trade_signal, "2trade_test")
    if result2:
        print(f"✅ Routed to: {result2['source']}")
        print(f"   Symbol: {result2['symbol']} {result2['direction']}")
    else:
        print("❌ Failed to route")
    
    # Статистика
    print(f"\n📊 Router Statistics:")
    stats = router.get_statistics()
    print(f"   Total signals: {stats['total_signals']}")
    print(f"   Parsed: {stats['parsed_signals']}")
    print(f"   Success rate: {stats['success_rate']:.1f}%")
    
    return router

if __name__ == "__main__":
    asyncio.run(test_signal_router())
