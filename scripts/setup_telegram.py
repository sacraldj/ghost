#!/usr/bin/env python3
"""
Скрипт для настройки Telegram авторизации
Создает сессию для доступа к каналам
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from telethon import TelegramClient

async def setup_telegram():
    """Настройка Telegram авторизации"""
    
    # Получаем API данные из .env
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    
    if not api_id or not api_hash:
        print("❌ Ошибка: TELEGRAM_API_ID и TELEGRAM_API_HASH не найдены в .env файле")
        print("💡 Получите их на https://my.telegram.org/apps")
        return False
    
    print("🔑 Настройка Telegram авторизации...")
    print(f"📱 API ID: {api_id}")
    print(f"🔐 API Hash: {api_hash[:10]}...")
    
    # Создаем клиент
    client = TelegramClient('ghost_session', int(api_id), api_hash)
    
    try:
        print("🚀 Подключение к Telegram...")
        await client.start()
        
        # Проверяем авторизацию
        if await client.is_user_authorized():
            me = await client.get_me()
            print(f"✅ Авторизация успешна!")
            print(f"👤 Пользователь: {me.first_name} (@{me.username})")
            print(f"📞 Телефон: {me.phone}")
            
            # Получаем список каналов
            print("\n📡 Доступные каналы:")
            dialogs = await client.get_dialogs()
            channels = []
            
            for dialog in dialogs:
                if dialog.is_channel:
                    channels.append({
                        'id': dialog.id,
                        'title': dialog.title,
                        'username': dialog.entity.username if hasattr(dialog.entity, 'username') else None
                    })
            
            if channels:
                print(f"Найдено {len(channels)} каналов:")
                for i, channel in enumerate(channels[:10]):  # Показываем первые 10
                    username = f"@{channel['username']}" if channel['username'] else "Приватный"
                    print(f"  {i+1}. {channel['title']} ({username}) - ID: {channel['id']}")
            else:
                print("  Каналов не найдено")
                
            print(f"\n💾 Сессия сохранена как 'ghost_session.session'")
            print("✅ Теперь модули могут подключаться к Telegram без интерактивного ввода")
            return True
            
        else:
            print("❌ Авторизация не удалась")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False
        
    finally:
        await client.disconnect()

def main():
    """Главная функция"""
    print("🎭 GHOST - Настройка Telegram")
    print("=" * 40)
    
    try:
        success = asyncio.run(setup_telegram())
        if success:
            print("\n🎉 Настройка завершена успешно!")
            print("🚀 Теперь можете запустить telegram_listener")
        else:
            print("\n💥 Настройка не удалась")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Настройка прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Неожиданная ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()