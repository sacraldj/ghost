#!/usr/bin/env python3
"""
GHOST Telegram Setup Script
Интерактивная настройка Telegram listener

Usage:
    python scripts/setup_telegram.py
"""

import os
import asyncio
import logging
from telethon import TelegramClient
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


async def setup_telegram_session():
    """Интерактивная настройка Telegram сессии"""
    
    print("🤖 GHOST Telegram Setup")
    print("=" * 50)
    
    # Get API credentials
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    
    if not api_id or not api_hash:
        print("❌ Ошибка: TELEGRAM_API_ID и TELEGRAM_API_HASH не найдены")
        print("\n📝 Получите API ключи:")
        print("1. Перейдите на https://my.telegram.org")
        print("2. Войдите с номером телефона")
        print("3. Создайте новое приложение в 'API development tools'")
        print("4. Добавьте ключи в .env.local:")
        print("   TELEGRAM_API_ID=your_api_id")
        print("   TELEGRAM_API_HASH=your_api_hash")
        return False
    
    session_name = input("\n📱 Имя сессии (по умолчанию 'ghost_trader'): ").strip()
    if not session_name:
        session_name = "ghost_trader"
    
    print(f"\n🔧 Создаю сессию '{session_name}'...")
    
    try:
        client = TelegramClient(session_name, api_id, api_hash)
        
        await client.start()
        
        # Get account info
        me = await client.get_me()
        print(f"✅ Успешно вошли как: {me.first_name} (@{me.username})")
        
        # Test message sending (optional)
        test_send = input("\n📤 Отправить тестовое сообщение себе? (y/N): ").strip().lower()
        if test_send in ['y', 'yes']:
            await client.send_message('me', '🤖 GHOST Telegram listener настроен!')
            print("✅ Тестовое сообщение отправлено")
        
        await client.disconnect()
        
        print(f"\n🎉 Сессия '{session_name}.session' создана успешно!")
        print(f"📁 Файл сессии: {os.path.abspath(session_name + '.session')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания сессии: {e}")
        return False


async def test_channels_access():
    """Тест доступа к каналам"""
    
    print("\n🔍 Тестирование доступа к каналам...")
    
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_name = "ghost_trader"
    
    try:
        client = TelegramClient(session_name, api_id, api_hash)
        await client.start()
        
        # Get dialogs (chats/channels)
        print("\n📋 Ваши каналы и чаты:")
        async for dialog in client.iter_dialogs(limit=10):
            if dialog.is_channel:
                print(f"📢 {dialog.name} (ID: {dialog.id})")
            elif dialog.is_group:
                print(f"👥 {dialog.name} (ID: {dialog.id})")
        
        await client.disconnect()
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")


def main():
    """Main setup function"""
    
    print("🚀 Настройка GHOST Telegram Listener")
    
    choice = input("""
Выберите действие:
1. 🔧 Создать новую сессию
2. 🔍 Тестировать доступ к каналам  
3. 📝 Показать инструкции

Ваш выбор (1-3): """).strip()

    if choice == "1":
        success = asyncio.run(setup_telegram_session())
        if success:
            asyncio.run(test_channels_access())
    elif choice == "2":
        asyncio.run(test_channels_access())
    elif choice == "3":
        print("""
📖 Инструкции по настройке:

1. 🔑 Получите API ключи:
   - Перейдите на https://my.telegram.org
   - Войдите с номером телефона
   - Создайте приложение в 'API development tools'
   
2. 📝 Добавьте в .env.local:
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   
3. 🔧 Запустите настройку:
   python scripts/setup_telegram.py
   
4. 📋 Настройте каналы в:
   news_engine/config/telegram_channels.yaml
   
5. 🚀 Запустите listener:
   python news_engine/telegram_listener.py
""")
    else:
        print("❌ Неверный выбор")


if __name__ == "__main__":
    main()
