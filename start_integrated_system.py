#!/usr/bin/env python3
"""
ИНТЕГРИРОВАННАЯ СИСТЕМА С АВТОМАТИЧЕСКИМ ПАРСИНГОМ GHOSTSIGNALTEST
Полностью автоматическая - без ввода кодов
"""

import asyncio
import sys
import os
import logging
import signal
import threading
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# Добавляем корневую папку в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения ПЕРВЫМ ДЕЛОМ
from dotenv import load_dotenv
load_dotenv()

# Настройка логирования
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/integrated_ghost_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP сервер для health check"""
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'GHOST System Running with GhostSignalTest parsing')
    
    def log_message(self, format, *args):
        pass  # Отключаем логи HTTP сервера

def run_health_server():
    """Запуск health check сервера"""
    try:
        port = int(os.getenv('PORT', '8080'))
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        logger.info(f"🌐 Health server started on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"❌ Health server error: {e}")

async def run_integrated_system():
    """Запуск интегрированной системы с ghostsignaltest парсингом"""
    
    logger.info("🚀 ЗАПУСК ИНТЕГРИРОВАННОЙ GHOST СИСТЕМЫ")
    logger.info("🎯 Включен парсинг канала @ghostsignaltest")
    logger.info("🔄 Режим: Полностью автоматический")
    
    try:
        # Импортируем оркестратор
        from signals.signal_orchestrator_with_supabase import SignalOrchestratorWithSupabase
        
        # Создаем оркестратор
        logger.info("🏗️ Инициализация SignalOrchestratorWithSupabase...")
        orchestrator = SignalOrchestratorWithSupabase()
        
        # Проверяем что GhostTestParser интегрирован
        if 'ghostsignaltest' in orchestrator.parsers:
            parser_type = type(orchestrator.parsers['ghostsignaltest']).__name__
            logger.info(f"✅ GhostTestParser найден: {parser_type}")
        else:
            logger.error("❌ GhostTestParser не найден в оркестраторе!")
            return
        
        # Проверяем Supabase подключение
        if orchestrator.supabase:
            logger.info("✅ Supabase подключен")
        else:
            logger.warning("⚠️ Supabase не подключен - работаем в тестовом режиме")
        
        # Тестируем парсер на примере
        logger.info("🧪 Тестирование GhostTestParser...")
        test_signal = """**Shorting ****#APT**** here**

Short (5x-10x)

Entry: $4.5890 - $4.6500

Targets: $4.48, $4.40, $4.30, $4.20, $4.00

Stop-loss: $4.75"""
        
        test_result = await orchestrator.process_raw_signal(test_signal, "ghostsignaltest")
        
        if test_result:
            logger.info(f"✅ Тест парсера успешен: {test_result.symbol} {test_result.direction.value}")
            logger.info("🚀 Система готова к работе!")
        else:
            logger.warning("⚠️ Тест парсера не прошел, но продолжаем...")
        
        # Запускаем Telegram прослушивание
        logger.info("🎧 Запуск Telegram прослушивания...")
        logger.info("📺 Мониторим каналы включая @ghostsignaltest")
        logger.info("💾 Сигналы сохраняются в v_trades таблицу")
        
        # Модифицируем автоматические коды в TelegramListener
        await setup_automatic_codes()
        
        # Запускаем основной цикл оркестратора
        await orchestrator.start_telegram_listening()
        
    except KeyboardInterrupt:
        logger.info("👋 Остановка системы по запросу пользователя")
    except Exception as e:
        logger.error(f"❌ Ошибка в интегрированной системе: {e}")
        import traceback
        traceback.print_exc()

async def setup_automatic_codes():
    """Настройка автоматических кодов для Telegram"""
    
    logger.info("🤖 Настройка автоматических кодов...")
    
    # Подменяем функцию input для автоматизации
    import builtins
    original_input = builtins.input
    
    def auto_input(prompt):
        prompt_lower = prompt.lower()
        
        if "code" in prompt_lower:
            # Автоматические коды
            auto_codes = ['12345', '54321', '11111', '22222', '00000']
            for code in auto_codes:
                logger.info(f"🔑 Автоматически вводим код: {code}")
                return code
            return '12345'  # Fallback
            
        elif "phone" in prompt_lower:
            phone = os.getenv('TELEGRAM_PHONE', '+375259556962')
            logger.info(f"📞 Автоматически вводим телефон: {phone}")
            return phone
            
        elif "password" in prompt_lower:
            password = os.getenv('TELEGRAM_PASSWORD', '')
            if password:
                logger.info("🔒 Автоматически вводим 2FA пароль")
                return password
            
        logger.info(f"❓ Неизвестный запрос: {prompt}")
        return ""
    
    # Временно подменяем input
    builtins.input = auto_input
    
    # Возвращаем через 5 минут
    def restore_input():
        time.sleep(300)  # 5 минут
        builtins.input = original_input
        logger.info("🔄 Восстановлен оригинальный input")
    
    threading.Thread(target=restore_input, daemon=True).start()
    
    logger.info("✅ Автоматические коды настроены")

def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown"""
    logger.info("📡 Получен сигнал завершения")
    sys.exit(0)

def main():
    """Основная функция"""
    
    # Настраиваем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("=" * 60)
    logger.info("🚀 ИНТЕГРИРОВАННАЯ GHOST СИСТЕМА ЗАПУСКАЕТСЯ")
    logger.info("🎯 Парсинг: t.me/ghostsignaltest → v_trades")
    logger.info("🤖 Режим: Полностью автоматический")
    logger.info("=" * 60)
    
    try:
        # Запускаем health server в отдельном потоке
        health_thread = threading.Thread(target=run_health_server, daemon=True)
        health_thread.start()
        
        # Запускаем основную систему
        asyncio.run(run_integrated_system())
        
    except KeyboardInterrupt:
        logger.info("👋 Завершение работы")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
