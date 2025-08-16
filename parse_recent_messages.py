#!/usr/bin/env python3
"""
Парсинг последних сообщений из каналов (без ограничения по дате)
"""

import asyncio
import os
import json
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

try:
    from telethon import TelegramClient
    from supabase import create_client, Client
except ImportError as e:
    print(f"❌ Отсутствуют модули: {e}")
    exit(1)

async def parse_recent_messages():
    """Парсинг последних сообщений"""
    
    # Настройки
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone = os.getenv('TELEGRAM_PHONE')
    
    supabase_url = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    print("🔧 Подключение к Telegram...")
    client = TelegramClient('ghost_session', api_id, api_hash)
    await client.start(phone=phone)
    
    print("🔧 Подключение к Supabase...")
    supabase = create_client(supabase_url, supabase_key)
    
    # Каналы
    channels = {
        '-1001263635145': 'cryptoattack24',  # КриптоАтака 24
        '-1001288385100': 'whales_guide_main'  # Whales Crypto Guide
    }
    
    total_messages = 0
    total_signals = 0
    
    for channel_id, trader_id in channels.items():
        print(f"\n📡 Канал: {channel_id} ({trader_id})")
        
        try:
            entity = await client.get_entity(int(channel_id))
            print(f"   ✅ Подключен: {entity.title}")
            
            message_count = 0
            signal_count = 0
            
            # Получаем последние 100 сообщений
            async for message in client.iter_messages(entity, limit=100):
                message_count += 1
                total_messages += 1
                
                if message.text:
                    text = message.text
                    
                    # Простая проверка на сигнал
                    signal_keywords = [
                        'запампили', 'закрепился', 'рост', 'топе', 'покупкам',
                        'long', 'short', 'buy', 'sell', 'entry', 'target', 'tp', 'sl'
                    ]
                    
                    text_lower = text.lower()
                    is_signal = any(keyword in text_lower for keyword in signal_keywords)
                    
                    if is_signal:
                        signal_count += 1
                        total_signals += 1
                        
                        # Создаем уникальный ID
                        signal_id = f"{trader_id}_{message.id}_{int(message.date.timestamp())}"
                        
                        # Сохраняем сырой сигнал
                        raw_signal = {
                            'signal_id': signal_id,
                            'trader_id': trader_id,
                            'raw_text': text[:1000],  # Ограничиваем длину
                            'posted_at': message.date.isoformat(),
                            'source_type': 'telegram',
                            'channel_id': channel_id
                        }
                        
                        try:
                            result = supabase.table('signals_raw').upsert(raw_signal).execute()
                            print(f"   💾 Сохранен сигнал: {signal_id}")
                            
                            # Простой парсинг для signals_parsed
                            parsed_signal = {
                                'signal_id': signal_id,
                                'trader_id': trader_id,
                                'symbol': 'UNKNOWN',
                                'side': 'UNKNOWN',
                                'confidence': 50,
                                'is_valid': True,
                                'posted_at': message.date.isoformat()
                            }
                            
                            # Попытка извлечь символ
                            words = text.upper().split()
                            for word in words:
                                if 'USDT' in word or 'BTC' in word or 'ETH' in word:
                                    parsed_signal['symbol'] = word
                                    break
                            
                            # Попытка определить направление
                            if any(word in text_lower for word in ['long', 'buy', 'покупка', 'запампили']):
                                parsed_signal['side'] = 'BUY'
                            elif any(word in text_lower for word in ['short', 'sell', 'продажа']):
                                parsed_signal['side'] = 'SELL'
                            
                            supabase.table('signals_parsed').upsert(parsed_signal).execute()
                            
                        except Exception as e:
                            print(f"   ❌ Ошибка сохранения: {e}")
                
                # Показываем прогресс
                if message_count % 20 == 0:
                    print(f"   📊 Обработано: {message_count}, найдено сигналов: {signal_count}")
            
            print(f"   ✅ Итого: {message_count} сообщений, {signal_count} сигналов")
            
        except Exception as e:
            print(f"   ❌ Ошибка канала {channel_id}: {e}")
    
    print(f"\n📊 ОБЩАЯ СТАТИСТИКА:")
    print(f"   Всего сообщений: {total_messages}")
    print(f"   Всего сигналов: {total_signals}")
    
    await client.disconnect()
    print("\n✅ Парсинг завершен!")

if __name__ == "__main__":
    asyncio.run(parse_recent_messages())
