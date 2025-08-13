#!/usr/bin/env python3
"""
GHOST Telegram Listener Starter
Скрипт для запуска слушателя Telegram каналов
"""

import os
import sys
import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.telegram_listener import TelegramListener, ChannelConfig
from core.signal_router import SignalRouter

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/telegram_listener.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class TelegramListenerService:
    """Сервис для запуска и управления Telegram слушателем"""
    
    def __init__(self):
        self.listener: TelegramListener = None
        self.signal_router: SignalRouter = None
        self.running = False
        
        # Загружаем конфигурацию из переменных окружения
        self.load_env_config()
    
    def load_env_config(self):
        """Загрузка конфигурации из .env файла"""
        env_file = project_root / '.env.local'
        
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        value = value.strip('"\'')
                        os.environ[key] = value
        
        # Проверяем наличие необходимых переменных
        required_vars = [
            'TELEGRAM_API_ID',
            'TELEGRAM_API_HASH',
            'TELEGRAM_PHONE'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            sys.exit(1)
    
    async def initialize(self):
        """Инициализация сервиса"""
        try:
            logger.info("Initializing Telegram Listener Service...")
            
            # Создаем роутер сигналов
            self.signal_router = SignalRouter()
            
            # Создаем слушателя Telegram
            self.listener = TelegramListener(
                api_id=os.getenv('TELEGRAM_API_ID'),
                api_hash=os.getenv('TELEGRAM_API_HASH'),
                phone=os.getenv('TELEGRAM_PHONE')
            )
            
            # Инициализируем Telegram клиент
            if not await self.listener.initialize():
                logger.error("Failed to initialize Telegram client")
                return False
            
            # Загружаем конфигурацию каналов
            await self.load_channels_config()
            
            logger.info("Telegram Listener Service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing service: {e}")
            return False
    
    async def load_channels_config(self):
        """Загрузка конфигурации каналов"""
        config_file = project_root / 'config' / 'telegram_channels.json'
        
        if not config_file.exists():
            logger.warning(f"Channels config file not found: {config_file}")
            return
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Добавляем каналы в слушателя
            for channel_data in config_data.get('channels', []):
                # Пропускаем каналы без ID (нужно заполнить вручную)
                if not channel_data.get('channel_id'):
                    logger.warning(f"Skipping channel {channel_data.get('channel_name')} - no channel_id")
                    continue
                
                config = ChannelConfig(
                    channel_id=channel_data['channel_id'],
                    channel_name=channel_data['channel_name'],
                    trader_id=channel_data['trader_id'],
                    is_active=channel_data.get('is_active', True),
                    keywords_filter=channel_data.get('keywords_filter', []),
                    exclude_keywords=channel_data.get('exclude_keywords', [])
                )
                
                self.listener.add_channel(config)
                
                # Регистрируем трейдера в системе
                await self.register_trader(channel_data)
            
            logger.info(f"Loaded {len(self.listener.channels)} channels")
            
        except Exception as e:
            logger.error(f"Error loading channels config: {e}")
    
    async def register_trader(self, channel_data: dict):
        """Регистрация трейдера в системе"""
        try:
            # Здесь должна быть логика регистрации трейдера в БД
            # Пока просто логируем
            logger.info(f"Registering trader: {channel_data['trader_id']} ({channel_data['channel_name']})")
            
            # TODO: Добавить в trader_registry через API
            
        except Exception as e:
            logger.error(f"Error registering trader {channel_data['trader_id']}: {e}")
    
    async def start(self):
        """Запуск сервиса"""
        if self.running:
            logger.warning("Service is already running")
            return
        
        logger.info("Starting Telegram Listener Service...")
        self.running = True
        
        try:
            # Запускаем слушателя
            await self.listener.start_listening()
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, stopping...")
            
        except Exception as e:
            logger.error(f"Error in service: {e}")
            
        finally:
            await self.stop()
    
    async def stop(self):
        """Остановка сервиса"""
        if not self.running:
            return
        
        logger.info("Stopping Telegram Listener Service...")
        self.running = False
        
        if self.listener:
            await self.listener.stop()
        
        logger.info("Service stopped")
    
    def get_status(self):
        """Получение статуса сервиса"""
        if not self.running or not self.listener:
            return {
                'status': 'stopped',
                'timestamp': datetime.now().isoformat()
            }
        
        listener_stats = self.listener.get_statistics()
        router_stats = self.signal_router.get_statistics() if self.signal_router else {}
        
        return {
            'status': 'running',
            'listener_stats': listener_stats,
            'router_stats': router_stats,
            'timestamp': datetime.now().isoformat()
        }

async def main():
    """Главная функция"""
    logger.info("Starting GHOST Telegram Listener...")
    
    # Создаем директории для логов
    logs_dir = project_root / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    # Создаем сервис
    service = TelegramListenerService()
    
    # Инициализируем
    if not await service.initialize():
        logger.error("Failed to initialize service")
        sys.exit(1)
    
    # Запускаем
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Запуск с обработкой сигналов
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete.")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
