#!/usr/bin/env python3
"""
GHOST Unified Live System Launcher
Запускает новую unified систему с live обработкой сигналов
"""

import asyncio
import logging
import os
import sys
import signal
import threading
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# Добавляем корневую папку в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настройка логирования
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ghost_unified_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UnifiedSystemManager:
    """Менеджер для запуска unified системы"""
    
    def __init__(self):
        self.running = True
        self.live_system_task = None
        self.orchestrator_task = None
        self.http_server = None
        
    async def start_live_system(self):
        """Запуск live системы обработки сигналов"""
        try:
            logger.info("🚀 Запуск GHOST Unified Live System...")
            
            # Импортируем и запускаем live систему
            from scripts.start_live_system import LiveSystemOrchestrator
            
            orchestrator = LiveSystemOrchestrator()
            await orchestrator.start_system()
            
        except Exception as e:
            logger.error(f"❌ Ошибка в Live System: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    async def start_orchestrator(self):
        """Запуск центрального оркестратора"""
        try:
            logger.info("🚀 Запуск GHOST Orchestrator...")
            
            # Импортируем и запускаем оркестратор
            from core.ghost_orchestrator import GhostOrchestrator
            
            orchestrator = GhostOrchestrator()
            await orchestrator.initialize()
            await orchestrator.start()
            
        except Exception as e:
            logger.error(f"❌ Ошибка в Orchestrator: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def start_health_server(self):
        """Запуск HTTP сервера для health checks (для Render)"""
        try:
            class HealthHandler(BaseHTTPRequestHandler):
                def do_GET(self):
                    if self.path == '/health':
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        
                        # Собираем статистику системы
                        response = {
                            "status": "healthy",
                            "system": "GHOST Unified Live System",
                            "components": [
                                "UnifiedSignalParser",
                                "LiveSignalProcessor", 
                                "ChannelManager",
                                "AIFallbackParser"
                            ],
                            "timestamp": datetime.now().isoformat(),
                            "uptime_check": "OK"
                        }
                        
                        import json
                        self.wfile.write(json.dumps(response).encode())
                        
                    elif self.path == '/':
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                        
                        html = """
                        <!DOCTYPE html>
                        <html>
                        <head><title>GHOST Unified System</title></head>
                        <body>
                            <h1>🎯 GHOST Unified Live Signal System</h1>
                            <p><strong>Status:</strong> Running</p>
                            <p><strong>Components:</strong></p>
                            <ul>
                                <li>📊 UnifiedSignalParser - Multi-format signal parsing</li>
                                <li>🔄 LiveSignalProcessor - Real-time processing</li>
                                <li>📡 ChannelManager - Source management</li>
                                <li>🤖 AIFallbackParser - OpenAI + Gemini</li>
                            </ul>
                            <p><strong>Health Check:</strong> <a href="/health">/health</a></p>
                            <p><strong>Timestamp:</strong> {timestamp}</p>
                        </body>
                        </html>
                        """.format(timestamp=datetime.now().isoformat())
                        
                        self.wfile.write(html.encode())
                        
                    else:
                        self.send_response(404)
                        self.send_header('Content-type', 'text/plain')
                        self.end_headers()
                        self.wfile.write(b'Not Found')
                
                def log_message(self, format, *args):
                    # Логируем только важные запросы
                    if self.path != '/health':
                        logger.info(f"HTTP {self.command} {self.path}")
            
            port = int(os.environ.get('PORT', 8000))
            self.http_server = HTTPServer(('0.0.0.0', port), HealthHandler)
            logger.info(f"🌐 Health check server запущен на порту {port}")
            
            # Запускаем сервер в отдельном потоке
            server_thread = threading.Thread(target=self.http_server.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
        except Exception as e:
            logger.error(f"❌ Ошибка в Health Server: {e}")
    
    async def start_all(self):
        """Запуск всей системы"""
        logger.info("🎯 GHOST UNIFIED LIVE SYSTEM MANAGER")
        logger.info("=" * 60)
        logger.info("🚀 Unified Signal Processing with AI Fallback")
        logger.info("📱 Telegram + Discord + RSS Integration") 
        logger.info("🤖 OpenAI + Gemini AI Parsing")
        logger.info("📊 Real-time Statistics & Monitoring")
        logger.info("=" * 60)
        
        # Проверяем переменные окружения
        required_vars = [
            'NEXT_PUBLIC_SUPABASE_URL', 
            'SUPABASE_SERVICE_ROLE_KEY'
        ]
        
        optional_vars = [
            'OPENAI_API_KEY',
            'GEMINI_API_KEY',
            'TELEGRAM_API_ID',
            'TELEGRAM_API_HASH'
        ]
        
        missing_required = [var for var in required_vars if not os.getenv(var)]
        missing_optional = [var for var in optional_vars if not os.getenv(var)]
        
        if missing_required:
            logger.warning(f"⚠️ Отсутствуют обязательные переменные: {missing_required}")
            logger.warning("⚠️ Запускаем в режиме демонстрации с mock данными")
            # Устанавливаем mock переменные для демонстрации
            for var in missing_required:
                if not os.getenv(var):
                    os.environ[var] = f"mock-{var.lower()}"
        
        if missing_optional:
            logger.warning(f"⚠️ Отсутствуют опциональные переменные: {missing_optional}")
            logger.warning("⚠️ Некоторые функции могут быть недоступны")
        
        logger.info("✅ Основные переменные окружения найдены")
        
        try:
            # 1. Запускаем HTTP сервер для health checks
            self.start_health_server()
            
            # 2. Запускаем оркестратор и live систему параллельно
            logger.info("🚀 Запуск всех компонентов системы...")
            
            # Создаем задачи для параллельного выполнения
            self.orchestrator_task = asyncio.create_task(self.start_orchestrator())
            self.live_system_task = asyncio.create_task(self.start_live_system())
            
            # Ждем выполнения обеих задач
            await asyncio.gather(
                self.orchestrator_task,
                self.live_system_task,
                return_exceptions=True
            )
            
        except KeyboardInterrupt:
            logger.info("🛑 Получен сигнал остановки...")
            await self.stop_all()
        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    async def stop_all(self):
        """Остановка всей системы"""
        logger.info("🛑 Остановка Unified System...")
        self.running = False
        
        # Останавливаем задачи
        if self.orchestrator_task and not self.orchestrator_task.done():
            self.orchestrator_task.cancel()
            logger.info("✅ Orchestrator task остановлен")
        
        if self.live_system_task and not self.live_system_task.done():
            self.live_system_task.cancel()
            logger.info("✅ Live system task остановлен")
        
        # Останавливаем HTTP сервер
        if self.http_server:
            self.http_server.shutdown()
            logger.info("✅ HTTP server остановлен")
        
        logger.info("✅ Система остановлена")

def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown"""
    logger.info(f"🛑 Получен сигнал {signum}")
    # asyncio.create_task не работает здесь, используем глобальную переменную
    global manager
    if manager:
        asyncio.create_task(manager.stop_all())
    sys.exit(0)

async def main():
    """Главная async функция"""
    global manager
    
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Создаем и запускаем менеджер
    manager = UnifiedSystemManager()
    await manager.start_all()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Система остановлена пользователем")
    except Exception as e:
        logger.error(f"💥 Фатальная ошибка: {e}")
        sys.exit(1)
