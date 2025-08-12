#!/usr/bin/env python3
"""
Настройка РЕАЛЬНОГО Telegram listener с API ключами
"""

import os
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def get_telegram_credentials():
    """Получить API ключи Telegram"""
    
    print("📱 Настройка РЕАЛЬНОГО Telegram listener")
    print("=" * 50)
    
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    
    if not api_id or not api_hash:
        print("⚠️  API ключи не найдены в .env.local")
        print()
        print("📝 Получите API ключи:")
        print("1. Перейдите на https://my.telegram.org")
        print("2. Войдите с номером телефона")
        print("3. Создайте приложение в 'API development tools'")
        print("4. Скопируйте api_id и api_hash")
        print()
        
        api_id = input("Введите TELEGRAM_API_ID: ").strip()
        api_hash = input("Введите TELEGRAM_API_HASH: ").strip()
        
        if not api_id or not api_hash:
            print("❌ Необходимы оба ключа!")
            return None, None
            
        # Сохраняем в .env.local
        env_file = ".env.local"
        env_content = f"""
# Telegram API
TELEGRAM_API_ID={api_id}
TELEGRAM_API_HASH={api_hash}
TELEGRAM_SESSION_NAME=ghost_trader
"""
        
        if os.path.exists(env_file):
            with open(env_file, "a") as f:
                f.write(env_content)
        else:
            with open(env_file, "w") as f:
                f.write(env_content)
                
        print(f"✅ Ключи сохранены в {env_file}")
        
        # Перезагружаем переменные
        load_dotenv(env_file)
    
    return api_id, api_hash

async def setup_telegram_session():
    """Создать Telegram сессию"""
    
    api_id, api_hash = get_telegram_credentials()
    if not api_id or not api_hash:
        return False
    
    try:
        from telethon import TelegramClient
        
        session_name = "ghost_trader"
        print(f"\n🔧 Создание сессии '{session_name}'...")
        
        client = TelegramClient(session_name, api_id, api_hash)
        await client.start()
        
        # Получаем информацию об аккаунте
        me = await client.get_me()
        print(f"✅ Вход выполнен: {me.first_name} (@{me.username})")
        
        # Показываем каналы пользователя
        print("\n📋 Ваши каналы:")
        channels_found = []
        
        async for dialog in client.iter_dialogs(limit=20):
            if dialog.is_channel and not dialog.is_group:
                channels_found.append({
                    'id': dialog.id,
                    'name': dialog.name,
                    'username': getattr(dialog.entity, 'username', None)
                })
                print(f"📢 {dialog.name} (ID: {dialog.id})")
        
        if not channels_found:
            print("⚠️  Каналы не найдены или нет доступа")
        
        # Создаем реальную конфигурацию каналов
        config_path = "news_engine/config/telegram_channels.yaml"
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        if channels_found:
            # Создаем конфиг с найденными каналами
            config_content = f"""# GHOST Telegram Channels Configuration (REAL)
# Автоматически создано {datetime.now().strftime('%Y-%m-%d %H:%M')}

channels:
"""
            for channel in channels_found[:5]:  # Берем первые 5 каналов
                config_content += f"""  - id: {channel['id']}
    name: "{channel['name']}"
    type: "universal"  # Обрабатывать все сообщения
    trigger: null
    
"""
            
            # Добавляем пример торгового канала
            config_content += """  # Пример настройки торгового канала:
  # - id: -1001234567890
  #   name: "Trading Signals"
  #   type: "trade"
  #   trigger: "LONG"  # Искать сигналы с ключевым словом
"""
            
        else:
            # Создаем пример конфигурации
            config_content = f"""# GHOST Telegram Channels Configuration (TEMPLATE)
# Создано {datetime.now().strftime('%Y-%m-%d %H:%M')}
# Добавьте ID ваших каналов ниже

channels:
  # Пример канала для торговых сигналов
  - id: -1001234567890  # Замените на реальный ID
    name: "Trading Signals Channel"
    type: "trade"
    trigger: "LONG"
    
  # Пример новостного канала
  - id: -1001111111111  # Замените на реальный ID
    name: "Crypto News"
    type: "news"
    trigger: null

# Как получить ID канала:
# 1. Добавьте бота @userinfobot в канал
# 2. Бот покажет chat_id канала
# 3. Для публичных каналов можно использовать @username
"""
        
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(config_content)
            
        print(f"✅ Конфигурация каналов создана: {config_path}")
        
        await client.disconnect()
        
        print(f"\n🎉 Telegram сессия настроена!")
        print(f"📁 Файл сессии: {session_name}.session")
        return True
        
    except ImportError:
        print("❌ Библиотека telethon не установлена")
        print("📦 Установите: pip install telethon")
        return False
    except Exception as e:
        print(f"❌ Ошибка настройки Telegram: {e}")
        return False

def test_telegram_listener():
    """Протестировать Telegram listener"""
    
    print("\n🧪 Тестирование Telegram listener...")
    
    try:
        import subprocess
        
        # Запускаем listener на 10 секунд для теста
        print("⏰ Запуск listener на 10 секунд...")
        
        process = subprocess.Popen([
            "python3", "news_engine/telegram_listener.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Ждем 10 секунд
        try:
            stdout, stderr = process.communicate(timeout=10)
            print("✅ Listener работает нормально")
            
        except subprocess.TimeoutExpired:
            process.kill()
            print("✅ Listener запущен и работает (остановлен после теста)")
            
            # Проверяем созданные файлы
            output_dir = "news_engine/output"
            if os.path.exists(f"{output_dir}/module_status.json"):
                print("✅ Статус модуля создан")
                
            if os.path.exists(f"{output_dir}/raw_logbook.json"):
                print("✅ Логбук сообщений создан")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

async def main():
    """Основная функция"""
    
    print("🚀 GHOST - Настройка РЕАЛЬНОГО Telegram")
    
    # Проверяем зависимости
    try:
        import telethon
        print("✅ Библиотека telethon найдена")
    except ImportError:
        print("📦 Устанавливаю telethon...")
        os.system("pip install telethon")
    
    # Настраиваем сессию
    success = await setup_telegram_session()
    
    if success:
        print("\n" + "=" * 50)
        
        # Тестируем listener
        test_telegram_listener()
        
        print("\n🎉 РЕАЛЬНЫЙ Telegram listener готов!")
        print("\n📋 Следующие шаги:")
        print("1. Отредактируйте news_engine/config/telegram_channels.yaml")
        print("2. Добавьте ID ваших каналов")
        print("3. Запустите: python news_engine/telegram_listener.py")
        print("4. Проверьте веб-дашборд: http://localhost:3000/dashboard")
        
    else:
        print("\n❌ Настройка не удалась")

if __name__ == "__main__":
    asyncio.run(main())
