#!/usr/bin/env python3
"""
GHOST Channel ID Getter
Скрипт для получения ID Telegram каналов
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from telethon import TelegramClient
    from telethon.tl.types import Channel, Chat
except ImportError:
    print("❌ Telethon не установлен. Установи: pip install telethon")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_channel_ids():
    """Получение ID каналов"""
    
    # Загружаем конфигурацию из .env.local
    env_file = project_root / '.env.local'
    
    if not env_file.exists():
        print("❌ Файл .env.local не найден")
        return
    
    # Читаем переменные окружения
    with open(env_file, 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                value = value.strip('"\'')
                os.environ[key] = value
    
    # Проверяем наличие API ключей
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone = os.getenv('TELEGRAM_PHONE')
    
    if not all([api_id, api_hash]):
        print("❌ Не найдены TELEGRAM_API_ID или TELEGRAM_API_HASH в .env.local")
        print("📝 Добавь их в .env.local:")
        print('TELEGRAM_API_ID="твой_api_id"')
        print('TELEGRAM_API_HASH="твой_api_hash"')
        print('TELEGRAM_PHONE="+твой_номер"')
        return
    
    try:
        # Создаем клиент
        client = TelegramClient('ghost_channel_scanner', api_id, api_hash)
        
        print("🔗 Подключаемся к Telegram...")
        await client.start(phone=phone)
        
        if not await client.is_user_authorized():
            print("❌ Не авторизован в Telegram")
            return
        
        me = await client.get_me()
        print(f"✅ Авторизован как: {me.first_name} (@{me.username or 'нет username'})")
        
        print("\n📋 Получаем список ваших каналов и чатов...")
        
        # Получаем все диалоги
        dialogs = await client.get_dialogs()
        
        print(f"\n🔍 Найдено {len(dialogs)} диалогов:")
        print("=" * 80)
        
        channels_found = 0
        
        for dialog in dialogs:
            entity = dialog.entity
            
            # Фильтруем только каналы и супергруппы
            if isinstance(entity, Channel):
                channels_found += 1
                
                # Определяем тип
                entity_type = "Канал" if entity.broadcast else "Супергруппа"
                
                # Получаем базовую информацию
                title = entity.title or "Без названия"
                username = f"@{entity.username}" if entity.username else "Приватный"
                subscribers = entity.participants_count if hasattr(entity, 'participants_count') else "?"
                
                print(f"\n🔹 {entity_type}: {title}")
                print(f"   ID: {entity.id}")
                print(f"   Username: {username}")
                print(f"   Участников: {subscribers}")
                
                # Проверяем, подходит ли для мониторинга
                if any(keyword in title.lower() for keyword in ['signal', 'trade', 'crypto', 'vip']):
                    print(f"   ⭐ РЕКОМЕНДУЕТСЯ для мониторинга сигналов!")
                
                print(f"   📋 Для config: \"channel_id\": \"{entity.id}\"")
        
        if channels_found == 0:
            print("\n❌ Каналы не найдены")
            print("💡 Подпишись на каналы с торговыми сигналами и запусти скрипт снова")
        else:
            print(f"\n✅ Найдено {channels_found} каналов")
            print("\n📝 Скопируй нужные ID в config/telegram_channels.json")
        
        print("=" * 80)
        
        await client.disconnect()
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        print(f"❌ Ошибка: {e}")

async def main():
    """Главная функция"""
    print("🔍 GHOST Channel ID Scanner")
    print("Получение ID Telegram каналов для мониторинга сигналов\n")
    
    await get_channel_ids()
    
    print("\n📋 Следующие шаги:")
    print("1. Скопируй ID нужных каналов")
    print("2. Вставь их в config/telegram_channels.json")
    print("3. Запусти telegram listener: python3 scripts/start_telegram_listener.py")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Сканирование прервано")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        print(f"❌ Критическая ошибка: {e}")
