#!/usr/bin/env python3
"""
ФИНАЛЬНАЯ СИСТЕМА АВТОМАТИЧЕСКОЙ АВТОРИЗАЦИИ

ЭТАП 1: Создаем reader сессию (ОДИН РАЗ ввод кода)
ЭТАП 2: Все остальные сессии - АВТОМАТИЧЕСКИ

ЗАПУСК:
1. python final_auto_auth.py setup    # ОДИН РАЗ создать reader
2. python final_auto_auth.py auth session_name  # Авторизовать любую сессию АВТОМАТИЧЕСКИ
"""

import asyncio
import os
import re
import logging
import sys
from datetime import datetime, timedelta
from typing import Optional
from telethon import TelegramClient
from telethon.errors import PhoneCodeInvalidError, SessionPasswordNeededError
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FinalAutoAuth:
    """Финальная система автоматической авторизации"""
    
    def __init__(self):
        self.api_id = int(os.getenv('TELEGRAM_API_ID'))
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.phone = os.getenv('TELEGRAM_PHONE')
        self.reader_session = 'ghost_code_reader'
        
    async def setup_reader(self) -> bool:
        """ЭТАП 1: Создание reader сессии (один раз)"""
        print("🔑 ЭТАП 1: СОЗДАНИЕ READER СЕССИИ")
        print("=" * 50)
        print("🎯 Нужно ОДИН РАЗ ввести код")
        print("🚀 После этого ВСЕ сессии - АВТОМАТИЧЕСКИ!")
        print("=" * 50)
        
        # Проверяем уже есть ли
        if await self._check_session(self.reader_session):
            print("✅ Reader сессия уже готова!")
            return await self._test_reader()
        
        print(f"\n📱 Создаем {self.reader_session}...")
        print("🔢 Введите код ТОЛЬКО ОДИН РАЗ ↓")
        
        client = TelegramClient(self.reader_session, self.api_id, self.api_hash)
        
        try:
            await client.start(phone=self.phone)
            me = await client.get_me()
            
            print(f"\n🎉 READER СОЗДАН!")
            print(f"✅ {me.first_name} (@{me.username})")
            
            # Тест чтения кодов
            if await self._test_reader():
                print(f"\n🚀 ГОТОВО! Теперь автоматизируйте любые сессии:")
                print(f"   python {sys.argv[0]} auth session_name")
                return True
            else:
                print("❌ Проблема с доступом к кодам")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return False
        finally:
            await client.disconnect()
    
    async def _test_reader(self) -> bool:
        """Тест reader сессии"""
        try:
            client = TelegramClient(self.reader_session, self.api_id, self.api_hash)
            await client.connect()
            
            if not await client.is_user_authorized():
                await client.disconnect()
                return False
            
            # Тест доступа к кодам
            try:
                entity = await client.get_entity(777000)
                print(f"📱 Доступ к Telegram Service: ✅")
                
                # Проверяем можем ли читать сообщения
                async for message in client.iter_messages(entity, limit=1):
                    if message.message and "Login code:" in message.message:
                        print(f"📋 Найден код: {message.message[:30]}...")
                        break
                
                await client.disconnect()
                return True
                
            except Exception:
                # Если нет доступа к 777000, пробуем Saved Messages
                try:
                    me = await client.get_me()
                    print(f"💾 Используем Saved Messages для кодов")
                    await client.disconnect()
                    return True
                except Exception:
                    await client.disconnect()
                    return False
            
        except Exception as e:
            logger.debug(f"Тест reader: {e}")
            return False
    
    async def auto_auth(self, target_session: str) -> bool:
        """ЭТАП 2: Автоматическая авторизация любой сессии"""
        logger.info(f"🤖 АВТОМАТИЧЕСКАЯ АВТОРИЗАЦИЯ: {target_session}")
        
        # 1. Проверяем reader
        if not await self._check_session(self.reader_session):
            logger.error("❌ Reader сессия не найдена!")
            logger.info("💡 Сначала запустите: python final_auto_auth.py setup")
            return False
        
        # 2. Проверяем target
        if await self._check_session(target_session):
            logger.info(f"✅ {target_session} уже авторизована")
            return True
        
        # 3. Автоматически авторизуем
        return await self._perform_auto_auth(target_session)
    
    async def _check_session(self, session_name: str) -> bool:
        """Проверяем сессию"""
        try:
            client = TelegramClient(session_name, self.api_id, self.api_hash)
            await client.connect()
            
            is_auth = await client.is_user_authorized()
            await client.disconnect()
            return is_auth
            
        except Exception:
            return False
    
    async def _perform_auto_auth(self, target_session: str) -> bool:
        """Автоматическая авторизация"""
        target_client = TelegramClient(target_session, self.api_id, self.api_hash)
        reader_client = TelegramClient(self.reader_session, self.api_id, self.api_hash)
        
        try:
            await target_client.connect()
            await reader_client.connect()
            
            # Отправляем запрос кода
            logger.info("📱 Отправляем запрос кода...")
            await target_client.send_code_request(self.phone)
            request_time = datetime.now()
            
            # Автоматически ищем и вводим код
            for attempt in range(6):
                logger.info(f"🔍 Поиск кода, попытка {attempt + 1}/6...")
                
                code = await self._find_code(reader_client, request_time)
                
                if code:
                    logger.info(f"🎯 КОД НАЙДЕН АВТОМАТИЧЕСКИ: {code}")
                    
                    try:
                        await target_client.sign_in(self.phone, code)
                        logger.info("✅ АВТОМАТИЧЕСКАЯ АВТОРИЗАЦИЯ УСПЕШНА!")
                        
                        me = await target_client.get_me()
                        logger.info(f"🎉 {me.first_name} (@{me.username})")
                        return True
                        
                    except PhoneCodeInvalidError:
                        logger.warning(f"❌ Код {code} неверный")
                        
                    except SessionPasswordNeededError:
                        logger.error("🔒 Требуется 2FA - автоматизация невозможна")
                        return False
                
                if attempt < 5:
                    await asyncio.sleep(10)
            
            logger.error("❌ Код не найден автоматически")
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            return False
            
        finally:
            await target_client.disconnect()
            await reader_client.disconnect()
    
    async def _find_code(self, client: TelegramClient, request_time: datetime) -> Optional[str]:
        """Автоматический поиск кода"""
        
        # Telegram Service (777000)
        try:
            entity = await client.get_entity(777000)
            time_threshold = request_time - timedelta(minutes=2)
            
            async for message in client.iter_messages(entity, limit=10):
                if not message.message or not message.date:
                    continue
                    
                if message.date < time_threshold:
                    continue
                
                code = self._extract_code(message.message)
                if code:
                    return code
        except Exception:
            pass
        
        # Saved Messages
        try:
            me = await client.get_me()
            time_threshold = request_time - timedelta(minutes=2)
            
            async for message in client.iter_messages(me.id, limit=5):
                if not message.message or not message.date:
                    continue
                    
                if message.date < time_threshold:
                    continue
                
                code = self._extract_code(message.message)
                if code:
                    return code
        except Exception:
            pass
        
        return None
    
    def _extract_code(self, text: str) -> Optional[str]:
        """Извлекаем код из текста"""
        if not text:
            return None
        
        patterns = [
            r'Login code:\s*(\d{5,6})',
            r'Код для входа:\s*(\d{5,6})', 
            r'(\d{5,6})\s*is your',
            r'(\d{5,6})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                code = match.group(1)
                if code.isdigit() and 4 <= len(code) <= 6:
                    return code
        
        return None


async def main():
    """Главная функция"""
    auth = FinalAutoAuth()
    
    if len(sys.argv) < 2:
        print("📋 ИСПОЛЬЗОВАНИЕ:")
        print(f"  {sys.argv[0]} setup                    # Создать reader (ОДИН РАЗ)")
        print(f"  {sys.argv[0]} auth session_name        # Авторизовать сессию АВТОМАТИЧЕСКИ")
        return
    
    command = sys.argv[1]
    
    if command == 'setup':
        print("🚀 НАСТРОЙКА АВТОМАТИЧЕСКОЙ АВТОРИЗАЦИИ")
        success = await auth.setup_reader()
        if success:
            print("\n✅ НАСТРОЙКА ЗАВЕРШЕНА! Теперь можете авторизовать любые сессии автоматически!")
        else:
            print("\n❌ Ошибка настройки")
            
    elif command == 'auth':
        if len(sys.argv) < 3:
            print("❌ Укажите имя сессии: python final_auto_auth.py auth session_name")
            return
            
        session_name = sys.argv[2]
        print(f"🤖 АВТОМАТИЧЕСКАЯ АВТОРИЗАЦИЯ: {session_name}")
        
        success = await auth.auto_auth(session_name)
        if success:
            print(f"\n🎉 ГОТОВО! Сессия {session_name} авторизована АВТОМАТИЧЕСКИ!")
        else:
            print(f"\n❌ Не удалось авторизовать {session_name}")
    
    else:
        print(f"❌ Неизвестная команда: {command}")


if __name__ == "__main__":
    asyncio.run(main())
