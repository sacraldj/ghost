"""
Telegram → Render → Supabase → Vercel Bridge
Супер точная интеграция для полной цепочки обработки сигналов
"""

import asyncio
import logging
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import aiohttp
import time

# Telegram imports
try:
    from telethon import TelegramClient, events
    from telethon.errors import FloodWaitError
except ImportError:
    print("❌ Telethon not installed. Run: pip install telethon")
    sys.exit(1)

# Добавляем путь к парсерам
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'telegram_parsers'))

# Импортируем парсеры
try:
    from cryptoattack24_parser import CryptoAttack24Parser
except ImportError:
    print("⚠️ CryptoAttack24Parser not found, using basic parser")
    CryptoAttack24Parser = None

logger = logging.getLogger(__name__)

@dataclass
class TelegramMessage:
    """Структура telegram сообщения"""
    message_id: int
    chat_id: int
    chat_title: str
    text: str
    date: datetime
    sender_id: Optional[int] = None
    forward_from: Optional[str] = None
    media_type: Optional[str] = None
    raw_data: Optional[Dict] = None

@dataclass
class ProcessedSignal:
    """Обработанный сигнал"""
    source: str
    trader_id: str
    symbol: str
    signal_type: str
    confidence: float
    raw_text: str
    processed_at: datetime
    metadata: Dict[str, Any]

class TelegramRenderBridge:
    """Мост Telegram → Render для обработки сигналов"""
    
    def __init__(self, config_path: str = "config/telegram_channels.json"):
        self.config_path = config_path
        self.client = None
        self.channels = []
        self.parsers = {}
        self.render_webhook_url = os.getenv('RENDER_WEBHOOK_URL')
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        # Статистика
        self.stats = {
            'messages_received': 0,
            'signals_parsed': 0,
            'signals_sent': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
        
        # Инициализация
        self._load_config()
        self._init_parsers()

    def _load_config(self):
        """Загрузка конфигурации каналов"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.channels = [ch for ch in config.get('channels', []) if ch.get('is_active', False)]
                logger.info(f"Loaded {len(self.channels)} active channels")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.channels = []

    def _init_parsers(self):
        """Инициализация парсеров"""
        # CryptoAttack24 парсер
        if CryptoAttack24Parser:
            self.parsers['cryptoattack24_v1'] = CryptoAttack24Parser()
            logger.info("✅ CryptoAttack24 parser initialized")
        
        # Можно добавить другие парсеры
        logger.info(f"Initialized {len(self.parsers)} parsers")

    async def init_telegram_client(self):
        """Инициализация Telegram клиента"""
        try:
            api_id = os.getenv('TELEGRAM_API_ID')
            api_hash = os.getenv('TELEGRAM_API_HASH')
            
            if not api_id or not api_hash:
                raise ValueError("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set")
            
            self.client = TelegramClient('ghost_session', int(api_id), api_hash)
            await self.client.start()
            
            # Проверяем авторизацию
            me = await self.client.get_me()
            logger.info(f"✅ Telegram client authorized as: {me.first_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Telegram client: {e}")
            return False

    async def setup_message_handlers(self):
        """Настройка обработчиков сообщений"""
        if not self.client:
            logger.error("Telegram client not initialized")
            return
        
        # Получаем ID каналов
        channel_entities = []
        for channel_config in self.channels:
            try:
                if channel_config.get('channel_id'):
                    entity = await self.client.get_entity(int(channel_config['channel_id']))
                    channel_entities.append(entity)
                    logger.info(f"✅ Connected to channel: {channel_config['channel_name']}")
                else:
                    logger.warning(f"⚠️ No channel_id for: {channel_config['channel_name']}")
            except Exception as e:
                logger.error(f"❌ Failed to connect to {channel_config['channel_name']}: {e}")
        
        if not channel_entities:
            logger.error("❌ No channels connected!")
            return
        
        # Обработчик новых сообщений
        @self.client.on(events.NewMessage(chats=channel_entities))
        async def handle_new_message(event):
            await self._process_telegram_message(event)
        
        logger.info(f"✅ Message handlers set up for {len(channel_entities)} channels")

    async def _process_telegram_message(self, event):
        """Обработка нового сообщения из Telegram"""
        try:
            self.stats['messages_received'] += 1
            
            # Извлекаем данные сообщения
            message = TelegramMessage(
                message_id=event.message.id,
                chat_id=event.chat_id,
                chat_title=getattr(event.chat, 'title', 'Unknown'),
                text=event.message.text or '',
                date=event.message.date,
                sender_id=event.sender_id,
                raw_data=event.message.to_dict()
            )
            
            logger.info(f"📨 New message from {message.chat_title}: {message.text[:50]}...")
            
            # Находим конфигурацию канала
            channel_config = self._find_channel_config(message.chat_id)
            if not channel_config:
                logger.debug(f"No config found for chat_id: {message.chat_id}")
                return
            
            # Парсим сообщение
            signals = await self._parse_message(message, channel_config)
            
            # Отправляем сигналы
            for signal in signals:
                await self._send_to_render(signal)
                await self._save_to_supabase(signal)
                self.stats['signals_sent'] += 1
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Error processing message: {e}")

    def _find_channel_config(self, chat_id: int) -> Optional[Dict]:
        """Поиск конфигурации канала по chat_id"""
        chat_id_str = str(chat_id)
        for config in self.channels:
            if config.get('channel_id') == chat_id_str:
                return config
        return None

    async def _parse_message(self, message: TelegramMessage, channel_config: Dict) -> List[ProcessedSignal]:
        """Парсинг сообщения с помощью соответствующего парсера"""
        signals = []
        
        try:
            # Получаем парсер для канала
            parsing_profile = channel_config.get('parsing_profile', 'default')
            parser = self.parsers.get(parsing_profile)
            
            if not parser:
                logger.warning(f"No parser found for profile: {parsing_profile}")
                return signals
            
            # Парсим сообщение
            if hasattr(parser, 'parse_message'):
                result = parser.parse_message(message.text, message.date)
                
                if result:
                    signal = ProcessedSignal(
                        source=f"telegram:{channel_config['trader_id']}",
                        trader_id=channel_config['trader_id'],
                        symbol=result.symbol,
                        signal_type=result.action,
                        confidence=result.confidence,
                        raw_text=message.text,
                        processed_at=datetime.now(),
                        metadata={
                            'chat_id': message.chat_id,
                            'chat_title': message.chat_title,
                            'message_id': message.message_id,
                            'price_movement': getattr(result, 'price_movement', None),
                            'exchange': getattr(result, 'exchange', None),
                            'sector': getattr(result, 'sector', None),
                            'parsing_profile': parsing_profile
                        }
                    )
                    signals.append(signal)
                    self.stats['signals_parsed'] += 1
                    logger.info(f"✅ Parsed signal: {signal.symbol} {signal.signal_type} (confidence: {signal.confidence:.2f})")
            
        except Exception as e:
            logger.error(f"Error parsing message: {e}")
        
        return signals

    async def _send_to_render(self, signal: ProcessedSignal):
        """Отправка сигнала на Render webhook"""
        if not self.render_webhook_url:
            logger.debug("No Render webhook URL configured")
            return
        
        try:
            payload = {
                'type': 'telegram_signal',
                'timestamp': signal.processed_at.isoformat(),
                'data': asdict(signal)
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.render_webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.debug(f"✅ Signal sent to Render: {signal.symbol}")
                    else:
                        logger.error(f"❌ Render webhook error: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error sending to Render: {e}")

    async def _save_to_supabase(self, signal: ProcessedSignal):
        """Сохранение сигнала в Supabase"""
        if not self.supabase_url or not self.supabase_key:
            logger.debug("No Supabase credentials configured")
            return
        
        try:
            # Подготавливаем данные для вставки
            signal_data = {
                'id': f"{signal.trader_id}_{int(time.time() * 1000)}",
                'received_at': int(signal.processed_at.timestamp() * 1000),
                'source_name': signal.trader_id,
                'raw_text': signal.raw_text,
                'symbol_raw': signal.symbol,
                'symbol': signal.symbol,
                'side': 'Buy',  # По умолчанию
                'entry_low': 0.0,
                'entry_high': 0.0,
                'targets_json': '[]',
                'stoploss': 0.0,
                'parse_version': '1.0',
                'parsed_ok': 1 if signal.confidence > 0.7 else 0
            }
            
            headers = {
                'apikey': self.supabase_key,
                'Authorization': f'Bearer {self.supabase_key}',
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.supabase_url}/rest/v1/signals",
                    json=signal_data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status in [200, 201]:
                        logger.debug(f"✅ Signal saved to Supabase: {signal.symbol}")
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Supabase error: {response.status} - {error_text}")
                        
        except Exception as e:
            logger.error(f"Error saving to Supabase: {e}")

    async def start_listening(self):
        """Запуск прослушивания каналов"""
        logger.info("🚀 Starting Telegram → Render → Supabase bridge...")
        
        # Инициализация клиента
        if not await self.init_telegram_client():
            return False
        
        # Настройка обработчиков
        await self.setup_message_handlers()
        
        # Запуск
        logger.info("✅ Bridge is running! Listening for messages...")
        await self.client.run_until_disconnected()

    def get_stats(self) -> Dict:
        """Получение статистики работы"""
        uptime = datetime.now() - self.stats['start_time']
        return {
            **self.stats,
            'uptime_seconds': int(uptime.total_seconds()),
            'channels_count': len(self.channels),
            'parsers_count': len(self.parsers)
        }

    async def stop(self):
        """Остановка моста"""
        if self.client:
            await self.client.disconnect()
        logger.info("🛑 Bridge stopped")

# Функция для запуска
async def main():
    """Главная функция запуска"""
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Проверяем переменные окружения
    required_env = ['TELEGRAM_API_ID', 'TELEGRAM_API_HASH']
    missing = [var for var in required_env if not os.getenv(var)]
    
    if missing:
        logger.error(f"❌ Missing environment variables: {', '.join(missing)}")
        logger.info("Please set them in your .env file:")
        for var in missing:
            logger.info(f"  {var}=your_value_here")
        return
    
    # Создаем и запускаем мост
    bridge = TelegramRenderBridge()
    
    try:
        await bridge.start_listening()
    except KeyboardInterrupt:
        logger.info("👋 Shutting down...")
        await bridge.stop()
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        await bridge.stop()

if __name__ == "__main__":
    asyncio.run(main())
