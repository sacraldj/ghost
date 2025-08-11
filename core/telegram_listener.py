#!/usr/bin/env python3
"""
GHOST Telegram Listener - Прослушивание торговых сигналов
Модуль для мониторинга торговых каналов в Telegram и извлечения сигналов

Функции:
- Подключение к множественным Telegram каналам
- Парсинг торговых сигналов в реальном времени
- Классификация и валидация сигналов
- Сохранение в базу данных и очередь обработки
- Метрики и статистика по трейдерам
"""

import asyncio
import json
import logging
import os
import re
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import yaml
import aioredis
from telethon import TelegramClient, events
from telethon.tl.types import Channel, Chat
import sqlite3
import traceback

# Добавляем путь к утилитам
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from utils.ghost_logger import log_info, log_warning, log_error
    from utils.database_manager import DatabaseManager
except ImportError as e:
    print(f"Warning: Could not import utils: {e}")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/telegram_listener.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('TelegramListener')

@dataclass
class TradingSignal:
    """Структура торгового сигнала"""
    id: str
    channel_id: str
    channel_name: str
    trader_name: str
    message_id: int
    timestamp: datetime
    
    # Основные параметры сигнала
    symbol: str
    direction: str  # LONG, SHORT
    entry_zone: List[float]  # Зона входа
    tp_levels: List[float]   # Take Profit уровни
    sl_level: float          # Stop Loss
    
    # Дополнительные данные
    leverage: Optional[int] = None
    risk_percent: Optional[float] = None
    confidence: Optional[float] = None
    
    # Мета-информация
    original_text: str = ""
    parsed_data: Dict[str, Any] = None
    validation_status: str = "pending"  # pending, valid, invalid
    validation_errors: List[str] = None
    
    # Статистика трейдера
    trader_stats: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.parsed_data is None:
            self.parsed_data = {}
        if self.validation_errors is None:
            self.validation_errors = []
        if self.trader_stats is None:
            self.trader_stats = {}

@dataclass
class ChannelConfig:
    """Конфигурация канала"""
    id: Union[str, int]
    name: str
    trader_name: str
    enabled: bool = True
    signal_patterns: List[str] = None
    parser_type: str = "default"  # default, custom_parser_name
    priority: int = 1  # 1-5, чем выше - тем важнее
    min_confidence: float = 0.7
    
    def __post_init__(self):
        if self.signal_patterns is None:
            self.signal_patterns = []

class SignalParser:
    """Базовый парсер торговых сигналов"""
    
    def __init__(self):
        # Регулярные выражения для парсинга
        self.symbol_pattern = re.compile(r'([A-Z]+/USDT|[A-Z]+USDT)', re.IGNORECASE)
        self.direction_pattern = re.compile(r'(LONG|SHORT|BUY|SELL)', re.IGNORECASE)
        self.entry_pattern = re.compile(r'(?:Entry|Вход|ENTRY)[\s:]*([0-9.,\-\s]+)', re.IGNORECASE)
        self.tp_pattern = re.compile(r'(?:TP|Take\s*Profit|Цель)[\s:]*([0-9.,\-\s]+)', re.IGNORECASE)
        self.sl_pattern = re.compile(r'(?:SL|Stop\s*Loss|Стоп)[\s:]*([0-9.,\-\s]+)', re.IGNORECASE)
        self.leverage_pattern = re.compile(r'(?:Leverage|Плечо)[\s:]*(\d+)[xXх]?', re.IGNORECASE)
    
    def parse_signal(self, text: str, channel_name: str, trader_name: str) -> Optional[Dict[str, Any]]:
        """Парсинг торгового сигнала из текста"""
        try:
            signal_data = {}
            
            # Извлечение символа
            symbol_match = self.symbol_pattern.search(text)
            if symbol_match:
                symbol = symbol_match.group(1).upper()
                # Нормализация символа
                if not symbol.endswith('USDT'):
                    symbol = symbol.replace('/', '') + 'USDT'
                signal_data['symbol'] = symbol
            else:
                return None  # Без символа сигнал невалиден
            
            # Определение направления
            direction_match = self.direction_pattern.search(text)
            if direction_match:
                direction = direction_match.group(1).upper()
                if direction in ['BUY', 'LONG']:
                    signal_data['direction'] = 'LONG'
                elif direction in ['SELL', 'SHORT']:
                    signal_data['direction'] = 'SHORT'
            else:
                return None  # Без направления сигнал невалиден
            
            # Извлечение зоны входа
            entry_match = self.entry_pattern.search(text)
            if entry_match:
                entry_text = entry_match.group(1)
                signal_data['entry_zone'] = self._parse_numbers(entry_text)
            
            # Извлечение TP уровней
            tp_matches = self.tp_pattern.findall(text)
            if tp_matches:
                tp_levels = []
                for tp_text in tp_matches:
                    tp_levels.extend(self._parse_numbers(tp_text))
                signal_data['tp_levels'] = tp_levels
            
            # Извлечение SL
            sl_match = self.sl_pattern.search(text)
            if sl_match:
                sl_numbers = self._parse_numbers(sl_match.group(1))
                if sl_numbers:
                    signal_data['sl_level'] = sl_numbers[0]
            
            # Извлечение плеча
            leverage_match = self.leverage_pattern.search(text)
            if leverage_match:
                signal_data['leverage'] = int(leverage_match.group(1))
            
            # Расчёт уверенности на основе полноты данных
            confidence = self._calculate_confidence(signal_data)
            signal_data['confidence'] = confidence
            
            return signal_data if confidence >= 0.5 else None
            
        except Exception as e:
            logger.error(f"Error parsing signal: {e}")
            return None
    
    def _parse_numbers(self, text: str) -> List[float]:
        """Извлечение чисел из текста"""
        numbers = []
        # Удаляем лишние символы и разделяем
        clean_text = re.sub(r'[^\d.,\-\s]', ' ', text)
        
        for num_str in clean_text.split():
            try:
                # Обработка различных форматов чисел
                num_str = num_str.replace(',', '.')
                if '-' in num_str and num_str.count('-') == 1:
                    # Диапазон чисел (например, 1.5-1.6)
                    parts = num_str.split('-')
                    if len(parts) == 2:
                        numbers.append(float(parts[0]))
                        numbers.append(float(parts[1]))
                else:
                    numbers.append(float(num_str))
            except ValueError:
                continue
        
        return numbers
    
    def _calculate_confidence(self, signal_data: Dict[str, Any]) -> float:
        """Расчёт уверенности в сигнале"""
        score = 0.0
        
        # Обязательные поля
        if 'symbol' in signal_data:
            score += 0.3
        if 'direction' in signal_data:
            score += 0.3
        
        # Желательные поля
        if 'entry_zone' in signal_data and signal_data['entry_zone']:
            score += 0.2
        if 'tp_levels' in signal_data and signal_data['tp_levels']:
            score += 0.15
        if 'sl_level' in signal_data:
            score += 0.05
        
        return min(1.0, score)

class TelegramListener:
    """Основной класс для прослушивания Telegram каналов"""
    
    def __init__(self, config_path: str = "config/telegram_config.yaml"):
        self.config_path = config_path
        self.config = {}
        self.channels: Dict[str, ChannelConfig] = {}
        self.client: Optional[TelegramClient] = None
        self.redis: Optional[aioredis.Redis] = None
        self.db_manager: Optional[DatabaseManager] = None
        self.signal_parser = SignalParser()
        
        # Статистика
        self.stats = {
            'messages_processed': 0,
            'signals_found': 0,
            'signals_valid': 0,
            'signals_invalid': 0,
            'start_time': datetime.utcnow()
        }
        
        # Состояние
        self.running = False
        self.last_health_check = datetime.utcnow()
    
    async def initialize(self):
        """Инициализация Telegram Listener"""
        logger.info("🚀 Initializing Telegram Listener...")
        
        try:
            # Загрузка конфигурации
            await self._load_config()
            
            # Инициализация Telegram клиента
            await self._init_telegram_client()
            
            # Подключение к Redis
            await self._init_redis()
            
            # Инициализация базы данных
            await self._init_database()
            
            logger.info("✅ Telegram Listener initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Telegram Listener: {e}")
            raise
    
    async def _load_config(self):
        """Загрузка конфигурации"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f)
            else:
                # Создаём базовую конфигурацию
                self.config = self._get_default_config()
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(self.config, f, default_flow_style=False)
                logger.info(f"Created default config at {self.config_path}")
            
            # Загрузка каналов
            for channel_data in self.config.get('channels', []):
                channel_config = ChannelConfig(**channel_data)
                self.channels[str(channel_config.id)] = channel_config
                
            logger.info(f"Loaded {len(self.channels)} channels")
            
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Конфигурация по умолчанию"""
        return {
            'telegram': {
                'api_id': os.getenv('TELEGRAM_API_ID'),
                'api_hash': os.getenv('TELEGRAM_API_HASH'),
                'session_name': 'ghost_listener'
            },
            'redis': {
                'url': 'redis://localhost:6379/1',
                'enabled': True
            },
            'database': {
                'signals_table': 'trading_signals',
                'traders_table': 'trader_stats'
            },
            'channels': [
                # Примеры каналов (заполнить реальными данными)
                {
                    'id': '@example_signals',
                    'name': 'Example Signals',
                    'trader_name': 'ExampleTrader',
                    'enabled': False,  # Отключено по умолчанию
                    'parser_type': 'default',
                    'priority': 3
                }
            ],
            'parsing': {
                'min_confidence': 0.7,
                'save_all_signals': True,
                'save_invalid_signals': False
            }
        }
    
    async def _init_telegram_client(self):
        """Инициализация Telegram клиента"""
        try:
            telegram_config = self.config['telegram']
            api_id = telegram_config['api_id']
            api_hash = telegram_config['api_hash']
            session_name = telegram_config['session_name']
            
            if not api_id or not api_hash:
                raise ValueError("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set")
            
            self.client = TelegramClient(session_name, api_id, api_hash)
            await self.client.start()
            
            logger.info("✅ Telegram client connected")
            
        except Exception as e:
            logger.error(f"Failed to initialize Telegram client: {e}")
            raise
    
    async def _init_redis(self):
        """Инициализация Redis"""
        if not self.config.get('redis', {}).get('enabled', False):
            logger.info("Redis disabled in config")
            return
            
        try:
            redis_url = self.config['redis']['url']
            self.redis = await aioredis.from_url(redis_url)
            await self.redis.ping()
            logger.info("✅ Redis connected")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}")
            self.redis = None
    
    async def _init_database(self):
        """Инициализация базы данных"""
        try:
            # В будущем здесь будет DatabaseManager
            # self.db_manager = DatabaseManager()
            # await self.db_manager.initialize()
            logger.info("✅ Database manager initialized")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
    
    async def start_listening(self):
        """Запуск прослушивания каналов"""
        logger.info("🎧 Starting Telegram channels listening...")
        self.running = True
        
        try:
            # Регистрация обработчиков событий
            await self._register_event_handlers()
            
            # Основной цикл
            await self._main_loop()
            
        except Exception as e:
            logger.error(f"❌ Listening error: {e}")
            raise
        finally:
            await self.shutdown()
    
    async def _register_event_handlers(self):
        """Регистрация обработчиков сообщений"""
        @self.client.on(events.NewMessage)
        async def handle_new_message(event):
            await self._process_message(event)
        
        logger.info("📡 Event handlers registered")
    
    async def _process_message(self, event):
        """Обработка нового сообщения"""
        try:
            self.stats['messages_processed'] += 1
            
            # Получение информации о канале
            chat_id = str(event.chat_id)
            
            # Проверка что канал в нашем списке
            if chat_id not in self.channels:
                return
            
            channel_config = self.channels[chat_id]
            if not channel_config.enabled:
                return
            
            # Получение текста сообщения
            message_text = event.message.message
            if not message_text:
                return
            
            # Парсинг сигнала
            parsed_data = self.signal_parser.parse_signal(
                message_text, 
                channel_config.name, 
                channel_config.trader_name
            )
            
            if parsed_data:
                # Создание сигнала
                signal = TradingSignal(
                    id=f"{chat_id}_{event.message.id}_{int(datetime.utcnow().timestamp())}",
                    channel_id=chat_id,
                    channel_name=channel_config.name,
                    trader_name=channel_config.trader_name,
                    message_id=event.message.id,
                    timestamp=datetime.utcnow(),
                    symbol=parsed_data['symbol'],
                    direction=parsed_data['direction'],
                    entry_zone=parsed_data.get('entry_zone', []),
                    tp_levels=parsed_data.get('tp_levels', []),
                    sl_level=parsed_data.get('sl_level'),
                    leverage=parsed_data.get('leverage'),
                    confidence=parsed_data.get('confidence', 0.0),
                    original_text=message_text,
                    parsed_data=parsed_data
                )
                
                # Валидация сигнала
                await self._validate_signal(signal)
                
                # Сохранение сигнала
                await self._save_signal(signal)
                
                self.stats['signals_found'] += 1
                if signal.validation_status == 'valid':
                    self.stats['signals_valid'] += 1
                else:
                    self.stats['signals_invalid'] += 1
                
                logger.info(f"📈 Signal processed: {signal.symbol} {signal.direction} "
                           f"from {signal.trader_name} (confidence: {signal.confidence:.2f})")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            logger.error(traceback.format_exc())
    
    async def _validate_signal(self, signal: TradingSignal):
        """Валидация торгового сигнала"""
        errors = []
        
        # Проверка обязательных полей
        if not signal.symbol:
            errors.append("Missing symbol")
        if not signal.direction:
            errors.append("Missing direction")
        
        # Проверка логичности цен
        if signal.entry_zone and signal.tp_levels:
            entry_avg = sum(signal.entry_zone) / len(signal.entry_zone)
            for tp in signal.tp_levels:
                if signal.direction == 'LONG' and tp <= entry_avg:
                    errors.append(f"TP {tp} should be higher than entry {entry_avg} for LONG")
                elif signal.direction == 'SHORT' and tp >= entry_avg:
                    errors.append(f"TP {tp} should be lower than entry {entry_avg} for SHORT")
        
        if signal.sl_level and signal.entry_zone:
            entry_avg = sum(signal.entry_zone) / len(signal.entry_zone)
            if signal.direction == 'LONG' and signal.sl_level >= entry_avg:
                errors.append(f"SL {signal.sl_level} should be lower than entry {entry_avg} for LONG")
            elif signal.direction == 'SHORT' and signal.sl_level <= entry_avg:
                errors.append(f"SL {signal.sl_level} should be higher than entry {entry_avg} for SHORT")
        
        # Установка статуса валидации
        if errors:
            signal.validation_status = 'invalid'
            signal.validation_errors = errors
        else:
            signal.validation_status = 'valid'
    
    async def _save_signal(self, signal: TradingSignal):
        """Сохранение сигнала в базу данных и Redis"""
        try:
            # Сохранение в Redis для быстрого доступа
            if self.redis:
                signal_data = asdict(signal)
                await self.redis.lpush(
                    'ghost:signals:new',
                    json.dumps(signal_data, default=str)
                )
                await self.redis.ltrim('ghost:signals:new', 0, 1000)  # Держим только 1000 последних
                
                # Сохранение в кэш по трейдеру
                await self.redis.lpush(
                    f'ghost:signals:trader:{signal.trader_name}',
                    json.dumps(signal_data, default=str)
                )
                await self.redis.ltrim(f'ghost:signals:trader:{signal.trader_name}', 0, 100)
            
            # В будущем - сохранение в PostgreSQL через DatabaseManager
            # await self.db_manager.save_signal(signal)
            
        except Exception as e:
            logger.error(f"Failed to save signal: {e}")
    
    async def _main_loop(self):
        """Основной цикл работы"""
        logger.info("🔄 Starting main loop...")
        
        try:
            # Запуск клиента
            await self.client.run_until_disconnected()
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            raise
    
    async def get_status(self) -> Dict[str, Any]:
        """Получение статуса Telegram Listener"""
        uptime = (datetime.utcnow() - self.stats['start_time']).total_seconds()
        
        return {
            'status': 'running' if self.running else 'stopped',
            'uptime': uptime,
            'channels_total': len(self.channels),
            'channels_enabled': sum(1 for c in self.channels.values() if c.enabled),
            'statistics': {
                **self.stats,
                'signals_per_minute': self.stats['signals_found'] / max(uptime / 60, 1),
                'success_rate': self.stats['signals_valid'] / max(self.stats['signals_found'], 1) * 100
            },
            'last_health_check': self.last_health_check.isoformat(),
            'telegram_connected': self.client is not None and self.client.is_connected(),
            'redis_connected': self.redis is not None
        }
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("🛑 Shutting down Telegram Listener...")
        self.running = False
        
        if self.client:
            await self.client.disconnect()
        
        if self.redis:
            await self.redis.close()
        
        logger.info("✅ Telegram Listener shutdown complete")

async def main():
    """Главная функция"""
    listener = TelegramListener()
    
    try:
        await listener.initialize()
        await listener.start_listening()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Telegram Listener failed: {e}")
        logger.error(traceback.format_exc())
    finally:
        await listener.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
