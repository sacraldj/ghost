#!/usr/bin/env python3
"""
РАБОЧАЯ АВТОМАТИЧЕСКАЯ АВТОРИЗАЦИЯ
Берем ПОСЛЕДНИЙ доступный код (без ограничений по времени)
"""

import asyncio
import os
import re
import logging
from typing import Optional
from telethon import TelegramClient
from telethon.errors import PhoneCodeInvalidError, SessionPasswordNeededError
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WorkingAutoAuth:
    """Рабочая автоматическая авторизация"""
    
    def __init__(self):
        self.api_id = int(os.getenv('TELEGRAM_API_ID'))
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.phone = os.getenv('TELEGRAM_PHONE')
        self.reader_session = 'ghost_code_reader'
    
    async def auto_auth(self, target_session: str) -> bool:
        """Автоматическая авторизация"""
        logger.info(f"🤖 РАБОЧАЯ АВТОРИЗАЦИЯ: {target_session}")
        
        # Проверяем target
        if await self._check_session(target_session):
            logger.info(f"✅ {target_session} уже авторизована")
            return True
        
        return await self._working_auth_process(target_session)
    
    async def _working_auth_process(self, target_session: str) -> bool:
        """Рабочий процесс авторизации"""
        target_client = TelegramClient(target_session, self.api_id, self.api_hash)
        reader_client = TelegramClient(self.reader_session, self.api_id, self.api_hash)
        
        try:
            await target_client.connect()
            
            # ВСЕГДА проверяем возможность восстановления reader сессии из переменной окружения
            logger.info("🔍 Проверяем наличие переменной окружения GHOST_READER_SESSION_B64...")
            if self._try_restore_reader_session():
                logger.info("✅ Reader сессия восстановлена из переменной окружения!")
            
            # Проверяем есть ли reader сессия
            reader_available = False
            try:
                await reader_client.connect()
                if await reader_client.is_user_authorized():
                    reader_available = True
                    logger.info("✅ Reader сессия доступна")
                else:
                    logger.warning("⚠️ Reader сессия не авторизована")
            except Exception as e:
                logger.warning(f"⚠️ Reader сессия недоступна: {e}")
            
            if not reader_available:
                logger.info("🔄 Работаем БЕЗ reader сессии - используем fallback")
                return await self._fallback_auth_process(target_client)
            
            # 1. Получаем последний доступный код СНАЧАЛА
            old_code = await self._get_latest_code(reader_client)
            if old_code:
                logger.info(f"📋 Последний код до запроса: {old_code}")
            
            # 2. Запрашиваем новый код
            logger.info("📱 Отправляем запрос НОВОГО кода...")
            await target_client.send_code_request(self.phone)
            
            # 3. Ждем и пробуем разные коды
            for attempt in range(6):
                logger.info(f"🔍 Поиск кода, попытка {attempt + 1}/6...")
                
                # Сначала ждем немного
                await asyncio.sleep(5)
                
                # Получаем актуальный последний код
                current_code = await self._get_latest_code(reader_client)
                
                if current_code and current_code != old_code:
                    logger.info(f"🆕 НОВЫЙ КОД НАЙДЕН: {current_code}")
                    code_to_try = current_code
                elif current_code:
                    logger.info(f"🔄 ИСПОЛЬЗУЕМ ПОСЛЕДНИЙ КОД: {current_code}")
                    code_to_try = current_code
                else:
                    logger.warning("❌ Коды не найдены")
                    continue
                
                # Пробуем код
                try:
                    await target_client.sign_in(self.phone, code_to_try)
                    logger.info("✅ АВТОРИЗАЦИЯ УСПЕШНА!")
                    
                    me = await target_client.get_me()
                    logger.info(f"🎉 {me.first_name} (@{me.username})")
                    return True
                    
                except PhoneCodeInvalidError:
                    logger.warning(f"❌ Код {code_to_try} не подошел")
                    old_code = current_code  # Обновляем чтобы не пробовать еще раз
                    
                except SessionPasswordNeededError:
                    logger.error("🔒 Требуется 2FA")
                    return False
            
            logger.error("❌ Не удалось авторизоваться")
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            return False
            
        finally:
            await target_client.disconnect()
            await reader_client.disconnect()
    
    async def _get_latest_code(self, client: TelegramClient) -> Optional[str]:
        """Получаем ПОСЛЕДНИЙ код из Telegram Service"""
        try:
            entity = await client.get_entity(777000)
            
            # Берем самое последнее сообщение с кодом
            async for message in client.iter_messages(entity, limit=10):
                if not message.message:
                    continue
                
                code = self._extract_code(message.message)
                if code:
                    logger.debug(f"📱 Найден код: {code} от {message.date}")
                    return code
            
            return None
            
        except Exception as e:
            logger.debug(f"Ошибка получения кода: {e}")
            return None
    
    def _extract_code(self, text: str) -> Optional[str]:
        """Извлекаем код из текста"""
        if not text or "login code" not in text.lower():
            return None
        
        match = re.search(r'Login code:\s*(\d{5,6})', text, re.IGNORECASE)
        
        if match:
            code = match.group(1)
            if code.isdigit() and 4 <= len(code) <= 6:
                return code
        
        return None
    
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
    
    def _try_restore_reader_session(self) -> bool:
        """Пробуем восстановить reader сессию из переменной окружения"""
        try:
            import base64
            
            # Имя переменной окружения с base64 данными
            env_var = 'GHOST_READER_SESSION_B64'
            session_data_b64 = os.getenv(env_var)
            
            logger.info(f"🔍 Ищем переменную {env_var}...")
            if not session_data_b64:
                logger.warning(f"❌ Переменная {env_var} не найдена в окружении!")
                return False
            
            logger.info(f"✅ Переменная {env_var} найдена! Размер: {len(session_data_b64)} символов")
            logger.info("🔄 Восстанавливаем reader сессию из переменной окружения...")
            
            # Декодируем base64
            session_data = base64.b64decode(session_data_b64)
            logger.info(f"✅ Base64 декодирован: {len(session_data)} байт")
            
            # Записываем в файл
            session_file = f'{self.reader_session}.session'
            logger.info(f"📁 Записываем в файл: {session_file}")
            with open(session_file, 'wb') as f:
                f.write(session_data)
            
            # Устанавливаем права доступа
            os.chmod(session_file, 0o600)
            
            logger.info(f"✅ Reader сессия успешно восстановлена: {len(session_data)} байт")
            return True
            
        except Exception as e:
            logger.debug(f"Ошибка восстановления reader сессии: {e}")
            return False
    
    async def _fallback_auth_process(self, target_client: TelegramClient) -> bool:
        """Fallback авторизация БЕЗ reader сессии"""
        logger.info("🆘 FALLBACK: Пробуем авторизацию без reader сессии")
        
        try:
            # Запрашиваем код
            logger.info("📱 Отправляем запрос кода...")
            await target_client.send_code_request(self.phone)
            
            # Ждем немного и пробуем использовать саму target сессию для чтения
            await asyncio.sleep(3)
            
            # Если target сессия хоть частично авторизована, можем попробовать читать через неё
            logger.info("🔄 Пробуем создать временный reader из target...")
            
            # Простой fallback - просим код вручную (только для тестирования)
            logger.error("⚠️ НУЖЕН READER SESSION!")
            logger.error("⚠️ Создайте ghost_code_reader.session на сервере")
            logger.error("⚠️ Или реализуйте другой способ получения кодов")
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Fallback ошибка: {e}")
            return False


async def working_auth_session(session_name: str) -> bool:
    """Рабочая автоматическая авторизация"""
    auth = WorkingAutoAuth()
    return await auth.auto_auth(session_name)


if __name__ == "__main__":
    import sys
    
    session_name = sys.argv[1] if len(sys.argv) > 1 else 'test_working_session'
    
    async def main():
        print("💪 РАБОЧАЯ АВТОМАТИЧЕСКАЯ АВТОРИЗАЦИЯ")
        print("=" * 50)
        
        success = await working_auth_session(session_name)
        
        if success:
            print(f"\n🎉 УСПЕХ! {session_name} авторизована!")
        else:
            print(f"\n❌ Ошибка авторизации {session_name}")
        
        print("=" * 50)
    
    asyncio.run(main())
