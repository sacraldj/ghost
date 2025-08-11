#!/usr/bin/env python3
"""
GHOST Logger - Централизованная система логирования
Обеспечивает единообразное логирование во всей системе GHOST
"""

import logging
import logging.handlers
import json
import os
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass
import aioredis
import aiofiles

@dataclass
class LogEvent:
    """Событие логирования"""
    timestamp: datetime
    level: str
    module: str
    message: str
    data: Dict[str, Any]
    trace_id: Optional[str] = None
    user_id: Optional[str] = None

class GhostLogger:
    """Централизованный логгер GHOST"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.redis = None
        self.log_queue = asyncio.Queue()
        self.running = False
        
    async def initialize(self):
        """Инициализация логгера"""
        # Подключение к Redis
        if self.config.get('redis', {}).get('enabled'):
            try:
                self.redis = await aioredis.from_url(self.config['redis']['url'])
            except Exception as e:
                print(f"Redis connection failed: {e}")
        
        # Создание директорий для логов
        log_dir = self.config.get('orchestrator', {}).get('log_dir', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        self.running = True
        # Запуск обработчика очереди логов
        asyncio.create_task(self._process_log_queue())
    
    async def log(self, level: str, module: str, message: str, 
                  data: Dict[str, Any] = None, trace_id: str = None, user_id: str = None):
        """Асинхронное логирование"""
        event = LogEvent(
            timestamp=datetime.utcnow(),
            level=level,
            module=module,
            message=message,
            data=data or {},
            trace_id=trace_id,
            user_id=user_id
        )
        
        await self.log_queue.put(event)
    
    async def _process_log_queue(self):
        """Обработка очереди логов"""
        while self.running:
            try:
                event = await asyncio.wait_for(self.log_queue.get(), timeout=1.0)
                await self._write_log_event(event)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Error processing log event: {e}")
    
    async def _write_log_event(self, event: LogEvent):
        """Запись события в различные назначения"""
        # Форматирование сообщения
        log_data = {
            'timestamp': event.timestamp.isoformat(),
            'level': event.level,
            'module': event.module,
            'message': event.message,
            'data': event.data,
            'trace_id': event.trace_id,
            'user_id': event.user_id
        }
        
        # Запись в Redis
        if self.redis:
            try:
                await self.redis.lpush(
                    'ghost:logs',
                    json.dumps(log_data, default=str)
                )
                await self.redis.ltrim('ghost:logs', 0, 1000)  # Оставляем только 1000 последних
            except Exception as e:
                print(f"Failed to write to Redis: {e}")
        
        # Запись в файл
        log_file = os.path.join(
            self.config.get('orchestrator', {}).get('log_dir', 'logs'),
            f"{event.module}.log"
        )
        
        formatted_message = (
            f"{event.timestamp.isoformat()} - {event.level} - {event.module} - "
            f"{event.message}"
        )
        
        if event.data:
            formatted_message += f" - Data: {json.dumps(event.data, default=str)}"
        
        try:
            async with aiofiles.open(log_file, 'a', encoding='utf-8') as f:
                await f.write(formatted_message + '\n')
        except Exception as e:
            print(f"Failed to write to log file: {e}")
    
    async def shutdown(self):
        """Завершение работы логгера"""
        self.running = False
        
        # Обработка оставшихся событий
        while not self.log_queue.empty():
            try:
                event = self.log_queue.get_nowait()
                await self._write_log_event(event)
            except asyncio.QueueEmpty:
                break
        
        if self.redis:
            await self.redis.close()

# Глобальный экземпляр логгера
_ghost_logger = None

async def get_logger() -> GhostLogger:
    """Получение глобального логгера"""
    global _ghost_logger
    return _ghost_logger

async def init_logger(config: Dict[str, Any]) -> GhostLogger:
    """Инициализация глобального логгера"""
    global _ghost_logger
    _ghost_logger = GhostLogger(config)
    await _ghost_logger.initialize()
    return _ghost_logger

# Удобные функции для логирования
async def log_info(module: str, message: str, data: Dict[str, Any] = None, trace_id: str = None):
    """Логирование информации"""
    logger = await get_logger()
    if logger:
        await logger.log('INFO', module, message, data, trace_id)

async def log_warning(module: str, message: str, data: Dict[str, Any] = None, trace_id: str = None):
    """Логирование предупреждения"""
    logger = await get_logger()
    if logger:
        await logger.log('WARNING', module, message, data, trace_id)

async def log_error(module: str, message: str, data: Dict[str, Any] = None, trace_id: str = None):
    """Логирование ошибки"""
    logger = await get_logger()
    if logger:
        await logger.log('ERROR', module, message, data, trace_id)

async def log_debug(module: str, message: str, data: Dict[str, Any] = None, trace_id: str = None):
    """Логирование отладочной информации"""
    logger = await get_logger()
    if logger:
        await logger.log('DEBUG', module, message, data, trace_id)
