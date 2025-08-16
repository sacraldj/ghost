#!/usr/bin/env python3
"""
Простой тест Telegram подключения
"""

import asyncio
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

try:
    from telethon import TelegramClient
except ImportError:
    print("❌ telethon не установлен. Установите: pip install telethon")
    exit(1)

async def test_telegram_connection():
    """Тест подключения к Telegram"""
    
    # Получаем данные из .env
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone = os.getenv('TELEGRAM_PHONE')
    
    print(f"📱 Тестирую подключение к Telegram...")
    print(f"API ID: {api_id}")
    print(f"Phone: {phone}")
    
    if not api_id or not api_hash:
        print("❌ TELEGRAM_API_ID или TELEGRAM_API_HASH не найдены в .env")
        return False
        
    try:
        # Создаем клиент
        client = TelegramClient('test_session', api_id, api_hash)
        
        print("🔗 Подключаемся...")
        await client.start(phone=phone)
        
        if await client.is_user_authorized():
            print("✅ Авторизация успешна!")
            
            # Получаем информацию о себе
            me = await client.get_me()
            print(f"👤 Пользователь: {me.first_name} {me.last_name or ''}")
            print(f"📞 Телефон: {me.phone}")
            
            # Получаем список диалогов
            print("\n📋 Последние диалоги:")
            async for dialog in client.iter_dialogs(limit=5):
                print(f"  - {dialog.name} (ID: {dialog.id})")
            
            await client.disconnect()
            return True
        else:
            print("❌ Авторизация не пройдена")
            await client.disconnect()
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_telegram_connection())
    if result:
        print("\n✅ Тест пройден успешно!")
    else:
        print("\n❌ Тест не пройден!")
