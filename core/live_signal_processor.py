"""
GHOST Live Signal Processor
Интеграция UnifiedSignalSystem с ChannelManager для обработки live данных из Telegram
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import asdict

# Наши компоненты
from signals.unified_signal_system import UnifiedSignalParser, UnifiedSignal, SignalStatus, SignalSource
from core.channel_manager import ChannelManager, SourceConfig
from core.telegram_listener import TelegramListener

# Supabase интеграция
import os
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class LiveSignalProcessor:
    """Процессор живых сигналов от Telegram и других источников"""
    
    def __init__(self):
        # Основные компоненты
        self.unified_parser = UnifiedSignalParser()
        self.channel_manager = ChannelManager()
        self.telegram_listener = None
        
        # Supabase клиент
        self.supabase = self._init_supabase()
        
        # Кэш для дедупликации
        self.processed_messages = set()
        self.recent_signals = {}  # trader_id -> последние сигналы
        
        # Статистика обработки
        self.stats = {
            "messages_received": 0,
            "signals_detected": 0,
            "signals_parsed": 0,
            "signals_saved": 0,
            "duplicates_filtered": 0,
            "errors": 0
        }
        
        logger.info("Live Signal Processor initialized")
    
    def _init_supabase(self) -> Optional[Client]:
        """Инициализация Supabase клиента"""
        try:
            supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            
            if not supabase_url or not supabase_key:
                logger.warning("Supabase credentials not found")
                return None
            
            supabase = create_client(supabase_url, supabase_key)
            logger.info("✅ Supabase client initialized")
            return supabase
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase: {e}")
            return None
    
    async def start_processing(self):
        """Запуск обработки живых сигналов"""
        logger.info("🚀 Starting live signal processing...")
        
        # Загружаем активные источники
        active_sources = self.channel_manager.get_active_sources()
        logger.info(f"📡 Found {len(active_sources)} active sources")
        
        # Запускаем Telegram listener
        await self._start_telegram_processing()
        
        # Запускаем периодические задачи
        await self._start_background_tasks()
        
        logger.info("✅ Live signal processing started")
    
    async def _start_telegram_processing(self):
        """Запуск обработки Telegram сообщений"""
        try:
            from core.channel_manager import SourceType
            
            # Получаем Telegram источники
            telegram_sources = [
                s for s in self.channel_manager.get_active_sources() 
                if s.source_type in [SourceType.TELEGRAM_CHANNEL, SourceType.TELEGRAM_GROUP]
            ]
            
            if not telegram_sources:
                logger.warning("No active Telegram sources found")
                return
            
            # Создаем Telegram listener
            self.telegram_listener = TelegramListener()
            
            # Регистрируем обработчик сообщений
            self.telegram_listener.set_message_handler(self._handle_telegram_message)
            
            # Запускаем в фоне
            asyncio.create_task(self.telegram_listener.start())
            
            logger.info(f"📱 Telegram processing started for {len(telegram_sources)} sources")
            
        except Exception as e:
            logger.error(f"❌ Failed to start Telegram processing: {e}")
    
    async def _handle_telegram_message(self, message_data: Dict[str, Any]):
        """Обработка сообщения из Telegram"""
        try:
            self.stats["messages_received"] += 1
            
            # Извлекаем данные сообщения
            chat_id = message_data.get("chat_id")
            message_id = message_data.get("message_id")
            text = message_data.get("text", "")
            timestamp = message_data.get("timestamp", datetime.now())
            
            # Создаем уникальный ID для дедупликации
            unique_id = f"{chat_id}_{message_id}"
            
            if unique_id in self.processed_messages:
                self.stats["duplicates_filtered"] += 1
                return
            
            self.processed_messages.add(unique_id)
            
            # Определяем источник
            source_config = self._find_source_by_chat_id(chat_id)
            if not source_config:
                logger.debug(f"Unknown source for chat_id: {chat_id}")
                return
            
            # Преобразуем в SignalSource enum
            signal_source = self._map_source_type(source_config.source_type)
            
            # Фильтруем сообщения
            if not self._message_looks_like_signal(text, source_config):
                logger.debug(f"Message filtered out: {text[:50]}...")
                return
            
            self.stats["signals_detected"] += 1
            
            # Сохраняем сырой сигнал
            await self._save_raw_signal(text, source_config, message_data)
            
            # Парсим сигнал
            parsed_signal = await self.unified_parser.parse_signal(
                raw_text=text,
                source=signal_source,
                trader_id=source_config.source_id,
                message_id=str(message_id)
            )
            
            if parsed_signal and parsed_signal.is_valid:
                self.stats["signals_parsed"] += 1
                
                # Сохраняем обработанный сигнал
                await self._save_parsed_signal(parsed_signal, source_config)
                
                # Обновляем кэш последних сигналов
                self._update_recent_signals_cache(parsed_signal)
                
                logger.info(f"✅ Signal processed: {parsed_signal.symbol} {parsed_signal.side} from {source_config.name}")
                
            else:
                logger.warning(f"❌ Failed to parse signal from {source_config.name}")
                
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"❌ Error handling Telegram message: {e}")
    
    def _find_source_by_chat_id(self, chat_id: str) -> Optional[SourceConfig]:
        """Поиск источника по chat_id"""
        for source in self.channel_manager.get_active_sources():
            if str(source.connection_params.get("channel_id")) == str(chat_id):
                return source
        return None
    
    def _map_source_type(self, source_type) -> SignalSource:
        """Маппинг типа источника в SignalSource enum"""
        from core.channel_manager import SourceType
        
        # Если передан enum, извлекаем значение
        if isinstance(source_type, SourceType):
            source_type_str = source_type.value
        else:
            source_type_str = str(source_type)
            
        mapping = {
            "telegram_channel": SignalSource.TELEGRAM_WHALESGUIDE,
            "telegram_whalesguide": SignalSource.TELEGRAM_WHALESGUIDE,
            "telegram_2trade": SignalSource.TELEGRAM_2TRADE,
            "telegram_crypto_hub": SignalSource.TELEGRAM_CRYPTO_HUB,
            "telegram_coinpulse": SignalSource.TELEGRAM_COINPULSE,
            "discord_channel": SignalSource.DISCORD_VIP,
        }
        return mapping.get(source_type_str, SignalSource.UNKNOWN)
    
    def _message_looks_like_signal(self, text: str, source_config: SourceConfig) -> bool:
        """Проверка, похоже ли сообщение на сигнал"""
        
        # Проверяем минимальную длину
        if len(text.strip()) < 20:
            return False
        
        # Проверяем ключевые слова источника
        if source_config.keywords_filter:
            text_lower = text.lower()
            if not any(keyword in text_lower for keyword in source_config.keywords_filter):
                return False
        
        # Проверяем исключающие слова
        if source_config.exclude_keywords:
            text_lower = text.lower()
            if any(keyword in text_lower for keyword in source_config.exclude_keywords):
                return False
        
        # Базовые паттерны сигналов
        signal_patterns = [
            r"(entry|вход|входа)",
            r"(target|tp\d|цель)",
            r"(stop|sl|стоп)",
            r"(long|short|лонг|шорт)",
            r"(buy|sell|покуп|прода)",
            r"usdt",
            r"\$\d+",  # Цены с долларом
            r"\d+\.\d+",  # Десятичные числа
        ]
        
        text_lower = text.lower()
        matches = sum(1 for pattern in signal_patterns if __import__('re').search(pattern, text_lower))
        
        # Если есть хотя бы 3 совпадения - вероятно сигнал
        return matches >= 3
    
    async def _save_raw_signal(self, text: str, source_config: SourceConfig, message_data: Dict):
        """Сохранение сырого сигнала в базу"""
        try:
            if not self.supabase:
                return
            
            raw_signal_data = {
                "trader_id": source_config.source_id,
                "source_msg_id": str(message_data.get("message_id")),
                "posted_at": message_data.get("timestamp", datetime.now()).isoformat(),
                "text": text,
                "meta": {
                    "chat_id": message_data.get("chat_id"),
                    "source_name": source_config.name,
                    "source_type": source_config.source_type,
                    "processing_version": "v1.0"
                },
                "processed": False
            }
            
            result = self.supabase.table("signals_raw").insert(raw_signal_data).execute()
            
            if result.data:
                logger.debug(f"✅ Raw signal saved for {source_config.name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save raw signal: {e}")
    
    async def _save_parsed_signal(self, signal: UnifiedSignal, source_config: SourceConfig):
        """Сохранение обработанного сигнала в базу"""
        try:
            if not self.supabase:
                return
            
            # Подготавливаем данные для signals_parsed
            parsed_data = {
                "trader_id": signal.trader_id,
                "posted_at": signal.received_at.isoformat(),
                "symbol": signal.symbol,
                "side": signal.side,
                "entry_type": signal.entry_type,
                "entry": float(signal.entry_single) if signal.entry_single else None,
                "range_low": float(min(signal.entry_zone)) if signal.entry_zone else None,
                "range_high": float(max(signal.entry_zone)) if signal.entry_zone else None,
                "tp1": float(signal.tp1) if signal.tp1 else None,
                "tp2": float(signal.tp2) if signal.tp2 else None,
                "tp3": float(signal.tp3) if signal.tp3 else None,
                "tp4": float(signal.tp4) if signal.tp4 else None,
                "sl": float(signal.sl) if signal.sl else None,
                "leverage_hint": self._extract_leverage_number(signal.leverage),
                "confidence": float(signal.confidence) if signal.confidence else None,
                "parse_version": "unified_v1.0",
                "checksum": self._generate_signal_checksum(signal),
                "is_valid": signal.is_valid
            }
            
            result = self.supabase.table("signals_parsed").insert(parsed_data).execute()
            
            if result.data:
                self.stats["signals_saved"] += 1
                logger.debug(f"✅ Parsed signal saved: {signal.symbol} {signal.side}")
                
                # Запускаем симуляцию исхода в фоне
                asyncio.create_task(self._simulate_signal_outcome(result.data[0], signal))
            
        except Exception as e:
            logger.error(f"❌ Failed to save parsed signal: {e}")
    
    def _extract_leverage_number(self, leverage_str: Optional[str]) -> Optional[int]:
        """Извлечение числового значения плеча"""
        if not leverage_str:
            return None
        
        import re
        match = re.search(r"(\d+)", leverage_str)
        return int(match.group(1)) if match else None
    
    def _generate_signal_checksum(self, signal: UnifiedSignal) -> str:
        """Генерация контрольной суммы сигнала для дедупликации"""
        import hashlib
        
        key_data = f"{signal.trader_id}_{signal.symbol}_{signal.side}_{signal.entry_single or signal.avg_entry_price}_{signal.tp1}_{signal.sl}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def _simulate_signal_outcome(self, parsed_signal_data: Dict, original_signal: UnifiedSignal):
        """Симуляция исхода сигнала (отложенная задача)"""
        try:
            # Эта функция будет реализована позже
            # Здесь будет логика симуляции торговли по сигналу
            logger.debug(f"📊 Simulating outcome for {original_signal.symbol}")
            
        except Exception as e:
            logger.error(f"❌ Failed to simulate signal outcome: {e}")
    
    def _update_recent_signals_cache(self, signal: UnifiedSignal):
        """Обновление кэша последних сигналов"""
        trader_id = signal.trader_id
        
        if trader_id not in self.recent_signals:
            self.recent_signals[trader_id] = []
        
        self.recent_signals[trader_id].append({
            "symbol": signal.symbol,
            "side": signal.side,
            "timestamp": signal.received_at,
            "confidence": signal.confidence
        })
        
        # Оставляем только последние 10 сигналов на трейдера
        self.recent_signals[trader_id] = self.recent_signals[trader_id][-10:]
    
    async def _start_background_tasks(self):
        """Запуск фоновых задач"""
        
        # Задача очистки кэша
        asyncio.create_task(self._cleanup_cache_periodically())
        
        # Задача обновления статистики
        asyncio.create_task(self._update_stats_periodically())
        
        logger.info("📊 Background tasks started")
    
    async def _cleanup_cache_periodically(self):
        """Периодическая очистка кэша"""
        while True:
            try:
                await asyncio.sleep(3600)  # Каждый час
                
                # Очищаем старые processed_messages
                if len(self.processed_messages) > 10000:
                    # Оставляем только последние 5000
                    recent_messages = list(self.processed_messages)[-5000:]
                    self.processed_messages = set(recent_messages)
                
                # Очищаем старые сигналы из кэша
                cutoff_time = datetime.now() - timedelta(hours=24)
                for trader_id in list(self.recent_signals.keys()):
                    self.recent_signals[trader_id] = [
                        s for s in self.recent_signals[trader_id]
                        if s["timestamp"] > cutoff_time
                    ]
                    
                    if not self.recent_signals[trader_id]:
                        del self.recent_signals[trader_id]
                
                logger.debug("🧹 Cache cleanup completed")
                
            except Exception as e:
                logger.error(f"❌ Error in cache cleanup: {e}")
    
    async def _update_stats_periodically(self):
        """Периодическое обновление статистики"""
        while True:
            try:
                await asyncio.sleep(300)  # Каждые 5 минут
                
                # Выводим статистику
                logger.info(f"📊 Processing stats: {self.stats}")
                
                # Сохраняем статистику в базу (если нужно)
                await self._save_processing_stats()
                
            except Exception as e:
                logger.error(f"❌ Error updating stats: {e}")
    
    async def _save_processing_stats(self):
        """Сохранение статистики обработки"""
        try:
            if not self.supabase:
                return
            
            stats_data = {
                "timestamp": datetime.now().isoformat(),
                "component": "live_signal_processor",
                "stats": self.stats,
                "active_sources": len(self.channel_manager.get_active_sources()),
                "recent_traders": len(self.recent_signals)
            }
            
            # Можно сохранить в отдельную таблицу system_stats
            # self.supabase.table("system_stats").insert(stats_data).execute()
            
        except Exception as e:
            logger.error(f"❌ Failed to save processing stats: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение текущей статистики"""
        return {
            **self.stats,
            "active_sources": len(self.channel_manager.get_active_sources()),
            "recent_traders": len(self.recent_signals),
            "cache_size": len(self.processed_messages)
        }
    
    async def stop_processing(self):
        """Остановка обработки"""
        logger.info("🛑 Stopping live signal processing...")
        
        if self.telegram_listener:
            await self.telegram_listener.stop()
        
        logger.info("✅ Live signal processing stopped")


# Глобальный экземпляр процессора
live_processor = LiveSignalProcessor()

def get_live_processor() -> LiveSignalProcessor:
    """Получение глобального экземпляра процессора"""
    return live_processor


# Функция для тестирования
async def test_live_processor():
    """Тестирование live процессора"""
    print("🧪 ТЕСТИРОВАНИЕ LIVE SIGNAL PROCESSOR")
    print("=" * 60)
    
    processor = get_live_processor()
    
    # Проверяем компоненты
    print(f"📊 Компоненты:")
    print(f"   Unified Parser: ✅")
    print(f"   Channel Manager: ✅")
    print(f"   Supabase: {'✅' if processor.supabase else '❌'}")
    
    # Проверяем активные источники
    active_sources = processor.channel_manager.get_active_sources()
    print(f"\n📡 Активные источники: {len(active_sources)}")
    for source in active_sources:
        print(f"   • {source.name} ({source.source_type})")
    
    # Тестируем обработку сообщения
    test_message = {
        "chat_id": "-1001234567890",
        "message_id": "12345",
        "text": """Longing #BTCUSDT Here
        
        Entry: $45000 - $44500
        Targets: $46000, $47000
        Stoploss: $43000""",
        "timestamp": datetime.now()
    }
    
    print(f"\n🧪 Тестовое сообщение:")
    await processor._handle_telegram_message(test_message)
    
    # Статистика
    print(f"\n📊 Статистика: {processor.get_stats()}")
    
    print(f"\n🎉 LIVE PROCESSOR READY!")


if __name__ == "__main__":
    asyncio.run(test_live_processor())
