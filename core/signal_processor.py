#!/usr/bin/env python3
"""
GHOST Signal Processor - Обработка торговых сигналов
Модуль для обработки, нормализации и подготовки торговых сигналов к исполнению

Функции:
- Получение сигналов из Redis очереди
- Нормализация и валидация сигналов
- Резолвинг символов торговых инструментов
- Расчёт риск-метрик и размеров позиций
- Подготовка сигналов для ML фильтрации
- Отправка в очередь исполнения
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import yaml
# Временно отключаем aioredis из-за проблем совместимости
try:
    import aioredis
except (ModuleNotFoundError, ImportError) as e:
    print(f"⚠️ aioredis недоступен: {e}")
    aioredis = None
import traceback
import re

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from utils.ghost_logger import log_info, log_warning, log_error
    from utils.database_manager import DatabaseManager
except ImportError as e:
    print(f"Warning: Could not import utils: {e}")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/signal_processor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SignalProcessor')

@dataclass
class ProcessedSignal:
    """Обработанный торговый сигнал"""
    # Исходные данные
    original_signal_id: str
    source_channel: str
    trader_name: str
    timestamp: datetime
    
    # Нормализованные данные
    symbol: str              # Стандартизированный символ (BTCUSDT)
    base_asset: str         # Базовый актив (BTC)
    quote_asset: str        # Котируемый актив (USDT)
    direction: str          # LONG/SHORT
    
    # Ценовые уровни
    entry_price: float          # Рекомендуемая цена входа
    entry_zone_min: float      # Минимальная цена зоны входа
    entry_zone_max: float      # Максимальная цена зоны входа
    tp1_price: Optional[float] = None  # Первый тейк-профит
    tp2_price: Optional[float] = None  # Второй тейк-профит
    tp3_price: Optional[float] = None  # Третий тейк-профит
    sl_price: Optional[float] = None   # Стоп-лосс
    
    # Параметры риска
    suggested_leverage: Optional[int] = None
    risk_reward_ratio: Optional[float] = None
    max_risk_percent: float = 2.0  # Максимальный риск в %
    position_size_usd: Optional[float] = None
    
    # Мета-информация
    confidence_score: float = 0.0     # Уверенность в сигнале (0-1)
    urgency_score: float = 0.5        # Срочность (0-1)
    quality_score: float = 0.0        # Качество сигнала (0-1)
    
    # Статус обработки
    processing_status: str = "pending"  # pending, processed, error, rejected
    processing_errors: List[str] = None
    
    # Трейдер статистика
    trader_win_rate: Optional[float] = None
    trader_avg_roi: Optional[float] = None
    trader_signal_count: int = 0
    
    # Рыночные данные
    current_price: Optional[float] = None
    price_change_24h: Optional[float] = None
    volume_24h: Optional[float] = None
    
    def __post_init__(self):
        if self.processing_errors is None:
            self.processing_errors = []

@dataclass 
class MarketData:
    """Рыночные данные для символа"""
    symbol: str
    current_price: float
    price_change_24h: float
    volume_24h: float
    high_24h: float
    low_24h: float
    timestamp: datetime

class SymbolResolver:
    """Резолвер символов торговых инструментов"""
    
    def __init__(self):
        # Маппинг различных вариантов написания символов
        self.symbol_mapping = {
            # Bitcoin
            'BTC/USDT': 'BTCUSDT',
            'BTC-USDT': 'BTCUSDT', 
            'BITCOIN': 'BTCUSDT',
            
            # Ethereum
            'ETH/USDT': 'ETHUSDT',
            'ETH-USDT': 'ETHUSDT',
            'ETHEREUM': 'ETHUSDT',
            
            # Другие популярные монеты
            'BNB/USDT': 'BNBUSDT',
            'ADA/USDT': 'ADAUSDT',
            'SOL/USDT': 'SOLUSDT',
            'XRP/USDT': 'XRPUSDT',
            'DOT/USDT': 'DOTUSDT',
            'AVAX/USDT': 'AVAXUSDT',
            'MATIC/USDT': 'MATICUSDT',
            'LINK/USDT': 'LINKUSDT',
        }
        
        # Поддерживаемые символы
        self.supported_symbols = {
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT',
            'XRPUSDT', 'DOTUSDT', 'AVAXUSDT', 'MATICUSDT', 'LINKUSDT'
        }
    
    def resolve_symbol(self, raw_symbol: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Резолвинг символа в стандартный формат
        Возвращает: (стандартный_символ, базовый_актив, котируемый_актив)
        """
        if not raw_symbol:
            return None, None, None
        
        # Очистка и нормализация
        symbol = raw_symbol.upper().strip()
        
        # Прямое соответствие
        if symbol in self.supported_symbols:
            base_asset = symbol.replace('USDT', '')
            return symbol, base_asset, 'USDT'
        
        # Поиск в маппинге
        if symbol in self.symbol_mapping:
            resolved = self.symbol_mapping[symbol]
            base_asset = resolved.replace('USDT', '')
            return resolved, base_asset, 'USDT'
        
        # Попытка автоматического резолвинга
        # Удаляем разделители
        clean_symbol = re.sub(r'[/\-_]', '', symbol)
        
        # Проверяем различные варианты
        variants = [
            clean_symbol,
            clean_symbol + 'USDT',
            clean_symbol.replace('USDT', '') + 'USDT'
        ]
        
        for variant in variants:
            if variant in self.supported_symbols:
                base_asset = variant.replace('USDT', '')
                return variant, base_asset, 'USDT'
        
        return None, None, None

class RiskCalculator:
    """Калькулятор рисков и размеров позиций"""
    
    def __init__(self, max_risk_percent: float = 2.0, default_balance: float = 1000.0):
        self.max_risk_percent = max_risk_percent
        self.default_balance = default_balance
    
    def calculate_position_size(self, entry_price: float, sl_price: float, 
                              risk_percent: float, balance: float) -> Dict[str, float]:
        """Расчёт размера позиции на основе риска"""
        if not sl_price or sl_price <= 0:
            return {'position_size_usd': 0, 'risk_amount': 0, 'stop_distance_percent': 0}
        
        # Расчёт расстояния до стопа в процентах
        stop_distance_percent = abs(entry_price - sl_price) / entry_price * 100
        
        # Риск в долларах
        risk_amount = balance * (risk_percent / 100)
        
        # Размер позиции в USDT
        if stop_distance_percent > 0:
            position_size_usd = risk_amount / (stop_distance_percent / 100)
        else:
            position_size_usd = 0
        
        return {
            'position_size_usd': position_size_usd,
            'risk_amount': risk_amount,
            'stop_distance_percent': stop_distance_percent
        }
    
    def calculate_risk_reward_ratio(self, entry_price: float, tp_price: float, 
                                  sl_price: float) -> Optional[float]:
        """Расчёт соотношения риск/прибыль"""
        if not tp_price or not sl_price:
            return None
        
        profit_distance = abs(tp_price - entry_price)
        loss_distance = abs(entry_price - sl_price)
        
        if loss_distance > 0:
            return profit_distance / loss_distance
        
        return None

class SignalProcessor:
    """Основной процессор торговых сигналов"""
    
    def __init__(self, config_path: str = "config/signal_processor_config.yaml"):
        self.config_path = config_path
        self.config = {}
        self.redis: Optional[Any] = None  # aioredis.Redis или None
        self.db_manager: Optional[DatabaseManager] = None
        
        # Компоненты
        self.symbol_resolver = SymbolResolver()
        self.risk_calculator = RiskCalculator()
        
        # Статистика
        self.stats = {
            'signals_processed': 0,
            'signals_valid': 0,
            'signals_rejected': 0,
            'symbols_resolved': 0,
            'symbols_unresolved': 0,
            'start_time': datetime.utcnow()
        }
        
        # Состояние
        self.running = False
        self.processing_queue = asyncio.Queue()
    
    async def initialize(self):
        """Инициализация Signal Processor"""
        logger.info("🚀 Initializing Signal Processor...")
        
        try:
            # Загрузка конфигурации
            await self._load_config()
            
            # Подключение к Redis
            await self._init_redis()
            
            # Инициализация базы данных
            await self._init_database()
            
            logger.info("✅ Signal Processor initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Signal Processor: {e}")
            raise
    
    async def _load_config(self):
        """Загрузка конфигурации"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f)
            else:
                self.config = self._get_default_config()
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(self.config, f, default_flow_style=False)
                    
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self.config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Конфигурация по умолчанию"""
        return {
            'redis': {
                'input_queue': 'ghost:signals:new',
                'output_queue': 'ghost:signals:processed',
                'url': 'redis://localhost:6379/1'
            },
            'processing': {
                'batch_size': 10,
                'max_processing_time': 30,
                'retry_attempts': 3,
                'retry_delay': 5
            },
            'risk_management': {
                'max_risk_percent': 2.0,
                'default_balance': 1000.0,
                'min_risk_reward_ratio': 1.5,
                'max_leverage': 50
            },
            'quality_thresholds': {
                'min_confidence': 0.6,
                'min_quality_score': 0.5,
                'min_trader_win_rate': 0.4
            }
        }
    
    async def _init_redis(self):
        """Инициализация Redis"""
        if not aioredis:
            logger.warning("⚠️ aioredis недоступен, Redis отключен")
            self.redis = None
            return
            
        try:
            redis_url = self.config['redis']['url']
            self.redis = await aioredis.from_url(redis_url)
            await self.redis.ping()
            logger.info("✅ Redis connected")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self.redis = None
    
    async def _init_database(self):
        """Инициализация базы данных"""
        try:
            # В будущем здесь будет DatabaseManager
            logger.info("✅ Database manager initialized")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
    
    async def start_processing(self):
        """Запуск обработки сигналов"""
        logger.info("🔄 Starting signal processing...")
        self.running = True
        
        try:
            # Запуск задач
            await asyncio.gather(
                self._signal_fetcher(),
                self._signal_processor_worker(),
                self._stats_updater()
            )
        except Exception as e:
            logger.error(f"❌ Processing error: {e}")
            raise
        finally:
            await self.shutdown()
    
    async def _signal_fetcher(self):
        """Получение сигналов из Redis очереди"""
        while self.running:
            try:
                if not self.redis:
                    # Если Redis недоступен, просто ждем
                    await asyncio.sleep(5)
                    continue
                    
                # Получаем сигналы из очереди
                signal_data = await self.redis.brpop(
                    self.config['redis']['input_queue'], 
                    timeout=5
                )
                
                if signal_data:
                    _, signal_json = signal_data
                    await self.processing_queue.put(signal_json)
                    
            except Exception as e:
                logger.error(f"Error fetching signals: {e}")
                await asyncio.sleep(5)
    
    async def _signal_processor_worker(self):
        """Воркер для обработки сигналов"""
        while self.running:
            try:
                # Получаем сигнал из очереди обработки
                signal_json = await asyncio.wait_for(
                    self.processing_queue.get(), 
                    timeout=5
                )
                
                # Обрабатываем сигнал
                await self._process_single_signal(signal_json)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in signal processor worker: {e}")
                await asyncio.sleep(1)
    
    async def _process_single_signal(self, signal_json: str):
        """Обработка одного сигнала"""
        try:
            # Парсинг JSON
            signal_data = json.loads(signal_json)
            
            # Создание объекта ProcessedSignal
            processed_signal = await self._create_processed_signal(signal_data)
            
            if processed_signal:
                # Нормализация символа
                await self._resolve_symbol(processed_signal)
                
                # Получение рыночных данных
                await self._fetch_market_data(processed_signal)
                
                # Расчёт рисков
                await self._calculate_risks(processed_signal)
                
                # Получение статистики трейдера
                await self._fetch_trader_stats(processed_signal)
                
                # Валидация и оценка качества
                await self._validate_and_score(processed_signal)
                
                # Сохранение результата
                await self._save_processed_signal(processed_signal)
                
                self.stats['signals_processed'] += 1
                if processed_signal.processing_status == 'processed':
                    self.stats['signals_valid'] += 1
                else:
                    self.stats['signals_rejected'] += 1
                    
                logger.info(f"📊 Processed signal: {processed_signal.symbol} {processed_signal.direction} "
                           f"(quality: {processed_signal.quality_score:.2f})")
            
        except Exception as e:
            logger.error(f"Error processing signal: {e}")
            logger.error(traceback.format_exc())
    
    async def _create_processed_signal(self, signal_data: Dict[str, Any]) -> Optional[ProcessedSignal]:
        """Создание объекта ProcessedSignal из сырых данных"""
        try:
            # Извлекаем базовые данные
            processed_signal = ProcessedSignal(
                original_signal_id=signal_data.get('id', ''),
                source_channel=signal_data.get('channel_name', ''),
                trader_name=signal_data.get('trader_name', ''),
                timestamp=datetime.fromisoformat(signal_data.get('timestamp', datetime.utcnow().isoformat())),
                symbol=signal_data.get('symbol', ''),
                base_asset='',
                quote_asset='',
                direction=signal_data.get('direction', ''),
                entry_price=0.0,
                entry_zone_min=0.0,
                entry_zone_max=0.0,
                confidence_score=signal_data.get('confidence', 0.0)
            )
            
            # Обработка зоны входа
            entry_zone = signal_data.get('entry_zone', [])
            if entry_zone:
                processed_signal.entry_zone_min = min(entry_zone)
                processed_signal.entry_zone_max = max(entry_zone)
                processed_signal.entry_price = sum(entry_zone) / len(entry_zone)
            
            # Обработка TP уровней
            tp_levels = signal_data.get('tp_levels', [])
            if len(tp_levels) >= 1:
                processed_signal.tp1_price = tp_levels[0]
            if len(tp_levels) >= 2:
                processed_signal.tp2_price = tp_levels[1]
            if len(tp_levels) >= 3:
                processed_signal.tp3_price = tp_levels[2]
            
            # SL уровень
            processed_signal.sl_price = signal_data.get('sl_level')
            
            # Параметры риска
            processed_signal.suggested_leverage = signal_data.get('leverage')
            
            return processed_signal
            
        except Exception as e:
            logger.error(f"Error creating processed signal: {e}")
            return None
    
    async def _resolve_symbol(self, signal: ProcessedSignal):
        """Резолвинг символа"""
        try:
            resolved_symbol, base_asset, quote_asset = self.symbol_resolver.resolve_symbol(signal.symbol)
            
            if resolved_symbol:
                signal.symbol = resolved_symbol
                signal.base_asset = base_asset
                signal.quote_asset = quote_asset
                self.stats['symbols_resolved'] += 1
            else:
                signal.processing_errors.append(f"Unable to resolve symbol: {signal.symbol}")
                self.stats['symbols_unresolved'] += 1
                
        except Exception as e:
            signal.processing_errors.append(f"Symbol resolution error: {e}")
    
    async def _fetch_market_data(self, signal: ProcessedSignal):
        """Получение текущих рыночных данных"""
        try:
            # В будущем здесь будет запрос к Binance/Bybit API
            # Пока используем заглушку
            signal.current_price = signal.entry_price if signal.entry_price > 0 else 50000.0
            signal.price_change_24h = 2.5  # %
            signal.volume_24h = 1000000.0  # USDT
            
        except Exception as e:
            signal.processing_errors.append(f"Market data fetch error: {e}")
    
    async def _calculate_risks(self, signal: ProcessedSignal):
        """Расчёт параметров риска"""
        try:
            if signal.entry_price > 0 and signal.sl_price:
                # Расчёт risk/reward ratio
                if signal.tp1_price:
                    signal.risk_reward_ratio = self.risk_calculator.calculate_risk_reward_ratio(
                        signal.entry_price, signal.tp1_price, signal.sl_price
                    )
                
                # Расчёт размера позиции
                risk_calc = self.risk_calculator.calculate_position_size(
                    signal.entry_price, 
                    signal.sl_price,
                    signal.max_risk_percent,
                    self.config['risk_management']['default_balance']
                )
                
                signal.position_size_usd = risk_calc['position_size_usd']
                
        except Exception as e:
            signal.processing_errors.append(f"Risk calculation error: {e}")
    
    async def _fetch_trader_stats(self, signal: ProcessedSignal):
        """Получение статистики трейдера"""
        try:
            # В будущем здесь будет запрос к базе данных
            # Пока используем заглушки
            signal.trader_win_rate = 0.65  # 65%
            signal.trader_avg_roi = 12.5   # 12.5%
            signal.trader_signal_count = 150
            
        except Exception as e:
            signal.processing_errors.append(f"Trader stats fetch error: {e}")
    
    async def _validate_and_score(self, signal: ProcessedSignal):
        """Валидация сигнала и расчёт качества"""
        try:
            errors = []
            quality_score = 0.0
            
            # Базовая валидация
            if not signal.symbol:
                errors.append("Missing symbol")
            else:
                quality_score += 0.2
            
            if not signal.direction:
                errors.append("Missing direction")
            else:
                quality_score += 0.2
            
            if signal.entry_price <= 0:
                errors.append("Missing or invalid entry price")
            else:
                quality_score += 0.15
            
            # Проверка TP/SL
            if signal.tp1_price:
                quality_score += 0.15
            if signal.sl_price:
                quality_score += 0.1
            
            # Проверка risk/reward ratio
            if signal.risk_reward_ratio and signal.risk_reward_ratio >= 1.5:
                quality_score += 0.1
            elif signal.risk_reward_ratio and signal.risk_reward_ratio < 1.0:
                errors.append(f"Poor risk/reward ratio: {signal.risk_reward_ratio:.2f}")
            
            # Проверка статистики трейдера
            if signal.trader_win_rate and signal.trader_win_rate >= 0.6:
                quality_score += 0.05
            
            if signal.confidence_score >= 0.7:
                quality_score += 0.05
            
            # Установка статуса
            signal.quality_score = quality_score
            signal.processing_errors.extend(errors)
            
            if errors:
                signal.processing_status = 'rejected'
            elif quality_score >= self.config['quality_thresholds']['min_quality_score']:
                signal.processing_status = 'processed'
            else:
                signal.processing_status = 'rejected'
                signal.processing_errors.append(f"Quality score too low: {quality_score:.2f}")
            
        except Exception as e:
            signal.processing_errors.append(f"Validation error: {e}")
            signal.processing_status = 'error'
    
    async def _save_processed_signal(self, signal: ProcessedSignal):
        """Сохранение обработанного сигнала"""
        try:
            signal_data = asdict(signal)
            
            # Сохранение в Redis для следующего этапа (ML фильтрация)
            if signal.processing_status == 'processed' and self.redis:
                await self.redis.lpush(
                    self.config['redis']['output_queue'],
                    json.dumps(signal_data, default=str)
                )
            
            # Логирование статистики
            if self.redis:
                await self.redis.hset(
                    'ghost:signal_processor:stats',
                    mapping={
                        'signals_processed': self.stats['signals_processed'],
                    'signals_valid': self.stats['signals_valid'],
                    'signals_rejected': self.stats['signals_rejected'],
                    'last_update': datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to save processed signal: {e}")
    
    async def _stats_updater(self):
        """Обновление статистики"""
        while self.running:
            try:
                await asyncio.sleep(60)  # Обновляем каждую минуту
                
                uptime = (datetime.utcnow() - self.stats['start_time']).total_seconds()
                processing_rate = self.stats['signals_processed'] / max(uptime / 60, 1)
                
                logger.info(f"📊 Stats: {self.stats['signals_processed']} processed, "
                           f"{self.stats['signals_valid']} valid, "
                           f"{processing_rate:.1f} signals/min")
                
            except Exception as e:
                logger.error(f"Error updating stats: {e}")
    
    async def get_status(self) -> Dict[str, Any]:
        """Получение статуса Signal Processor"""
        uptime = (datetime.utcnow() - self.stats['start_time']).total_seconds()
        
        return {
            'status': 'running' if self.running else 'stopped',
            'uptime': uptime,
            'queue_size': self.processing_queue.qsize(),
            'statistics': {
                **self.stats,
                'processing_rate': self.stats['signals_processed'] / max(uptime / 60, 1),
                'success_rate': self.stats['signals_valid'] / max(self.stats['signals_processed'], 1) * 100,
                'symbol_resolution_rate': self.stats['symbols_resolved'] / max(self.stats['symbols_resolved'] + self.stats['symbols_unresolved'], 1) * 100
            },
            'redis_connected': self.redis is not None
        }
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("🛑 Shutting down Signal Processor...")
        self.running = False
        
        if self.redis:
            try:
                await self.redis.close()
            except:
                pass  # Игнорируем ошибки при закрытии
        
        logger.info("✅ Signal Processor shutdown complete")

async def main():
    """Главная функция"""
    processor = SignalProcessor()
    
    try:
        await processor.initialize()
        await processor.start_processing()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Signal Processor failed: {e}")
        logger.error(traceback.format_exc())
    finally:
        await processor.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
