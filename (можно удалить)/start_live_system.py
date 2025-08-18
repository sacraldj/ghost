#!/usr/bin/env python3
"""
Запуск полной live системы для unified signal processing
Интегрирует все компоненты: ChannelManager + UnifiedParser + LiveProcessor + Supabase
"""

import asyncio
import os
import sys
import logging
from datetime import datetime

# Добавляем корневую папку в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импорты наших компонентов
from core.live_signal_processor import LiveSignalProcessor, get_live_processor
from signals.unified_signal_system import get_unified_parser, test_unified_parser
from core.channel_manager import ChannelManager
from signals.ai_fallback_parser import get_ai_parser
from core.candle_websocket import get_candle_collector, CandleData
from core.signal_analyzer import get_signal_analyzer, SignalAnalysis
from supabase import create_client, Client

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/live_system.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

class LiveSystemOrchestrator:
    """Оркестратор для запуска всей live системы"""
    
    def __init__(self):
        # Инициализируем Supabase клиент с обработкой ошибок
        supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        self.supabase = None
        if supabase_url and supabase_key:
            try:
                self.supabase = create_client(supabase_url, supabase_key)
                print("✅ Supabase клиент успешно инициализирован")
            except Exception as e:
                print(f"⚠️ Ошибка инициализации Supabase: {e}")
                print("🔄 Система будет работать без Supabase интеграции")
                self.supabase = None
        
        # Основные компоненты
        self.live_processor = get_live_processor()
        self.unified_parser = get_unified_parser()
        self.ai_parser = get_ai_parser()
        self.channel_manager = ChannelManager()
        
        # НОВЫЕ КОМПОНЕНТЫ для честной статистики как у Дарена
        self.candle_collector = get_candle_collector(self.supabase) if self.supabase else None
        self.signal_analyzer = get_signal_analyzer(self.supabase) if self.supabase else None
        
        # Статистика системы
        self.system_stats = {
            "started_at": None,
            "uptime_seconds": 0,
            "total_messages": 0,
            "total_signals": 0,
            "analyzed_signals": 0,
            "live_candles": 0,
            "components_status": {}
        }
        
        logger.info("Live System Orchestrator initialized with full analysis stack")
    
    async def check_prerequisites(self) -> bool:
        """Проверка всех предварительных условий"""
        logger.info("🔍 Checking system prerequisites...")
        
        issues = []
        
        # 1. Проверяем переменные окружения
        required_env_vars = [
            "NEXT_PUBLIC_SUPABASE_URL",
            "SUPABASE_SERVICE_ROLE_KEY"
        ]
        
        for var in required_env_vars:
            if not os.getenv(var):
                issues.append(f"Missing environment variable: {var}")
        
        # 2. Проверяем доступность Supabase
        if self.live_processor.supabase is None:
            issues.append("Supabase client not initialized")
        
        # 3. Проверяем активные источники
        active_sources = self.channel_manager.get_active_sources()
        if not active_sources:
            issues.append("No active signal sources configured")
        
        # 4. Проверяем парсеры
        parser_stats = self.unified_parser.get_stats()
        if not parser_stats:
            issues.append("Unified parser not properly initialized")
        
        # 5. Проверяем AI доступность (опционально)
        ai_availability = self.ai_parser.is_available()
        if not ai_availability["any_available"]:
            logger.warning("⚠️ No AI parsers available (OpenAI/Gemini not configured)")
        
        if issues:
            logger.error("❌ Prerequisites check failed:")
            for issue in issues:
                logger.error(f"   • {issue}")
            return False
        
        logger.info("✅ All prerequisites satisfied")
        return True
    
    async def start_system(self):
        """Запуск всей системы"""
        logger.info("🚀 STARTING GHOST LIVE SIGNAL SYSTEM")
        logger.info("=" * 60)
        
        # Проверяем предварительные условия
        if not await self.check_prerequisites():
            logger.error("❌ Cannot start system - prerequisites not met")
            return False
        
        try:
            # Записываем время запуска
            self.system_stats["started_at"] = datetime.now()
            
            # 1. Запускаем live processor
            logger.info("📊 Starting Live Signal Processor...")
            await self.live_processor.start_processing()
            self.system_stats["components_status"]["live_processor"] = "running"
            
            # 2. Запускаем Live Candle Collector (как у Дарена)
            logger.info("📈 Starting Live Candle Collector...")
            await self.candle_collector.start()
            
            # Подписываемся на основные символы
            popular_symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "XRPUSDT", "SOLUSDT"]
            for symbol in popular_symbols:
                await self.candle_collector.subscribe_to_symbol(symbol, ["1m", "5m"])
            
            self.system_stats["components_status"]["candle_collector"] = "running"
            
            # 3. Настраиваем Signal Analyzer callbacks
            logger.info("🎯 Setting up Signal Analysis callbacks...")
            self._setup_signal_analysis_callbacks()
            self.system_stats["components_status"]["signal_analyzer"] = "running"
            
            # 4. Запускаем мониторинг системы
            logger.info("📈 Starting System Monitor...")
            asyncio.create_task(self._monitor_system())
            self.system_stats["components_status"]["system_monitor"] = "running"
            
            # 5. Запускаем периодические задачи
            logger.info("⏰ Starting Periodic Tasks...")
            asyncio.create_task(self._periodic_tasks())
            self.system_stats["components_status"]["periodic_tasks"] = "running"
            
            logger.info("✅ LIVE SYSTEM STARTED SUCCESSFULLY!")
            logger.info("🔍 Monitoring active sources:")
            
            for source in self.channel_manager.get_active_sources():
                logger.info(f"   📡 {source.name} ({source.source_type})")
            
            # Остаемся в работе
            await self._keep_running()
            
        except Exception as e:
            logger.error(f"❌ Error starting system: {e}")
            return False
    
    def _setup_signal_analysis_callbacks(self):
        """Настройка callbacks для анализа сигналов"""
        try:
            # Callback для обработки новых свечей
            async def on_new_candle(candle: CandleData):
                self.system_stats["live_candles"] += 1
                
                # Проверяем, есть ли открытые сигналы для этого символа
                if self.supabase:
                    result = self.supabase.table("signals_parsed") \
                        .select("signal_id, trader_id") \
                        .eq("symbol", candle.symbol) \
                        .eq("is_active", True) \
                        .execute()
                    
                    active_signals = result.data or []
                    
                    if active_signals:
                        logger.debug(f"📊 New candle for {len(active_signals)} active signals: {candle.symbol} @ {candle.close_price}")
            
            # Callback для анализа новых сигналов
            async def on_new_signal(signal_data: dict):
                try:
                    # Анализируем сигнал как у Дарена
                    analysis = await self.signal_analyzer.analyze_signal(signal_data)
                    self.system_stats["analyzed_signals"] += 1
                    
                    logger.info(f"🎯 Signal analyzed: {analysis.signal_id}")
                    logger.info(f"   TP1 Probability: {analysis.tp1_probability}%")
                    logger.info(f"   Confidence: {analysis.confidence_score}")
                    
                    # Подписываемся на свечи для этого символа если ещё не подписаны
                    await self.candle_collector.subscribe_to_symbol(signal_data.get("symbol", ""), ["1m"])
                    
                except Exception as e:
                    logger.error(f"❌ Error analyzing signal: {e}")
            
            # Регистрируем callbacks
            self.candle_collector.add_callback(on_new_candle)
            
            # Здесь бы добавить callback в live_processor для новых сигналов
            # self.live_processor.add_signal_callback(on_new_signal)
            
            logger.info("✅ Signal analysis callbacks configured")
            
        except Exception as e:
            logger.error(f"❌ Error setting up signal analysis callbacks: {e}")
    
    async def _monitor_system(self):
        """Мониторинг состояния системы"""
        while True:
            try:
                await asyncio.sleep(60)  # Каждую минуту
                
                # Обновляем uptime
                if self.system_stats["started_at"]:
                    uptime = datetime.now() - self.system_stats["started_at"]
                    self.system_stats["uptime_seconds"] = int(uptime.total_seconds())
                
                # Собираем статистику
                processor_stats = self.live_processor.get_stats()
                parser_stats = self.unified_parser.get_stats()
                ai_stats = self.ai_parser.get_ai_stats()
                
                # Обновляем общую статистику
                self.system_stats["total_messages"] = processor_stats.get("messages_received", 0)
                self.system_stats["total_signals"] = processor_stats.get("signals_parsed", 0)
                
                # Выводим краткую статистику
                logger.info(f"📊 System Status - Uptime: {self.system_stats['uptime_seconds']}s, Messages: {self.system_stats['total_messages']}, Signals: {self.system_stats['total_signals']}")
                
            except Exception as e:
                logger.error(f"❌ Error in system monitor: {e}")
    
    async def _periodic_tasks(self):
        """Периодические задачи"""
        while True:
            try:
                await asyncio.sleep(300)  # Каждые 5 минут
                
                # 1. Обновляем статистику парсеров
                await self._update_parser_statistics()
                
                # 2. Проверяем здоровье системы
                await self._health_check()
                
                # 3. Очищаем старые данные (раз в час)
                current_minute = datetime.now().minute
                if current_minute == 0:  # Каждый час
                    await self._cleanup_old_data()
                
            except Exception as e:
                logger.error(f"❌ Error in periodic tasks: {e}")
    
    async def _update_parser_statistics(self):
        """Обновление статистики парсеров"""
        try:
            parser_stats = self.unified_parser.get_stats()
            
            # Сохраняем в базу если есть Supabase
            if self.live_processor.supabase:
                stats_data = {
                    "parser_type": "unified_system",
                    "date": datetime.now().date().isoformat(),
                    "total_attempts": parser_stats.get("total_signals", 0),
                    "successful_parses": parser_stats.get("parsed_by_rules", 0) + parser_stats.get("parsed_by_ai", 0),
                    "failed_parses": parser_stats.get("failed_parsing", 0),
                    "ai_fallback_used": parser_stats.get("parsed_by_ai", 0),
                    "avg_confidence": parser_stats.get("avg_confidence", 0),
                    "sources_processed": [],
                    "traders_detected": []
                }
                
                # Upsert статистику
                result = self.live_processor.supabase.table("parser_stats").upsert(
                    stats_data,
                    on_conflict="parser_type,date"
                ).execute()
                
                logger.debug("📊 Parser statistics updated")
                
        except Exception as e:
            logger.error(f"❌ Error updating parser statistics: {e}")
    
    async def _health_check(self):
        """Проверка здоровья системы"""
        try:
            health_status = {
                "live_processor": "healthy",
                "unified_parser": "healthy", 
                "ai_parser": "healthy",
                "channel_manager": "healthy",
                "supabase": "healthy"
            }
            
            # Проверяем каждый компонент
            try:
                processor_stats = self.live_processor.get_stats()
                if processor_stats.get("errors", 0) > 100:  # Много ошибок
                    health_status["live_processor"] = "degraded"
            except:
                health_status["live_processor"] = "unhealthy"
            
            try:
                ai_availability = self.ai_parser.is_available()
                if not ai_availability["any_available"]:
                    health_status["ai_parser"] = "unavailable"
            except:
                health_status["ai_parser"] = "unhealthy"
            
            try:
                if not self.live_processor.supabase:
                    health_status["supabase"] = "unavailable"
            except:
                health_status["supabase"] = "unhealthy"
            
            # Логируем проблемы
            unhealthy_components = [k for k, v in health_status.items() if v != "healthy"]
            if unhealthy_components:
                logger.warning(f"⚠️ Health issues detected: {unhealthy_components}")
            
        except Exception as e:
            logger.error(f"❌ Error in health check: {e}")
    
    async def _cleanup_old_data(self):
        """Очистка старых данных"""
        try:
            logger.info("🧹 Running cleanup tasks...")
            
            # Очищаем кэш в live processor
            cache_size = len(self.live_processor.processed_messages)
            if cache_size > 5000:
                # Оставляем только последние 2500
                recent_messages = list(self.live_processor.processed_messages)[-2500:]
                self.live_processor.processed_messages = set(recent_messages)
                logger.info(f"🧹 Cleaned message cache: {cache_size} -> {len(recent_messages)}")
            
        except Exception as e:
            logger.error(f"❌ Error in cleanup: {e}")
    
    async def _keep_running(self):
        """Поддержание работы системы"""
        try:
            while True:
                await asyncio.sleep(30)
                
                # Проверяем, что все компоненты работают
                if not all(status == "running" for status in self.system_stats["components_status"].values()):
                    logger.warning("⚠️ Some components not running properly")
                
        except KeyboardInterrupt:
            logger.info("📢 Received shutdown signal")
            await self.stop_system()
        except Exception as e:
            logger.error(f"❌ Error in main loop: {e}")
            await self.stop_system()
    
    async def stop_system(self):
        """Остановка системы"""
        logger.info("🛑 Stopping Live Signal System...")
        
        try:
            # Останавливаем live processor
            await self.live_processor.stop_processing()
            
            # Сохраняем финальную статистику
            if self.live_processor.supabase:
                final_stats = {
                    "timestamp": datetime.now().isoformat(),
                    "component": "system_shutdown",
                    "stats": self.system_stats,
                    "active_sources": len(self.channel_manager.get_active_sources()),
                    "recent_traders": len(self.live_processor.recent_signals)
                }
                
                if self.supabase:
                    try:
                        self.supabase.table("system_stats").insert(final_stats).execute()
                        print("✅ Статистика сохранена в Supabase")
                    except Exception as e:
                        print(f"⚠️ Ошибка сохранения статистики: {e}")
                else:
                    print("ℹ️ Supabase недоступен, статистика не сохранена")
            
            logger.info("✅ System stopped gracefully")
            
        except Exception as e:
            logger.error(f"❌ Error stopping system: {e}")

async def main():
    """Главная функция"""
    print("🎯 GHOST LIVE SIGNAL SYSTEM")
    print("=" * 60)
    print("🚀 Unified Signal Processing with AI Fallback")
    print("📱 Telegram + Discord + RSS Integration") 
    print("🤖 OpenAI + Gemini AI Parsing")
    print("📊 Real-time Statistics & Monitoring")
    print("=" * 60)
    
    # Создаем и запускаем orchestrator
    orchestrator = LiveSystemOrchestrator()
    
    try:
        await orchestrator.start_system()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    # Создаем папку для логов если её нет
    os.makedirs("logs", exist_ok=True)
    
    # Запускаем систему
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
