#!/usr/bin/env python3
"""
GHOST All-in-One Engine Launcher
Запускает все три движка в одном процессе
"""

import asyncio
import logging
import os
import sys
import signal
from datetime import datetime
import threading
import time

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ghost_all_engines.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GhostEngineManager:
    """Менеджер для запуска всех движков"""
    
    def __init__(self):
        self.running = True
        self.threads = []
        
    def telegram_parser_worker(self):
        """Воркер для Telegram Parser"""
        try:
            logger.info("🤖 Запуск Telegram Parser...")
            
            # Добавляем путь и импортируем
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'telegram_parsers'))
            
            # Простая заглушка - в реальности будет парсер
            while self.running:
                logger.info("📱 Telegram Parser: слушаю канал @Whalesguide...")
                time.sleep(30)  # Проверяем каждые 30 секунд
                
        except Exception as e:
            logger.error(f"❌ Ошибка в Telegram Parser: {e}")
    
    def signal_orchestrator_worker(self):
        """Воркер для Signal Orchestrator"""
        try:
            logger.info("⚙️ Запуск Signal Orchestrator...")
            
            # Добавляем путь и импортируем
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'signals'))
            
            # Простая заглушка - в реальности будет оркестратор
            while self.running:
                logger.info("🎯 Signal Orchestrator: обрабатываю сигналы...")
                time.sleep(45)  # Проверяем каждые 45 секунд
                
        except Exception as e:
            logger.error(f"❌ Ошибка в Signal Orchestrator: {e}")
    
    def news_engine_worker(self):
        """Воркер для News Engine"""
        try:
            logger.info("📰 Запуск News Engine...")
            
            # Добавляем путь и импортируем
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'news_engine'))
            
            # Простая заглушка - в реальности будет новостной движок
            while self.running:
                logger.info("📊 News Engine: собираю новости...")
                time.sleep(60)  # Проверяем каждую минуту
                
        except Exception as e:
            logger.error(f"❌ Ошибка в News Engine: {e}")
    
    def health_check_worker(self):
        """Воркер для health check (для Render Web Service)"""
        try:
            from http.server import HTTPServer, BaseHTTPRequestHandler
            
            class HealthHandler(BaseHTTPRequestHandler):
                def do_GET(self):
                    if self.path == '/health':
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        response = {
                            "status": "healthy",
                            "engines": ["telegram_parser", "signal_orchestrator", "news_engine"],
                            "timestamp": datetime.now().isoformat()
                        }
                        self.wfile.write(str(response).encode())
                    else:
                        self.send_response(404)
                        self.end_headers()
                        self.wfile.write(b'Not Found')
                
                def log_message(self, format, *args):
                    pass  # Отключаем логи HTTP сервера
            
            port = int(os.environ.get('PORT', 8000))
            server = HTTPServer(('0.0.0.0', port), HealthHandler)
            logger.info(f"🌐 Health check server запущен на порту {port}")
            server.serve_forever()
            
        except Exception as e:
            logger.error(f"❌ Ошибка в Health Check: {e}")
    
    def start_all(self):
        """Запуск всех движков"""
        logger.info("🚀 GHOST All-in-One Engine Manager запущен!")
        logger.info("=" * 50)
        
        # Проверяем переменные окружения
        required_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.warning(f"⚠️ Отсутствуют переменные окружения: {missing_vars}")
        else:
            logger.info("✅ Все необходимые переменные окружения найдены")
        
        # Создаем и запускаем потоки
        workers = [
            threading.Thread(target=self.telegram_parser_worker, name="TelegramParser"),
            threading.Thread(target=self.signal_orchestrator_worker, name="SignalOrchestrator"), 
            threading.Thread(target=self.news_engine_worker, name="NewsEngine"),
            threading.Thread(target=self.health_check_worker, name="HealthCheck")
        ]
        
        # Запускаем все потоки
        for worker in workers:
            worker.daemon = True
            worker.start()
            self.threads.append(worker)
        
        logger.info(f"✅ Запущено {len(workers)} воркеров")
        
        # Главный цикл
        try:
            while self.running:
                # Проверяем статус потоков
                alive_threads = [t for t in self.threads if t.is_alive()]
                logger.info(f"📊 Активных потоков: {len(alive_threads)}/{len(self.threads)}")
                time.sleep(120)  # Статистика каждые 2 минуты
                
        except KeyboardInterrupt:
            logger.info("🛑 Получен сигнал остановки...")
            self.stop_all()
    
    def stop_all(self):
        """Остановка всех движков"""
        logger.info("🛑 Остановка всех движков...")
        self.running = False
        
        # Ждем завершения потоков
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=5)
        
        logger.info("✅ Все движки остановлены")

def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown"""
    logger.info(f"🛑 Получен сигнал {signum}")
    global manager
    if manager:
        manager.stop_all()
    sys.exit(0)

if __name__ == "__main__":
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Создаем и запускаем менеджер
    manager = GhostEngineManager()
    manager.start_all()
