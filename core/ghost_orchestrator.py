#!/usr/bin/env python3
"""
GHOST Unified System - Central Orchestrator
Центральный оркестратор для управления всей системой GHOST

Функции:
- Управление lifecycle всех модулей
- Мониторинг здоровья системы
- Автоматическое восстановление при сбоях
- Централизованное логирование
- Координация между модулями
"""

import asyncio
import json
import logging
import os
import sys
import time
import traceback
import psutil
import signal
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import yaml
# Temporarily disable Redis due to compatibility issues
aioredis = None
import subprocess
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импорты наших модулей (будут созданы)
try:
    from utils.ghost_logger import GhostLogger
except ImportError:
    GhostLogger = None

try:
    from utils.system_monitor import SystemMonitor
except ImportError:
    SystemMonitor = None

try:
    from utils.config_manager import ConfigManager
except ImportError:
    ConfigManager = None

try:
    from utils.database_manager import DatabaseManager
except ImportError:
    DatabaseManager = None

try:
    from utils.notification_manager import NotificationManager
except ImportError:
    NotificationManager = None

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('GhostOrchestrator')

@dataclass
class ModuleConfig:
    """Конфигурация модуля системы"""
    name: str
    module_path: str
    command: List[str]
    working_dir: str
    enabled: bool = True
    restart_on_failure: bool = True
    max_restarts: int = 3
    restart_delay: float = 5.0
    health_check_interval: float = 30.0
    dependencies: List[str] = None
    environment: Dict[str, str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.environment is None:
            self.environment = {}

@dataclass 
class ModuleStatus:
    """Статус модуля"""
    name: str
    process: Optional[subprocess.Popen] = None
    pid: Optional[int] = None
    status: str = "stopped"  # stopped, starting, running, failed, restarting
    last_restart: Optional[datetime] = None
    restart_count: int = 0
    last_health_check: Optional[datetime] = None
    health_status: str = "unknown"  # healthy, unhealthy, unknown
    start_time: Optional[datetime] = None
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    error_message: Optional[str] = None

class GhostOrchestrator:
    """Центральный оркестратор системы GHOST"""
    
    def __init__(self, config_path: str = "config/system_config.yaml"):
        self.config_path = config_path
        self.config = {}
        self.modules: Dict[str, ModuleConfig] = {}
        self.module_status: Dict[str, ModuleStatus] = {}
        self.redis = None
        self.db_manager = None
        self.notification_manager = None
        self.system_monitor = None
        self.ghost_logger = None
        
        # Контроль выполнения
        self.running = False
        self.shutdown_event = asyncio.Event()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Метрики системы
        self.system_metrics = {
            'start_time': datetime.utcnow(),
            'total_restarts': 0,
            'uptime': 0,
            'modules_healthy': 0,
            'modules_total': 0
        }
    
    async def initialize(self):
        """Инициализация оркестратора"""
        logger.info("🚀 Initializing GHOST Orchestrator...")
        
        try:
            # Загрузка конфигурации
            await self._load_config()
            
            # Инициализация компонентов
            await self._init_redis()
            await self._init_database()
            await self._init_notifications()
            await self._init_system_monitor()
            await self._init_logger()
            
            # Регистрация обработчиков сигналов
            self._setup_signal_handlers()
            
            # Загрузка модулей
            await self._load_modules()
            
            logger.info("✅ GHOST Orchestrator initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize orchestrator: {e}")
            logger.error(traceback.format_exc())
            raise
    
    async def _load_config(self):
        """Загрузка конфигурации системы"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f)
            else:
                # Создаём конфигурацию по умолчанию
                self.config = self._get_default_config()
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(self.config, f, default_flow_style=False)
                logger.info(f"Created default config at {self.config_path}")
                
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self.config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Конфигурация по умолчанию"""
        return {
            'orchestrator': {
                'check_interval': 10,
                'max_restarts': 3,
                'health_check_timeout': 30,
                'log_level': 'INFO'
            },
            'redis': {
                'url': 'redis://localhost:6379/0',
                'enabled': True
            },
            'database': {
                'supabase_url': os.getenv('SUPABASE_URL'),
                'supabase_key': os.getenv('SUPABASE_SECRET_KEY')
            },
            'modules': {
                'news_engine': {
                    'enabled': True,
                    'command': ['python3', 'enhanced_news_engine.py'],
                    'working_dir': 'news_engine',
                    'restart_on_failure': True,
                    'max_restarts': 3,
                    'dependencies': []
                },
                'price_feed': {
                    'enabled': True,
                    'command': ['python3', 'price_feed_engine.py'],
                    'working_dir': 'news_engine',
                    'restart_on_failure': True,
                    'max_restarts': 3,
                    'dependencies': []
                },
                'telegram_listener': {
                    'enabled': False,  # Пока отключен
                    'command': ['python3', 'telegram_listener.py'],
                    'working_dir': 'core',
                    'restart_on_failure': True,
                    'max_restarts': 5,
                    'dependencies': []
                },
                'trade_executor': {
                    'enabled': False,  # Пока отключен
                    'command': ['python3', 'trade_executor.py'],
                    'working_dir': 'core',
                    'restart_on_failure': True,
                    'max_restarts': 3,
                    'dependencies': ['telegram_listener']
                },
                'position_manager': {
                    'enabled': False,  # Пока отключен
                    'command': ['python3', 'position_manager.py'],
                    'working_dir': 'core',
                    'restart_on_failure': True,
                    'max_restarts': 3,
                    'dependencies': ['trade_executor']
                }
            }
        }
    
    async def _init_redis(self):
        """Инициализация Redis"""
        if not aioredis:
            logger.warning("⚠️ aioredis not available, Redis disabled")
            self.redis = None
            return
            
        if not self.config.get('redis', {}).get('enabled', False):
            logger.info("Redis disabled in config")
            return
            
        try:
            redis_url = self.config['redis']['url']
            self.redis = await aioredis.from_url(redis_url)
            await self.redis.ping()
            logger.info("✅ Redis connected")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}")
            self.redis = None
    
    async def _init_database(self):
        """Инициализация базы данных"""
        try:
            if DatabaseManager:
                self.db_manager = DatabaseManager(self.config['database'])
                await self.db_manager.initialize()
            logger.info("✅ Database manager initialized")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
    
    async def _init_notifications(self):
        """Инициализация системы уведомлений"""
        try:
            if NotificationManager:
                self.notification_manager = NotificationManager(self.config)
                await self.notification_manager.initialize()
            logger.info("✅ Notification manager initialized")
        except Exception as e:
            logger.error(f"❌ Notification manager initialization failed: {e}")
    
    async def _init_system_monitor(self):
        """Инициализация системного мониторинга"""
        try:
            if SystemMonitor:
                self.system_monitor = SystemMonitor()
            logger.info("✅ System monitor initialized")
        except Exception as e:
            logger.error(f"❌ System monitor initialization failed: {e}")
    
    async def _init_logger(self):
        """Инициализация логгера GHOST"""
        try:
            if GhostLogger:
                self.ghost_logger = GhostLogger(self.config)
            logger.info("✅ GHOST logger initialized")
        except Exception as e:
            logger.error(f"❌ GHOST logger initialization failed: {e}")
    
    def _setup_signal_handlers(self):
        """Настройка обработчиков сигналов"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Обработчик сигналов завершения"""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        asyncio.create_task(self.shutdown())
    
    async def _load_modules(self):
        """Загрузка конфигурации модулей"""
        modules_config = self.config.get('modules', {})
        
        for module_name, module_config in modules_config.items():
            if not module_config.get('enabled', True):
                continue
                
            self.modules[module_name] = ModuleConfig(
                name=module_name,
                module_path=module_config['working_dir'],
                command=module_config['command'],
                working_dir=module_config['working_dir'],
                enabled=module_config.get('enabled', True),
                restart_on_failure=module_config.get('restart_on_failure', True),
                max_restarts=module_config.get('max_restarts', 3),
                restart_delay=module_config.get('restart_delay', 5.0),
                dependencies=module_config.get('dependencies', []),
                environment=module_config.get('environment', {})
            )
            
            self.module_status[module_name] = ModuleStatus(name=module_name)
            
        logger.info(f"Loaded {len(self.modules)} modules")
    
    async def start(self):
        """Запуск оркестратора"""
        logger.info("🚀 Starting GHOST Orchestrator...")
        self.running = True
        
        try:
            # Запуск модулей в порядке зависимостей
            await self._start_modules()
            
            # Основной цикл мониторинга
            await self._main_loop()
            
        except Exception as e:
            logger.error(f"❌ Orchestrator error: {e}")
            logger.error(traceback.format_exc())
        finally:
            await self.shutdown()
    
    async def _start_modules(self):
        """Запуск всех модулей в правильном порядке"""
        # Топологическая сортировка по зависимостям
        sorted_modules = self._topological_sort()
        
        for module_name in sorted_modules:
            if self.modules[module_name].enabled:
                await self._start_module(module_name)
                # Небольшая пауза между запусками
                await asyncio.sleep(2)
    
    def _topological_sort(self) -> List[str]:
        """Топологическая сортировка модулей по зависимостям"""
        visited = set()
        temp_visited = set()
        result = []
        
        def visit(module_name: str):
            if module_name in temp_visited:
                raise ValueError(f"Circular dependency detected: {module_name}")
            if module_name in visited:
                return
                
            temp_visited.add(module_name)
            
            # Посещаем зависимости
            for dep in self.modules[module_name].dependencies:
                if dep in self.modules:
                    visit(dep)
            
            temp_visited.remove(module_name)
            visited.add(module_name)
            result.append(module_name)
        
        for module_name in self.modules:
            if module_name not in visited:
                visit(module_name)
        
        return result
    
    async def _start_module(self, module_name: str) -> bool:
        """Запуск конкретного модуля"""
        module_config = self.modules[module_name]
        module_status = self.module_status[module_name]
        
        logger.info(f"🟢 Starting module: {module_name}")
        
        try:
            # Проверка зависимостей
            for dep in module_config.dependencies:
                if dep not in self.module_status or self.module_status[dep].status != "running":
                    logger.error(f"❌ Dependency {dep} not running for {module_name}")
                    return False
            
            # Подготовка команды
            cmd = module_config.command
            working_dir = os.path.abspath(module_config.working_dir)
            
            # Подготовка окружения
            env = os.environ.copy()
            env.update(module_config.environment)
            
            # Запуск процесса
            module_status.status = "starting"
            module_status.start_time = datetime.utcnow()
            
            process = subprocess.Popen(
                cmd,
                cwd=working_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            module_status.process = process
            module_status.pid = process.pid
            module_status.status = "running"
            module_status.restart_count = 0
            
            logger.info(f"✅ Module {module_name} started with PID {process.pid}")
            
            # Сохранение статуса в Redis
            await self._save_module_status(module_name)
            
            return True
            
        except Exception as e:
            module_status.status = "failed"
            module_status.error_message = str(e)
            logger.error(f"❌ Failed to start module {module_name}: {e}")
            return False
    
    async def _main_loop(self):
        """Основной цикл мониторинга"""
        check_interval = self.config['orchestrator']['check_interval']
        
        while self.running and not self.shutdown_event.is_set():
            try:
                # Проверка здоровья модулей
                await self._check_modules_health()
                
                # Обновление метрик системы
                await self._update_system_metrics()
                
                # Сохранение статуса в Redis
                await self._save_system_status()
                
                # Ожидание следующей проверки
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(check_interval)
    
    async def _check_modules_health(self):
        """Проверка здоровья всех модулей"""
        for module_name, module_status in self.module_status.items():
            await self._check_module_health(module_name)
    
    async def _check_module_health(self, module_name: str):
        """Проверка здоровья конкретного модуля"""
        module_status = self.module_status[module_name]
        
        if module_status.status != "running":
            return
        
        try:
            # Проверка что процесс жив
            if module_status.process and module_status.process.poll() is not None:
                logger.warning(f"⚠️ Module {module_name} process died")
                module_status.status = "failed"
                module_status.error_message = f"Process exited with code {module_status.process.returncode}"
                await self._handle_module_failure(module_name)
                return
            
            # Получение метрик процесса
            if module_status.pid:
                try:
                    process = psutil.Process(module_status.pid)
                    module_status.cpu_usage = process.cpu_percent()
                    module_status.memory_usage = process.memory_info().rss / 1024 / 1024  # MB
                except psutil.NoSuchProcess:
                    logger.warning(f"⚠️ Process {module_status.pid} for {module_name} not found")
                    module_status.status = "failed"
                    await self._handle_module_failure(module_name)
                    return
            
            # Проверка health endpoint (если доступен)
            # Здесь можно добавить HTTP health check для модулей
            
            module_status.health_status = "healthy"
            module_status.last_health_check = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error checking health of {module_name}: {e}")
            module_status.health_status = "unhealthy"
    
    async def _handle_module_failure(self, module_name: str):
        """Обработка сбоя модуля"""
        module_config = self.modules[module_name]
        module_status = self.module_status[module_name]
        
        logger.error(f"❌ Module {module_name} failed: {module_status.error_message}")
        
        # Уведомление о сбое
        if self.notification_manager:
            await self.notification_manager.send_alert(
                f"Module {module_name} failed",
                module_status.error_message or "Unknown error"
            )
        
        # Проверка возможности перезапуска
        if (module_config.restart_on_failure and 
            module_status.restart_count < module_config.max_restarts):
            
            logger.info(f"🔄 Attempting to restart {module_name} "
                       f"(attempt {module_status.restart_count + 1})")
            
            # Пауза перед перезапуском
            await asyncio.sleep(module_config.restart_delay)
            
            # Очистка старого процесса
            await self._cleanup_module(module_name)
            
            # Перезапуск
            module_status.restart_count += 1
            module_status.last_restart = datetime.utcnow()
            self.system_metrics['total_restarts'] += 1
            
            success = await self._start_module(module_name)
            if success:
                logger.info(f"✅ Module {module_name} restarted successfully")
            else:
                logger.error(f"❌ Failed to restart module {module_name}")
        else:
            logger.error(f"❌ Module {module_name} reached max restart limit or restart disabled")
    
    async def _cleanup_module(self, module_name: str):
        """Очистка ресурсов модуля"""
        module_status = self.module_status[module_name]
        
        if module_status.process:
            try:
                # Попытка graceful shutdown
                module_status.process.terminate()
                await asyncio.sleep(2)
                
                # Force kill если не остановился
                if module_status.process.poll() is None:
                    module_status.process.kill()
                    
            except Exception as e:
                logger.error(f"Error cleaning up module {module_name}: {e}")
        
        module_status.process = None
        module_status.pid = None
        module_status.status = "stopped"
    
    async def _update_system_metrics(self):
        """Обновление метрик системы"""
        self.system_metrics['uptime'] = (
            datetime.utcnow() - self.system_metrics['start_time']
        ).total_seconds()
        
        self.system_metrics['modules_total'] = len(self.modules)
        self.system_metrics['modules_healthy'] = sum(
            1 for status in self.module_status.values()
            if status.health_status == "healthy"
        )
    
    async def _save_system_status(self):
        """Сохранение статуса системы в Redis или файл"""
        try:
            status_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'orchestrator_status': 'running' if self.running else 'stopped',
                'system_metrics': self.system_metrics.copy(),
                'modules': {
                    name: {
                        'status': status.status,
                        'health': status.health_status,
                        'pid': status.pid,
                        'restart_count': status.restart_count,
                        'cpu_usage': status.cpu_usage,
                        'memory_usage': status.memory_usage,
                        'start_time': status.start_time.isoformat() if status.start_time else None,
                        'last_health_check': status.last_health_check.isoformat() if status.last_health_check else None
                    }
                    for name, status in self.module_status.items()
                }
            }
            
            # Convert datetime objects to strings for JSON serialization
            status_data['system_metrics']['start_time'] = status_data['system_metrics']['start_time'].isoformat()
            
            # Try Redis first
            if self.redis:
                await self.redis.setex(
                    'ghost:orchestrator:status',
                    300,  # TTL 5 минут
                    json.dumps(status_data, default=str)
                )
            else:
                # Fallback to file
                status_file = 'logs/orchestrator_status.json'
                os.makedirs(os.path.dirname(status_file), exist_ok=True)
                with open(status_file, 'w') as f:
                    json.dump(status_data, f, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"Failed to save system status: {e}")
    
    async def _save_module_status(self, module_name: str):
        """Сохранение статуса модуля в Redis"""
        if not self.redis:
            return
            
        try:
            status = self.module_status[module_name]
            status_data = {
                'name': status.name,
                'status': status.status,
                'health': status.health_status,
                'pid': status.pid,
                'restart_count': status.restart_count,
                'cpu_usage': status.cpu_usage,
                'memory_usage': status.memory_usage,
                'start_time': status.start_time.isoformat() if status.start_time else None,
                'last_health_check': status.last_health_check.isoformat() if status.last_health_check else None,
                'error_message': status.error_message
            }
            
            await self.redis.setex(
                f'ghost:module:{module_name}:status',
                300,  # TTL 5 минут
                json.dumps(status_data, default=str)
            )
            
        except Exception as e:
            logger.error(f"Failed to save module {module_name} status: {e}")
    
    async def shutdown(self):
        """Graceful shutdown оркестратора"""
        logger.info("🛑 Shutting down GHOST Orchestrator...")
        self.running = False
        self.shutdown_event.set()
        
        # Остановка всех модулей
        for module_name in list(self.module_status.keys()):
            await self._cleanup_module(module_name)
        
        # Закрытие соединений
        if self.redis:
            await self.redis.close()
        
        # Закрытие executor
        self.executor.shutdown(wait=True)
        
        logger.info("✅ GHOST Orchestrator shutdown complete")
    
    async def get_status(self) -> Dict[str, Any]:
        """Получение текущего статуса системы"""
        return {
            'orchestrator': {
                'running': self.running,
                'uptime': self.system_metrics['uptime'],
                'start_time': self.system_metrics['start_time'].isoformat(),
                'total_restarts': self.system_metrics['total_restarts']
            },
            'modules': {
                name: {
                    'status': status.status,
                    'health': status.health_status,
                    'pid': status.pid,
                    'restart_count': status.restart_count,
                    'cpu_usage': status.cpu_usage,
                    'memory_usage': status.memory_usage,
                    'start_time': status.start_time.isoformat() if status.start_time else None
                }
                for name, status in self.module_status.items()
            },
            'system_metrics': self.system_metrics
        }

async def main():
    """Главная функция"""
    orchestrator = GhostOrchestrator()
    
    try:
        await orchestrator.initialize()
        await orchestrator.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Orchestrator failed: {e}")
        logger.error(traceback.format_exc())
    finally:
        await orchestrator.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
