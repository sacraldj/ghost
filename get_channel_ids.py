#!/usr/bin/env python3
"""
Получение ID Telegram каналов по их названиям
"""

import asyncio
import os
import json
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

try:
    from telethon import TelegramClient
except ImportError:
    print("❌ telethon не установлен. Установите: pip install telethon")
    exit(1)

async def get_channel_ids():
    """Получение ID каналов"""
    
    # Получаем данные из .env
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone = os.getenv('TELEGRAM_PHONE')
    
    print(f"🔍 Поиск ID каналов...")
    
    if not api_id or not api_hash:
        print("❌ TELEGRAM_API_ID или TELEGRAM_API_HASH не найдены в .env")
        return False
        
    try:
        # Создаем клиент
        client = TelegramClient('ghost_session', api_id, api_hash)
        
        print("🔗 Подключаемся...")
        await client.start(phone=phone)
        
        if not await client.is_user_authorized():
            print("❌ Не авторизован в Telegram")
            return False
            
        print("✅ Авторизован!")
        
        # Список каналов для поиска (из конфигурации)
        channels_to_find = [
            "КриптоАтака 24",
            "@cryptoattack24", 
            "Whales Crypto Guide",
            "@Whalesguide",
            "2Trade Premium", 
            "@2trade_slivaem",
            "CoinPulse Signals",
            "@coinpulse_signals",
            "Crypto Hub VIP",
            "@crypto_hub_vip",
            "Slivaem Info",
            "@slivaeminfo"
        ]
        
        print(f"\n📋 Ищем {len(channels_to_find)} каналов...")
        
        found_channels = {}
        
        # Получаем все диалоги
        print("📥 Получаем список диалогов...")
        async for dialog in client.iter_dialogs(limit=200):
            dialog_name = dialog.name or ""
            dialog_username = getattr(dialog.entity, 'username', None)
            dialog_id = str(dialog.id)
            
            # Проверяем совпадения
            for search_term in channels_to_find:
                if search_term.lower() in dialog_name.lower() or \
                   (dialog_username and search_term.lower().replace('@', '') == dialog_username.lower()):
                    
                    found_channels[search_term] = {
                        "id": dialog_id,
                        "name": dialog_name,
                        "username": f"@{dialog_username}" if dialog_username else None,
                        "type": "channel" if dialog.is_channel else "group"
                    }
                    
                    print(f"  ✅ {search_term} → ID: {dialog_id} ({dialog_name})")
        
        # Дополнительный поиск по username
        print(f"\n🔍 Дополнительный поиск по username...")
        usernames_to_search = [
            "cryptoattack24",
            "Whalesguide", 
            "2trade_slivaem",
            "coinpulse_signals",
            "crypto_hub_vip",
            "slivaeminfo"
        ]
        
        for username in usernames_to_search:
            try:
                entity = await client.get_entity(username)
                entity_id = str(entity.id)
                entity_name = getattr(entity, 'title', getattr(entity, 'first_name', username))
                
                if username not in [k.lower().replace('@', '') for k in found_channels.keys()]:
                    found_channels[f"@{username}"] = {
                        "id": entity_id,
                        "name": entity_name,
                        "username": f"@{username}",
                        "type": "channel" if hasattr(entity, 'broadcast') else "group"
                    }
                    print(f"  ✅ @{username} → ID: {entity_id} ({entity_name})")
                    
            except Exception as e:
                print(f"  ❌ @{username} не найден: {e}")
        
        print(f"\n📊 Результат:")
        print(f"  Найдено каналов: {len(found_channels)}")
        
        # Сохраняем результат
        with open('found_channel_ids.json', 'w', encoding='utf-8') as f:
            json.dump(found_channels, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Результат сохранен в found_channel_ids.json")
        
        # Показываем итоговую таблицу
        print(f"\n📋 НАЙДЕННЫЕ КАНАЛЫ:")
        print(f"{'Название':<25} {'ID':<20} {'Username':<20}")
        print("-" * 65)
        
        for search_term, info in found_channels.items():
            name = info['name'][:22] + "..." if len(info['name']) > 25 else info['name']
            username = info['username'] or "N/A"
            print(f"{name:<25} {info['id']:<20} {username:<20}")
        
        await client.disconnect()
        return True
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(get_channel_ids())
    if success:
        print("\n✅ Поиск завершен успешно!")
    else:
        print("\n❌ Ошибка поиска каналов!")
