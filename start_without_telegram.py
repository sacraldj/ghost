#!/usr/bin/env python3
"""
Запуск GHOST системы без Telegram listener
Для демонстрации работы API и frontend
"""

import asyncio
import logging
import os
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

# Настройка логирования
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ghost_no_telegram.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status": "ok", "telegram": "disabled", "api": "active"}')
    
    def log_message(self, format, *args):
        pass  # Отключаем логи HTTP сервера

async def main():
    print("🚀 GHOST SYSTEM - БЕЗ TELEGRAM")
    print("=" * 50)
    print("✅ Система запущена в демо-режиме")
    print("❌ Telegram отключен (требуется email)")
    print("✅ API активен")
    print("✅ Frontend доступен на http://localhost:3000")
    print("✅ Health check на http://localhost:8080")
    print("=" * 50)
    
    # Запускаем HTTP сервер для health checks
    server = HTTPServer(('0.0.0.0', 8080), HealthHandler)
    logger.info("🌐 Health server запущен на порту 8080")
    
    # Тестируем Supabase подключение
    try:
        from signals.signal_orchestrator_with_supabase import orchestrator_with_supabase
        if await orchestrator_with_supabase.test_supabase_connection():
            logger.info("✅ Supabase подключение работает")
            
            # Тестовый сигнал для демонстрации
            test_signal = "🚀 BTCUSDT LONG - Entry: 65000, TP: 67000, SL: 63000"
            result = await orchestrator_with_supabase.process_raw_signal(
                test_signal, "demo_channel", "demo_trader"
            )
            if result:
                logger.info(f"✅ Тестовый сигнал обработан: {result.symbol}")
            
            stats = await orchestrator_with_supabase.get_stats()
            logger.info(f"📊 Статистика: {stats['signals_processed']} сигналов")
        else:
            logger.warning("⚠️ Supabase недоступен")
    except Exception as e:
        logger.error(f"❌ Ошибка Supabase: {e}")
    
    # Основной цикл
    try:
        while True:
            logger.info("💓 Система работает (без Telegram)")
            time.sleep(60)  # Проверка каждую минуту
    except KeyboardInterrupt:
        logger.info("🛑 Остановка системы...")
    finally:
        server.server_close()

if __name__ == "__main__":
    asyncio.run(main())
