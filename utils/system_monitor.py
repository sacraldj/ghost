#!/usr/bin/env python3
"""
System Monitor - Мониторинг системных ресурсов
Отслеживает производительность системы и модулей GHOST
"""

import asyncio
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import json

@dataclass
class SystemMetrics:
    """Метрики системы"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used: int  # bytes
    memory_total: int  # bytes
    disk_percent: float
    disk_used: int  # bytes
    disk_total: int  # bytes
    network_sent: int  # bytes
    network_recv: int  # bytes
    load_average: List[float]  # 1, 5, 15 минут
    process_count: int
    
@dataclass
class ProcessMetrics:
    """Метрики процесса"""
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    memory_rss: int  # bytes
    memory_vms: int  # bytes
    status: str
    create_time: float
    num_threads: int
    open_files: int

class SystemMonitor:
    """Монитор системных ресурсов"""
    
    def __init__(self):
        self.metrics_history: List[SystemMetrics] = []
        self.process_metrics: Dict[int, ProcessMetrics] = {}
        self.alerts: List[Dict[str, Any]] = []
        self.running = False
        
        # Базовые метрики сети для расчёта дельты
        self._last_network_io = None
        
    async def start_monitoring(self, interval: float = 60.0):
        """Запуск мониторинга"""
        self.running = True
        
        while self.running:
            try:
                # Сбор системных метрик
                system_metrics = await self._collect_system_metrics()
                self.metrics_history.append(system_metrics)
                
                # Ограничиваем историю (храним последние 24 часа при интервале 60 сек)
                max_history = int(24 * 60 * 60 / interval)
                if len(self.metrics_history) > max_history:
                    self.metrics_history = self.metrics_history[-max_history:]
                
                # Проверка алертов
                await self._check_alerts(system_metrics)
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                print(f"Error in system monitoring: {e}")
                await asyncio.sleep(interval)
    
    async def _collect_system_metrics(self) -> SystemMetrics:
        """Сбор системных метрик"""
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Память
        memory = psutil.virtual_memory()
        
        # Диск
        disk = psutil.disk_usage('/')
        
        # Сеть
        network = psutil.net_io_counters()
        network_sent = network.bytes_sent
        network_recv = network.bytes_recv
        
        # Load average (только для Unix)
        try:
            load_avg = list(psutil.getloadavg())
        except AttributeError:
            load_avg = [0.0, 0.0, 0.0]
        
        # Количество процессов
        process_count = len(psutil.pids())
        
        return SystemMetrics(
            timestamp=datetime.utcnow(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used=memory.used,
            memory_total=memory.total,
            disk_percent=disk.percent,
            disk_used=disk.used,
            disk_total=disk.total,
            network_sent=network_sent,
            network_recv=network_recv,
            load_average=load_avg,
            process_count=process_count
        )
    
    async def collect_process_metrics(self, pids: List[int]) -> Dict[int, ProcessMetrics]:
        """Сбор метрик для конкретных процессов"""
        metrics = {}
        
        for pid in pids:
            try:
                process = psutil.Process(pid)
                
                # Получаем метрики процесса
                with process.oneshot():
                    metrics[pid] = ProcessMetrics(
                        pid=pid,
                        name=process.name(),
                        cpu_percent=process.cpu_percent(),
                        memory_percent=process.memory_percent(),
                        memory_rss=process.memory_info().rss,
                        memory_vms=process.memory_info().vms,
                        status=process.status(),
                        create_time=process.create_time(),
                        num_threads=process.num_threads(),
                        open_files=len(process.open_files())
                    )
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Процесс недоступен или завершился
                continue
            except Exception as e:
                print(f"Error collecting metrics for PID {pid}: {e}")
                continue
        
        self.process_metrics = metrics
        return metrics
    
    async def _check_alerts(self, metrics: SystemMetrics):
        """Проверка условий для алертов"""
        alerts = []
        
        # Проверка CPU
        if metrics.cpu_percent > 80:
            alerts.append({
                'type': 'high_cpu',
                'severity': 'warning' if metrics.cpu_percent < 90 else 'critical',
                'message': f'High CPU usage: {metrics.cpu_percent:.1f}%',
                'value': metrics.cpu_percent,
                'threshold': 80,
                'timestamp': metrics.timestamp
            })
        
        # Проверка памяти
        if metrics.memory_percent > 85:
            alerts.append({
                'type': 'high_memory',
                'severity': 'warning' if metrics.memory_percent < 95 else 'critical',
                'message': f'High memory usage: {metrics.memory_percent:.1f}%',
                'value': metrics.memory_percent,
                'threshold': 85,
                'timestamp': metrics.timestamp
            })
        
        # Проверка диска
        if metrics.disk_percent > 90:
            alerts.append({
                'type': 'high_disk',
                'severity': 'warning' if metrics.disk_percent < 95 else 'critical',
                'message': f'High disk usage: {metrics.disk_percent:.1f}%',
                'value': metrics.disk_percent,
                'threshold': 90,
                'timestamp': metrics.timestamp
            })
        
        # Проверка load average (только для Unix)
        if len(metrics.load_average) > 0 and metrics.load_average[0] > psutil.cpu_count():
            alerts.append({
                'type': 'high_load',
                'severity': 'warning',
                'message': f'High load average: {metrics.load_average[0]:.2f}',
                'value': metrics.load_average[0],
                'threshold': psutil.cpu_count(),
                'timestamp': metrics.timestamp
            })
        
        # Добавляем новые алерты
        for alert in alerts:
            self.alerts.append(alert)
        
        # Ограничиваем количество алертов
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-1000:]
    
    def get_current_metrics(self) -> Optional[SystemMetrics]:
        """Получение текущих метрик"""
        return self.metrics_history[-1] if self.metrics_history else None
    
    def get_metrics_history(self, hours: int = 1) -> List[SystemMetrics]:
        """Получение истории метрик за указанный период"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [m for m in self.metrics_history if m.timestamp >= cutoff_time]
    
    def get_recent_alerts(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Получение недавних алертов"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [a for a in self.alerts if a['timestamp'] >= cutoff_time]
    
    def get_system_health_score(self) -> float:
        """Расчёт общего балла здоровья системы (0-100)"""
        if not self.metrics_history:
            return 0.0
        
        current = self.metrics_history[-1]
        score = 100.0
        
        # Штрафы за высокое использование ресурсов
        if current.cpu_percent > 70:
            score -= (current.cpu_percent - 70) * 2
        
        if current.memory_percent > 70:
            score -= (current.memory_percent - 70) * 2
        
        if current.disk_percent > 80:
            score -= (current.disk_percent - 80) * 3
        
        # Штраф за высокий load average
        if len(current.load_average) > 0:
            cpu_count = psutil.cpu_count()
            if current.load_average[0] > cpu_count:
                score -= (current.load_average[0] - cpu_count) * 10
        
        return max(0.0, min(100.0, score))
    
    def get_performance_trends(self) -> Dict[str, str]:
        """Анализ трендов производительности"""
        if len(self.metrics_history) < 2:
            return {'trend': 'insufficient_data'}
        
        # Сравниваем последние 10 минут с предыдущими 10 минутами
        recent_count = min(10, len(self.metrics_history) // 2)
        
        recent_metrics = self.metrics_history[-recent_count:]
        previous_metrics = self.metrics_history[-(recent_count * 2):-recent_count]
        
        if not previous_metrics:
            return {'trend': 'insufficient_data'}
        
        # Средние значения
        recent_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        previous_cpu = sum(m.cpu_percent for m in previous_metrics) / len(previous_metrics)
        
        recent_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        previous_memory = sum(m.memory_percent for m in previous_metrics) / len(previous_metrics)
        
        trends = {}
        
        # Тренд CPU
        cpu_diff = recent_cpu - previous_cpu
        if abs(cpu_diff) < 5:
            trends['cpu'] = 'stable'
        elif cpu_diff > 0:
            trends['cpu'] = 'increasing'
        else:
            trends['cpu'] = 'decreasing'
        
        # Тренд памяти
        memory_diff = recent_memory - previous_memory
        if abs(memory_diff) < 5:
            trends['memory'] = 'stable'
        elif memory_diff > 0:
            trends['memory'] = 'increasing'
        else:
            trends['memory'] = 'decreasing'
        
        return trends
    
    def export_metrics(self, format: str = 'json') -> str:
        """Экспорт метрик в различных форматах"""
        if format == 'json':
            data = {
                'system_metrics': [asdict(m) for m in self.metrics_history],
                'process_metrics': {str(k): asdict(v) for k, v in self.process_metrics.items()},
                'alerts': self.alerts,
                'health_score': self.get_system_health_score(),
                'trends': self.get_performance_trends(),
                'export_time': datetime.utcnow().isoformat()
            }
            return json.dumps(data, default=str, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def stop_monitoring(self):
        """Остановка мониторинга"""
        self.running = False
