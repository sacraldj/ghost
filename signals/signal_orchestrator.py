"""
GHOST Signal Orchestrator
Оркестратор для управления всеми специализированными парсерами сигналов
Каждый канал трейдера имеет свой специализированный парсер
"""

import asyncio
import logging
import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import asdict

# Импортируем специализированные парсеры для каждого канала
from signals.whales_crypto_parser import WhalesCryptoParser
from signals.parser_2trade import TwoTradeParser
from signals.crypto_hub_parser import CryptoHubParser
from signals.signal_parser_base import ParsedSignal

# Импортируем CryptoAttack24 парсер
try:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'telegram_parsers'))
    from cryptoattack24_parser import CryptoAttack24Parser
    CRYPTOATTACK24_AVAILABLE = True
except ImportError:
    CRYPTOATTACK24_AVAILABLE = False

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/signal_orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SignalOrchestrator:
    """Оркестратор для управления всеми специализированными парсерами сигналов"""
    
    def __init__(self):
        # Инициализируем специализированные парсеры для каждого канала трейдера
        self.parsers = {
            # Основные парсеры каналов
            'whales_guide_main': WhalesCryptoParser(),
            'whales_crypto_guide': WhalesCryptoParser(),  # Алиас
            '2trade_premium': TwoTradeParser(),
            'slivaeminfo': TwoTradeParser(),  # Алиас для 2Trade
            'crypto_hub_vip': CryptoHubParser(),
            'cryptohubvip': CryptoHubParser(),  # Алиас
        }
        
        # Добавляем CryptoAttack24 парсер если доступен
        if CRYPTOATTACK24_AVAILABLE:
            # Создаем wrapper для совместимости с SignalParserBase
            class CryptoAttack24Wrapper:
                def __init__(self):
                    self.parser = CryptoAttack24Parser()
                    self.source_name = "cryptoattack24"
                
                def can_parse(self, text: str) -> bool:
                    return self.parser._is_noise(text) == False and len(text.strip()) > 20
                
                def parse_signal(self, text: str, trader_id: str) -> Optional[ParsedSignal]:
                    result = self.parser.parse_message(text)
                    if result and result.confidence >= 0.6:
                        # Конвертируем в ParsedSignal формат
                        return self._convert_to_parsed_signal(result, trader_id, text)
                    return None
                
                def _convert_to_parsed_signal(self, ca24_signal, trader_id: str, raw_text: str) -> ParsedSignal:
                    from signals.signal_parser_base import SignalDirection
                    
                    # Определяем направление на основе действия
                    direction = SignalDirection.BUY if ca24_signal.action in ["pump", "growth"] else SignalDirection.SELL
                    
                    signal = ParsedSignal(
                        signal_id=f"{trader_id}_{int(datetime.now().timestamp())}",
                        source="cryptoattack24",
                        trader_id=trader_id,
                        raw_text=raw_text,
                        timestamp=ca24_signal.timestamp or datetime.now(),
                        symbol=ca24_signal.symbol,
                        direction=direction
                    )
                    
                    # Дополнительные поля
                    signal.confidence = ca24_signal.confidence
                    signal.reason = ca24_signal.context
                    signal.is_valid = True
                    
                    return signal
            
            self.parsers['cryptoattack24'] = CryptoAttack24Wrapper()
            logger.info("✅ CryptoAttack24 parser integrated successfully")
        
        # Локальная база данных для кеширования
        self.local_db_path = 'signals_orchestrator.db'
        
        # Статистика
        self.stats = {
            'signals_processed': 0,
            'signals_saved': 0,
            'signals_failed': 0,
            'parsers_used': {name: 0 for name in self.parsers.keys()},
            'started_at': datetime.now()
        }
        
        self.init_local_database()
        logger.info(f"Signal Orchestrator initialized with {len(self.parsers)} specialized parsers")
    
    def init_local_database(self):
        """Инициализация локальной базы данных для кеширования"""
        try:
            os.makedirs('logs', exist_ok=True)
            
            with sqlite3.connect(self.local_db_path) as conn:
                cursor = conn.cursor()
                
                # Таблица для сырых сигналов
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS signals_raw (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        trader_id TEXT NOT NULL,
                        parser_used TEXT NOT NULL,
                        raw_text TEXT NOT NULL,
                        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        success BOOLEAN NOT NULL,
                        confidence REAL,
                        metadata TEXT
                    )
                ''')
                
                # Таблица для обработанных сигналов
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS signals_parsed (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        signal_id TEXT UNIQUE NOT NULL,
                        trader_id TEXT NOT NULL,
                        parser_used TEXT NOT NULL,
                        symbol TEXT NOT NULL,
                        direction TEXT NOT NULL,
                        entry_zone TEXT,
                        targets TEXT,
                        stop_loss REAL,
                        leverage TEXT,
                        confidence REAL,
                        is_valid BOOLEAN,
                        reason TEXT,
                        raw_text TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logger.info("✅ Local database initialized")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize local database: {e}")
    
    async def process_raw_signal(self, raw_text: str, trader_id: str, source_hint: str = None) -> Optional[ParsedSignal]:
        """
        Обработка сырого текста сигнала через подходящий специализированный парсер
        
        Args:
            raw_text: Исходный текст сигнала
            trader_id: Идентификатор трейдера/канала
            source_hint: Подсказка об источнике для выбора парсера
            
        Returns:
            Обработанный сигнал или None
        """
        try:
            self.stats['signals_processed'] += 1
            
            # Определяем подходящий парсер
            best_parser = None
            best_parser_name = None
            
            # 1. Сначала пробуем по trader_id (самый точный способ)
            if trader_id in self.parsers:
                parser = self.parsers[trader_id]
                if parser.can_parse(raw_text):
                    best_parser = parser
                    best_parser_name = trader_id
            
            # 2. Если не нашли, пробуем по source_hint
            if not best_parser and source_hint and source_hint in self.parsers:
                parser = self.parsers[source_hint]
                if parser.can_parse(raw_text):
                    best_parser = parser
                    best_parser_name = source_hint
            
            # 3. Если все еще не нашли, пробуем все парсеры по порядку
            if not best_parser:
                # Приоритет: специализированные парсеры сначала
                priority_order = ['whales_guide_main', 'cryptoattack24', '2trade_premium', 'crypto_hub_vip']
                
                for parser_name in priority_order:
                    if parser_name in self.parsers:
                        parser = self.parsers[parser_name]
                        if parser.can_parse(raw_text):
                            best_parser = parser
                            best_parser_name = parser_name
                            break
                
                # Если приоритетные не сработали, пробуем остальные
                if not best_parser:
                    for parser_name, parser in self.parsers.items():
                        if parser_name not in priority_order and parser.can_parse(raw_text):
                            best_parser = parser
                            best_parser_name = parser_name
                            break
            
            if not best_parser:
                logger.warning(f"⚠️ No suitable parser found for signal from {trader_id}")
                self.stats['signals_failed'] += 1
                await self._save_raw_signal(trader_id, "none", raw_text, False, 0.0)
                return None
            
            # Парсим сигнал
            signal = best_parser.parse_signal(raw_text, trader_id)
            
            if not signal:
                logger.warning(f"⚠️ Failed to parse signal with {best_parser_name}")
                self.stats['signals_failed'] += 1
                await self._save_raw_signal(trader_id, best_parser_name, raw_text, False, 0.0)
                return None
            
            # Обновляем статистику парсера
            self.stats['parsers_used'][best_parser_name] += 1
            self.stats['signals_saved'] += 1
            
            # Сохраняем результат
            await self._save_raw_signal(trader_id, best_parser_name, raw_text, True, signal.confidence)
            await self._save_parsed_signal(signal, best_parser_name)
            
            logger.info(f"✅ Signal parsed successfully: {signal.symbol} {signal.direction.value} by {best_parser_name}")
            return signal
            
        except Exception as e:
            logger.error(f"❌ Error processing signal: {e}")
            self.stats['signals_failed'] += 1
            return None
    
    async def _save_raw_signal(self, trader_id: str, parser_used: str, raw_text: str, success: bool, confidence: float):
        """Сохранение информации о сырых сигналах"""
        try:
            with sqlite3.connect(self.local_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO signals_raw (trader_id, parser_used, raw_text, success, confidence, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (trader_id, parser_used, raw_text, success, confidence, json.dumps({
                    'text_length': len(raw_text),
                    'processed_at': datetime.now().isoformat()
                })))
                conn.commit()
        except Exception as e:
            logger.error(f"Error saving raw signal: {e}")
    
    async def _save_parsed_signal(self, signal: ParsedSignal, parser_used: str):
        """Сохранение обработанного сигнала"""
        try:
            with sqlite3.connect(self.local_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO signals_parsed 
                    (signal_id, trader_id, parser_used, symbol, direction, entry_zone, targets, 
                     stop_loss, leverage, confidence, is_valid, reason, raw_text)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    signal.signal_id,
                    signal.trader_id,
                    parser_used,
                    signal.symbol,
                    signal.direction.value,
                    json.dumps(signal.entry_zone) if signal.entry_zone else None,
                    json.dumps(signal.targets) if signal.targets else None,
                    signal.stop_loss,
                    signal.leverage,
                    signal.confidence,
                    signal.is_valid,
                    signal.reason,
                    signal.raw_text
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Error saving parsed signal: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики работы оркестратора"""
        uptime = datetime.now() - self.stats['started_at']
        
        return {
            'total_parsers': len(self.parsers),
            'available_parsers': list(self.parsers.keys()),
            'cryptoattack24_available': CRYPTOATTACK24_AVAILABLE,
            'uptime_seconds': int(uptime.total_seconds()),
            'signals_processed': self.stats['signals_processed'],
            'signals_saved': self.stats['signals_saved'],
            'signals_failed': self.stats['signals_failed'],
            'success_rate': (self.stats['signals_saved'] / max(self.stats['signals_processed'], 1)) * 100,
            'parsers_usage': self.stats['parsers_used'],
            'started_at': self.stats['started_at'].isoformat()
        }
    
    def get_parser_for_trader(self, trader_id: str) -> Optional[str]:
        """Получение рекомендуемого парсера для трейдера"""
        if trader_id in self.parsers:
            return trader_id
        
        # Поиск по алиасам
        aliases = {
            'whales_guide': 'whales_guide_main',
            'whalesguide': 'whales_guide_main',
            '2trade': '2trade_premium',
            'slivaem': 'slivaeminfo',
            'crypto_hub': 'crypto_hub_vip',
            'cryptohub': 'crypto_hub_vip',
            'cryptoattack': 'cryptoattack24'
        }
        
        for alias, real_name in aliases.items():
            if alias in trader_id.lower():
                return real_name
        
        return None
    
    async def test_all_parsers(self, test_signals: Dict[str, str]) -> Dict[str, Any]:
        """Тестирование всех парсеров с тестовыми сигналами"""
        results = {}
        
        for parser_name, parser in self.parsers.items():
            results[parser_name] = {
                'can_parse': {},
                'parse_results': {},
                'success_count': 0,
                'total_tests': 0
            }
            
            for signal_name, signal_text in test_signals.items():
                results[parser_name]['total_tests'] += 1
                
                # Тест can_parse
                can_parse = parser.can_parse(signal_text)
                results[parser_name]['can_parse'][signal_name] = can_parse
                
                if can_parse:
                    # Тест parse_signal
                    try:
                        parsed = parser.parse_signal(signal_text, f"test_{parser_name}")
                        if parsed and parsed.is_valid:
                            results[parser_name]['parse_results'][signal_name] = {
                                'success': True,
                                'symbol': parsed.symbol,
                                'direction': parsed.direction.value,
                                'confidence': parsed.confidence
                            }
                            results[parser_name]['success_count'] += 1
                        else:
                            results[parser_name]['parse_results'][signal_name] = {
                                'success': False,
                                'error': 'Invalid or failed parsing'
                            }
                    except Exception as e:
                        results[parser_name]['parse_results'][signal_name] = {
                            'success': False,
                            'error': str(e)
                        }
                else:
                    results[parser_name]['parse_results'][signal_name] = {
                        'success': False,
                        'error': 'Parser cannot handle this signal'
                    }
            
            # Рассчитываем успешность
            results[parser_name]['success_rate'] = (
                results[parser_name]['success_count'] / max(results[parser_name]['total_tests'], 1)
            ) * 100
        
        return results


# Глобальный экземпляр для использования в других модулях
_orchestrator_instance = None

def get_signal_orchestrator() -> SignalOrchestrator:
    """Получение глобального экземпляра оркестратора"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = SignalOrchestrator()
    return _orchestrator_instance
