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
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from telethon import TelegramClient, events
from telethon.tl.types import Channel, Chat

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.signal_router import route_signal
from core.trader_registry import TraderRegistry
from signals.image_parser import get_image_parser

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
        self.phone = phone or os.getenv('TELEGRAM_PHONE')
        
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
        
        # Парсер изображений
        self.image_parser = get_image_parser()
        
        # Внешний обработчик сообщений
        self.external_message_handler = None
        
        logger.info("Telegram Listener initialized")
    
    async def _get_code_from_telegram(self):
        """Автоматическое получение кода из Telegram сообщений"""
        try:
            logger.info("📱 Ожидаем код авторизации...")
            
            # Проверяем переменную окружения с кодом
            telegram_code = os.getenv('TELEGRAM_CODE')
            if telegram_code:
                logger.info(f"✅ Используем код из переменной окружения: {telegram_code}")
                return telegram_code
            
            # Попытка автоматического получения кода из Telegram
            try:
                logger.info("⏳ Ожидаем код в сообщениях от Telegram...")
                
                # Используем основной клиент для получения сообщений
                import asyncio
                import re
                from datetime import datetime, timedelta
                
                # Ждем код в течение 60 секунд
                start_time = datetime.now()
                timeout = timedelta(seconds=60)
                
                while datetime.now() - start_time < timeout:
                    try:
                        # Получаем последние сообщения от Telegram (777000)
                        async for message in self.client.iter_messages(777000, limit=5):
                            if message.message and message.date > start_time - timedelta(minutes=2):
                                text = message.message
                                
                                # Ищем код в сообщении
                                code_patterns = [
                                    r'Login code: (\d{5,6})',
                                    r'Telegram code: (\d{5,6})',
                                    r'code: (\d{5,6})',
                                    r'код: (\d{5,6})',
                                    r'Код: (\d{5,6})',
                                    r'\b(\d{5,6})\b'  # Любые 5-6 цифр
                                ]
                                
                                for pattern in code_patterns:
                                    match = re.search(pattern, text)
                                    if match:
                                        code = match.group(1)
                                        logger.info(f"✅ Получен код из сообщения: {code}")
                                        logger.debug(f"Текст сообщения: {text}")
                                        return code
                        
                        # Ждем 2 секунды перед следующей попыткой
                        await asyncio.sleep(2)
                        
                    except Exception as msg_error:
                        logger.debug(f"Ошибка получения сообщения: {msg_error}")
                        await asyncio.sleep(1)
                
                logger.warning("⏰ Время ожидания кода истекло (60 сек)")
                
            except Exception as e:
                logger.error(f"❌ Ошибка автоматического получения кода: {e}")
            
            # Fallback - возвращаем пустую строку для автоматического режима
            logger.error("❌ Не удалось получить код автоматически")
            logger.info("💡 Установите TELEGRAM_CODE в переменные окружения")
            
            # В серверном режиме не можем запрашивать ввод
            return ""
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка получения кода: {e}")
            return ""
    
    async def _get_code_from_telegram_after_request(self):
        """Получение кода из Telegram после отправки запроса"""
        try:
            # Проверяем переменную окружения с кодом
            telegram_code = os.getenv('TELEGRAM_CODE')
            if telegram_code:
                logger.info(f"✅ Используем код из переменной окружения: {telegram_code}")
                return telegram_code
            
            logger.info("⏳ Ожидаем код в сообщениях от Telegram...")
            
            # Создаем отдельный клиент для получения сообщений
            import asyncio
                        import re
            from datetime import datetime, timedelta
            
            try:
                # Создаем временный клиент для чтения сообщений
                temp_client = TelegramClient(':memory:', int(self.api_id), self.api_hash)
                await temp_client.connect()
                
                # Пытаемся авторизоваться с существующей сессией
                if os.path.exists('ghost_session.session'):
                    try:
                        session_client = TelegramClient('ghost_session', int(self.api_id), self.api_hash)
                        await session_client.connect()
                        
                        if await session_client.is_user_authorized():
                            logger.info("📱 Используем существующую сессию для получения кода")
                            
                            # Ждем код в течение 60 секунд
                            start_time = datetime.now()
                            timeout = timedelta(seconds=60)
                            
                            while datetime.now() - start_time < timeout:
                                try:
                                    # Получаем последние сообщения от Telegram (777000)
                                    async for message in session_client.iter_messages(777000, limit=5):
                                        if message.message and message.date > start_time - timedelta(minutes=2):
                                            text = message.message
                                            
                                            # Ищем код в сообщении
                                            code_patterns = [
                                                r'Login code: (\d{5,6})',
                                                r'Telegram code: (\d{5,6})',
                                                r'code: (\d{5,6})',
                                                r'код: (\d{5,6})',
                                                r'Код: (\d{5,6})',
                                                r'\b(\d{5,6})\b'  # Любые 5-6 цифр
                                            ]
                                            
                                            for pattern in code_patterns:
                                                match = re.search(pattern, text)
                                                if match:
                                                    code = match.group(1)
                                                    logger.info(f"✅ Получен код из сообщения: {code}")
                                                    await session_client.disconnect()
                            await temp_client.disconnect()
                            return code
                                    
                                    await asyncio.sleep(2)
                                    
                                except Exception as msg_error:
                                    logger.debug(f"Ошибка получения сообщения: {msg_error}")
                                    await asyncio.sleep(1)
                            
                            await session_client.disconnect()
                        
                    except Exception as session_error:
                        logger.debug(f"Не удалось использовать существующую сессию: {session_error}")
                
                await temp_client.disconnect()
                logger.warning("⏰ Время ожидания кода истекло")
                
            except Exception as e:
                logger.error(f"❌ Ошибка получения кода: {e}")
            
            # Fallback - возвращаем пустую строку
            logger.error("❌ Не удалось получить код автоматически")
            logger.info("💡 Установите TELEGRAM_CODE в переменные окружения")
            return ""
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка получения кода: {e}")
            return ""
    
    async def _perform_automatic_auth(self):
        """Выполнение полностью автоматической авторизации"""
        try:
            # Получаем телефон из переменных окружения
            if not self.phone:
                self.phone = os.getenv('TELEGRAM_PHONE')
                if not self.phone:
                    logger.error("❌ TELEGRAM_PHONE не указан в переменных окружения")
                    return False
            
            logger.info(f"📞 Автоматическая авторизация с номером: {self.phone}")
            
            # Отправляем запрос кода
            sent_code = await self.client.send_code_request(self.phone)
            logger.info("📱 Код авторизации отправлен")
            
            # Получаем код автоматически
            code = await self._get_code_from_telegram_after_request()
            
            if not code:
                logger.error("❌ Не удалось получить код автоматически")
                return False
            
            logger.info(f"🔑 Используем код: {code}")
            
            try:
                # Пытаемся войти с кодом
                await self.client.sign_in(self.phone, code)
                logger.info("✅ Авторизация с кодом успешна")
                return True
                
            except Exception as sign_in_error:
                error_str = str(sign_in_error)
                
                if "Two-step verification" in error_str or "password" in error_str.lower():
                    # Нужен пароль 2FA
                    password = os.getenv('TELEGRAM_PASSWORD')
                    if password:
                        logger.info("🔒 Используем пароль 2FA из переменных окружения")
                        await self.client.sign_in(password=password)
                        logger.info("✅ Авторизация с 2FA успешна")
                        return True
                    else:
                        logger.error("❌ Требуется пароль 2FA, но TELEGRAM_PASSWORD не установлен")
                        return False
                else:
                    logger.error(f"❌ Ошибка входа: {sign_in_error}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Ошибка автоматической авторизации: {e}")
            return False
    
    async def initialize(self):
        """Инициализация Telegram клиента"""
        try:
            # Создаем клиент
            # Путь к сессии относительно корня проекта
            session_path = 'ghost_session'
            self.client = TelegramClient(session_path, self.api_id, self.api_hash)
            
            # Подключаемся с автоматической авторизацией
            try:
                # Пробуем подключиться с существующей сессией
                await self.client.connect()
                
                if await self.client.is_user_authorized():
                    logger.info("✅ Используем существующую сессию")
                else:
                    logger.info("🔑 Сессия недействительна, выполняем автоматическую авторизацию...")
                    # Выполняем автоматическую авторизацию
                    if not await self._perform_automatic_auth():
                        logger.error("❌ Автоматическая авторизация не удалась")
                        return False
                        
            except Exception as auth_error:
                logger.info(f"🔑 Ошибка подключения, выполняем авторизацию: {auth_error}")
                
                # Выполняем автоматическую авторизацию
                if not await self._perform_automatic_auth():
                    logger.error("❌ Автоматическая авторизация не удалась")
                    return False
            
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
    
    def set_message_handler(self, handler_func):
        """Установка внешнего обработчика сообщений"""
        self.external_message_handler = handler_func
        logger.info("External message handler set")
    
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
            message_text = event.message.text or ""
            
            # Проверяем наличие изображения
            has_image = bool(event.message.photo or event.message.document)
            
            # Если нет ни текста, ни изображения - пропускаем
            if not message_text and not has_image:
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
            
            # Для канала Whales Guide - обрабатываем ВСЕ сообщения с контентом
            is_whales_guide = channel_config.trader_id == "whales_guide_main"
            
            if is_whales_guide:
                # Для Whales Guide - берем все сообщения с текстом или изображениями
                is_signal = (message_text and len(message_text) > 10) or has_image
            else:
                # Для других каналов - стандартная логика
            is_text_signal = message_text and self._looks_like_signal(message_text)
            is_image_signal = has_image
                is_signal = is_text_signal or is_image_signal
            
            if not is_signal:
                logger.debug("Message doesn't look like a trading signal")
                return
            
            # Обновляем статистику сигналов
            self.stats['signals_detected'] += 1
            self.stats['by_channel'][chat_id]['signals'] += 1
            
            logger.info(f"Signal detected from {channel_config.channel_name}")
            
            # Вызываем внешний обработчик если он установлен
            if self.external_message_handler:
                try:
                    message_data = {
                        "chat_id": chat_id,
                        "message_id": event.message.id,
                        "text": message_text,
                        "timestamp": event.message.date,
                        "has_image": has_image,
                        "channel_name": channel_config.channel_name,
                        "trader_id": channel_config.trader_id
                    }
                    
                    await self.external_message_handler(message_data)
                    logger.debug(f"External handler called for message from {channel_config.channel_name}")
                    
                except Exception as e:
                    logger.error(f"Error in external message handler: {e}")
            
            # Отправляем на парсинг (текст и/или изображение)
            await self._process_signal(message_text, channel_config, event, has_image)
            
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
        
        # Для канала Whales Guide - захватываем ВСЕ сообщения с криптовалютной информацией
        crypto_indicators = [
            'btc', 'eth', 'usdt', 'bnb', 'ada', 'xrp', 'sol', 'dot', 'doge', 'matic',
            'avax', 'shib', 'ltc', 'link', 'uni', 'atom', 'xlm', 'vet', 'icp', 'fil',
            'trx', 'etc', 'ftt', 'near', 'algo', 'mana', 'sand', 'gala', 'ape', 'lrc',
            'crypto', 'bitcoin', 'ethereum', 'binance', 'trading', 'signal', 'whale',
            'long', 'short', 'buy', 'sell', 'pump', 'dump', 'bullish', 'bearish',
            'entry', 'target', 'profit', 'loss', 'tp', 'sl', 'stop', 'resistance', 
            'support', 'breakout', 'moon', 'gem', 'x10', 'x100', 'hodl', 'fomo',
            'alert', 'call', 'analysis', 'market', 'price', 'trend', 'chart'
        ]
        
        # Если содержит хотя бы 1 криптовалютный индикатор - считаем сигналом
        for indicator in crypto_indicators:
            if indicator in text_lower:
                return True
        
        # Дополнительно проверяем паттерны цен и символов
        import re
        
        # Паттерны цен ($1.23, 45000, 0.001234)
        price_patterns = [
            r'\$\d+\.?\d*',  # $123.45
            r'\d+\.\d+',     # 123.45
            r'\d{4,}',       # 45000
        ]
        
        for pattern in price_patterns:
            if re.search(pattern, text):
                return True
        
        # Если сообщение длиннее 50 символов и содержит числа - тоже берем
        if len(text) > 50 and re.search(r'\d', text):
            return True
            
        return False
    
    async def _process_signal(self, text: str, config: ChannelConfig, event, has_image: bool = False):
        """Обработка сигнала через роутер (текст и/или изображение)"""
        try:
            # Дополнительная информация об источнике
            source_info = {
                'channel_id': config.channel_id,
                'channel_name': config.channel_name,
                'message_id': event.message.id,
                'message_date': event.message.date,
                'chat_type': 'channel',
                'has_image': has_image
            }
            
            result = None
            
            # Если есть изображение, анализируем его
            if has_image:
                logger.info(f"🖼️ Processing image signal from {config.channel_name}")
                image_result = await self._process_image_signal(event, text, config)
                if image_result:
                    result = image_result
                    logger.info(f"✅ Image signal parsed: {result.get('symbol')} {result.get('side')}")
            
            # Если нет результата от изображения, пробуем текст
            if not result and text:
                result = await route_signal(text, config.trader_id, source_info)
            
            if result:
                self.stats['signals_parsed'] += 1
                logger.info(f"Signal successfully parsed: {result.get('symbol')} {result.get('side', result.get('direction'))}")
                
                # Сохраняем сырой сигнал для истории
                await self._save_raw_signal(text, config, event, result, has_image)
                
            else:
                logger.warning(f"Failed to parse signal from {config.channel_name}")
                
                # Сохраняем неудачный сигнал
                await self._save_raw_signal(text, config, event, None, has_image)
                
        except Exception as e:
            logger.error(f"Error processing signal: {e}")
    
    async def _process_image_signal(self, event, caption: str, config: ChannelConfig) -> Optional[Dict[str, Any]]:
        """Обработка сигнала из изображения"""
        try:
            # Получаем изображение
            image_data = await self._download_image_from_event(event)
            if not image_data:
                return None
            
            # Анализируем изображение с помощью AI
            result = await self.image_parser.parse_image_signal(
                image_data=image_data,
                telegram_caption=caption
            )
            
            if result and result.get('is_signal'):
                # Преобразуем результат в формат системы
                return {
                    'symbol': result.get('symbol'),
                    'side': result.get('side'),
                    'entry': result.get('entry'),
                    'targets': result.get('targets'),
                    'stop_loss': result.get('stop_loss'),
                    'leverage': result.get('leverage'),
                    'reason': result.get('reason'),
                    'confidence': result.get('confidence', 0.8),
                    'source': 'image_analysis',
                    'ai_model': result.get('ai_model'),
                    'chart_pattern': result.get('chart_pattern'),
                    'timeframe': result.get('timeframe'),
                    'trader_id': config.trader_id
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error processing image signal: {e}")
            return None
    
    async def _download_image_from_event(self, event) -> Optional[bytes]:
        """Скачивание изображения из Telegram события"""
        try:
            if event.message.photo:
                # Скачиваем фото
                image_data = await event.message.download_media(file=bytes)
                return image_data
            elif event.message.document:
                # Проверяем, что это изображение
                if event.message.document.mime_type and event.message.document.mime_type.startswith('image/'):
                    image_data = await event.message.download_media(file=bytes)
                    return image_data
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error downloading image: {e}")
            return None
    
    async def _save_raw_signal(self, text: str, config: ChannelConfig, event, parsed_result: Optional[Dict], has_image: bool = False):
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
                    'parsed_direction': parsed_result.get('side', parsed_result.get('direction')) if parsed_result else None,
                    'has_image': has_image,
                    'source_type': parsed_result.get('source') if parsed_result else 'text_only',
                    'ai_model': parsed_result.get('ai_model') if parsed_result else None,
                    'confidence': parsed_result.get('confidence') if parsed_result else None
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

async def main():
    """Основная функция для запуска Telegram Listener"""
    import os
    
    # Получаем переменные из окружения
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH') 
    phone = os.getenv('TELEGRAM_PHONE')
    
    if not api_id or not api_hash:
        logger.error("❌ TELEGRAM_API_ID и TELEGRAM_API_HASH обязательны")
        return
    
    try:
        # Создаем listener
        listener = TelegramListener(api_id, api_hash, phone)
        
        # Загружаем конфигурацию каналов
        config_path = os.path.join('config', 'telegram_channels.json')
        listener.load_channels_from_config(config_path)
        
        # Инициализируем
        if await listener.initialize():
            logger.info("🟢 Telegram Listener запущен")
            
            # Запускаем прослушивание
            await listener.start_listening()
        else:
            logger.error("❌ Не удалось инициализировать Telegram Listener")
            
    except Exception as e:
        logger.error(f"❌ Ошибка в Telegram Listener: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())