#!/usr/bin/env python3
"""
Парсинг истории сообщений из Telegram каналов
Обрабатывает ВСЕ сообщения и сохраняет в базу данных
"""

import asyncio
import os
import json
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

try:
    from telethon import TelegramClient
    from supabase import create_client, Client
except ImportError as e:
    print(f"❌ Отсутствуют модули: {e}")
    print("Установите: pip install telethon supabase")
    exit(1)

# Добавляем путь к нашим модулям
sys.path.append('.')
sys.path.append('signals')
sys.path.append('core')

try:
    from signals.unified_signal_system import UnifiedSignalParser, SignalSource
except ImportError as e:
    print(f"⚠️ Не удалось импортировать парсер: {e}")
    print("Будем использовать базовый парсинг")

class ChannelHistoryParser:
    """Парсер истории каналов"""
    
    def __init__(self):
        # Telegram настройки
        self.api_id = os.getenv('TELEGRAM_API_ID')
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.phone = os.getenv('TELEGRAM_PHONE')
        
        # Supabase настройки
        self.supabase_url = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        # Клиенты
        self.telegram_client = None
        self.supabase_client = None
        self.signal_parser = None
        
        # Статистика
        self.stats = {
            'messages_processed': 0,
            'signals_found': 0,
            'signals_saved': 0,
            'errors': 0,
            'by_channel': {}
        }
        
        # Каналы для обработки
        self.channels = {
            '-1001263635145': {
                'name': 'КриптоАтака 24',
                'trader_id': 'cryptoattack24',
                'parser_type': 'cryptoattack24'
            },
            '-1001288385100': {
                'name': 'Whales Crypto Guide',
                'trader_id': 'whales_guide_main',
                'parser_type': 'whales_crypto_parser'
            }
        }
    
    async def initialize(self):
        """Инициализация всех компонентов"""
        print("🔧 Инициализация...")
        
        # Telegram клиент
        self.telegram_client = TelegramClient('ghost_session', self.api_id, self.api_hash)
        await self.telegram_client.start(phone=self.phone)
        
        if not await self.telegram_client.is_user_authorized():
            print("❌ Не авторизован в Telegram")
            return False
        
        # Supabase клиент
        self.supabase_client = create_client(self.supabase_url, self.supabase_key)
        
        # Парсер сигналов
        try:
            self.signal_parser = UnifiedSignalParser()
            print("✅ Unified Signal Parser загружен")
        except:
            print("⚠️ Используем базовый парсинг")
            
        print("✅ Инициализация завершена")
        return True
    
    async def parse_channel_history(self, channel_id: str, days_back: int = 7):
        """Парсинг истории канала"""
        channel_info = self.channels.get(channel_id)
        if not channel_info:
            print(f"❌ Канал {channel_id} не найден в конфигурации")
            return
        
        print(f"\n📡 Обработка канала: {channel_info['name']}")
        print(f"   ID: {channel_id}")
        print(f"   Trader: {channel_info['trader_id']}")
        
        # Временной диапазон
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        print(f"   Период: {start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}")
        
        try:
            entity = await self.telegram_client.get_entity(int(channel_id))
            print(f"   ✅ Подключен к каналу: {entity.title}")
            
            # Инициализируем статистику для канала
            self.stats['by_channel'][channel_id] = {
                'name': channel_info['name'],
                'messages': 0,
                'signals': 0,
                'saved': 0,
                'errors': 0
            }
            
            message_count = 0
            signals_found = 0
            
            # Получаем сообщения
            print(f"   📥 Получаем сообщения...")
            
            async for message in self.telegram_client.iter_messages(
                entity, 
                offset_date=end_date,
                reverse=True,
                limit=1000  # Ограничиваем для начала
            ):
                # Проверяем дату
                if message.date < start_date:
                    continue
                if message.date > end_date:
                    break
                
                message_count += 1
                self.stats['messages_processed'] += 1
                self.stats['by_channel'][channel_id]['messages'] += 1
                
                # Обрабатываем сообщение
                if message.text:
                    signal_data = await self.process_message(
                        message, 
                        channel_info
                    )
                    
                    if signal_data:
                        signals_found += 1
                        self.stats['signals_found'] += 1
                        self.stats['by_channel'][channel_id]['signals'] += 1
                        
                        # Сохраняем в базу
                        if await self.save_signal_to_db(signal_data, message, channel_info):
                            self.stats['signals_saved'] += 1
                            self.stats['by_channel'][channel_id]['saved'] += 1
                
                # Прогресс каждые 50 сообщений
                if message_count % 50 == 0:
                    print(f"   📊 Обработано: {message_count} сообщений, найдено: {signals_found} сигналов")
            
            print(f"   ✅ Завершено: {message_count} сообщений, {signals_found} сигналов")
            
        except Exception as e:
            print(f"   ❌ Ошибка обработки канала: {e}")
            self.stats['errors'] += 1
            if channel_id in self.stats['by_channel']:
                self.stats['by_channel'][channel_id]['errors'] += 1
    
    async def process_message(self, message, channel_info):
        """Обработка одного сообщения"""
        try:
            text = message.text or ""
            
            # Базовая фильтрация
            signal_keywords = [
                'long', 'short', 'buy', 'sell', 'entry', 'target', 'tp1', 'tp2', 'sl',
                'запампили', 'закрепился', 'рост', 'падение', 'сигнал', 'покупка', 'продажа'
            ]
            
            # Проверяем наличие ключевых слов
            text_lower = text.lower()
            has_signal_words = any(keyword in text_lower for keyword in signal_keywords)
            
            if not has_signal_words:
                return None
            
            # Используем унифицированный парсер если доступен
            if self.signal_parser:
                try:
                    signal_source = SignalSource.TELEGRAM
                    parsed = await self.signal_parser.parse_signal(
                        raw_text=text,
                        source=signal_source,
                        trader_id=channel_info['trader_id'],
                        message_id=str(message.id)
                    )
                    
                    if parsed and parsed.status.value != 'rejected':
                        return {
                            'unified_signal': parsed,
                            'raw_text': text,
                            'message_id': message.id,
                            'timestamp': message.date
                        }
                except Exception as e:
                    print(f"   ⚠️ Ошибка парсинга: {e}")
            
            # Базовый парсинг как fallback
            return {
                'raw_text': text,
                'message_id': message.id,
                'timestamp': message.date,
                'basic_signal': True
            }
            
        except Exception as e:
            print(f"   ❌ Ошибка обработки сообщения: {e}")
            return None
    
    async def save_signal_to_db(self, signal_data, message, channel_info):
        """Сохранение сигнала в базу данных"""
        try:
            # Подготавливаем данные для signals_raw
            raw_signal = {
                'signal_id': f"{channel_info['trader_id']}_{message.id}_{int(message.date.timestamp())}",
                'trader_id': channel_info['trader_id'],
                'raw_text': signal_data['raw_text'],
                'posted_at': message.date.isoformat(),
                'source_type': 'telegram',
                'channel_id': str(message.peer_id.channel_id) if hasattr(message.peer_id, 'channel_id') else 'unknown'
            }
            
            # Сохраняем сырой сигнал
            result = self.supabase_client.table('signals_raw').upsert(raw_signal).execute()
            
            # Если есть обработанный сигнал, сохраняем и его
            if 'unified_signal' in signal_data:
                unified_signal = signal_data['unified_signal']
                
                parsed_signal = {
                    'signal_id': raw_signal['signal_id'],
                    'trader_id': channel_info['trader_id'],
                    'symbol': unified_signal.symbol or 'UNKNOWN',
                    'side': unified_signal.side or 'UNKNOWN',
                    'entry_price': unified_signal.entry_prices[0] if unified_signal.entry_prices else None,
                    'tp1': unified_signal.targets[0] if len(unified_signal.targets) > 0 else None,
                    'tp2': unified_signal.targets[1] if len(unified_signal.targets) > 1 else None,
                    'sl': unified_signal.stop_loss,
                    'confidence': int(unified_signal.confidence * 100) if unified_signal.confidence else 50,
                    'is_valid': unified_signal.status.value != 'rejected',
                    'posted_at': message.date.isoformat()
                }
                
                # Сохраняем обработанный сигнал
                self.supabase_client.table('signals_parsed').upsert(parsed_signal).execute()
            
            return True
            
        except Exception as e:
            print(f"   ❌ Ошибка сохранения в БД: {e}")
            return False
    
    async def run_full_parsing(self, days_back: int = 7):
        """Запуск полного парсинга всех каналов"""
        print("🚀 ЗАПУСК ПОЛНОГО ПАРСИНГА КАНАЛОВ")
        print("=" * 50)
        
        if not await self.initialize():
            return False
        
        print(f"📊 Будет обработано каналов: {len(self.channels)}")
        print(f"📅 Период: последние {days_back} дней")
        
        # Обрабатываем каждый канал
        for channel_id in self.channels:
            await self.parse_channel_history(channel_id, days_back)
        
        # Финальная статистика
        print("\n" + "=" * 50)
        print("📊 ИТОГОВАЯ СТАТИСТИКА:")
        print(f"   Сообщений обработано: {self.stats['messages_processed']}")
        print(f"   Сигналов найдено: {self.stats['signals_found']}")
        print(f"   Сигналов сохранено: {self.stats['signals_saved']}")
        print(f"   Ошибок: {self.stats['errors']}")
        
        print("\n📋 ПО КАНАЛАМ:")
        for channel_id, stats in self.stats['by_channel'].items():
            print(f"   {stats['name']}:")
            print(f"     - Сообщений: {stats['messages']}")
            print(f"     - Сигналов: {stats['signals']}")
            print(f"     - Сохранено: {stats['saved']}")
            print(f"     - Ошибок: {stats['errors']}")
        
        await self.telegram_client.disconnect()
        
        print("\n✅ ПАРСИНГ ЗАВЕРШЕН!")
        return True

async def main():
    """Главная функция"""
    parser = ChannelHistoryParser()
    
    # Запускаем парсинг за последние 7 дней
    success = await parser.run_full_parsing(days_back=7)
    
    if success:
        print("\n🎉 Все каналы обработаны успешно!")
        print("💡 Проверьте базу данных - должны появиться новые сигналы")
    else:
        print("\n❌ Ошибка при обработке каналов")

if __name__ == "__main__":
    asyncio.run(main())
