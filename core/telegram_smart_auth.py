"""
УЛУЧШЕННАЯ СИСТЕМА TELEGRAM АВТОРИЗАЦИИ
- Автоматический поиск кодов в реальном времени
- Интеллектуальное обнаружение сообщений от @777000  
- Автоматический ввод найденных кодов
- Проверка валидности сессий
- Логика автоматического перезапроса
"""

import asyncio
import logging
import os
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from telethon import TelegramClient
from telethon.errors import (
    PhoneCodeInvalidError, 
    PhoneCodeExpiredError, 
    SessionPasswordNeededError,
    AuthKeyUnregisteredError,
    ApiIdInvalidError,
    PhoneNumberInvalidError,
    FloodWaitError
)

logger = logging.getLogger(__name__)

class SmartTelegramAuth:
    """
    Умная система авторизации Telegram с автоматическим поиском кодов
    """
    
    def __init__(self, api_id: str, api_hash: str, phone: str):
        self.api_id = int(api_id)
        self.api_hash = api_hash
        self.phone = phone
    
    async def smart_auth(self, session_path: str = 'ghost_session') -> bool:
        """
        УМНАЯ АВТОРИЗАЦИЯ с автоматическим поиском кодов
        """
        logger.info("🚀 Запуск УМНОЙ авторизации Telegram")
        logger.info(f"📞 Номер: {self.phone}")
        logger.info(f"💾 Сессия: {session_path}")
        
        try:
            # 1. Проверяем существующую сессию
            if await self._check_existing_session(session_path):
                logger.info("✅ Используем существующую рабочую сессию")
                return True
            
            # 2. Создаём новую авторизацию с поиском кодов
            return await self._create_new_session_with_smart_code_detection(session_path)
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка умной авторизации: {e}")
            return False
    
    async def _check_existing_session(self, session_path: str) -> bool:
        """Проверка существующей сессии"""
        session_file = f'{session_path}.session'
        
        if not os.path.exists(session_file):
            logger.info("📁 Файл сессии не найден")
            return False
        
        logger.info(f"🔍 Проверяем существующую сессию...")
        
        client = TelegramClient(session_path, self.api_id, self.api_hash)
        try:
            await client.connect()
            
            if await client.is_user_authorized():
                me = await client.get_me()
                logger.info(f"✅ Сессия действительна! Пользователь: {me.first_name}")
                return True
            else:
                logger.info("❌ Сессия недействительна")
                return False
                
        except Exception as e:
            logger.info(f"❌ Ошибка проверки сессии: {e}")
            return False
        finally:
            await client.disconnect()
    
    async def _create_new_session_with_smart_code_detection(self, session_path: str) -> bool:
        """
        Создание новой сессии с умным поиском кодов
        """
        logger.info("🔄 Создаём новую сессию с умным поиском кодов...")
        
        client = TelegramClient(session_path, self.api_id, self.api_hash)
        
        try:
            await client.connect()
            
            # 1. Отправляем запрос на код
            logger.info(f"📞 Отправляем запрос кода на {self.phone}")
            sent_code = await client.send_code_request(self.phone)
            
            logger.info("✅ Запрос кода отправлен!")
            logger.info("🔍 Начинаю поиск кода в сообщениях...")
            
            # 2. УМНЫЙ ПОИСК КОДА
            code = await self._smart_code_search()
            
            if not code:
                logger.error("❌ Код не найден автоматически")
                return False
            
            # 3. Авторизуемся с найденным кодом
            logger.info(f"🔐 Авторизуемся с кодом: {code}")
            await client.sign_in(phone=self.phone, code=code)
            
            # 4. Проверяем результат
            if await client.is_user_authorized():
                me = await client.get_me()
                logger.info(f"🎉 АВТОРИЗАЦИЯ УСПЕШНА! Пользователь: {me.first_name}")
                return True
            else:
                logger.error("❌ Авторизация не удалась")
                return False
                
        except PhoneCodeInvalidError:
            logger.error("❌ Неверный код авторизации")
            return False
        except PhoneCodeExpiredError:
            logger.error("❌ Код авторизации истёк")
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка создания сессии: {e}")
            return False
        finally:
            await client.disconnect()
    
    async def _smart_code_search(self, timeout_minutes: int = 5) -> Optional[str]:
        """
        УМНЫЙ ПОИСК кода в сообщениях Telegram
        """
        logger.info(f"🔍 Умный поиск кода в течение {timeout_minutes} минут...")
        
        # Попробуем найти код через все доступные сессии
        backup_sessions = [
            'ghost_session_backup',
            'ghost_session',
            'main_session',
            'telegram_session'
        ]
        
        start_time = datetime.now()
        timeout = timedelta(minutes=timeout_minutes)
        
        while datetime.now() - start_time < timeout:
            # Проверяем все возможные сессии
            for session_name in backup_sessions:
                try:
                    code = await self._search_code_in_session(session_name, start_time)
                    if code:
                        logger.info(f"🎉 КОД НАЙДЕН через сессию {session_name}: {code}")
                        return code
                except:
                    continue
            
            logger.info("⏳ Код не найден, ждём 10 секунд...")
            await asyncio.sleep(10)
        
        logger.error("⏰ Время поиска кода истекло")
        return None
    
    async def _search_code_in_session(self, session_name: str, start_time: datetime) -> Optional[str]:
        """Поиск кода через конкретную сессию"""
        session_file = f'{session_name}.session'
        
        if not os.path.exists(session_file):
            return None
        
        client = TelegramClient(session_name, self.api_id, self.api_hash)
        
        try:
            await client.connect()
            
            if not await client.is_user_authorized():
                return None
            
            logger.info(f"🔍 Ищем код через сессию {session_name}")
            
            # Поиск в официальных сообщениях Telegram
            code = await self._find_code_in_telegram_messages(client, start_time)
            if code:
                return code
            
            # Поиск в Saved Messages  
            code = await self._find_code_in_saved_messages(client, start_time)
            if code:
                return code
            
            return None
            
        finally:
            await client.disconnect()
    
    async def _find_code_in_telegram_messages(self, client: TelegramClient, start_time: datetime) -> Optional[str]:
        """Поиск кода в официальных сообщениях от Telegram"""
        try:
            # Ищем чат с Telegram Service
            entity = await client.get_entity(777000)  # Telegram Service Notifications
            
            logger.info("📱 Проверяем сообщения от Telegram Service (777000)...")
            
            time_threshold = start_time - timedelta(minutes=10)
            
            async for message in client.iter_messages(entity, limit=20):
                if not message.message or not message.date:
                    continue
                
                if message.date < time_threshold:
                    continue
                
                text = message.message
                logger.info(f"📩 Сообщение ({message.date}): {text}")
                
                code = self._extract_code_from_text(text)
                if code:
                    logger.info(f"✅ КОД НАЙДЕН в официальном сообщении: {code}")
                    return code
            
        except Exception as e:
            logger.debug(f"Ошибка поиска в официальных сообщениях: {e}")
        
        return None
    
    async def _find_code_in_saved_messages(self, client: TelegramClient, start_time: datetime) -> Optional[str]:
        """Поиск кода в Saved Messages"""
        try:
            me = await client.get_me()
            
            logger.info("💾 Проверяем Saved Messages...")
            
            time_threshold = start_time - timedelta(minutes=10)
            
            async for message in client.iter_messages(me.id, limit=15):
                if not message.message or not message.date:
                    continue
                
                if message.date < time_threshold:
                    continue
                
                text = message.message
                code = self._extract_code_from_text(text)
                if code:
                    logger.info(f"✅ КОД НАЙДЕН в Saved Messages: {code}")
                    return code
                    
        except Exception as e:
            logger.debug(f"Ошибка поиска в Saved Messages: {e}")
        
        return None
    
    def _extract_code_from_text(self, text: str) -> Optional[str]:
        """
        УЛУЧШЕННОЕ извлечение кода из текста
        """
        if not text:
            return None
        
        # Паттерны для поиска кода (в порядке приоритета)
        patterns = [
            # Точные паттерны Telegram
            r'Login code:\s*(\d{5,6})\.?\s*Do not give',  # Login code: 11690. Do not give...
            r'Login code:\s*(\d{5,6})',                    # Login code: 11690
            r'Код для входа:\s*(\d{5,6})',                 # Код для входа: 11690
            r'Your login code:\s*(\d{5,6})',               # Your login code: 11690
            r'Telegram code:\s*(\d{5,6})',                 # Telegram code: 11690
            
            # Общие паттерны
            r'(\d{5,6})\s*is your',                        # 11690 is your verification code  
            r'code:\s*(\d{5,6})',                          # code: 11690
            r'verification code:\s*(\d{5,6})',             # verification code: 11690
            
            # Простые паттерны (последний шанс)
            r'^(\d{5,6})\.?\s*Do not',                     # 11690. Do not give this code
            r'(\d{5,6})'                                   # просто число 5-6 цифр
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                code = match.group(1)
                if code.isdigit() and 4 <= len(code) <= 6:
                    return code
        
        return None

# Функция для использования в основной системе
async def create_smart_auth_client(api_id: str, api_hash: str, phone: str, session_path: str = 'ghost_session') -> Optional[TelegramClient]:
    """
    Создание авторизованного Telegram клиента с умной авторизацией
    """
    auth = SmartTelegramAuth(api_id, api_hash, phone)
    
    if await auth.smart_auth(session_path):
        # Создаём и возвращаем готовый клиент
        client = TelegramClient(session_path, int(api_id), api_hash)
        await client.connect()
        return client
    else:
        logger.error("❌ Умная авторизация не удалась")
        return None
