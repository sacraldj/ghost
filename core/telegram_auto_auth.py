"""
GHOST Telegram Auto Authentication System
Автоматическая авторизация Telegram без ручного ввода
Включает SMS API интеграцию и автоматическое получение кодов
"""

import asyncio
import logging
import json
import os
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from dotenv import load_dotenv
import httpx
import hashlib

# Загружаем переменные окружения
load_dotenv()

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

# Импортируем наш Rate Limiter
try:
    from core.telegram_rate_limiter import TelegramRateLimiter
except ImportError:
    logger.warning("⚠️ TelegramRateLimiter не найден")
    TelegramRateLimiter = None

# SMS Service удален - не используется

class TelegramAutoAuth:
    """Автоматическая авторизация Telegram"""
    
    def __init__(self, api_id: str, api_hash: str, phone: str = None, interactive: bool = True):
        self.api_id = int(api_id)
        self.api_hash = api_hash
        self.phone = phone or os.getenv('TELEGRAM_PHONE')
        self.interactive = interactive  # Разрешить ли ручной ввод
        
        # SMS сервисы удалены - не используются
        
        # Клиент
        self.client: Optional[TelegramClient] = None
        
        # ЗАЩИТА ОТ МНОГОКРАТНЫХ ПОДКЛЮЧЕНИЙ
        # Rate limiter можно отключить через переменную окружения DISABLE_RATE_LIMITER=1
        disable_rl = os.getenv('DISABLE_RATE_LIMITER') == '1'
        self.rate_limiter = None if disable_rl else (TelegramRateLimiter() if TelegramRateLimiter else None)
        
        # Настройки тайм-аутов
        self.code_timeout = 300  # 5 минут на получение кода
        self.sms_check_interval = 10  # Проверяем SMS каждые 10 секунд
        self.max_code_attempts = 2  # ДВЕ попытки автоввода кода (по требованию пользователя)
        
        # История попыток
        self.auth_attempts = []
        
        if self.rate_limiter:
            logger.info("TelegramAutoAuth initialized with rate limiting protection")
        else:
            logger.info("TelegramAutoAuth initialized without rate limiting")

    def get_manual_code_input(self, phone: str) -> Optional[str]:
        """
        Ручной ввод кода авторизации от пользователя
        
        Args:
            phone: номер телефона для которого запрашивается код
            
        Returns:
            Введенный пользователем код или None
        """
        try:
            print("\n" + "="*50)
            print("🔑 ТРЕБУЕТСЯ РУЧНОЙ ВВОД КОДА АВТОРИЗАЦИИ")
            print("="*50)
            print(f"📱 Телефон: {phone}")
            print("📨 Проверьте SMS или Telegram на этом устройстве")
            print("💡 Введите полученный код авторизации (5 цифр)")
            print("-"*50)
            
            # Запрашиваем код от пользователя
            code = input("🔢 Введите код: ").strip()
            
            # Валидация кода
            if not code:
                print("❌ Код не введен")
                return None
                
            # Проверяем что это цифры
            if not code.isdigit():
                print("❌ Код должен содержать только цифры")
                return None
                
            # Проверяем длину (обычно 5 цифр)
            if len(code) != 5:
                print("⚠️ Обычно код содержит 5 цифр, но попробуем...")
                
            logger.info(f"✅ Получен код от пользователя: {code}")
            return code
            
        except KeyboardInterrupt:
            print("\n❌ Ввод прерван пользователем")
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка ручного ввода кода: {e}")
            return None

    # SMS сервисы удалены - не используются

    # SMS код удален - не используется

    # SMS методы удалены - не используются

    # Все SMS методы удалены

    def _extract_code_from_sms(self, sms_text: str) -> Optional[str]:
        """Извлечение кода авторизации из текста SMS (улучшенный)"""
        if not sms_text or len(sms_text) < 4:
            return None
        
        # Очищаем текст от лишних символов
        cleaned_text = sms_text.strip()
        logger.debug(f"🔍 Поиск кода в тексте: '{cleaned_text[:100]}'...")
        
        # Паттерны для поиска кода в порядке приоритета (самые точные первыми)
        patterns = [
            # Точные паттерны для ТЕКУЩЕГО формата Telegram
            r'Login code:\s*(\d{5,6})\.?\s*Do not give',  # "Login code: 48827. Do not give..."
            r'Login code:\s*(\d{5,6})',                    # "Login code: 48827"
            r'Telegram code:\s*(\d{5,6})',
            r'Your login code:\s*(\d{5,6})',
            r'Verification code:\s*(\d{5,6})',
            
            # Паттерны для кода с контекстом безопасности
            r'(\d{5,6})\.?\s*Do not give this code',
            r'(\d{5,6})\.?\s*We never ask it for anything else',
            
            # Русские паттерны
            r'Код входа в Telegram:\s*(\d{5,6})',
            r'Ваш код:\s*(\d{5,6})',
            r'код авторизации:\s*(\d{5,6})',
            r'Код:\s*(\d{5,6})',
            r'код:\s*(\d{5,6})',
            
            # Общие паттерны
            r'Your code:\s*(\d{5,6})',
            r'code:\s*(\d{5,6})',
            r'Code:\s*(\d{5,6})',
            r'входа:\s*(\d{5,6})',
            r'авторизации:\s*(\d{5,6})',
            
            # Первые цифры в сообщении (часто код идет первым)
            r'^[^\d]*(\d{5,6})[^\d]',
            
            # Паттерны в скобках или кавычках
            r'["\'](\d{5,6})["\']',
            r'\[(\d{5,6})\]',
            r'\((\d{5,6})\)',
            
            # Общий поиск с границами слов
            r'\b(\d{5})\b',
            r'\b(\d{6})\b',
            
            # Последний резерв - любые 5-6 цифр подряд
            r'(\d{5,6})',
        ]
        
        for i, pattern in enumerate(patterns):
            try:
                matches = re.findall(pattern, cleaned_text, re.IGNORECASE)
                if matches:
                    # Берем первое совпадение
                    code = matches[0]
                    
                    # Проверяем, что код состоит только из цифр и имеет правильную длину
                    if code.isdigit() and 5 <= len(code) <= 6:
                        logger.info(f"🎯 КОД НАЙДЕН! Паттерн #{i+1}: '{pattern}' -> {code}")
                        return code
                        
            except re.error as e:
                logger.debug(f"⚠️ Ошибка в регулярном выражении #{i+1}: {e}")
                continue
        
        # Дополнительная проверка: ищем числа в тексте
        numbers = re.findall(r'\d{5,6}', cleaned_text)
        if numbers:
            # Берем первое число правильной длины
            for num in numbers:
                if 5 <= len(num) <= 6:
                    logger.debug(f"✅ Код найден дополнительным поиском: {num}")
                    return num
        
        logger.warning(f"❌ Код НЕ НАЙДЕН в тексте: '{cleaned_text[:200]}...'")
        logger.debug(f"📋 Проверено паттернов: {len(patterns)}")
        return None

    async def get_code_from_telegram_messages(self) -> Optional[str]:
        """Получение кода из сообщений Telegram (улучшенный метод)"""
        try:
            logger.info("📱 Ищем СВЕЖИЙ код авторизации в Telegram сообщениях...")
            logger.info("💡 Пробуем получить код через ЛЮБУЮ доступную сессию")
            
            # Попробуем все доступные сессии (включая резервные копии)
            session_files = [
                'ghost_session.session',
                'ghost_session_backup.session',  # Резервная копия для чтения сообщений
                'main_session.session', 
                'telegram_session.session',
                'reader_session.session'  # Дополнительная сессия только для чтения
            ]
            
            for session_file in session_files:
                if os.path.exists(session_file):
                    logger.info(f"🔍 Проверяем сессию: {session_file}")
                    code = await self._try_get_code_from_session(session_file)
                    if code:
                        logger.info(f"✅ НАЙДЕН СВЕЖИЙ КОД через {session_file}: {code}")
                        return code
            
            # Если нет готовых сессий, попробуем создать временную
            logger.info("🔄 Пробуем создать временную сессию для получения кода...")
            code = await self._get_code_from_temp_session()
            if code:
                logger.info(f"✅ НАЙДЕН СВЕЖИЙ КОД через временную сессию: {code}")
                return code
            
            logger.warning("⚠️ СВЕЖИЙ код не найден в сообщениях")
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения кода из Telegram: {e}")
            return None

    async def _try_get_code_from_session(self, session_name: str) -> Optional[str]:
        """Пытаемся получить код из конкретной сессии"""
        session_path = session_name.replace('.session', '')
        client = TelegramClient(session_path, self.api_id, self.api_hash)
        
        try:
            await client.connect()
            
            # Пытаемся получить код даже если сессия не полностью авторизована
            logger.info(f"🔗 Подключились к {session_name}, ищем код...")
            
            # Используем более агрессивный поиск кода
            code = await self._search_for_fresh_code(client)
            return code
            
        except Exception as e:
            logger.debug(f"⚠️ Ошибка с сессией {session_name}: {e}")
            return None
        finally:
            try:
                await client.disconnect()
            except:
                pass

    async def _search_for_fresh_code(self, client: TelegramClient) -> Optional[str]:
        """Агрессивный поиск СВЕЖЕГО кода в сообщениях"""
        try:
            current_time = datetime.now()
            # Ищем код только за последние 15 минут (свежий!)
            time_threshold = current_time - timedelta(minutes=15)
            
            logger.info("🔍 Ищем СВЕЖИЙ код за последние 15 минут...")
            
            # Способы поиска в порядке приоритета
            search_methods = [
                ("Telegram Service (777000)", self._search_in_telegram_service),
                ("Saved Messages", self._search_in_saved_messages),
                ("Все диалоги", self._search_in_all_dialogs)
            ]
            
            for method_name, search_func in search_methods:
                try:
                    logger.info(f"📱 Проверяем: {method_name}")
                    code = await search_func(client, time_threshold)
                    if code:
                        logger.info(f"🎯 НАЙДЕН СВЕЖИЙ КОД в {method_name}: {code}")
                        return code
                        
                except Exception as e:
                    logger.debug(f"⚠️ Ошибка поиска в {method_name}: {e}")
                    continue
            
            logger.info("❌ Свежий код не найден")
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка агрессивного поиска кода: {e}")
            return None

    async def _search_in_telegram_service(self, client: TelegramClient, time_threshold: datetime) -> Optional[str]:
        """Поиск в официальном Telegram Service (777000)"""
        try:
            # Пробуем получить чат 777000
            entity = await client.get_entity(777000)
            
            logger.info("📱 Проверяем сообщения от @777000 (Telegram Service)")
            
            async for message in client.iter_messages(entity, limit=10):
                if not message.text or not message.date:
                    continue
                
                # Проверяем что сообщение свежее (за последние 15 минут)
                if message.date.replace(tzinfo=None) < time_threshold:
                    continue
                
                code = self._extract_code_from_sms(message.text)
                if code:
                    logger.info(f"🎯 Найден код в сообщении от {message.date}: {message.text[:50]}...")
                    return code
                    
        except Exception as e:
            logger.debug(f"Не удалось проверить Telegram Service: {e}")
            
        return None

    async def _search_in_saved_messages(self, client: TelegramClient, time_threshold: datetime) -> Optional[str]:
        """Поиск в Saved Messages"""
        try:
            me = await client.get_me()
            
            logger.info("💾 Проверяем Saved Messages")
            
            async for message in client.iter_messages('me', limit=20):
                if not message.text or not message.date:
                    continue
                
                if message.date.replace(tzinfo=None) < time_threshold:
                    continue
                
                code = self._extract_code_from_sms(message.text)
                if code:
                    logger.info(f"🎯 Найден код в Saved Messages от {message.date}")
                    return code
                    
        except Exception as e:
            logger.debug(f"Не удалось проверить Saved Messages: {e}")
            
        return None

    async def _search_in_all_dialogs(self, client: TelegramClient, time_threshold: datetime) -> Optional[str]:
        """Поиск во всех диалогах (последняя попытка)"""
        try:
            logger.info("🌐 Проверяем все диалоги...")
            
            # Проверяем только первые 5 диалогов для экономии времени  
            dialog_count = 0
            async for dialog in client.iter_dialogs(limit=5):
                dialog_count += 1
                
                try:
                    async for message in client.iter_messages(dialog, limit=3):
                        if not message.text or not message.date:
                            continue
                        
                        if message.date.replace(tzinfo=None) < time_threshold:
                            continue
                        
                        code = self._extract_code_from_sms(message.text)
                        if code:
                            logger.info(f"🎯 Найден код в диалоге {dialog.name} от {message.date}")
                            return code
                            
                except:
                    continue
                    
            logger.info(f"🔍 Проверено {dialog_count} диалогов")
            
        except Exception as e:
            logger.debug(f"Ошибка поиска в диалогах: {e}")
            
            return None

    async def _get_code_from_existing_session(self) -> Optional[str]:
        """Получение кода через существующую сессию"""
        session_file = 'ghost_session.session'
        if not os.path.exists(session_file):
            return None
        
        session_client = TelegramClient('ghost_session', self.api_id, self.api_hash)
        try:
            await session_client.connect()
            
            if not await session_client.is_user_authorized():
                return None
            
            logger.info("📱 Используем существующую сессию для поиска кода")
            return await self._search_for_code_in_messages(session_client)
            
        finally:
            await session_client.disconnect()

    async def _get_code_from_temp_session(self) -> Optional[str]:
        """Получение кода через временную сессию"""
        temp_client = TelegramClient(':memory:', self.api_id, self.api_hash)
        try:
            await temp_client.connect()
            
            # Временная сессия обычно не авторизована, поэтому этот метод 
            # работает только если есть другие способы авторизации
            if await temp_client.is_user_authorized():
                return await self._search_for_code_in_messages(temp_client)
            else:
                return None
                
        finally:
            await temp_client.disconnect()

    async def _search_for_code_in_messages(self, client: TelegramClient) -> Optional[str]:
        """Поиск кода в сообщениях клиента"""
        start_time = datetime.now()
        timeout = timedelta(seconds=300)  # 5 минут
        check_interval = 8  # Проверяем каждые 8 секунд
        
        logger.info(f"🔍 Ищем код в сообщениях в течение {timeout.seconds} секунд...")
        
        while datetime.now() - start_time < timeout:
            try:
                # Проверяем сообщения от Telegram (777000)
                code = await self._check_telegram_official_messages(client, start_time)
                if code:
                    return code
                
                # Проверяем Saved Messages
                code = await self._check_saved_messages(client, start_time)
                if code:
                    return code
                
                # Проверяем все диалоги на случай если код пришел в неожиданное место
                code = await self._check_all_dialogs_for_code(client, start_time)
                if code:
                    return code
                
                logger.debug(f"⏳ Код не найден, ждем {check_interval} секунд...")
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.debug(f"Ошибка поиска кода: {e}")
                await asyncio.sleep(2)
        
        logger.warning("⏰ Время ожидания кода истекло")
        return None

    async def _check_telegram_official_messages(self, client: TelegramClient, start_time: datetime) -> Optional[str]:
        """Проверка официальных сообщений Telegram"""
        try:
            # Пробуем разные способы получить официальный чат Telegram
            telegram_entities = []
            
            # Способ 1: по ID 777000 (Telegram Service Notifications)
            try:
                entity = await client.get_entity(777000)
                telegram_entities.append(entity)
                logger.debug("✅ Найден чат Telegram по ID 777000")
            except:
                pass
            
            # Способ 2: по имени пользователя
            for username in ['telegram', 'Telegram']:
                try:
                    entity = await client.get_entity(username)
                    telegram_entities.append(entity)
                    logger.debug(f"✅ Найден чат Telegram по имени {username}")
                except:
                    continue
            
            # Проверяем сообщения во всех найденных чатах
            for entity in telegram_entities:
                async for message in client.iter_messages(entity, limit=15):
                    if message.message and message.date > start_time - timedelta(minutes=10):
                        text = message.message
                        logger.debug(f"🔍 Проверяем сообщение от Telegram: {text[:50]}...")
                        
                        code = self._extract_code_from_sms(text)
                        if code:
                            logger.info(f"✅ Найден код в официальных сообщениях Telegram: {code}")
                            return code
            
        except Exception as e:
            logger.debug(f"Ошибка проверки официальных сообщений Telegram: {e}")
        
        return None

    async def _check_saved_messages(self, client: TelegramClient, start_time: datetime) -> Optional[str]:
        """Проверка Saved Messages"""
        try:
            me = await client.get_me()
            
            async for message in client.iter_messages(me.id, limit=10):
                if message.message and message.date > start_time - timedelta(minutes=10):
                    text = message.message
                    logger.debug(f"🔍 Проверяем Saved Messages: {text[:50]}...")
                    
                    code = self._extract_code_from_sms(text)
                    if code:
                        logger.info(f"✅ Найден код в Saved Messages: {code}")
                        return code
                        
        except Exception as e:
            logger.debug(f"Ошибка проверки Saved Messages: {e}")
        
        return None

    async def _check_all_dialogs_for_code(self, client: TelegramClient, start_time: datetime) -> Optional[str]:
        """Проверка всех диалогов на случай если код пришел в неожиданное место"""
        try:
            checked_count = 0
            max_dialogs_to_check = 10  # Проверяем только первые 10 диалогов
            
            async for dialog in client.iter_dialogs(limit=max_dialogs_to_check):
                checked_count += 1
                
                # Проверяем только последние 3 сообщения в каждом диалоге
                async for message in client.iter_messages(dialog.entity, limit=3):
                    if message.message and message.date > start_time - timedelta(minutes=10):
                        text = message.message
                        
                        # Ищем код только если сообщение содержит ключевые слова
                        if any(keyword in text.lower() for keyword in ['login', 'code', 'telegram', 'код', 'авторизац']):
                            logger.debug(f"🔍 Потенциальный код в диалоге {dialog.name}: {text[:50]}...")
                            
                            code = self._extract_code_from_sms(text)
                            if code:
                                logger.info(f"✅ Найден код в диалоге {dialog.name}: {code}")
                                return code
            
            logger.debug(f"🔍 Проверено диалогов: {checked_count}")
            
        except Exception as e:
            logger.debug(f"Ошибка проверки всех диалогов: {e}")
        
        return None

    async def get_code_from_env(self) -> Optional[str]:
        """Получение кода из переменной окружения"""
        code = os.getenv('TELEGRAM_CODE')
        if code and code.isdigit() and len(code) in [5, 6]:
            logger.info(f"✅ Используем код из переменной окружения: {code}")
            return code
        return None

    async def get_auth_code(self, phone_number: str = None, skip_env: bool = False) -> Optional[str]:
        """Получение кода авторизации всеми доступными способами"""
        phone = phone_number or self.phone
        
        # Метод 1: Чтение из Telegram сообщений (приоритет для автоматического получения)
        logger.info("🔄 Пытаемся получить код из Telegram сообщений...")
        code = await self.get_code_from_telegram_messages()
        if code:
            return code
        
        # SMS сервисы удалены
        
        # ТОЛЬКО СВЕЖИЕ КОДЫ! Без старых из .env
        logger.error("❌ Не удалось получить СВЕЖИЙ код из Telegram сообщений")
        logger.info("💡 Убедитесь что:")
        logger.info("  1. Код приходит в Telegram от @777000")
        logger.info("  2. У вас есть доступ к чтению сообщений в одной из сессий")
        logger.info("  3. Код свежий (за последние 15 минут)")
        logger.info("🚫 СТАРЫЕ КОДЫ из .env НЕ ИСПОЛЬЗУЮТСЯ!")
        
        return None

    async def get_auth_code_after_request(self, phone_number: str = None) -> Optional[str]:
        """Получение кода авторизации после отправки запроса (специально для новых сессий)"""
        phone = phone_number or self.phone
        
        logger.info("📱 Ожидаем код авторизации после отправки запроса...")
        
        # Увеличиваем время ожидания и делаем несколько попыток
        max_attempts = 5  # 5 попыток
        wait_time = 3     # Начинаем с 3 секунд
        
        for attempt in range(max_attempts):
            logger.info(f"⏰ Попытка {attempt + 1}/{max_attempts} получить код (ожидание: {wait_time}с)")
            await asyncio.sleep(wait_time)
            
            # Пробуем получить код из Telegram сообщений
            code = await self.get_code_from_telegram_messages()
            if code:
                logger.info(f"✅ КОД ПОЛУЧЕН на попытке {attempt + 1}: {code}")
                return code
            
            # Увеличиваем время ожидания для следующей попытки
            wait_time = min(wait_time + 2, 10)  # Максимум 10 секунд
        
        # SMS сервисы удалены
        
        # Метод 2: Поиск в существующих Telegram сессиях
        logger.info("🔄 Ищем код в Telegram сообщениях...")
        
        # Попробуем найти код в существующих сессиях (включая резервные копии)
        session_files = [
            'ghost_session',
            'ghost_session_backup',  # Резервная копия для чтения сообщений  
            'ghost_master_session', 
            'telegram_reader',
            'reader_session',        # Дополнительная сессия для чтения
            'main_session'
        ]
        
        for session_name in session_files:
            try:
                session_file = f'{session_name}.session'
                if os.path.exists(session_file):
                    logger.info(f"🔍 Проверяем сессию {session_name}...")
                    
                    temp_client = TelegramClient(session_name, self.api_id, self.api_hash)
                    await temp_client.connect()
                    
                    if await temp_client.is_user_authorized():
                        logger.info(f"✅ Используем сессию {session_name} для поиска кода")
                        
                        # Ищем код в сообщениях
                        start_time = datetime.now()
                        timeout = timedelta(seconds=120)  # 2 минуты ожидания
                        
                        for _ in range(12):  # 12 attempts = 60 seconds
                            code = await self.get_code_from_telegram_messages()
                            if code:
                                return code
                            await asyncio.sleep(5)
                        
                        logger.warning(f"⏰ Время ожидания кода в сессии {session_name} истекло")
                        await temp_client.disconnect()
                    else:
                        await temp_client.disconnect()
                        continue
                        
            except Exception as e:
                logger.debug(f"Ошибка работы с сессией {session_name}: {e}")
                continue
        
        # ТОЛЬКО СВЕЖИЕ КОДЫ! Никаких старых кодов из .env
        logger.error("❌ Не удалось получить СВЕЖИЙ код авторизации")
        logger.info("💡 Проверьте:")
        logger.info("  1. Свежий код должен прийти в Telegram от @777000")
        logger.info("  2. Код должен быть за последние 15 минут")
        logger.info("  3. Нужен доступ к одной из существующих сессий для чтения")
        logger.info("🚫 Система НЕ использует старые коды из .env - только свежие!")
        
        return None

    async def perform_auth(self, session_path: str = 'ghost_session') -> bool:
        """Выполнение полной автоматической авторизации"""
        try:
            # Проверяем наличие требуемых данных
            if not self.phone:
                logger.error("❌ Номер телефона не указан (TELEGRAM_PHONE)")
                return False
            
            # 🛡️ ПРОВЕРКА RATE LIMITER
            if self.rate_limiter:
                can_attempt, reason = self.rate_limiter.can_attempt_auth(self.phone)
                if not can_attempt:
                    logger.error(f"🚫 Попытка авторизации заблокирована: {reason}")
                    return False
                else:
                    logger.info("🛡️ Защита от частых подключений: попытка разрешена")
            
            logger.info(f"🔐 Начинаем автоматическую авторизацию для {self.phone}")
            
            # Создаем клиент
            self.client = TelegramClient(session_path, self.api_id, self.api_hash)
            
            # Подключаемся
            await self.client.connect()
            
            # Проверяем существующую авторизацию
            if await self.client.is_user_authorized():
                logger.info("✅ Клиент уже авторизован")
                # 📝 Записываем успешную попытку (авторизация уже была)
                if self.rate_limiter:
                    self.rate_limiter.record_attempt(self.phone, True)
                return True
            
            # Запускаем процесс авторизации
            for attempt in range(self.max_code_attempts):
                try:
                    logger.info(f"📞 Попытка авторизации {attempt + 1}/{self.max_code_attempts}")
                    
                    # Отправляем запрос кода
                    sent_code = await self.client.send_code_request(self.phone)
                    logger.info(f"📱 Код отправлен на номер {self.phone}")
                    
                    # Получаем код автоматически после отправки запроса
                    code = await self.get_auth_code_after_request(self.phone)
                    
                    if not code:
                        logger.warning(f"⚠️ Не удалось получить код автоматически, попытка {attempt + 1}")
                        if attempt < self.max_code_attempts - 1:
                            logger.info("⏳ Ждем 30 секунд перед следующей попыткой...")
                            await asyncio.sleep(30)
                            continue
                        else:
                            logger.error("❌ Исчерпаны все попытки автоматического получения кода")
                            logger.info("🔄 Переходим к ручному вводу кода...")
                            
                            # Попытка ручного ввода кода (если разрешена интерактивность)
                            if self.interactive:
                                manual_code = self.get_manual_code_input(self.phone)
                                if manual_code:
                                    code = manual_code
                                    logger.info("✅ Получен код через ручной ввод")
                                else:
                                    logger.error("❌ Ручной ввод кода не удался или был прерван")
                                    logger.info("💡 Как резерв можно установить TELEGRAM_CODE в переменные окружения")
                                    # 📝 Записываем неудачу получения кода
                                    if self.rate_limiter:
                                        self.rate_limiter.record_attempt(self.phone, False, "CodeNotReceived_ManualFailed")
                                    return False
                            else:
                                logger.error("❌ Автоматические попытки исчерпаны, интерактивный режим отключен")
                                logger.info("💡 Установите TELEGRAM_CODE в переменные окружения или включите interactive=True")
                                # 📝 Записываем неудачу получения кода
                                if self.rate_limiter:
                                    self.rate_limiter.record_attempt(self.phone, False, "CodeNotReceived_NonInteractive")
                                return False
                    
                    # Пытаемся авторизоваться с кодом
                    try:
                        await self.client.sign_in(self.phone, code)
                        logger.info("✅ Авторизация с кодом успешна!")
                        # 📝 Записываем успешную попытку
                        if self.rate_limiter:
                            self.rate_limiter.record_attempt(self.phone, True)
                        return True
                        
                    except SessionPasswordNeededError:
                        # Требуется 2FA пароль
                        password = os.getenv('TELEGRAM_PASSWORD')
                        if password:
                            logger.info("🔒 Вводим пароль 2FA")
                            await self.client.sign_in(password=password)
                            logger.info("✅ Авторизация с 2FA успешна!")
                            # 📝 Записываем успешную попытку с 2FA
                            if self.rate_limiter:
                                self.rate_limiter.record_attempt(self.phone, True)
                            return True
                        else:
                            logger.warning("⚠️ TELEGRAM_PASSWORD не установлен")
                            
                            if self.interactive:
                                logger.info("🔄 Переходим к ручному вводу пароля 2FA...")
                                print("\n" + "="*50)
                                print("🔒 ТРЕБУЕТСЯ ПАРОЛЬ ДВУХФАКТОРНОЙ АУТЕНТИФИКАЦИИ")
                                print("="*50)
                                print(f"📱 Телефон: {self.phone}")
                                print("🔑 Введите пароль от вашего Telegram аккаунта")
                                print("-"*50)
                                
                                try:
                                    manual_password = input("🔒 Введите пароль 2FA: ").strip()
                                    if manual_password:
                                        await self.client.sign_in(password=manual_password)
                                        logger.info("✅ Авторизация с ручным вводом 2FA пароля успешна!")
                                        # 📝 Записываем успешную попытку с ручным 2FA
                                        if self.rate_limiter:
                                            self.rate_limiter.record_attempt(self.phone, True)
                                        return True
                                    else:
                                        logger.error("❌ Пароль 2FA не введен")
                                        # 📝 Записываем неудачу 2FA
                                        if self.rate_limiter:
                                            self.rate_limiter.record_attempt(self.phone, False, "2FA_PasswordEmpty")
                                        return False
                                except KeyboardInterrupt:
                                    logger.error("❌ Ввод пароля 2FA прерван пользователем")
                                    # 📝 Записываем прерывание 2FA
                                    if self.rate_limiter:
                                        self.rate_limiter.record_attempt(self.phone, False, "2FA_InputCancelled")
                                    return False
                            else:
                                logger.error("❌ Требуется пароль 2FA, но интерактивный режим отключен")
                                logger.info("💡 Установите TELEGRAM_PASSWORD в переменные окружения или включите interactive=True")
                                # 📝 Записываем неудачу 2FA
                                if self.rate_limiter:
                                    self.rate_limiter.record_attempt(self.phone, False, "2FA_PasswordMissing_NonInteractive")
                                return False
                    
                    except FloodWaitError as e:
                        logger.info("⚠️ FloodWaitError игнорируется")
                        # Полностью игнорируем FloodWaitError
                        continue
                    
                    except (PhoneCodeInvalidError, PhoneCodeExpiredError) as e:
                        logger.warning(f"⚠️ Ошибка кода: {e}")
                        if attempt < self.max_code_attempts - 1:
                            logger.info("🔄 Пробуем получить новый код...")
                            await asyncio.sleep(10)
                            continue
                        else:
                            logger.warning("❌ Все автоматически полученные коды недействительны")
                            logger.info("🔄 Предлагаем ручной ввод нового кода...")
                            
                            # Последний шанс - ручной ввод свежего кода (если разрешена интерактивность)
                            if self.interactive:
                                manual_code = self.get_manual_code_input(self.phone)
                                if manual_code:
                                    try:
                                        await self.client.sign_in(self.phone, manual_code)
                                        logger.info("✅ Авторизация с ручным кодом успешна!")
                                        # 📝 Записываем успешную попытку с ручным кодом
                                        if self.rate_limiter:
                                            self.rate_limiter.record_attempt(self.phone, True)
                                        return True
                                    except (PhoneCodeInvalidError, PhoneCodeExpiredError):
                                        logger.error("❌ Ручной код также недействителен")
                            else:
                                logger.info("💡 Интерактивный режим отключен, ручной ввод недоступен")
                            
                            logger.error("❌ Все попытки ввода кода исчерпаны")
                            # 📝 Записываем неудачную попытку
                            if self.rate_limiter:
                                self.rate_limiter.record_attempt(self.phone, False, "AllCodesInvalid")
                            return False
                            
                except FloodWaitError as e:
                    logger.info("⚠️ FloodWaitError игнорируется, продолжаем...")
                    # Полностью игнорируем FloodWaitError
                    continue
                            
                except Exception as e:
                    logger.error(f"❌ Ошибка при попытке {attempt + 1}: {e}")
                    if attempt < self.max_code_attempts - 1:
                        await asyncio.sleep(15)
                        continue
                    else:
                        # 📝 Записываем критическую ошибку
                        if self.rate_limiter:
                            self.rate_limiter.record_attempt(self.phone, False, str(type(e).__name__))
                        raise
            
            # 📝 Все попытки исчерпаны - записываем неудачу
            if self.rate_limiter:
                self.rate_limiter.record_attempt(self.phone, False, "ExhaustedAttempts")
            return False
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка авторизации: {e}")
            # 📝 Записываем критическую ошибку
            if self.rate_limiter:
                self.rate_limiter.record_attempt(self.phone, False, f"CriticalError_{type(e).__name__}")
            return False

    async def validate_session(self, session_path: str = 'ghost_session') -> bool:
        """Проверка действительности сессии"""
        try:
            if not os.path.exists(f'{session_path}.session'):
                logger.info("📁 Файл сессии не найден")
                return False
            
            # Создаем тестовый клиент
            test_client = TelegramClient(session_path, self.api_id, self.api_hash)
            await test_client.connect()
            
            if await test_client.is_user_authorized():
                me = await test_client.get_me()
                logger.info(f"✅ Сессия действительна: {me.first_name} (@{me.username})")
                await test_client.disconnect()
                return True
            else:
                logger.warning("⚠️ Сессия недействительна")
                await test_client.disconnect()
                return False
                
        except AuthKeyUnregisteredError:
            logger.warning("⚠️ Ключ авторизации не зарегистрирован, сессия недействительна")
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка проверки сессии: {e}")
            return False

    async def ensure_auth(self, session_path: str = 'ghost_session') -> TelegramClient:
        """Гарантированная авторизация - проверяет сессию и авторизуется если нужно"""
        try:
            # Проверяем существующую сессию
            if await self.validate_session(session_path):
                logger.info("✅ Используем существующую действительную сессию")
                client = TelegramClient(session_path, self.api_id, self.api_hash)
                await client.connect()
                return client
            
            # Если сессия недействительна, НЕ УДАЛЯЕМ ее сразу
            # Сначала создаем резервную копию для чтения сообщений
            backup_session = f'{session_path}_backup'
            try:
                import shutil
                if os.path.exists(f'{session_path}.session'):
                    shutil.copy2(f'{session_path}.session', f'{backup_session}.session')
                    logger.info(f"💾 Создана резервная копия сессии для чтения сообщений: {backup_session}")
            except Exception as e:
                logger.debug(f"Не удалось создать резервную копию: {e}")
            
            # Выполняем новую авторизацию (БЕЗ удаления старой сессии)
            logger.info("🔄 Выполняем новую авторизацию...")
            auth_success = await self.perform_auth(session_path)
            
            if auth_success:
                # Если авторизация прошла успешно, ТОГДА удаляем старые файлы
                for ext in ['.session', '.session-journal']:
                    old_session_file = f'{session_path}_old{ext}'
                    session_file = f'{session_path}{ext}'
                    backup_file = f'{backup_session}{ext}'
                    
                    # Удаляем резервную копию
                    if os.path.exists(backup_file):
                        try:
                            os.remove(backup_file)
                            logger.debug(f"🗑️ Удалена резервная копию: {backup_file}")
                        except:
                            pass
                logger.info("✅ Авторизация успешна, старые сессии очищены")
                
            if auth_success:
                return self.client
            else:
                raise Exception("Не удалось выполнить авторизацию")
                
        except Exception as e:
            logger.error(f"❌ Ошибка обеспечения авторизации: {e}")
            raise

    def get_auth_statistics(self) -> Dict[str, Any]:
        """Получение статистики авторизации"""
        return {
            'phone': self.phone,
            'api_id': self.api_id,
            'auth_attempts': len(self.auth_attempts),
            'last_attempt': self.auth_attempts[-1] if self.auth_attempts else None
        }

# Функции для внешнего использования

async def create_auto_auth_client(api_id: str = None, api_hash: str = None, phone: str = None, interactive: bool = True) -> TelegramClient:
    """
    Создание клиента с автоматической авторизацией
    
    Args:
        api_id: ID API Telegram
        api_hash: Hash API Telegram  
        phone: номер телефона
        interactive: разрешить ли ручной ввод кода/пароля при неудаче автоматической авторизации
    """
    
    # Получаем параметры из переменных окружения если не переданы
    api_id = api_id or os.getenv('TELEGRAM_API_ID')
    api_hash = api_hash or os.getenv('TELEGRAM_API_HASH')
    phone = phone or os.getenv('TELEGRAM_PHONE')
    
    if not api_id or not api_hash:
        raise ValueError("TELEGRAM_API_ID и TELEGRAM_API_HASH обязательны")
    
    # Создаем авто-авторизатор с поддержкой интерактивности
    auth = TelegramAutoAuth(api_id, api_hash, phone, interactive=interactive)
    
    # Получаем авторизованный клиент
    return await auth.ensure_auth()

async def test_auto_auth():
    """Тестирование системы автоматической авторизации"""
    logger.info("🧪 Тестируем систему автоматической авторизации")
    
    try:
        # Тестируем создание клиента
        client = await create_auto_auth_client()
        
        # Проверяем авторизацию
        if await client.is_user_authorized():
            me = await client.get_me()
            logger.info(f"✅ Тест пройден: авторизован как {me.first_name} (@{me.username})")
            
            # Получаем список диалогов для проверки работоспособности
            dialog_count = 0
            async for dialog in client.iter_dialogs(limit=5):
                dialog_count += 1
                logger.info(f"  📋 Диалог: {dialog.name}")
            
            logger.info(f"📊 Найдено диалогов: {dialog_count}")
            
            await client.disconnect()
            return True
        else:
            logger.error("❌ Тест не прошел: клиент не авторизован")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_auto_auth())
