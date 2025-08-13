"""
GHOST Telegram Listener
Подключение к Telegram каналам для сбора сигналов
На основе архитектуры core/telegram_listener.py системы Дарена
"""

import asyncio
import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass

from telethon import TelegramClient, events
from telethon.tl.types import Channel, Chat

from core.signal_router import route_signal
from core.trader_registry import TraderRegistry

logger = logging.getLogger(__name__)

@dataclass
class ChannelConfig:
    """Конфигурация канала для мониторинга"""
    channel_id: str
    channel_name: str
    trader_id: str
    is_active: bool = True
    keywords_filter: List[str] = None
    exclude_keywords: List[str] = None
    
    def __post_init__(self):
        if self.keywords_filter is None:
            self.keywords_filter = []
        if self.exclude_keywords is None:
            self.exclude_keywords = []

class TelegramListener:
    """Слушатель Telegram каналов"""
    
    def __init__(self, api_id: str, api_hash: str, phone: str = None):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        
        # Telegram клиент
        self.client: Optional[TelegramClient] = None
        
        # Конфигурация каналов
        self.channels: Dict[str, ChannelConfig] = {}
        
        # Статистика
        self.stats = {
            'messages_received': 0,
            'signals_detected': 0,
            'signals_parsed': 0,
            'by_channel': {}
        }
        
        # Фильтры
        self.global_signal_keywords = [
            'long', 'short', 'buy', 'sell', 'entry', 'target', 'tp1', 'tp2', 'tp3', 'sl', 'stop',
            'лонг', 'шорт', 'покупка', 'продажа', 'вход', 'цель', 'стоп'
        ]
        
        # Обработанные сообщения (анти-дубликаты)
        self.processed_messages: Set[str] = set()
        
        logger.info("Telegram Listener initialized")
    
    async def initialize(self):
        """Инициализация Telegram клиента"""
        try:
            # Создаем клиент
            self.client = TelegramClient('ghost_session', self.api_id, self.api_hash)
            
            # Подключаемся
            await self.client.start(phone=self.phone)
            
            # Проверяем авторизацию
            if await self.client.is_user_authorized():
                me = await self.client.get_me()
                logger.info(f"Telegram client authorized as: {me.first_name} (@{me.username})")
                return True
            else:
                logger.error("Telegram client not authorized")
                return False
                
        except Exception as e:
            logger.error(f"Error initializing Telegram client: {e}")
            return False
    
    def add_channel(self, channel_config: ChannelConfig):
        """Добавление канала для мониторинга"""
        self.channels[channel_config.channel_id] = channel_config
        self.stats['by_channel'][channel_config.channel_id] = {
            'messages': 0,
            'signals': 0,
            'name': channel_config.channel_name
        }
        logger.info(f"Added channel: {channel_config.channel_name} (ID: {channel_config.channel_id})")
    
    def load_channels_from_config(self, config_path: str):
        """Загрузка каналов из конфигурационного файла"""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                for channel_data in config_data.get('channels', []):
                    config = ChannelConfig(
                        channel_id=channel_data['channel_id'],
                        channel_name=channel_data['channel_name'],
                        trader_id=channel_data['trader_id'],
                        is_active=channel_data.get('is_active', True),
                        keywords_filter=channel_data.get('keywords_filter', []),
                        exclude_keywords=channel_data.get('exclude_keywords', [])
                    )
                    self.add_channel(config)
                
                logger.info(f"Loaded {len(self.channels)} channels from config")
            
            else:
                logger.warning(f"Config file not found: {config_path}")
                
        except Exception as e:
            logger.error(f"Error loading channels config: {e}")
    
    async def start_listening(self):
        """Запуск прослушивания каналов"""
        if not self.client:
            logger.error("Telegram client not initialized")
            return
        
        if not self.channels:
            logger.warning("No channels configured for listening")
            return
        
        logger.info(f"Starting to listen to {len(self.channels)} channels...")
        
        # Подписываемся на новые сообщения
        @self.client.on(events.NewMessage())
        async def handle_new_message(event):
            await self._handle_message(event)
        
        # Держим клиент активным
        try:
            await self.client.run_until_disconnected()
        except Exception as e:
            logger.error(f"Error in Telegram listener: {e}")
            raise
    
    async def _handle_message(self, event):
        """Обработка нового сообщения"""
        try:
            # Получаем информацию о чате
            chat = await event.get_chat()
            
            # Определяем ID канала
            if hasattr(chat, 'id'):
                chat_id = str(chat.id)
            else:
                return
            
            # Проверяем, мониторим ли мы этот канал
            if chat_id not in self.channels:
                return
            
            channel_config = self.channels[chat_id]
            
            # Проверяем, активен ли канал
            if not channel_config.is_active:
                return
            
            # Получаем текст сообщения
            message_text = event.message.text
            if not message_text:
                return
            
            # Генерируем уникальный ID сообщения для анти-дубликатов
            message_id = f"{chat_id}_{event.message.id}"
            if message_id in self.processed_messages:
                return
            
            self.processed_messages.add(message_id)
            
            # Обновляем статистику
            self.stats['messages_received'] += 1
            self.stats['by_channel'][chat_id]['messages'] += 1
            
            logger.debug(f"New message from {channel_config.channel_name}: {message_text[:100]}...")
            
            # Проверяем фильтры
            if not self._message_passes_filters(message_text, channel_config):
                return
            
            # Проверяем, похоже ли на торговый сигнал
            if not self._looks_like_signal(message_text):
                logger.debug("Message doesn't look like a trading signal")
                return
            
            # Обновляем статистику сигналов
            self.stats['signals_detected'] += 1
            self.stats['by_channel'][chat_id]['signals'] += 1
            
            logger.info(f"Signal detected from {channel_config.channel_name}")
            
            # Отправляем на парсинг
            await self._process_signal(message_text, channel_config, event)
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    def _message_passes_filters(self, text: str, config: ChannelConfig) -> bool:
        """Проверка сообщения через фильтры"""
        text_lower = text.lower()
        
        # Проверяем исключающие ключевые слова
        if config.exclude_keywords:
            for keyword in config.exclude_keywords:
                if keyword.lower() in text_lower:
                    logger.debug(f"Message excluded by keyword: {keyword}")
                    return False
        
        # Проверяем включающие ключевые слова (если есть)
        if config.keywords_filter:
            for keyword in config.keywords_filter:
                if keyword.lower() in text_lower:
                    return True
            logger.debug("Message doesn't match include keywords")
            return False
        
        return True
    
    def _looks_like_signal(self, text: str) -> bool:
        """Проверка, похож ли текст на торговый сигнал"""
        text_lower = text.lower()
        
        # Должно содержать хотя бы 2 ключевых слова сигнала
        keyword_count = 0
        for keyword in self.global_signal_keywords:
            if keyword in text_lower:
                keyword_count += 1
        
        return keyword_count >= 2
    
    async def _process_signal(self, text: str, config: ChannelConfig, event):
        """Обработка сигнала через роутер"""
        try:
            # Дополнительная информация об источнике
            source_info = {
                'channel_id': config.channel_id,
                'channel_name': config.channel_name,
                'message_id': event.message.id,
                'message_date': event.message.date,
                'chat_type': 'channel'
            }
            
            # Отправляем в роутер сигналов
            result = await route_signal(text, config.trader_id, source_info)
            
            if result:
                self.stats['signals_parsed'] += 1
                logger.info(f"Signal successfully parsed: {result['symbol']} {result['direction']}")
                
                # Сохраняем сырой сигнал для истории
                await self._save_raw_signal(text, config, event, result)
                
            else:
                logger.warning(f"Failed to parse signal from {config.channel_name}")
                
                # Сохраняем неудачный сигнал
                await self._save_raw_signal(text, config, event, None)
                
        except Exception as e:
            logger.error(f"Error processing signal: {e}")
    
    async def _save_raw_signal(self, text: str, config: ChannelConfig, event, parsed_result: Optional[Dict]):
        """Сохранение сырого сигнала в БД"""
        try:
            raw_signal_data = {
                'trader_id': config.trader_id,
                'source_msg_id': str(event.message.id),
                'posted_at': event.message.date.isoformat(),
                'text': text,
                'meta': {
                    'channel_id': config.channel_id,
                    'channel_name': config.channel_name,
                    'parsed': parsed_result is not None,
                    'parsed_symbol': parsed_result.get('symbol') if parsed_result else None,
                    'parsed_direction': parsed_result.get('direction') if parsed_result else None
                }
            }
            
            # TODO: Сохранение в signals_raw таблицу через Supabase
            logger.debug(f"Saving raw signal from {config.trader_id}")
            
        except Exception as e:
            logger.error(f"Error saving raw signal: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики работы слушателя"""
        return {
            **self.stats,
            'channels_count': len(self.channels),
            'active_channels': len([c for c in self.channels.values() if c.is_active]),
            'parse_rate': (self.stats['signals_parsed'] / max(self.stats['signals_detected'], 1)) * 100
        }
    
    async def stop(self):
        """Остановка слушателя"""
        if self.client:
            await self.client.disconnect()
            logger.info("Telegram listener stopped")

# Функции для внешнего использования
async def create_telegram_listener(api_id: str, api_hash: str, phone: str = None) -> TelegramListener:
    """Создание и инициализация слушателя Telegram"""
    listener = TelegramListener(api_id, api_hash, phone)
    
    if await listener.initialize():
        return listener
    else:
        raise Exception("Failed to initialize Telegram listener")

def create_default_channels_config() -> List[Dict[str, Any]]:
    """Создание конфигурации по умолчанию для каналов"""
    return [
        {
            "channel_id": "",  # Заполнить реальный ID канала
            "channel_name": "Crypto Hub VIP",
            "trader_id": "crypto_hub_vip",
            "is_active": True,
            "keywords_filter": ["longing", "shorting", "entry", "targets"],
            "exclude_keywords": ["test", "admin"]
        },
        {
            "channel_id": "",  # Заполнить реальный ID канала
            "channel_name": "2Trade",
            "trader_id": "2trade",
            "is_active": True,
            "keywords_filter": ["pair:", "direction:", "entry:"],
            "exclude_keywords": ["demo", "test"]
        }
    ]

# Тестирование
async def test_telegram_listener():
    """Тестирование Telegram слушателя"""
    print("🧪 Testing Telegram Listener")
    
    # Создаем мок-конфигурацию
    test_config = ChannelConfig(
        channel_id="test_channel",
        channel_name="Test Channel",
        trader_id="test_trader"
    )
    
    # Создаем слушатель без реального подключения
    listener = TelegramListener("test_api_id", "test_api_hash")
    listener.add_channel(test_config)
    
    # Тестируем фильтры
    test_messages = [
        "Longing #SUI Here - Long (5x - 10x) Entry: $3.89",  # Должен пройти
        "Hello everyone! How are you today?",  # Не должен пройти
        "PAIR: BTC DIRECTION: LONG ENTRY: $43000",  # Должен пройти
        "Admin announcement: server maintenance",  # Не должен пройти
    ]
    
    for i, msg in enumerate(test_messages):
        passes_filter = listener._message_passes_filters(msg, test_config)
        looks_like_signal = listener._looks_like_signal(msg)
        
        print(f"Message {i+1}: {'✅' if (passes_filter and looks_like_signal) else '❌'}")
        print(f"  Text: {msg[:50]}...")
        print(f"  Passes filter: {passes_filter}")
        print(f"  Looks like signal: {looks_like_signal}")
        print()
    
    return listener

if __name__ == "__main__":
    asyncio.run(test_telegram_listener())