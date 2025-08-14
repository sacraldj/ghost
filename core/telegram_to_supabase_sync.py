#!/usr/bin/env python3
"""
🚀 GHOST Telegram to Supabase Sync
Модуль для записи всех Telegram сигналов в продвинутую базу данных Supabase
Основан на лучших практиках торговых фондов
"""

import asyncio
import logging
import os
import sys
import json
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from telethon import TelegramClient, events
from telethon.tl.types import Channel, Chat
from supabase import create_client, Client

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/telegram_supabase_sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('TelegramSupabaseSync')

class TelegramSupabaseSync:
    """Синхронизация Telegram сигналов с продвинутой Supabase базой"""
    
    def __init__(self):
        # Telegram настройки
        self.api_id = os.getenv('TELEGRAM_API_ID')
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.phone = os.getenv('TELEGRAM_PHONE')
        
        # Supabase настройки
        self.supabase_url = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        # Клиенты
        self.telegram_client: Optional[TelegramClient] = None
        self.supabase_client: Optional[Client] = None
        
        # Конфигурация каналов для мониторинга
        self.monitored_channels = {
            -1001288385100: {  # Whales Crypto Guide
                'source_code': 'whales_crypto_guide',
                'source_name': 'Whales Crypto Guide',
                'trader_id': 'whales_guide'
            }
            # Можно добавить больше каналов
        }
        
        # Паттерны для парсинга сигналов
        self.signal_patterns = {
            'symbol': r'[#$]?([A-Z]{2,10}USDT?)',
            'direction': r'\b(LONG|SHORT|BUY|SELL)\b',
            'entry': r'(?:Entry|Вход|ENTRY)[\s:]*(\d+\.?\d*)',
            'stop': r'(?:Stop|Стоп|SL|STOP)[\s:]*(\d+\.?\d*)',
            'targets': r'(?:Target|TP|Цель)[\s:]*(\d+\.?\d*)',
            'leverage': r'(?:Leverage|Плечо)[\s:]*(\d+)x?',
            'risk': r'(?:Risk|Риск)[\s:]*(\d+\.?\d*)%?'
        }
        
        # Статистика
        self.stats = {
            'messages_received': 0,
            'signals_parsed': 0,
            'signals_saved': 0,
            'errors': 0
        }
    
    async def initialize(self):
        """Инициализация всех подключений"""
        try:
            # Инициализация Telegram
            await self._init_telegram()
            
            # Инициализация Supabase
            await self._init_supabase()
            
            logger.info("🚀 TelegramSupabaseSync инициализирован успешно")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации: {e}")
            return False
    
    async def _init_telegram(self):
        """Инициализация Telegram клиента"""
        if not self.api_id or not self.api_hash:
            raise ValueError("TELEGRAM_API_ID и TELEGRAM_API_HASH обязательны")
        
        # Путь к сессии
        session_path = os.path.join('..', 'ghost_session')
        self.telegram_client = TelegramClient(session_path, int(self.api_id), self.api_hash)
        
        await self.telegram_client.start()
        
        if await self.telegram_client.is_user_authorized():
            me = await self.telegram_client.get_me()
            logger.info(f"✅ Telegram авторизован: {me.first_name} (@{me.username})")
        else:
            raise Exception("Telegram не авторизован")
    
    async def _init_supabase(self):
        """Инициализация Supabase клиента"""
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL и SUPABASE_SERVICE_ROLE_KEY обязательны")
        
        self.supabase_client = create_client(self.supabase_url, self.supabase_key)
        
        # Проверяем подключение
        try:
            result = self.supabase_client.table('signal_sources').select('*').limit(1).execute()
            logger.info("✅ Supabase подключен успешно")
        except Exception as e:
            logger.warning(f"⚠️ Проблема с Supabase: {e}")
            # Создаем таблицы если их нет
            await self._ensure_tables_exist()
    
    async def _ensure_tables_exist(self):
        """Убеждаемся что все нужные таблицы существуют"""
        logger.info("🔧 Проверяем наличие таблиц в Supabase...")
        
        # Список критически важных таблиц
        required_tables = [
            'signal_sources',
            'signals_raw', 
            'signals_parsed',
            'instruments',
            'trades'
        ]
        
        for table in required_tables:
            try:
                self.supabase_client.table(table).select('id').limit(1).execute()
                logger.info(f"✅ Таблица {table} существует")
            except Exception as e:
                logger.warning(f"⚠️ Таблица {table} недоступна: {e}")
    
    async def start_monitoring(self):
        """Запуск мониторинга Telegram каналов"""
        if not self.telegram_client:
            raise Exception("Telegram клиент не инициализирован")
        
        logger.info(f"📡 Начинаем мониторинг {len(self.monitored_channels)} каналов...")
        
        # Подписываемся на новые сообщения
        @self.telegram_client.on(events.NewMessage)
        async def handle_message(event):
            await self._process_message(event)
        
        # Запускаем бесконечный цикл
        logger.info("🔄 Мониторинг запущен. Ожидаем сообщения...")
        await self.telegram_client.run_until_disconnected()
    
    async def _process_message(self, event):
        """Обработка нового сообщения из Telegram"""
        try:
            # Проверяем что сообщение из мониторимого канала
            chat_id = event.chat_id
            if chat_id not in self.monitored_channels:
                return
            
            channel_info = self.monitored_channels[chat_id]
            message = event.message
            
            self.stats['messages_received'] += 1
            
            logger.info(f"📨 Новое сообщение из {channel_info['source_name']}")
            
            # 1. Сохраняем сырое сообщение
            raw_signal_id = await self._save_raw_signal(message, channel_info)
            
            # 2. Парсим сигнал
            parsed_signal = await self._parse_signal(message.text or "", channel_info)
            
            if parsed_signal:
                # 3. Сохраняем обработанный сигнал
                parsed_signal_id = await self._save_parsed_signal(parsed_signal, raw_signal_id, channel_info)
                
                # 4. Создаем снимок рынка (если это торговый сигнал)
                if parsed_signal.get('symbol'):
                    await self._save_market_snapshot(parsed_signal_id, parsed_signal['symbol'])
                
                # 5. Создаем алерт
                await self._create_alert(parsed_signal, parsed_signal_id)
                
                self.stats['signals_parsed'] += 1
                logger.info(f"✅ Сигнал обработан: {parsed_signal.get('symbol', 'Unknown')} {parsed_signal.get('direction', 'Unknown')}")
            
            # Логируем статистику каждые 10 сообщений
            if self.stats['messages_received'] % 10 == 0:
                await self._log_stats()
                
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"❌ Ошибка обработки сообщения: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    async def _save_raw_signal(self, message, channel_info) -> str:
        """Сохранение сырого сообщения в signals_raw"""
        try:
            # Получаем ID источника
            source_result = self.supabase_client.table('signal_sources').select('id').eq('source_code', channel_info['source_code']).execute()
            source_id = source_result.data[0]['id'] if source_result.data else None
            
            # Извлекаем хэштеги и упоминания
            text = message.text or ""
            hashtags = re.findall(r'#(\w+)', text)
            mentions = re.findall(r'@(\w+)', text)
            
            # Простой анализ sentiment
            positive_words = ['buy', 'long', 'profit', 'target', 'bullish', 'up']
            negative_words = ['sell', 'short', 'loss', 'stop', 'bearish', 'down']
            
            text_lower = text.lower()
            pos_count = sum(1 for word in positive_words if word in text_lower)
            neg_count = sum(1 for word in negative_words if word in text_lower)
            
            sentiment_score = 0.0
            if pos_count + neg_count > 0:
                sentiment_score = (pos_count - neg_count) / (pos_count + neg_count)
            
            raw_data = {
                'source_id': source_id,
                'message_id': str(message.id),
                'channel_id': str(message.chat_id),
                'raw_text': text,
                'message_timestamp': message.date.isoformat(),
                'received_timestamp': datetime.now(timezone.utc).isoformat(),
                'sender_username': getattr(message.sender, 'username', None),
                'sender_id': str(message.sender_id) if message.sender_id else None,
                'message_type': 'text',
                'forwarded_from': str(message.forward.from_id) if message.forward else None,
                'hashtags': hashtags,
                'mentions': mentions,
                'character_count': len(text),
                'word_count': len(text.split()),
                'sentiment_score': sentiment_score,
                'urgency_indicators': [word for word in ['BREAKING', 'URGENT', 'NOW', 'ALERT'] if word in text.upper()],
                'processing_status': 'processed'
            }
            
            result = self.supabase_client.table('signals_raw').insert(raw_data).execute()
            
            if result.data:
                return result.data[0]['id']
            else:
                logger.error("Не удалось сохранить сырой сигнал")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения сырого сигнала: {e}")
            return None
    
    async def _parse_signal(self, text: str, channel_info: Dict) -> Optional[Dict]:
        """Парсинг торгового сигнала из текста"""
        if not text:
            return None
        
        # Ищем основные компоненты сигнала
        parsed = {}
        
        # Символ
        symbol_match = re.search(self.signal_patterns['symbol'], text, re.IGNORECASE)
        if symbol_match:
            parsed['symbol'] = symbol_match.group(1).upper()
        
        # Направление
        direction_match = re.search(self.signal_patterns['direction'], text, re.IGNORECASE)
        if direction_match:
            parsed['direction'] = direction_match.group(1).upper()
            parsed['signal_type'] = 'LONG' if direction_match.group(1).upper() in ['LONG', 'BUY'] else 'SHORT'
        
        # Цена входа
        entry_match = re.search(self.signal_patterns['entry'], text, re.IGNORECASE)
        if entry_match:
            parsed['entry_price'] = float(entry_match.group(1))
        
        # Стоп-лосс
        stop_match = re.search(self.signal_patterns['stop'], text, re.IGNORECASE)
        if stop_match:
            parsed['stop_loss'] = float(stop_match.group(1))
        
        # Цели (могут быть множественными)
        targets = re.findall(self.signal_patterns['targets'], text, re.IGNORECASE)
        if targets:
            parsed['take_profit_levels'] = [float(t) for t in targets]
        
        # Плечо
        leverage_match = re.search(self.signal_patterns['leverage'], text, re.IGNORECASE)
        if leverage_match:
            parsed['leverage'] = int(leverage_match.group(1))
        
        # Дополнительные уровни входа (как в примере ORDIUSDT)
        # Ищем числа которые могут быть уровнями входа
        numbers = re.findall(r'\b\d+\.?\d*\b', text)
        if len(numbers) > 3:  # Если много чисел, возможно это уровни
            try:
                entry_levels = []
                for num in numbers[1:5]:  # Берем следующие 4 числа после первого
                    level = float(num)
                    if parsed.get('entry_price') and abs(level - parsed['entry_price']) / parsed['entry_price'] < 0.1:  # В пределах 10%
                        entry_levels.append(level)
                if entry_levels:
                    parsed['entry_levels'] = entry_levels
            except:
                pass
        
        # Если нашли основные компоненты - это сигнал
        if parsed.get('symbol') and parsed.get('direction'):
            # Дополняем метаданными
            parsed.update({
                'signal_timestamp': datetime.now(timezone.utc).isoformat(),
                'confidence_score': self._calculate_confidence(parsed, text),
                'parsing_method': 'regex',
                'parser_version': 'v1.0.0',
                'validation_status': 'valid' if self._validate_signal(parsed) else 'suspicious',
                'technical_reason': self._extract_technical_reason(text),
                'timeframe': self._extract_timeframe(text),
                'tags': self._extract_tags(text)
            })
            
            return parsed
        
        return None
    
    def _calculate_confidence(self, parsed: Dict, text: str) -> float:
        """Расчет уверенности в правильности парсинга"""
        confidence = 0.5  # Базовая уверенность
        
        # Увеличиваем за наличие ключевых полей
        if parsed.get('entry_price'):
            confidence += 0.2
        if parsed.get('stop_loss'):
            confidence += 0.2
        if parsed.get('take_profit_levels'):
            confidence += 0.1
        
        # Проверяем логичность цен
        if parsed.get('entry_price') and parsed.get('stop_loss'):
            entry = parsed['entry_price']
            stop = parsed['stop_loss']
            direction = parsed.get('direction', '')
            
            if direction == 'LONG' and stop < entry:
                confidence += 0.1
            elif direction == 'SHORT' and stop > entry:
                confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _validate_signal(self, parsed: Dict) -> bool:
        """Валидация сигнала на логичность"""
        try:
            # Проверяем наличие обязательных полей
            if not all([parsed.get('symbol'), parsed.get('direction')]):
                return False
            
            # Проверяем логичность цен
            entry = parsed.get('entry_price')
            stop = parsed.get('stop_loss')
            direction = parsed.get('direction')
            
            if entry and stop and direction:
                if direction == 'LONG' and stop >= entry:
                    return False
                if direction == 'SHORT' and stop <= entry:
                    return False
            
            # Проверяем разумность плеча
            leverage = parsed.get('leverage', 1)
            if leverage > 100:  # Слишком высокое плечо
                return False
            
            return True
            
        except:
            return False
    
    def _extract_technical_reason(self, text: str) -> Optional[str]:
        """Извлечение технической причины сигнала"""
        technical_indicators = ['RSI', 'MACD', 'EMA', 'SMA', 'Support', 'Resistance', 'Breakout', 'Fibonacci']
        found_indicators = [indicator for indicator in technical_indicators if indicator.lower() in text.lower()]
        
        if found_indicators:
            return f"Technical: {', '.join(found_indicators)}"
        
        return None
    
    def _extract_timeframe(self, text: str) -> Optional[str]:
        """Извлечение таймфрейма"""
        timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w']
        for tf in timeframes:
            if tf in text.lower():
                return tf
        return None
    
    def _extract_tags(self, text: str) -> List[str]:
        """Извлечение тегов из текста"""
        tags = []
        
        # Типы сигналов
        if any(word in text.lower() for word in ['scalp', 'quick']):
            tags.append('scalping')
        if any(word in text.lower() for word in ['swing', 'hold']):
            tags.append('swing')
        if any(word in text.lower() for word in ['breakout', 'break']):
            tags.append('breakout')
        if any(word in text.lower() for word in ['reversal', 'reverse']):
            tags.append('reversal')
        
        return tags
    
    async def _save_parsed_signal(self, parsed_signal: Dict, raw_signal_id: str, channel_info: Dict) -> Optional[str]:
        """Сохранение обработанного сигнала"""
        try:
            # Получаем ID источника
            source_result = self.supabase_client.table('signal_sources').select('id').eq('source_code', channel_info['source_code']).execute()
            source_id = source_result.data[0]['id'] if source_result.data else None
            
            # Получаем или создаем инструмент
            instrument_id = await self._get_or_create_instrument(parsed_signal['symbol'])
            
            signal_data = {
                'raw_signal_id': raw_signal_id,
                'source_id': source_id,
                'instrument_id': instrument_id,
                'signal_type': parsed_signal.get('signal_type', 'UNKNOWN'),
                'symbol': parsed_signal['symbol'],
                'direction': parsed_signal['direction'],
                'entry_price': parsed_signal.get('entry_price'),
                'entry_levels': parsed_signal.get('entry_levels', []),
                'stop_loss': parsed_signal.get('stop_loss'),
                'take_profit_levels': parsed_signal.get('take_profit_levels', []),
                'leverage': parsed_signal.get('leverage'),
                'confidence_score': parsed_signal.get('confidence_score', 0.5),
                'signal_timestamp': parsed_signal['signal_timestamp'],
                'technical_reason': parsed_signal.get('technical_reason'),
                'timeframe': parsed_signal.get('timeframe'),
                'parsing_confidence': parsed_signal.get('confidence_score', 0.5),
                'parsing_method': parsed_signal.get('parsing_method', 'regex'),
                'parser_version': parsed_signal.get('parser_version', 'v1.0.0'),
                'validation_status': parsed_signal.get('validation_status', 'valid'),
                'tags': parsed_signal.get('tags', [])
            }
            
            result = self.supabase_client.table('signals_parsed').insert(signal_data).execute()
            
            if result.data:
                self.stats['signals_saved'] += 1
                return result.data[0]['id']
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения обработанного сигнала: {e}")
            return None
    
    async def _get_or_create_instrument(self, symbol: str) -> Optional[str]:
        """Получение инструмента (без создания, так как таблица instruments недоступна)"""
        try:
            # Возвращаем None, так как таблица instruments недоступна
            # В будущем можно будет использовать когда таблица будет создана
            logger.info(f"ℹ️ Инструмент {symbol} - используем без ID (таблица instruments недоступна)")
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка работы с инструментом {symbol}: {e}")
            return None
    
    async def _save_market_snapshot(self, signal_id: str, symbol: str):
        """Сохранение снимка рынка (пропускаем, так как таблица недоступна)"""
        try:
            # Таблица market_snapshots недоступна, пропускаем
            logger.info(f"ℹ️ Снимок рынка для {symbol} - пропущен (таблица недоступна)")
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения снимка рынка: {e}")
    
    async def _create_alert(self, parsed_signal: Dict, signal_id: str):
        """Создание алерта о новом сигнале (пропускаем, так как таблица недоступна)"""
        try:
            # Таблица alerts недоступна, просто логируем
            logger.info(f"🔔 Алерт для сигнала {parsed_signal['symbol']} {parsed_signal['direction']} - создан в логах")
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания алерта: {e}")
    
    async def _log_stats(self):
        """Логирование статистики"""
        logger.info(f"📊 Статистика: Сообщений: {self.stats['messages_received']}, "
                   f"Сигналов: {self.stats['signals_parsed']}, "
                   f"Сохранено: {self.stats['signals_saved']}, "
                   f"Ошибок: {self.stats['errors']}")

async def main():
    """Главная функция"""
    logger.info("🚀 Запуск Telegram to Supabase Sync")
    
    sync = TelegramSupabaseSync()
    
    if await sync.initialize():
        logger.info("✅ Инициализация завершена успешно")
        await sync.start_monitoring()
    else:
        logger.error("❌ Ошибка инициализации")
        return 1

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Остановка по запросу пользователя")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        sys.exit(1)
