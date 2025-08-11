# GHOST Orchestrator - Подробное руководство
**Центральный оркестратор системы управления**

## 🎯 Назначение и роль

GHOST Orchestrator (`core/ghost_orchestrator.py`) - это **центральный мозг** всей объединённой системы GHOST. Он выполняет роль "дирижёра оркестра", координируя работу всех модулей и обеспечивая их слаженное взаимодействие.

## 🏗 Архитектура оркестратора

### Основные компоненты:

```python
class GhostOrchestrator:
    """Центральный оркестратор системы GHOST"""
    
    # Конфигурация и состояние
    config: Dict[str, Any]              # Конфигурация системы
    modules: Dict[str, ModuleConfig]    # Конфигурации модулей
    module_status: Dict[str, ModuleStatus]  # Статусы модулей
    
    # Внешние сервисы
    redis: aioredis.Redis              # Кэш и межпроцессное взаимодействие
    db_manager: DatabaseManager       # Управление базой данных
    notification_manager: NotificationManager  # Уведомления
    system_monitor: SystemMonitor     # Мониторинг ресурсов
    ghost_logger: GhostLogger         # Централизованное логирование
```

## 🔧 Основные функции

### 1. **Управление жизненным циклом модулей (Lifecycle Management)**

#### Запуск модулей:
```python
async def _start_modules(self):
    """Запуск всех модулей в правильном порядке"""
    # Топологическая сортировка по зависимостям
    sorted_modules = self._topological_sort()
    
    for module_name in sorted_modules:
        if self.modules[module_name].enabled:
            await self._start_module(module_name)
            await asyncio.sleep(2)  # Пауза между запусками
```

**Что происходит при запуске модуля:**
1. ✅ Проверка зависимостей (все ли нужные модули уже запущены)
2. ✅ Подготовка рабочей директории и окружения
3. ✅ Запуск процесса с помощью `subprocess.Popen`
4. ✅ Сохранение PID и статуса
5. ✅ Регистрация в системе мониторинга

#### Остановка модулей:
```python
async def _cleanup_module(self, module_name: str):
    """Graceful shutdown модуля"""
    # 1. Отправка SIGTERM (graceful shutdown)
    module_status.process.terminate()
    await asyncio.sleep(2)
    
    # 2. Если не остановился - принудительное завершение
    if module_status.process.poll() is None:
        module_status.process.kill()
```

### 2. **Мониторинг здоровья системы (Health Monitoring)**

#### Непрерывная проверка:
```python
async def _check_module_health(self, module_name: str):
    """Проверка здоровья конкретного модуля"""
    
    # Проверка что процесс жив
    if module_status.process.poll() is not None:
        await self._handle_module_failure(module_name)
        return
    
    # Сбор метрик процесса
    process = psutil.Process(module_status.pid)
    module_status.cpu_usage = process.cpu_percent()
    module_status.memory_usage = process.memory_info().rss / 1024 / 1024
    
    # Можно добавить HTTP health check
    # await self._check_http_health(module_name)
```

**Контролируемые параметры:**
- 🔍 **Статус процесса** - работает ли модуль
- 📊 **Использование CPU** - не перегружен ли модуль
- 💾 **Потребление памяти** - нет ли утечек памяти
- ⏱️ **Время отклика** - HTTP health checks (планируется)
- 🔄 **Количество перезапусков** - не зацикливается ли модуль

### 3. **Автоматическое восстановление (Auto-Recovery)**

#### Обработка сбоев:
```python
async def _handle_module_failure(self, module_name: str):
    """Обработка сбоя модуля"""
    
    # Проверка лимитов перезапуска
    if (module_config.restart_on_failure and 
        module_status.restart_count < module_config.max_restarts):
        
        # Пауза перед перезапуском
        await asyncio.sleep(module_config.restart_delay)
        
        # Очистка ресурсов
        await self._cleanup_module(module_name)
        
        # Перезапуск
        success = await self._start_module(module_name)
        if success:
            logger.info(f"✅ Module {module_name} restarted successfully")
```

**Стратегии восстановления:**
- 🔄 **Автоматический перезапуск** - до достижения лимита попыток
- ⏰ **Экспоненциальная задержка** - увеличение времени между попытками
- 📧 **Уведомления об ошибках** - в Telegram/email при критических сбоях
- 🛡️ **Graceful degradation** - отключение зависимых модулей при критических ошибках

### 4. **Управление зависимостями (Dependency Management)**

#### Топологическая сортировка:
```python
def _topological_sort(self) -> List[str]:
    """Определение порядка запуска модулей по зависимостям"""
    
    # Модули запускаются в правильном порядке:
    # 1. news_engine (нет зависимостей)
    # 2. price_feed (нет зависимостей)  
    # 3. supabase_sync (зависит от news_engine, price_feed)
    # 4. telegram_listener (нет зависимостей)
    # 5. signal_processor (зависит от telegram_listener)
    # 6. trade_executor (зависит от signal_processor)
```

**Пример зависимостей:**
```yaml
modules:
  trade_executor:
    dependencies: ["signal_processor", "ml_filtering"]
  signal_processor:
    dependencies: ["telegram_listener"]  
  ml_filtering:
    dependencies: ["news_engine", "price_feed"]
```

### 5. **Централизованное логирование (Centralized Logging)**

#### Система логов:
```python
async def _save_system_status(self):
    """Сохранение статуса в Redis и логи"""
    
    status_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'orchestrator_status': 'running',
        'system_metrics': self.system_metrics,
        'modules': {
            name: {
                'status': status.status,
                'health': status.health_status,
                'cpu_usage': status.cpu_usage,
                'memory_usage': status.memory_usage
            }
            for name, status in self.module_status.items()
        }
    }
    
    # Сохранение в Redis для API
    await self.redis.setex('ghost:orchestrator:status', 300, json.dumps(status_data))
```

**Уровни логирования:**
- 🔍 **DEBUG** - подробная отладочная информация
- ℹ️ **INFO** - обычные операции (запуск/остановка модулей)
- ⚠️ **WARNING** - предупреждения (высокое использование ресурсов)
- ❌ **ERROR** - ошибки (сбой модуля, проблемы с БД)
- 🚨 **CRITICAL** - критические ошибки (отказ системы)

### 6. **Конфигурационное управление (Configuration Management)**

#### Структура конфигурации:
```yaml
# config/system_config.yaml
orchestrator:
  check_interval: 10          # Интервал проверки модулей (сек)
  max_restarts: 3            # Максимум перезапусков
  health_check_timeout: 30   # Таймаут health check

modules:
  news_engine:
    enabled: true
    command: ["python3", "enhanced_news_engine.py"]
    working_dir: "news_engine"
    restart_on_failure: true
    max_restarts: 3
    restart_delay: 5.0
    dependencies: []
    environment:
      PYTHONPATH: ${PYTHONPATH}
    resources:
      cpu_limit: 1.0
      memory_limit: 512  # MB
```

### 7. **Интеграция с внешними сервисами**

#### Redis (кэш и состояние):
```python
# Сохранение статуса модуля
await self.redis.setex(
    f'ghost:module:{module_name}:status',
    300,  # TTL 5 минут
    json.dumps(status_data)
)

# Межпроцессное взаимодействие
await self.redis.publish('ghost:events', json.dumps({
    'type': 'module_restarted',
    'module': module_name,
    'timestamp': datetime.utcnow().isoformat()
}))
```

#### Supabase (база данных):
```python
# Сохранение событий системы
await self.db_manager.log_system_event({
    'event_type': 'module_failure',
    'module_name': module_name,
    'error_message': error_message,
    'timestamp': datetime.utcnow(),
    'restart_count': restart_count
})
```

## 🔄 Алгоритм работы оркестратора

### Основной цикл:
```python
async def _main_loop(self):
    """Основной цикл мониторинга"""
    check_interval = self.config['orchestrator']['check_interval']
    
    while self.running:
        try:
            # 1. Проверка здоровья всех модулей
            await self._check_modules_health()
            
            # 2. Обновление системных метрик
            await self._update_system_metrics()
            
            # 3. Сохранение статуса в Redis
            await self._save_system_status()
            
            # 4. Ожидание следующей итерации
            await asyncio.sleep(check_interval)
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            await asyncio.sleep(check_interval)
```

### Последовательность запуска:
1. 📋 **Инициализация** - загрузка конфигурации, подключение к Redis/БД
2. 🔗 **Подключение сервисов** - Redis, Supabase, система уведомлений
3. 📊 **Запуск мониторинга** - системный монитор, health checks
4. 🚀 **Запуск модулей** - в порядке зависимостей
5. 🔄 **Основной цикл** - непрерывный мониторинг и управление
6. 🛑 **Graceful shutdown** - корректная остановка всех компонентов

## 📊 Метрики и мониторинг

### Системные метрики:
```python
self.system_metrics = {
    'start_time': datetime.utcnow(),
    'total_restarts': 0,           # Общее количество перезапусков
    'uptime': 0,                   # Время работы системы
    'modules_healthy': 0,          # Количество здоровых модулей
    'modules_total': 0,            # Общее количество модулей
    'cpu_usage_avg': 0.0,         # Средняя нагрузка CPU
    'memory_usage_total': 0.0,     # Общее потребление памяти
    'errors_last_hour': 0,         # Ошибки за последний час
    'performance_score': 100.0     # Общий балл производительности
}
```

### API для внешнего доступа:
```typescript
// GET /api/system/status
{
  "orchestrator_status": "running",
  "uptime": 3600,
  "modules_summary": {
    "total": 10,
    "running": 8,
    "healthy": 7,
    "failed": 1
  },
  "system_health": {
    "overall_status": "healthy",
    "health_score": 85,
    "issues": ["High memory usage in ml_filtering module"]
  }
}
```

## 🚨 Обработка ошибок и алерты

### Типы алертов:
1. **🔴 CRITICAL** - полный отказ системы
2. **🟠 HIGH** - отказ критически важного модуля
3. **🟡 MEDIUM** - превышение лимитов ресурсов
4. **🔵 LOW** - предупреждения и информационные сообщения

### Каналы уведомлений:
- 📱 **Telegram** - мгновенные алерты админам
- 📧 **Email** - детальные отчёты об ошибках
- 🔗 **Webhook** - интеграция с внешними системами мониторинга
- 📝 **Logs** - подробное логирование всех событий

## 🎛️ Команды управления

### Через API:
```bash
# Перезапуск модуля
curl -X POST /api/system/control \
  -d '{"action": "restart_module", "module": "news_engine"}'

# Получение логов
curl -X POST /api/system/control \
  -d '{"action": "get_logs", "module": "trade_executor", "lines": 100}'

# Изменение конфигурации
curl -X POST /api/system/control \
  -d '{"action": "update_config", "module": "ml_filtering", "config": {...}}'
```

### Через скрипт:
```bash
# Запуск системы
./start_orchestrator.sh start

# Проверка статуса
./start_orchestrator.sh status

# Перезапуск
./start_orchestrator.sh restart

# Просмотр логов
./start_orchestrator.sh logs
```

## 🔮 Будущие улучшения

### Планируемые функции:
1. **🤖 AI-мониторинг** - предсказание сбоев на основе метрик
2. **📈 Автомасштабирование** - динамическое изменение ресурсов
3. **🔄 Rolling updates** - обновление модулей без остановки системы
4. **🌐 Распределённое развёртывание** - запуск модулей на разных серверах
5. **📊 Advanced analytics** - детальная аналитика производительности

---

Это и есть **"мозг"** всей системы GHOST - он знает о каждом модуле, следит за их здоровьем, автоматически восстанавливает при сбоях и предоставляет единый интерфейс управления всей сложной торговой системой!
