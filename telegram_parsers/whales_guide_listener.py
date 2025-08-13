"""
GHOST Whales Guide Telegram Listener
Слушает новые сигналы из канала @Whalesguide в режиме реального времени
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Optional
import sqlite3
import json

# Добавляем путь к корню проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telethon import TelegramClient, events
from telethon.tl.types import Channel, Chat
from signals.whales_crypto_parser import WhalesCryptoParser
from database.supabase_client import SupabaseClient

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('whales_guide_listener.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WhalesGuideListener:
    """Слушатель канала Whales Crypto Guide"""
    
    def __init__(self):
        # Telegram API credentials (нужно получить от @BotFather)
        self.api_id = os.getenv('TELEGRAM_API_ID')
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.phone = os.getenv('TELEGRAM_PHONE')  # Ваш номер телефона
        
        # Настройки канала
        self.channel_username = 'Whalesguide'  # Без @
        self.channel_id = None
        
        # Парсер сигналов
        self.signal_parser = WhalesCryptoParser()
        
        # База данных
        self.supabase = SupabaseClient()
        self.local_db_path = 'whales_signals.db'
        
        # Telegram клиент
        self.client = None
        
        # Статистика
        self.stats = {
            'messages_received': 0,
            'signals_parsed': 0,
            'signals_saved': 0,
            'errors': 0,
            'started_at': datetime.now()
        }
        
        self.init_local_database()
    
    def init_local_database(self):
        """Инициализация локальной базы данных для кэширования"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            # Таблица для кэширования сообщений
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS whales_messages (
                    id INTEGER PRIMARY KEY,
                    message_id INTEGER UNIQUE,
                    channel_id INTEGER,
                    text TEXT,
                    date TIMESTAMP,
                    is_signal BOOLEAN DEFAULT FALSE,
                    parsed_signal TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица для статистики
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stats (
                    id INTEGER PRIMARY KEY,
                    date DATE UNIQUE,
                    messages_count INTEGER DEFAULT 0,
                    signals_count INTEGER DEFAULT 0,
                    errors_count INTEGER DEFAULT 0
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("✅ Local database initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize local database: {e}")
    
    async def start_listening(self):
        """Запуск прослушивания канала"""
        try:
            # Проверяем наличие учетных данных
            if not self.api_id or not self.api_hash:
                logger.error("❌ Telegram API credentials not found in environment variables")
                logger.info("Please set TELEGRAM_API_ID and TELEGRAM_API_HASH")
                return
            
            # Создаем клиент
            self.client = TelegramClient('whales_session', self.api_id, self.api_hash)
            
            # Подключаемся
            await self.client.start(phone=self.phone)
            logger.info("✅ Connected to Telegram")
            
            # Находим канал
            channel = await self.find_channel()
            if not channel:
                logger.error("❌ Channel @Whalesguide not found")
                return
            
            self.channel_id = channel.id
            logger.info(f"✅ Found channel: {channel.title} (ID: {channel.id})")
            
            # Регистрируем обработчик новых сообщений
            @self.client.on(events.NewMessage(chats=channel))
            async def handle_new_message(event):
                await self.process_message(event)
            
            # Запускаем бесконечный цикл
            logger.info("🚀 Started listening for new messages...")
            self.print_stats()
            
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"❌ Error starting listener: {e}")
            self.stats['errors'] += 1
    
    async def find_channel(self):
        """Поиск канала по username"""
        try:
            # Попробуем несколько вариантов
            channel_variants = [
                'Whalesguide',
                '@Whalesguide', 
                'whalesguide',
                '@whalesguide'
            ]
            
            for variant in channel_variants:
                try:
                    entity = await self.client.get_entity(variant)
                    if isinstance(entity, Channel):
                        return entity
                except Exception as e:
                    logger.debug(f"Failed to find channel with variant '{variant}': {e}")
                    continue
            
            # Если не найден, попробуем через диалоги
            async for dialog in self.client.iter_dialogs():
                if dialog.is_channel:
                    if 'whales' in dialog.name.lower() and 'guide' in dialog.name.lower():
                        logger.info(f"Found potential channel: {dialog.name}")
                        return dialog.entity
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding channel: {e}")
            return None
    
    async def process_message(self, event):
        """Обработка нового сообщения"""
        try:
            message = event.message
            self.stats['messages_received'] += 1
            
            # Логируем получение сообщения
            logger.info(f"📨 New message: ID={message.id}, Date={message.date}")
            
            # Сохраняем сообщение в локальную БД
            await self.save_message_to_cache(message)
            
            # Проверяем, является ли сообщение сигналом
            if message.text and self.signal_parser.can_parse(message.text):
                logger.info("🎯 Detected potential signal!")
                await self.process_signal(message)
            else:
                logger.debug("📝 Regular message (not a signal)")
            
            # Обновляем статистику каждые 10 сообщений
            if self.stats['messages_received'] % 10 == 0:
                self.print_stats()
                
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")
            self.stats['errors'] += 1
    
    async def process_signal(self, message):
        """Обработка сигнала"""
        try:
            # Парсим сигнал
            signal = self.signal_parser.parse_signal(
                message.text, 
                f"whales_guide_msg_{message.id}"
            )
            
            if not signal:
                logger.warning("⚠️ Failed to parse signal")
                return
            
            self.stats['signals_parsed'] += 1
            
            # Добавляем метаданные Telegram
            signal.telegram_message_id = message.id
            signal.telegram_channel_id = self.channel_id
            signal.telegram_date = message.date
            signal.source_url = f"https://t.me/{self.channel_username}/{message.id}"
            
            logger.info(f"✅ Parsed signal: {signal.symbol} {signal.direction.value} (confidence: {signal.confidence:.1f}%)")
            
            # Сохраняем в базу данных
            await self.save_signal(signal, message)
            
            # Логируем детали сигнала
            self.log_signal_details(signal)
            
        except Exception as e:
            logger.error(f"❌ Error processing signal: {e}")
            self.stats['errors'] += 1
    
    async def save_message_to_cache(self, message):
        """Сохранение сообщения в локальный кэш"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO whales_messages 
                (message_id, channel_id, text, date) 
                VALUES (?, ?, ?, ?)
            ''', (
                message.id,
                self.channel_id,
                message.text or '',
                message.date
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving message to cache: {e}")
    
    async def save_signal(self, signal, message):
        """Сохранение сигнала в базу данных"""
        try:
            # Сохраняем в Supabase
            signal_data = {
                'trader_id': 'whales_crypto_guide',
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
                'source': 'whales_crypto_guide',
                'source_url': f"https://t.me/{self.channel_username}/{message.id}",
                'timestamp': signal.timestamp.isoformat(),
                'telegram_message_id': message.id,
                'telegram_channel_id': self.channel_id,
                'analysis_notes': signal.reason,
                'targets': json.dumps(signal.targets) if signal.targets else None,
                'entry_zone': json.dumps(signal.entry_zone) if signal.entry_zone else None,
                'signal_quality': 'high' if signal.confidence > 80 else 'medium' if signal.confidence > 60 else 'low'
            }
            
            # Сохраняем в Supabase
            result = self.supabase.insert_trade(signal_data)
            
            if result:
                self.stats['signals_saved'] += 1
                logger.info(f"💾 Signal saved to database: {signal.symbol}")
                
                # Обновляем локальный кэш
                conn = sqlite3.connect(self.local_db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE whales_messages 
                    SET is_signal = TRUE, parsed_signal = ?
                    WHERE message_id = ?
                ''', (json.dumps(signal_data), message.id))
                
                conn.commit()
                conn.close()
            else:
                logger.error("❌ Failed to save signal to database")
                
        except Exception as e:
            logger.error(f"❌ Error saving signal: {e}")
            self.stats['errors'] += 1
    
    def log_signal_details(self, signal):
        """Детальное логирование сигнала"""
        logger.info("=" * 50)
        logger.info(f"🎯 SIGNAL DETAILS:")
        logger.info(f"Symbol: {signal.symbol}")
        logger.info(f"Direction: {signal.direction.value}")
        logger.info(f"Entry Zone: {signal.entry_zone}")
        logger.info(f"Targets: {signal.targets}")
        logger.info(f"Stop Loss: {signal.stop_loss}")
        logger.info(f"Leverage: {signal.leverage}")
        logger.info(f"Confidence: {signal.confidence:.1f}%")
        if signal.reason:
            logger.info(f"Reason: {signal.reason}")
        logger.info("=" * 50)
    
    def print_stats(self):
        """Вывод статистики"""
        uptime = datetime.now() - self.stats['started_at']
        
        logger.info("📊 LISTENER STATISTICS:")
        logger.info(f"   Uptime: {uptime}")
        logger.info(f"   Messages received: {self.stats['messages_received']}")
        logger.info(f"   Signals parsed: {self.stats['signals_parsed']}")
        logger.info(f"   Signals saved: {self.stats['signals_saved']}")
        logger.info(f"   Errors: {self.stats['errors']}")
        
        if self.stats['messages_received'] > 0:
            signal_rate = (self.stats['signals_parsed'] / self.stats['messages_received']) * 100
            logger.info(f"   Signal detection rate: {signal_rate:.1f}%")
    
    async def stop(self):
        """Остановка слушателя"""
        if self.client:
            await self.client.disconnect()
        logger.info("🛑 Listener stopped")
        self.print_stats()

# Функция для запуска
async def main():
    """Основная функция запуска"""
    listener = WhalesGuideListener()
    
    try:
        await listener.start_listening()
    except KeyboardInterrupt:
        logger.info("🛑 Stopping listener...")
        await listener.stop()
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
