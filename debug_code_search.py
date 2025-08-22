#!/usr/bin/env python3
"""
Отладка поиска кода - проверяем что происходит при поиске
"""

import asyncio
import os
import re
from datetime import datetime, timedelta
from telethon import TelegramClient
from dotenv import load_dotenv

load_dotenv()

def extract_code_debug(text: str):
    """Отладочная версия извлечения кода"""
    if not text:
        return None
    
    print(f"🔍 Анализируем текст: '{text}'")
    
    patterns = [
        r'Login code:\s*(\d{5,6})',
        r'Код для входа:\s*(\d{5,6})', 
        r'(\d{5,6})\s*is your',
        r'(\d{5,6})'
    ]
    
    for i, pattern in enumerate(patterns):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            code = match.group(1)
            print(f"✅ Паттерн {i+1} нашел код: {code}")
            if code.isdigit() and 4 <= len(code) <= 6:
                print(f"✅ Код {code} валидный")
                return code
            else:
                print(f"❌ Код {code} невалидный")
    
    print("❌ Код не найден")
    return None

async def debug_search():
    api_id = int(os.getenv('TELEGRAM_API_ID'))
    api_hash = os.getenv('TELEGRAM_API_HASH')
    
    client = TelegramClient('ghost_code_reader', api_id, api_hash)
    
    try:
        await client.connect()
        
        print("🔍 ОТЛАДКА ПОИСКА КОДА")
        print("=" * 40)
        
        # Проверяем последние сообщения в Telegram Service
        entity = await client.get_entity(777000)
        
        print("📱 Последние 5 сообщений из Telegram Service:")
        now = datetime.now()
        
        async for message in client.iter_messages(entity, limit=5):
            if message.message and message.date:
                time_diff = now - message.date.replace(tzinfo=None)
                time_diff_minutes = time_diff.total_seconds() / 60
                
                print(f"\n⏰ {message.date} ({time_diff_minutes:.1f} мин назад)")
                print(f"📝 Текст: {message.message[:100]}...")
                
                code = extract_code_debug(message.message)
                if code:
                    print(f"🎯 НАЙДЕННЫЙ КОД: {code}")
                print("-" * 40)
        
        # Тест временной логики
        print(f"\n🕐 ТЕКУЩЕЕ ВРЕМЯ: {now}")
        print(f"🕐 ПОИСК КОДОВ ПОСЛЕ: {now - timedelta(minutes=2)}")
        
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(debug_search())
