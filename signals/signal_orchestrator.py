"""
GHOST Signal Orchestrator
Оркестратор для обработки сигналов из разных источников и сохранения в БД
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import sqlite3
from dataclasses import asdict

# Добавляем путь к корню проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from signals.signal_parser_base import ParsedSignal
from signals.whales_crypto_parser import WhalesCryptoParser
from signals.parser_2trade import TwoTradeParser
from signals.crypto_hub_parser import CryptoHubParser
from database.supabase_client import SupabaseClient

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('signal_orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SignalOrchestrator:
    """Оркестратор для управления всеми парсерами сигналов"""
    
    def __init__(self):
        # Инициализируем парсеры
        self.parsers = {
            'whales_crypto': WhalesCryptoParser(),
            'two_trade': TwoTradeParser(),
            'crypto_hub': CryptoHubParser()
        }
        
        # База данных
        self.supabase = SupabaseClient()
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
    
    def init_local_database(self):
        """Инициализация локальной базы данных"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            # Таблица для обработанных сигналов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processed_signals (
                    id INTEGER PRIMARY KEY,
                    signal_id TEXT UNIQUE,
                    source TEXT,
                    trader_id TEXT,
                    symbol TEXT,
                    direction TEXT,
                    confidence REAL,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    saved_to_supabase BOOLEAN DEFAULT FALSE,
                    error_message TEXT
                )
            ''')
            
            # Таблица для статистики парсеров
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS parser_stats (
                    id INTEGER PRIMARY KEY,
                    parser_name TEXT,
                    date DATE,
                    signals_processed INTEGER DEFAULT 0,
                    success_rate REAL DEFAULT 0.0,
                    avg_confidence REAL DEFAULT 0.0
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("✅ Local orchestrator database initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize local database: {e}")
    
    async def process_raw_signal(self, raw_text: str, source: str, trader_id: str) -> Optional[ParsedSignal]:
        """
        Обработка сырого текста сигнала через подходящий парсер
        
        Args:
            raw_text: Исходный текст сигнала
            source: Источник сигнала (whales_crypto, two_trade, etc.)
            trader_id: Идентификатор трейдера
            
        Returns:
            Обработанный сигнал или None
        """
        try:
            self.stats['signals_processed'] += 1
            
            # Пробуем найти подходящий парсер
            best_parser = None
            best_parser_name = None
            
            # Если указан конкретный источник, используем его
            if source in self.parsers:
                parser = self.parsers[source]
                if parser.can_parse(raw_text):
                    best_parser = parser
                    best_parser_name = source
            else:
                # Автоматический выбор парсера
                for parser_name, parser in self.parsers.items():
                    if parser.can_parse(raw_text):
                        best_parser = parser
                        best_parser_name = parser_name
                        break
            
            if not best_parser:
                logger.warning(f"⚠️ No suitable parser found for signal from {source}")
                self.stats['signals_failed'] += 1
                return None
            
            # Парсим сигнал
            signal = best_parser.parse_signal(raw_text, trader_id)
            
            if not signal:
                logger.warning(f"⚠️ Failed to parse signal with {best_parser_name}")
                self.stats['signals_failed'] += 1
                return None
            
            # Обновляем статистику парсера
            self.stats['parsers_used'][best_parser_name] += 1
            
            # Дополняем информацией об источнике
            signal.parser_used = best_parser_name
            signal.processed_at = datetime.now()
            
            logger.info(f"✅ Signal parsed by {best_parser_name}: {signal.symbol} {signal.direction.value}")
            
            # Сохраняем в локальную БД
            await self.save_signal_local(signal)
            
            # Сохраняем в Supabase
            saved = await self.save_signal_supabase(signal)
            
            if saved:
                self.stats['signals_saved'] += 1
                logger.info(f"💾 Signal saved to database: {signal.symbol}")
            else:
                logger.error(f"❌ Failed to save signal: {signal.symbol}")
                self.stats['signals_failed'] += 1
            
            return signal
            
        except Exception as e:
            logger.error(f"❌ Error processing signal: {e}")
            self.stats['signals_failed'] += 1
            return None
    
    async def save_signal_local(self, signal: ParsedSignal):
        """Сохранение сигнала в локальную БД"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO processed_signals 
                (signal_id, source, trader_id, symbol, direction, confidence, processed_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                signal.signal_id,
                signal.source,
                signal.trader_id,
                signal.symbol,
                signal.direction.value,
                signal.confidence,
                signal.processed_at
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving signal to local DB: {e}")
    
    async def save_signal_supabase(self, signal: ParsedSignal) -> bool:
        """Сохранение сигнала в Supabase"""
        try:
            # Подготавливаем данные для сохранения
            signal_data = {
                'trader_id': signal.trader_id,
                'symbol': signal.symbol,
                'direction': signal.direction.value,
                'entry_single': float(signal.entry_single) if signal.entry_single else None,
                'entry_min': float(min(signal.entry_zone)) if signal.entry_zone else None,
                'entry_max': float(max(signal.entry_zone)) if signal.entry_zone else None,
                'tp1': float(signal.tp1) if signal.tp1 else None,
                'tp2': float(signal.tp2) if signal.tp2 else None,
                'tp3': float(signal.tp3) if signal.tp3 else None,
                'tp4': float(signal.tp4) if signal.tp4 else None,
                'stop_loss': float(signal.stop_loss) if signal.stop_loss else None,
                'leverage': signal.leverage,
                'confidence': float(signal.confidence),
                'original_text': signal.raw_text,
                'source': signal.source,
                'timestamp': signal.timestamp.isoformat(),
                'analysis_notes': signal.reason,
                'targets': json.dumps(signal.targets) if signal.targets else None,
                'entry_zone': json.dumps(signal.entry_zone) if signal.entry_zone else None,
                'signal_quality': self.get_signal_quality(signal.confidence),
                'parser_used': getattr(signal, 'parser_used', None),
                'processed_at': getattr(signal, 'processed_at', datetime.now()).isoformat()
            }
            
            # Добавляем Telegram метаданные если есть
            if hasattr(signal, 'telegram_message_id'):
                signal_data['telegram_message_id'] = signal.telegram_message_id
            if hasattr(signal, 'telegram_channel_id'):
                signal_data['telegram_channel_id'] = signal.telegram_channel_id
            if hasattr(signal, 'source_url'):
                signal_data['source_url'] = signal.source_url
            
            # Сохраняем в Supabase
            result = self.supabase.insert_trade(signal_data)
            
            if result:
                # Обновляем локальную БД
                conn = sqlite3.connect(self.local_db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE processed_signals 
                    SET saved_to_supabase = TRUE 
                    WHERE signal_id = ?
                ''', (signal.signal_id,))
                
                conn.commit()
                conn.close()
                
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"❌ Error saving signal to Supabase: {e}")
            
            # Сохраняем ошибку в локальную БД
            try:
                conn = sqlite3.connect(self.local_db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE processed_signals 
                    SET error_message = ? 
                    WHERE signal_id = ?
                ''', (str(e), signal.signal_id))
                
                conn.commit()
                conn.close()
            except:
                pass
            
            return False
    
    def get_signal_quality(self, confidence: float) -> str:
        """Определение качества сигнала по уверенности"""
        if confidence >= 85:
            return 'excellent'
        elif confidence >= 75:
            return 'high'
        elif confidence >= 60:
            return 'medium'
        elif confidence >= 40:
            return 'low'
        else:
            return 'poor'
    
    async def batch_process_signals(self, signals_data: List[Dict]) -> List[ParsedSignal]:
        """
        Пакетная обработка сигналов
        
        Args:
            signals_data: Список словарей с данными сигналов
                         [{raw_text, source, trader_id}, ...]
        
        Returns:
            Список обработанных сигналов
        """
        processed_signals = []
        
        for signal_data in signals_data:
            try:
                signal = await self.process_raw_signal(
                    signal_data['raw_text'],
                    signal_data.get('source', ''),
                    signal_data['trader_id']
                )
                
                if signal:
                    processed_signals.append(signal)
                    
            except Exception as e:
                logger.error(f"Error in batch processing: {e}")
        
        logger.info(f"📦 Batch processed {len(processed_signals)}/{len(signals_data)} signals")
        
        return processed_signals
    
    def get_stats(self) -> Dict:
        """Получение статистики оркестратора"""
        uptime = datetime.now() - self.stats['started_at']
        
        success_rate = 0.0
        if self.stats['signals_processed'] > 0:
            success_rate = (self.stats['signals_saved'] / self.stats['signals_processed']) * 100
        
        return {
            'uptime': str(uptime),
            'signals_processed': self.stats['signals_processed'],
            'signals_saved': self.stats['signals_saved'],
            'signals_failed': self.stats['signals_failed'],
            'success_rate': round(success_rate, 2),
            'parsers_used': self.stats['parsers_used'],
            'started_at': self.stats['started_at'].isoformat()
        }
    
    def print_stats(self):
        """Вывод статистики в лог"""
        stats = self.get_stats()
        
        logger.info("📊 SIGNAL ORCHESTRATOR STATISTICS:")
        logger.info(f"   Uptime: {stats['uptime']}")
        logger.info(f"   Signals processed: {stats['signals_processed']}")
        logger.info(f"   Signals saved: {stats['signals_saved']}")
        logger.info(f"   Signals failed: {stats['signals_failed']}")
        logger.info(f"   Success rate: {stats['success_rate']}%")
        logger.info(f"   Parsers usage: {stats['parsers_used']}")

# Функция для тестирования
async def test_orchestrator():
    """Тестирование оркестратора"""
    orchestrator = SignalOrchestrator()
    
    # Тестовый сигнал Whales Crypto
    test_signal = """
    Longing #SWARMS Here

    Long (5x - 10x)

    Entry: $0.02569 - $0.02400

    Reason: Chart looks bullish for it. Worth buying for short-mid term quick profits too.

    Targets: $0.027, $0.028, $0.029, $0.03050, $0.032, $0.034, $0.036, $0.03859

    Stoploss: $0.02260
    """
    
    logger.info("🧪 Testing Signal Orchestrator")
    
    # Обрабатываем сигнал
    result = await orchestrator.process_raw_signal(
        test_signal, 
        'whales_crypto', 
        'test_trader'
    )
    
    if result:
        logger.info(f"✅ Test successful: {result.symbol} {result.direction.value}")
    else:
        logger.error("❌ Test failed")
    
    # Выводим статистику
    orchestrator.print_stats()

if __name__ == "__main__":
    asyncio.run(test_orchestrator())
