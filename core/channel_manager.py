"""
GHOST Channel Manager
Централизованное управление множественными источниками сигналов
(Telegram каналы, Discord, Twitter, RSS, API и др.)
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import yaml

logger = logging.getLogger(__name__)

class SourceType(Enum):
    """Типы источников сигналов"""
    TELEGRAM_CHANNEL = "telegram_channel"
    TELEGRAM_GROUP = "telegram_group"
    DISCORD_CHANNEL = "discord_channel"
    TWITTER_ACCOUNT = "twitter_account"
    RSS_FEED = "rss_feed"
    WEBHOOK = "webhook"
    API_ENDPOINT = "api_endpoint"
    FILE_WATCHER = "file_watcher"

class SourceStatus(Enum):
    """Статусы источников"""
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    ERROR = "error"
    CONNECTING = "connecting"

@dataclass
class SourceConfig:
    """Конфигурация источника сигналов"""
    source_id: str
    source_type: SourceType
    name: str
    description: str
    
    # Подключение
    connection_params: Dict[str, Any]
    
    # Парсинг
    parser_type: str
    parser_config: Dict[str, Any]
    
    # Фильтрация
    filters: Dict[str, Any]
    
    # Статус и настройки
    status: SourceStatus = SourceStatus.ACTIVE
    priority: int = 100  # чем меньше - тем выше приоритет
    
    # Мониторинг
    check_interval: int = 60  # секунды
    max_retries: int = 3
    retry_delay: int = 300  # секунды
    
    # Метаданные
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_success: Optional[datetime] = None
    last_error: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()

@dataclass
class SourceStats:
    """Статистика по источнику"""
    source_id: str
    messages_received: int = 0
    signals_detected: int = 0
    signals_parsed: int = 0
    signals_successful: int = 0
    errors_count: int = 0
    uptime_percentage: float = 0.0
    avg_response_time: float = 0.0
    last_activity: Optional[datetime] = None

class ChannelManager:
    """Централизованный менеджер источников сигналов"""
    
    def __init__(self, config_dir: str = "config/sources"):
        self.config_dir = config_dir
        self.sources: Dict[str, SourceConfig] = {}
        self.listeners: Dict[str, Any] = {}  # Активные слушатели
        self.stats: Dict[str, SourceStats] = {}
        self.parser_registry: Dict[str, Callable] = {}
        
        # Создаем директорию конфигов если не существует
        os.makedirs(config_dir, exist_ok=True)
        
        # Автоматически загружаем источники из JSON конфигурации
        self.load_sources_from_json()
        
        logger.info(f"Channel Manager initialized with config dir: {config_dir}")
    
    def register_parser(self, parser_type: str, parser_class: Callable):
        """Регистрация парсера для определенного типа источника"""
        self.parser_registry[parser_type] = parser_class
        logger.info(f"Registered parser: {parser_type}")
    
    def add_source(self, source_config: SourceConfig) -> bool:
        """Добавление нового источника"""
        try:
            # Валидация конфигурации
            if not self._validate_source_config(source_config):
                return False
            
            # Добавляем в реестр
            self.sources[source_config.source_id] = source_config
            
            # Инициализируем статистику
            self.stats[source_config.source_id] = SourceStats(source_config.source_id)
            
            # Сохраняем конфигурацию
            self._save_source_config(source_config)
            
            logger.info(f"Added source: {source_config.name} ({source_config.source_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error adding source {source_config.source_id}: {e}")
            return False
    
    def load_sources_from_json(self) -> int:
        """Загрузка источников из JSON конфигурации"""
        loaded_count = 0
        json_config_path = "config/sources.json"
        
        try:
            if not os.path.exists(json_config_path):
                logger.warning(f"JSON config file not found: {json_config_path}")
                return 0
                
            with open(json_config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            sources = config_data.get('sources', [])
            
            for source_data in sources:
                try:
                    # Создаем SourceConfig из JSON данных
                    source_config = self._config_from_json_dict(source_data)
                    
                    if source_config and source_data.get('is_active', False):
                        # Добавляем источник в реестр
                        self.sources[source_config.source_id] = source_config
                        self.stats[source_config.source_id] = SourceStats(source_config.source_id)
                        loaded_count += 1
                        
                        logger.info(f"✅ Loaded active source: {source_config.name} ({source_config.source_id})")
                    else:
                        logger.debug(f"⏸️ Skipped inactive source: {source_data.get('name', 'Unknown')}")
                        
                except Exception as e:
                    logger.error(f"Error loading source from JSON: {e}")
                    
            logger.info(f"📡 Loaded {loaded_count} active sources from JSON config")
            return loaded_count
            
        except Exception as e:
            logger.error(f"Error loading sources from JSON config: {e}")
            return 0
    
    def _config_from_json_dict(self, data: Dict) -> Optional[SourceConfig]:
        """Создание SourceConfig из JSON данных"""
        try:
            # Преобразуем source_type в enum
            source_type = SourceType(data.get('source_type', 'telegram_channel'))
            
            # Создаем SourceConfig
            config = SourceConfig(
                source_id=data.get('source_id', ''),
                source_type=source_type,
                name=data.get('name', ''),
                description=data.get('notes', ''),
                connection_params=data.get('connection_params', {}),
                parser_type=data.get('parser_type', 'whales_universal'),
                parser_config={},
                filters={
                    'keywords_include': data.get('keywords_filter', []),
                    'keywords_exclude': data.get('exclude_keywords', [])
                },
                status=SourceStatus.ACTIVE if data.get('is_active', False) else SourceStatus.DISABLED,
                priority=data.get('priority', 100)
            )
            
            return config
            
        except Exception as e:
            logger.error(f"Error creating SourceConfig from JSON: {e}")
            return None
    
    def load_sources_from_config(self) -> int:
        """Загрузка всех источников из конфигурационных файлов"""
        loaded_count = 0
        
        try:
            # Ищем все YAML файлы в директории конфигов
            for filename in os.listdir(self.config_dir):
                if filename.endswith('.yaml') or filename.endswith('.yml'):
                    filepath = os.path.join(self.config_dir, filename)
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            config_data = yaml.safe_load(f)
                        
                        # Создаем SourceConfig из YAML
                        source_config = self._config_from_dict(config_data)
                        
                        if source_config and self.add_source(source_config):
                            loaded_count += 1
                            
                    except Exception as e:
                        logger.error(f"Error loading config from {filepath}: {e}")
            
            logger.info(f"Loaded {loaded_count} sources from config directory")
            return loaded_count
            
        except Exception as e:
            logger.error(f"Error loading sources from config: {e}")
            return 0
    
    async def start_source(self, source_id: str) -> bool:
        """Запуск конкретного источника"""
        if source_id not in self.sources:
            logger.error(f"Source not found: {source_id}")
            return False
        
        source = self.sources[source_id]
        
        try:
            # Проверяем что источник не уже запущен
            if source_id in self.listeners:
                logger.warning(f"Source {source_id} already running")
                return True
            
            # Обновляем статус
            source.status = SourceStatus.CONNECTING
            
            # Запускаем соответствующий слушатель
            listener = await self._create_listener(source)
            
            if listener:
                self.listeners[source_id] = listener
                source.status = SourceStatus.ACTIVE
                source.last_success = datetime.now()
                
                logger.info(f"Started source: {source.name}")
                return True
            else:
                source.status = SourceStatus.ERROR
                return False
                
        except Exception as e:
            logger.error(f"Error starting source {source_id}: {e}")
            source.status = SourceStatus.ERROR
            source.last_error = str(e)
            return False
    
    async def stop_source(self, source_id: str) -> bool:
        """Остановка конкретного источника"""
        if source_id not in self.listeners:
            logger.warning(f"Source {source_id} not running")
            return True
        
        try:
            listener = self.listeners[source_id]
            
            # Останавливаем слушатель
            if hasattr(listener, 'stop'):
                await listener.stop()
            elif hasattr(listener, 'close'):
                await listener.close()
            
            # Удаляем из активных
            del self.listeners[source_id]
            
            # Обновляем статус
            if source_id in self.sources:
                self.sources[source_id].status = SourceStatus.PAUSED
            
            logger.info(f"Stopped source: {source_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping source {source_id}: {e}")
            return False
    
    async def start_all_sources(self) -> Dict[str, bool]:
        """Запуск всех активных источников"""
        results = {}
        
        for source_id, source in self.sources.items():
            if source.status == SourceStatus.ACTIVE:
                results[source_id] = await self.start_source(source_id)
        
        active_count = sum(1 for success in results.values() if success)
        logger.info(f"Started {active_count}/{len(results)} sources")
        
        return results
    
    async def stop_all_sources(self) -> Dict[str, bool]:
        """Остановка всех источников"""
        results = {}
        
        for source_id in list(self.listeners.keys()):
            results[source_id] = await self.stop_source(source_id)
        
        return results
    
    def get_source_stats(self, source_id: str) -> Optional[SourceStats]:
        """Получение статистики по источнику"""
        return self.stats.get(source_id)
    
    def get_all_stats(self) -> Dict[str, SourceStats]:
        """Получение статистики по всем источникам"""
        return self.stats.copy()
    
    def get_active_sources(self) -> List[SourceConfig]:
        """Получение всех активных источников"""
        return [source for source in self.sources.values() if source.status == SourceStatus.ACTIVE]
    
    def update_source_stats(self, source_id: str, **kwargs):
        """Обновление статистики источника"""
        if source_id in self.stats:
            stats = self.stats[source_id]
            
            for key, value in kwargs.items():
                if hasattr(stats, key):
                    if key.endswith('_count'):
                        # Счетчики увеличиваем
                        setattr(stats, key, getattr(stats, key) + value)
                    else:
                        # Остальные значения устанавливаем
                        setattr(stats, key, value)
            
            stats.last_activity = datetime.now()
    
    async def _create_listener(self, source: SourceConfig) -> Optional[Any]:
        """Создание слушателя для конкретного источника"""
        try:
            if source.source_type == SourceType.TELEGRAM_CHANNEL:
                return await self._create_telegram_listener(source)
            elif source.source_type == SourceType.DISCORD_CHANNEL:
                return await self._create_discord_listener(source)
            elif source.source_type == SourceType.RSS_FEED:
                return await self._create_rss_listener(source)
            elif source.source_type == SourceType.WEBHOOK:
                return await self._create_webhook_listener(source)
            else:
                logger.error(f"Unsupported source type: {source.source_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating listener for {source.source_id}: {e}")
            return None
    
    async def _create_telegram_listener(self, source: SourceConfig) -> Optional[Any]:
        """Создание Telegram слушателя"""
        from core.telegram_listener import TelegramListener
        
        # Получаем параметры подключения
        params = source.connection_params
        
        # Создаем слушатель
        listener = TelegramListener(
            api_id=params.get('api_id'),
            api_hash=params.get('api_hash'),
            phone=params.get('phone')
        )
        
        # Инициализируем
        if await listener.initialize():
            # Добавляем канал
            from core.telegram_listener import ChannelConfig
            
            channel_config = ChannelConfig(
                channel_id=params.get('channel_id'),
                channel_name=source.name,
                trader_id=source.source_id,
                is_active=True,
                keywords_filter=source.filters.get('keywords_include', []),
                exclude_keywords=source.filters.get('keywords_exclude', [])
            )
            
            listener.add_channel(channel_config)
            
            # Запускаем прослушивание
            asyncio.create_task(listener.start_listening())
            
            return listener
        
        return None
    
    async def _create_discord_listener(self, source: SourceConfig) -> Optional[Any]:
        """Создание Discord слушателя (заглушка для будущей реализации)"""
        logger.info(f"Discord listener for {source.source_id} - not implemented yet")
        return None
    
    async def _create_rss_listener(self, source: SourceConfig) -> Optional[Any]:
        """Создание RSS слушателя (заглушка для будущей реализации)"""
        logger.info(f"RSS listener for {source.source_id} - not implemented yet")
        return None
    
    async def _create_webhook_listener(self, source: SourceConfig) -> Optional[Any]:
        """Создание Webhook слушателя (заглушка для будущей реализации)"""
        logger.info(f"Webhook listener for {source.source_id} - not implemented yet")
        return None
    
    def _validate_source_config(self, source: SourceConfig) -> bool:
        """Валидация конфигурации источника"""
        if not source.source_id:
            logger.error("Source ID is required")
            return False
        
        if source.source_id in self.sources:
            logger.error(f"Source ID already exists: {source.source_id}")
            return False
        
        if not source.connection_params:
            logger.error(f"Connection params required for {source.source_id}")
            return False
        
        return True
    
    def _save_source_config(self, source: SourceConfig):
        """Сохранение конфигурации источника в файл"""
        try:
            filename = f"{source.source_id}.yaml"
            filepath = os.path.join(self.config_dir, filename)
            
            # Конвертируем в словарь
            config_dict = asdict(source)
            
            # Конвертируем datetime в строки
            for key, value in config_dict.items():
                if isinstance(value, datetime):
                    config_dict[key] = value.isoformat()
            
            # Конвертируем enums в строки
            config_dict['source_type'] = source.source_type.value
            config_dict['status'] = source.status.value
            
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
                
        except Exception as e:
            logger.error(f"Error saving config for {source.source_id}: {e}")
    
    def _config_from_dict(self, config_data: Dict[str, Any]) -> Optional[SourceConfig]:
        """Создание SourceConfig из словаря"""
        try:
            # Конвертируем строки обратно в enums
            if 'source_type' in config_data:
                config_data['source_type'] = SourceType(config_data['source_type'])
            
            if 'status' in config_data:
                config_data['status'] = SourceStatus(config_data['status'])
            
            # Конвертируем строки обратно в datetime
            for date_field in ['created_at', 'updated_at', 'last_success']:
                if date_field in config_data and config_data[date_field]:
                    config_data[date_field] = datetime.fromisoformat(config_data[date_field])
            
            return SourceConfig(**config_data)
            
        except Exception as e:
            logger.error(f"Error creating SourceConfig from dict: {e}")
            return None


# Функция для создания примеров конфигураций
def create_example_sources():
    """Создание примеров конфигураций источников"""
    
    # 1. Whales Guide Telegram
    whales_guide = SourceConfig(
        source_id="whalesguide_telegram",
        source_type=SourceType.TELEGRAM_CHANNEL,
        name="Whales Guide",
        description="Main crypto signals channel",
        connection_params={
            "api_id": "YOUR_API_ID",
            "api_hash": "YOUR_API_HASH", 
            "phone": "YOUR_PHONE",
            "channel_id": "-1001234567890"
        },
        parser_type="whales_crypto_parser",
        parser_config={
            "confidence_threshold": 0.7,
            "auto_detect_trader": True
        },
        filters={
            "keywords_include": ["longing", "buying", "long", "short"],
            "keywords_exclude": ["spam", "promo", "advertisement"],
            "min_confidence": 0.8
        },
        priority=10  # Высокий приоритет
    )
    
    # 2. 2Trade Channel
    trade_2_channel = SourceConfig(
        source_id="2trade_telegram",
        source_type=SourceType.TELEGRAM_CHANNEL,
        name="2Trade Channel",
        description="Secondary signals source",
        connection_params={
            "api_id": "YOUR_API_ID",
            "api_hash": "YOUR_API_HASH",
            "phone": "YOUR_PHONE", 
            "channel_id": "-1001234567891"
        },
        parser_type="2trade_parser",
        parser_config={
            "confidence_threshold": 0.6
        },
        filters={
            "keywords_include": ["signal", "entry", "target"],
            "keywords_exclude": ["test", "demo"]
        },
        priority=20
    )
    
    # 3. VIP Private Group
    vip_group = SourceConfig(
        source_id="vip_private_group",
        source_type=SourceType.TELEGRAM_GROUP,
        name="VIP Private Signals",
        description="Premium signals group",
        connection_params={
            "api_id": "YOUR_API_ID",
            "api_hash": "YOUR_API_HASH",
            "phone": "YOUR_PHONE",
            "channel_id": "-1001234567892"
        },
        parser_type="vip_signals_parser",
        parser_config={
            "confidence_threshold": 0.9,
            "premium_features": True
        },
        filters={
            "keywords_include": ["🔥", "💎", "VIP"],
            "min_targets": 2
        },
        priority=5  # Самый высокий приоритет
    )
    
    return [whales_guide, trade_2_channel, vip_group]


if __name__ == "__main__":
    # Тестирование Channel Manager
    async def test_channel_manager():
        print("🧪 ТЕСТИРОВАНИЕ CHANNEL MANAGER")
        print("=" * 60)
        
        # Создаем менеджер
        manager = ChannelManager("config/test_sources")
        
        # Добавляем примеры источников
        examples = create_example_sources()
        
        for source in examples:
            success = manager.add_source(source)
            print(f"{'✅' if success else '❌'} Added: {source.name}")
        
        # Показываем статистику
        print(f"\n📊 SOURCES LOADED: {len(manager.sources)}")
        
        for source_id, source in manager.sources.items():
            print(f"   • {source.name} ({source.source_type.value}) - {source.status.value}")
        
        print(f"\n🎯 CHANNEL MANAGER ГОТОВ К РАБОТЕ!")
    
    # Запускаем тест
    asyncio.run(test_channel_manager())
