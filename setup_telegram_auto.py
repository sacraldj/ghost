#!/usr/bin/env python3
"""
Автоматическая настройка Telegram авторизации для Ghost системы
"""

import os
import asyncio
import logging
import re
from dotenv import load_dotenv, set_key

# Загружаем переменные окружения
load_dotenv()

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class TelegramAutoSetup:
    """Автоматическая настройка Telegram"""
    
    def __init__(self):
        self.api_id = None
        self.api_hash = None
        self.phone = None
        self.session_name = 'ghost_session'
        
    async def setup(self):
        """Основной процесс настройки"""
        print("🚀 АВТОМАТИЧЕСКАЯ НАСТРОЙКА TELEGRAM")
        print("=" * 50)
        
        # 1. Получаем API ключи
        if not await self.get_api_credentials():
            return False
            
        # 2. Получаем номер телефона
        if not self.get_phone_number():
            return False
            
        # 3. Выполняем авторизацию
        if not await self.perform_authorization():
            return False
            
        # 4. Получаем список каналов
        await self.get_channels_list()
        
        print("\n🎉 НАСТРОЙКА ЗАВЕРШЕНА УСПЕШНО!")
        print("✅ Telegram авторизован и готов к работе")
        print("💡 Обновите channel_id в config/sources.json")
        
        return True
    
    async def get_api_credentials(self):
        """Получение API ключей"""
        print("\n🔑 Проверка API ключей...")
        
        self.api_id = os.getenv('TELEGRAM_API_ID')
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        
        if self.api_id and self.api_hash:
            print(f"✅ API ID: {self.api_id}")
            print(f"✅ API Hash: {self.api_hash[:10]}...")
            return True
            
        print("❌ API ключи не найдены")
        print("\n📝 Получите API ключи:")
        print("1. Перейдите на https://my.telegram.org")
        print("2. Войдите с номером телефона")
        print("3. Создайте приложение в 'API development tools'")
        print("4. Скопируйте api_id и api_hash")
        
        while True:
            api_id = input("\n📱 Введите TELEGRAM_API_ID: ").strip()
            api_hash = input("🔐 Введите TELEGRAM_API_HASH: ").strip()
            
            if api_id and api_hash:
                # Сохраняем в .env
                env_file = '.env'
                set_key(env_file, 'TELEGRAM_API_ID', api_id)
                set_key(env_file, 'TELEGRAM_API_HASH', api_hash)
                
                self.api_id = api_id
                self.api_hash = api_hash
                
                print(f"✅ API ключи сохранены в {env_file}")
                return True
            else:
                print("❌ Необходимо ввести оба ключа!")
    
    def get_phone_number(self):
        """Получение номера телефона"""
        print("\n📞 Проверка номера телефона...")
        
        self.phone = os.getenv('TELEGRAM_PHONE')
        
        if self.phone:
            print(f"✅ Номер телефона: {self.phone}")
            return True
            
        print("❌ Номер телефона не найден")
        
        while True:
            phone = input("\n📱 Введите номер телефона (с кодом страны, например +1234567890): ").strip()
            
            # Проверяем формат номера
            if re.match(r'^\+\d{10,15}$', phone):
                # Сохраняем в .env
                env_file = '.env'
                set_key(env_file, 'TELEGRAM_PHONE', phone)
                
                self.phone = phone
                print(f"✅ Номер телефона сохранен: {phone}")
                return True
            else:
                print("❌ Неправильный формат! Используйте +1234567890")
    
    async def perform_authorization(self):
        """Выполнение авторизации"""
        print("\n🔐 Авторизация в Telegram...")
        
        try:
            from telethon import TelegramClient
            
            # Создаем клиент
            client = TelegramClient(self.session_name, self.api_id, self.api_hash)
            
            print("🔌 Подключение к Telegram...")
            await client.start()
            
            if not await client.is_user_authorized():
                print("📱 Отправляем код авторизации...")
                await client.send_code_request(self.phone)
                
                print("⏳ Ждите SMS с кодом...")
                print("💡 Код также может прийти в Telegram от @777000")
                
                # Автоматическое получение кода
                code = await self.get_auth_code(client)
                
                if not code:
                    # Fallback на ручной ввод
                    code = input("📱 Введите код из SMS/Telegram: ").strip()
                
                if code:
                    try:
                        await client.sign_in(self.phone, code)
                        print("✅ Авторизация успешна!")
                        
                    except Exception as e:
                        if "Two-step verification" in str(e) or "password" in str(e).lower():
                            password = input("🔒 Введите пароль двухфакторной аутентификации: ").strip()
                            if password:
                                await client.sign_in(password=password)
                                # Сохраняем пароль для автоматического использования
                                set_key('.env', 'TELEGRAM_PASSWORD', password)
                                print("✅ Авторизация с 2FA успешна!")
                        else:
                            raise e
            else:
                print("✅ Уже авторизован!")
            
            # Проверяем финальную авторизацию
            if await client.is_user_authorized():
                me = await client.get_me()
                print(f"👤 Авторизован как: {me.first_name} (@{me.username})")
                await client.disconnect()
                return True
            else:
                print("❌ Авторизация не удалась")
                await client.disconnect()
                return False
                
        except ImportError:
            print("❌ Telethon не установлен")
            print("💡 Установите: pip install telethon")
            return False
            
        except Exception as e:
            print(f"❌ Ошибка авторизации: {e}")
            return False
    
    async def get_auth_code(self, client):
        """Автоматическое получение кода авторизации"""
        try:
            print("🔍 Попытка автоматического получения кода...")
            
            # Ждем код в течение 60 секунд
            for attempt in range(60):
                try:
                    async for message in client.iter_messages(777000, limit=1):
                        if message.message:
                            # Ищем код в сообщении
                            code_patterns = [
                                r'Login code: (\d{5,6})',
                                r'code: (\d{5,6})',
                                r'(\d{5,6})',
                                r'код: (\d{5,6})',
                                r'Код: (\d{5,6})'
                            ]
                            
                            for pattern in code_patterns:
                                match = re.search(pattern, message.message)
                                if match:
                                    code = match.group(1)
                                    print(f"✅ Получен код автоматически: {code}")
                                    return code
                except:
                    pass
                
                await asyncio.sleep(1)
                
                if attempt % 10 == 0:
                    print(f"⏳ Ожидание кода... ({attempt}/60 сек)")
            
            print("⏰ Время ожидания истекло")
            return None
            
        except Exception as e:
            print(f"❌ Ошибка получения кода: {e}")
            return None
    
    async def get_channels_list(self):
        """Получение списка каналов"""
        print("\n📺 Получение списка ваших каналов...")
        
        try:
            from telethon import TelegramClient
            
            client = TelegramClient(self.session_name, self.api_id, self.api_hash)
            await client.start()
            
            if await client.is_user_authorized():
                print("\n📋 ВАШИ КАНАЛЫ:")
                print("-" * 40)
                
                channel_count = 0
                async for dialog in client.iter_dialogs():
                    if dialog.is_channel:
                        channel_count += 1
                        print(f"📺 {dialog.name}")
                        print(f"   ID: {dialog.id}")
                        if hasattr(dialog.entity, 'username') and dialog.entity.username:
                            print(f"   @{dialog.entity.username}")
                        print()
                
                if channel_count == 0:
                    print("⚠️  Каналы не найдены")
                    print("💡 Подпишитесь на каналы с торговыми сигналами")
                else:
                    print(f"✅ Найдено каналов: {channel_count}")
                    print("\n💡 Скопируйте нужные ID и обновите config/sources.json")
            
            await client.disconnect()
            
        except Exception as e:
            print(f"❌ Ошибка получения каналов: {e}")

async def main():
    """Основная функция"""
    try:
        setup = TelegramAutoSetup()
        success = await setup.setup()
        
        if success:
            print("\n🚀 СИСТЕМА ГОТОВА К РАБОТЕ!")
            print("📋 Следующие шаги:")
            print("1. Обновите channel_id в config/sources.json")
            print("2. Запустите систему: python scripts/start_live_system.py")
        else:
            print("\n❌ НАСТРОЙКА НЕ ЗАВЕРШЕНА")
            print("💡 Проверьте ошибки выше и попробуйте снова")
            
    except KeyboardInterrupt:
        print("\n👋 Настройка прервана пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
