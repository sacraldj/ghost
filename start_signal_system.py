#!/usr/bin/env python3
"""
Запуск системы отслеживания сигналов и сбора свечей
Основной entry point для сервиса
"""

import asyncio
import logging
import signal
import sys
import os
from datetime import datetime

# Настройка путей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Импорты системы
from core.signal_candle_tracker import get_signal_tracker
from core.bybit_websocket import get_bybit_client

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/signal_system.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class SignalSystemService:
    """Главный сервис системы отслеживания сигналов"""
    
    def __init__(self):
        self.tracker = get_signal_tracker()
        self.bybit_client = get_bybit_client()
        self.is_running = False
        
    async def start(self):
        """Запуск системы"""
        logger.info("🚀 Starting Signal Tracking System...")
        logger.info(f"📅 Start time: {datetime.now().isoformat()}")
        
        try:
            self.is_running = True
            
            # Запускаем трекер в фоне
            tracking_task = asyncio.create_task(self.tracker.start_tracking())
            
            logger.info("✅ Signal Tracking System started successfully")
            logger.info("📊 Monitoring for new signals and collecting candles...")
            
            # Выводим статистику каждые 5 минут
            while self.is_running:
                await asyncio.sleep(300)  # 5 минут
                await self._print_statistics()
                
        except asyncio.CancelledError:
            logger.info("📋 Received shutdown signal")
        except Exception as e:
            logger.error(f"❌ Error in main loop: {e}")
            raise
        finally:
            await self.stop()
    
    async def stop(self):
        """Остановка системы"""
        logger.info("🛑 Stopping Signal Tracking System...")
        
        try:
            self.is_running = False
            
            # Останавливаем трекер
            await self.tracker.stop()
            
            logger.info("✅ Signal Tracking System stopped successfully")
            
        except Exception as e:
            logger.error(f"❌ Error stopping system: {e}")
    
    async def _print_statistics(self):
        """Вывод текущей статистики"""
        try:
            # Статистика трекера
            tracker_stats = self.tracker.get_statistics()
            
            # Статистика WebSocket клиента
            ws_stats = self.bybit_client.get_statistics()
            
            logger.info("📊 === SYSTEM STATISTICS ===")
            logger.info(f"🔍 Tracked signals: {tracker_stats['signals_tracked']}")
            logger.info(f"📈 Active symbols: {tracker_stats['symbols_active']}")
            logger.info(f"💾 Candles saved: {tracker_stats['candles_saved']}")
            logger.info(f"🔌 WS connections: {ws_stats['active_connections']}")
            logger.info(f"📊 Total WS candles: {ws_stats['total_candles']}")
            logger.info(f"⚡ Candles/hour: {tracker_stats.get('candles_per_hour', 0)}")
            logger.info(f"⏱️ Uptime: {tracker_stats['uptime_seconds']}s")
            
            if tracker_stats['tracked_signals']:
                logger.info(f"📋 Signals: {', '.join(tracker_stats['tracked_signals'])}")
            
            if tracker_stats['active_symbols']:
                logger.info(f"💰 Symbols: {', '.join(tracker_stats['active_symbols'])}")
                
        except Exception as e:
            logger.error(f"❌ Error getting statistics: {e}")

# Глобальный экземпляр сервиса
service = None

def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown"""
    logger.info(f"📋 Received signal {signum}")
    if service:
        asyncio.create_task(service.stop())

async def main():
    """Главная функция"""
    global service
    
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Создаем и запускаем сервис
    service = SignalSystemService()
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("📋 Received keyboard interrupt")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Создаем директорию логов если не существует
    os.makedirs('logs', exist_ok=True)
    
    # Запускаем систему
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("✅ System shutdown complete")
    except Exception as e:
        logger.error(f"❌ System crashed: {e}")
        sys.exit(1)
