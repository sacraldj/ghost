#!/usr/bin/env python3
"""
Быстрый тест: может ли система читать сообщения из тестового канала
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).parent))
load_dotenv()

from telethon import TelegramClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_channel_access():
    """Тестируем доступ к каналу ghostsignaltest"""
    logger.info("🧪 ТЕСТ: Доступ к каналу t.me/ghostsignaltest")
    
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    
    # Тестируем разные сессии
    sessions_to_test = [
        'ghost_session',
        'ghost_session_test', 
        'test_session_74660'
    ]
    
    test_channel_id = 2974041293  # ID из конфигурации
    
    for session_name in sessions_to_test:
        try:
            logger.info(f"🔍 Тестируем сессию: {session_name}")
            
            client = TelegramClient(session_name, int(api_id), api_hash)
            await client.connect()
            
            if await client.is_user_authorized():
                me = await client.get_me()
                logger.info(f"✅ Сессия {session_name} авторизована: {me.first_name}")
                
                # Пробуем получить сообщения из тестового канала
                try:
                    logger.info(f"📱 Читаем сообщения из канала {test_channel_id}...")
                    
                    message_count = 0
                    recent_messages = []
                    
                    async for message in client.iter_messages(test_channel_id, limit=10):
                        message_count += 1
                        if message.message:
                            recent_messages.append({
                                'id': message.id,
                                'text': message.message[:100],
                                'date': message.date
                            })
                    
                    logger.info(f"📊 Найдено сообщений: {message_count}")
                    
                    if recent_messages:
                        logger.info("📝 Последние сообщения:")
                        for msg in recent_messages[:5]:
                            logger.info(f"   {msg['date']}: {msg['text']}...")
                        
                        logger.info(f"✅ УСПЕХ! Сессия {session_name} может читать канал!")
                        await client.disconnect()
                        return session_name
                    else:
                        logger.warning("⚠️ Канал пустой или нет доступа к сообщениям")
                
                except Exception as channel_error:
                    logger.error(f"❌ Ошибка доступа к каналу: {channel_error}")
            
            await client.disconnect()
            
        except Exception as e:
            logger.debug(f"Сессия {session_name} не работает: {e}")
            continue
    
    logger.error("❌ Ни одна сессия не работает!")
    return None

async def main():
    working_session = await test_channel_access()
    
    if working_session:
        print(f"\n🎉 ГОТОВО! Используйте сессию: {working_session}")
        print("💡 Обновите конфигурацию чтобы использовать эту сессию")
        print("📱 Теперь отправьте сигнал в t.me/ghostsignaltest")
    else:
        print("\n❌ Нет рабочих сессий")
        print("💡 Нужно подождать снятия ограничений Telegram (~3 часа)")
        print("🔑 Или установить новый код: TELEGRAM_CODE=новый_код")

if __name__ == "__main__":
    asyncio.run(main())
