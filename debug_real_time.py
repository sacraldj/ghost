#!/usr/bin/env python3
"""
Отладка в реальном времени - проверяем коды прямо сейчас
"""

import asyncio
import os
import re
from datetime import datetime
from telethon import TelegramClient
from dotenv import load_dotenv

load_dotenv()

async def debug_real_time():
    api_id = int(os.getenv('TELEGRAM_API_ID'))
    api_hash = os.getenv('TELEGRAM_API_HASH')
    
    client = TelegramClient('ghost_code_reader', api_id, api_hash)
    
    try:
        await client.connect()
        
        entity = await client.get_entity(777000)
        
        print(f"🕐 ТЕКУЩЕЕ ВРЕМЯ: {datetime.now()}")
        print("🔍 ПОСЛЕДНИЕ КОДЫ ИЗ TELEGRAM SERVICE:")
        print("=" * 50)
        
        async for message in client.iter_messages(entity, limit=8):
            if not message.message or not message.date:
                continue
                
            msg_time = message.date.replace(tzinfo=None)
            time_diff = datetime.now() - msg_time
            minutes_ago = time_diff.total_seconds() / 60
            
            # Ищем код
            code = None
            if "login code" in message.message.lower():
                match = re.search(r'Login code:\s*(\d{5,6})', message.message)
                if match:
                    code = match.group(1)
            
            print(f"⏰ {msg_time} ({minutes_ago:.1f} мин назад)")
            
            if code:
                print(f"🎯 КОД: {code}")
                
                # Проверяем свежесть
                if minutes_ago <= 30:
                    print(f"✅ СВЕЖИЙ КОД (< 30 мин)")
                else:
                    print(f"❌ СТАРЫЙ КОД (> 30 мин)")
            else:
                print(f"📝 {message.message[:60]}...")
                
            print("-" * 30)
            
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(debug_real_time())
