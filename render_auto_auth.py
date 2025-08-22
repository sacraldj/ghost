#!/usr/bin/env python3
"""
АВТОМАТИЧЕСКАЯ АВТОРИЗАЦИЯ ЧЕРЕЗ RENDER API
Использует авторизованную сессию на Render для локальной авторизации
"""

import asyncio
import os
import requests
import logging
from datetime import datetime
from typing import Optional
from telethon import TelegramClient
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RenderAutoAuth:
    """Автоматическая авторизация через Render"""
    
    def __init__(self):
        self.api_id = int(os.getenv('TELEGRAM_API_ID'))
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.phone = os.getenv('TELEGRAM_PHONE')
        self.render_url = "https://ghost-kuxh.onrender.com"  # Твой домен
    
    async def authorize_via_render(self, session_name: str = 'ghost_session') -> bool:
        """Авторизация через Render API"""
        logger.info(f"🌐 АВТОРИЗАЦИЯ ЧЕРЕЗ RENDER: {session_name}")
        
        # 1. Проверяем уже авторизован ли
        if await self._check_local_session(session_name):
            logger.info(f"✅ Сессия {session_name} уже авторизована локально")
            return True
        
        # 2. Запрашиваем автоматическую авторизацию через Render
        try:
            logger.info("📡 Отправляем запрос на Render...")
            
            response = requests.post(
                f"{self.render_url}/api/telegram/auto-auth",
                json={
                    "phone": self.phone,
                    "session_name": session_name
                },
                timeout=60  # Даем время на обработку
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    logger.info("✅ Render принял запрос на авторизацию")
                    
                    # 3. Ждем результат
                    return await self._wait_for_auth_result(session_name)
                else:
                    logger.error(f"❌ Render отклонил запрос: {data.get('error')}")
                    return False
            else:
                logger.error(f"❌ Ошибка HTTP: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка связи с Render: {e}")
            return False
    
    async def _check_local_session(self, session_name: str) -> bool:
        """Проверяем локальную сессию"""
        try:
            client = TelegramClient(session_name, self.api_id, self.api_hash)
            await client.connect()
            
            is_auth = await client.is_user_authorized()
            await client.disconnect()
            
            return is_auth
            
        except Exception:
            return False
    
    async def _wait_for_auth_result(self, session_name: str, max_wait: int = 120) -> bool:
        """Ждем результат авторизации"""
        logger.info(f"⏰ Ждем авторизацию сессии {session_name} (до {max_wait}с)...")
        
        for attempt in range(max_wait // 10):
            # Проверяем локально
            if await self._check_local_session(session_name):
                logger.info(f"🎉 Сессия {session_name} авторизована!")
                return True
            
            # Проверяем статус через API
            try:
                response = requests.get(
                    f"{self.render_url}/api/telegram/auto-auth",
                    params={"session": session_name},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status', 'unknown')
                    logger.info(f"📊 Статус: {status}")
                    
                    if status == 'completed':
                        return True
                    elif status == 'failed':
                        logger.error("❌ Авторизация не удалась на Render")
                        return False
                        
            except Exception as e:
                logger.debug(f"Ошибка проверки статуса: {e}")
            
            # Ждем
            if attempt < (max_wait // 10) - 1:
                await asyncio.sleep(10)
        
        logger.error("⏰ Превышено время ожидания авторизации")
        return False


async def auto_auth_via_render(session_name: str = 'ghost_session') -> bool:
    """Главная функция для авторизации через Render"""
    auth = RenderAutoAuth()
    return await auth.authorize_via_render(session_name)


if __name__ == "__main__":
    import sys
    
    session_name = sys.argv[1] if len(sys.argv) > 1 else 'ghost_session'
    
    async def main():
        logger.info("🚀 АВТОМАТИЧЕСКАЯ АВТОРИЗАЦИЯ ЧЕРЕЗ RENDER")
        logger.info("=" * 50)
        
        success = await auto_auth_via_render(session_name)
        
        if success:
            print(f"\n🎉 УСПЕХ! Сессия {session_name} авторизована через Render!")
        else:
            print(f"\n❌ ОШИБКА! Не удалось авторизовать {session_name}")
        
        logger.info("=" * 50)
    
    asyncio.run(main())
