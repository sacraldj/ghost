#!/usr/bin/env python3
"""
GHOST Unified Live System Launcher - УПРОЩЁННАЯ ВЕРСИЯ
Запускает только SignalOrchestratorWithSupabase с встроенным TelegramListener
"""

import asyncio
import logging
import os
import sys
import signal
import threading
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
        logging.FileHandler('logs/ghost_simple_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SimpleSystemManager:
    """Простой менеджер для запуска unified системы"""
    
    def __init__(self):
        self.running = True
        self.system_task = None
        self.http_server = None
        
    async def start_live_system(self):
        """Запуск live системы с SignalOrchestratorWithSupabase"""
        try:
            logger.info("🚀 Запуск GHOST System с Supabase...")
            
            from signals.signal_orchestrator_with_supabase import orchestrator_with_supabase
            logger.info("✅ Запускаем SignalOrchestratorWithSupabase...")
            
            # Тестируем подключение к Supabase
            if await orchestrator_with_supabase.test_supabase_connection():
                logger.info("✅ Supabase подключение успешно!")
                
                # Запускаем обработку тестового сигнала
                test_signal = "🚀🔥 #ALPINE запампили на +57% со вчерашнего вечера"
                result = await orchestrator_with_supabase.process_raw_signal(test_signal, "cryptoattack24", "cryptoattack24")
                
                if result:
                    logger.info(f"✅ Тестовый сигнал обработан: {result.symbol}")
                
                # Статистика оркестратора
                stats = await orchestrator_with_supabase.get_stats()
                logger.info(f"📊 Статистика оркестратора: {stats['signals_processed']} обработано, {stats['supabase_saves']} сохранено")
                
                # Запускаем прослушивание Telegram
                telegram_started = await orchestrator_with_supabase.start_telegram_listening()
                if telegram_started:
                    logger.info("✅ Telegram прослушивание запущено!")
                else:
                    logger.warning("⚠️ Telegram прослушивание не удалось запустить")
                
                # Запускаем основной цикл
                await self.run_orchestrator_loop(orchestrator_with_supabase)
            else:
                logger.error("❌ Supabase недоступен!")
                raise Exception("Supabase connection failed")
                
        except Exception as e:
            logger.error(f"❌ Ошибка в Live System: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise e
    
    async def run_orchestrator_loop(self, orchestrator):
        """Основной цикл оркестратора"""
        try:
            logger.info("✅ Запуск основного цикла SignalOrchestratorWithSupabase...")
            
            # Цикл обработки сигналов
            while self.running:
                try:
                    # Проверяем состояние системы
                    stats = await orchestrator.get_stats()
                    
                    if stats['signals_processed'] % 10 == 0 and stats['signals_processed'] > 0:
                        logger.info(
                            f"📊 Статистика: {stats['signals_processed']} обработано, "
                            f"{stats['supabase_saves']} сохранено"
                        )
                    
                    # Ждем 30 секунд перед следующей проверкой
                    await asyncio.sleep(30)
                    
                except asyncio.CancelledError:
                    logger.info("🛑 Получен сигнал отмены основного цикла...")
                    break
                except Exception as e:
                    logger.error(f"❌ Ошибка в основном цикле оркестратора: {e}")
                    await asyncio.sleep(30)  # Пауза при ошибке
                    
        except Exception as e:
            logger.error(f"❌ Критическая ошибка в цикле оркестратора: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def start_health_server(self):
        """Запуск HTTP сервера для health checks"""
        try:
            class HealthHandler(BaseHTTPRequestHandler):
                def do_GET(self):
                    if self.path == '/health':
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        response = {'status': 'healthy', 'service': 'ghost-system'}
                        self.wfile.write(str(response).encode('utf-8'))
                    else:
                        self.send_response(404)
                        self.end_headers()
                        
                def log_message(self, format, *args):
                    pass  # Отключаем стандартные логи HTTP сервера
            
            # Запускаем сервер в отдельном потоке
            def run_server():
                try:
                    server = HTTPServer(('0.0.0.0', 8080), HealthHandler)
                    server.serve_forever()
                except Exception as e:
                    logger.error(f"Health server error: {e}")
            
            health_thread = threading.Thread(target=run_server, daemon=True)
            health_thread.start()
            
            logger.info("✅ Health server started on port 8080")
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска health server: {e}")
    
    async def start_all(self):
        """Запуск всей системы"""
        logger.info("🚀 GHOST СИСТЕМА - ПРОСТАЯ ВЕРСИЯ")
        logger.info("=" * 60)
        
        try:
            # 1. Запускаем HTTP сервер для health checks
            self.start_health_server()
            
            # 2. Запускаем главную систему
            logger.info("🚀 Запуск SignalOrchestratorWithSupabase...")
            self.system_task = asyncio.create_task(self.start_live_system())
            
            logger.info("⏳ Система запущена, поддерживаем работу...")
            
            # Цикл поддержания работы на Render
            while self.running:
                try:
                    # Проверяем состояние системы
                    if self.system_task.done():
                        logger.warning("⚠️ System task завершилась, перезапускаем...")
                        self.system_task = asyncio.create_task(self.start_live_system())
                    
                    await asyncio.sleep(30)
                    
                except asyncio.CancelledError:
                    logger.info("🛑 Получен сигнал отмены...")
                    break
                except Exception as e:
                    logger.error(f"❌ Ошибка в основном цикле: {e}")
                    await asyncio.sleep(30)
                    
        except Exception as e:
            logger.error(f"💥 Критическая ошибка системы: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("🛑 Завершение работы системы...")
        self.running = False
        
        if self.system_task and not self.system_task.done():
            self.system_task.cancel()
            try:
                await self.system_task
            except asyncio.CancelledError:
                pass

# Глобальный менеджер системы
manager = SimpleSystemManager()

def signal_handler(sig, frame):
    """Обработчик сигналов для graceful shutdown"""
    logger.info(f"Получен сигнал {sig}, завершаем работу...")
    asyncio.create_task(manager.shutdown())

async def main():
    """Главная функция"""
    # Обработка сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    await manager.start_all()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Система остановлена пользователем")
    except Exception as e:
        logger.error(f"💥 Фатальная ошибка: {e}")
        sys.exit(1)
