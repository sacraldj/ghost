#!/usr/bin/env python3
"""
ПРОСТОЙ ТЕСТ АВТОМАТИЧЕСКОЙ АВТОРИЗАЦИИ
Берем САМЫЙ СВЕЖИЙ код из Telegram Service
"""

import asyncio
import os
import re
from datetime import datetime
from telethon import TelegramClient
from telethon.errors import PhoneCodeInvalidError
from dotenv import load_dotenv

load_dotenv()

async def simple_auto_auth():
    api_id = int(os.getenv('TELEGRAM_API_ID'))
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone = os.getenv('TELEGRAM_PHONE')
    
    reader_session = 'ghost_code_reader'
    target_session = 'test_simple_auth'
    
    print("🤖 ПРОСТОЙ ТЕСТ АВТОМАТИЧЕСКОЙ АВТОРИЗАЦИИ")
    print("=" * 50)
    
    # Клиенты
    reader_client = TelegramClient(reader_session, api_id, api_hash)
    target_client = TelegramClient(target_session, api_id, api_hash)
    
    try:
        await reader_client.connect()
        await target_client.connect()
        
        # Проверяем reader
        if not await reader_client.is_user_authorized():
            print("❌ Reader не авторизован")
            return
            
        # Проверяем target
        if await target_client.is_user_authorized():
            print("✅ Target уже авторизован")
            return
        
        print("📱 Отправляем запрос кода...")
        await target_client.send_code_request(phone)
        
        print("⏰ Ждем 3 секунды для получения кода...")
        await asyncio.sleep(3)
        
        # Берем САМЫЙ СВЕЖИЙ код
        print("🔍 Ищем самый свежий код...")
        entity = await reader_client.get_entity(777000)
        
        latest_code = None
        async for message in reader_client.iter_messages(entity, limit=3):
            if message.message and "Login code:" in message.message:
                # Извлекаем код
                match = re.search(r'Login code:\s*(\d{5,6})', message.message)
                if match:
                    code = match.group(1)
                    print(f"📅 Найден код {code} от {message.date}")
                    latest_code = code
                    break  # Берем самый свежий
        
        if latest_code:
            print(f"🎯 ПРОБУЕМ КОД: {latest_code}")
            try:
                await target_client.sign_in(phone, latest_code)
                me = await target_client.get_me()
                print(f"🎉 УСПЕХ! Авторизован как {me.first_name}")
                return True
                
            except PhoneCodeInvalidError:
                print(f"❌ Код {latest_code} неверный или истек")
                return False
        else:
            print("❌ Код не найден")
            return False
            
    finally:
        await reader_client.disconnect()
        await target_client.disconnect()

if __name__ == "__main__":
    asyncio.run(simple_auto_auth())
