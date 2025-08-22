"""
GHOST Signal Orchestrator с полной интеграцией Supabase
Оркестратор для управления всеми специализированными парсерами сигналов
Каждый канал трейдера имеет свой специализированный парсер
ВСЕ ДАННЫЕ СОХРАНЯЮТСЯ В SUPABASE
"""

import asyncio
import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import asdict
from dotenv import load_dotenv
from supabase import create_client, Client

# Загружаем переменные окружения
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Импортируем специализированные парсеры для каждого канала
from signals.parsers.whales_crypto_parser import WhalesCryptoParser
from signals.parsers.parser_2trade import TwoTradeParser
from signals.parsers.crypto_hub_parser import CryptoHubParser
from signals.parsers.ghost_test_parser import GhostTestParser
from signals.parsers.signal_parser_base import ParsedSignal

# Импортируем CryptoAttack24 парсер
try:
    from signals.parsers.cryptoattack24_parser import CryptoAttack24Parser
    CRYPTOATTACK24_AVAILABLE = True
except ImportError:
    CRYPTOATTACK24_AVAILABLE = False

# Импортируем виртуальный трейдинг
try:
    from core.virtual_position_manager import virtual_position_manager
    VIRTUAL_TRADING_AVAILABLE = True
except ImportError:
    VIRTUAL_TRADING_AVAILABLE = False

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/signal_orchestrator_supabase.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SignalOrchestratorWithSupabase:
    """Оркестратор с полной интеграцией Supabase для всех парсеров"""
    
    def __init__(self):
        # Инициализация Supabase ПЕРВЫМ ДЕЛОМ
        self.supabase = self._init_supabase()
        
        # Инициализация Telegram Listener для РЕАЛЬНОГО прослушивания
        self.telegram_listener = None
        
        # Инициализируем специализированные парсеры для каждого канала трейдера
        self.parsers = {
            # Основные парсеры каналов
            'whales_guide_main': WhalesCryptoParser(),
            'whales_crypto_guide': WhalesCryptoParser(),  # Алиас
            '2trade_premium': TwoTradeParser(),
            'slivaeminfo': TwoTradeParser(),  # Алиас для 2Trade
            'crypto_hub_vip': CryptoHubParser(),
            'cryptohubvip': CryptoHubParser(),  # Алиас
            # Тестовый канал
            'ghostsignaltest': GhostTestParser(),
            'ghost_test': GhostTestParser(),  # Алиас
        }
        
        # Добавляем CryptoAttack24 парсер если доступен
        if CRYPTOATTACK24_AVAILABLE:
            # Создаем wrapper для совместимости с SignalParserBase
            class CryptoAttack24Wrapper:
                def __init__(self):
                    self.parser = CryptoAttack24Parser()
                    self.source_name = "cryptoattack24"
                
                def can_parse(self, text: str) -> bool:
                    return self.parser._is_noise(text) == False and len(text.strip()) > 20
                
                def parse_signal(self, text: str, trader_id: str) -> Optional[ParsedSignal]:
                    result = self.parser.parse_message(text)
                    if result and result.confidence >= 0.6:
                        # Конвертируем в ParsedSignal формат
                        return self._convert_to_parsed_signal(result, trader_id, text)
                    return None
                
                def _convert_to_parsed_signal(self, ca24_signal, trader_id: str, raw_text: str) -> ParsedSignal:
                    from signals.parsers.signal_parser_base import SignalDirection
                    
                    # Определяем направление на основе действия
                    direction = SignalDirection.BUY if ca24_signal.action in ["pump", "growth"] else SignalDirection.SELL
                    
                    signal = ParsedSignal(
                        signal_id=f"{trader_id}_{int(datetime.now().timestamp())}",
                        source="cryptoattack24",
                        trader_id=trader_id,
                        raw_text=raw_text,
                        timestamp=ca24_signal.timestamp or datetime.now(),
                        symbol=ca24_signal.symbol,
                        direction=direction
                    )
                    
                    # Дополнительные поля
                    signal.confidence = ca24_signal.confidence
                    signal.reason = ca24_signal.context
                    signal.is_valid = True
                    
                    return signal
            
            self.parsers['cryptoattack24'] = CryptoAttack24Wrapper()
            logger.info("✅ CryptoAttack24 parser integrated successfully")
        
        # Статистика
        self.stats = {
            'signals_processed': 0,
            'signals_saved': 0,
            'signals_failed': 0,
            'parsers_used': {name: 0 for name in self.parsers.keys()},
            'started_at': datetime.now(),
            'supabase_saves': 0,
            'supabase_errors': 0
        }
        
        # Инициализация виртуального трейдинга
        if VIRTUAL_TRADING_AVAILABLE:
            virtual_position_manager.set_supabase(self.supabase)
            logger.info("✅ Virtual trading integration enabled")
        else:
            logger.warning("⚠️ Virtual trading not available - install dependencies")
        
        logger.info(f"✅ SignalOrchestrator with Supabase initialized with {len(self.parsers)} parsers")
    
    async def start_telegram_listening(self):
        """Запуск прослушивания Telegram каналов"""
        try:
            from core.telegram_listener import TelegramListener
            
            api_id = os.getenv('TELEGRAM_API_ID')
            api_hash = os.getenv('TELEGRAM_API_HASH')
            phone = os.getenv('TELEGRAM_PHONE')
            
            if not api_id or not api_hash:
                logger.error("❌ TELEGRAM_API_ID and TELEGRAM_API_HASH required")
                return False
                
            self.telegram_listener = TelegramListener(api_id, api_hash, phone)
            
            # Добавляем каналы с правильными числовыми ID (НЕ username!)
            channels = [
                ("-1001288385100", "whales_guide_main", "@whalesguide"),
                ("-1001915101334", "2trade_premium", "@slivaeminfo"), 
                ("-1001263635145", "cryptoattack24", "@cryptoattack24"),
                ("-1002974041293", "ghostsignaltest", "@ghostsignaltest")  # Тестовый канал для v_trades
            ]
            
            for channel_id, trader_id, username in channels:
                from core.telegram_listener import ChannelConfig
                config = ChannelConfig(
                    channel_id=channel_id,  # Используем числовой ID!
                    channel_name=trader_id,
                    trader_id=trader_id,
                    is_active=True
                )
                self.telegram_listener.add_channel(config)
                logger.info(f"Added channel: {trader_id} (Username: {username}, ID: {channel_id})")
            
            # Устанавливаем обработчик
            self.telegram_listener.set_message_handler(self._handle_telegram_message)
            
            # Запускаем
            await self.telegram_listener.initialize()
            asyncio.create_task(self.telegram_listener.start_listening())
            
            # Запускаем мониторинг виртуальных позиций
            if VIRTUAL_TRADING_AVAILABLE:
                await virtual_position_manager.start_monitoring()
                logger.info("🔄 Virtual position monitoring started")
            
            logger.info("✅ Telegram listening started")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start Telegram: {e}")
            return False
    
    async def _handle_telegram_message(self, message_data):
        """Обработчик сообщений из Telegram"""
        try:
            text = message_data.get("text", "")
            trader_id = message_data.get("trader_id", "unknown")
            
            # Обрабатываем через наши парсеры
            result = await self.process_raw_signal(text, trader_id, trader_id)
            if result:
                logger.info(f"✅ Processed live signal: {result.symbol}")
                
        except Exception as e:
            logger.error(f"❌ Error handling Telegram message: {e}")
    
    def _init_supabase(self) -> Optional[Client]:
        """Инициализация Supabase клиента"""
        try:
            supabase_url = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
            
            if not supabase_url or not supabase_key:
                logger.warning("⚠️ Supabase credentials not found")
                return None
            
            client = create_client(supabase_url, supabase_key)
            logger.info("✅ Supabase client initialized")
            return client
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase: {e}")
            return None
    
    async def process_raw_signal(self, raw_text: str, trader_id: str, source_hint: str = None) -> Optional[ParsedSignal]:
        """Обработка сырого сигнала со всеми парсерами и сохранением в Supabase"""
        try:
            self.stats['signals_processed'] += 1
            
            # Убеждаемся что трейдер существует в trader_registry
            await self._ensure_trader_exists(trader_id, source_hint)
            
            # Сначала сохраняем сырой сигнал в Supabase
            await self._save_raw_signal_to_supabase(trader_id, raw_text)
            
            # Этап 1: Выбор лучшего парсера
            best_parser = None
            best_parser_name = None
            
            # ПРИОРИТЕТ: Сначала ищем специальный парсер для этого трейдера
            if trader_id in self.parsers:
                parser = self.parsers[trader_id]
                logger.info(f"🎯 Проверяем специализированный парсер для {trader_id}: {type(parser).__name__}")
                
                if parser.can_parse(raw_text):
                    best_parser = parser
                    best_parser_name = trader_id
                    logger.info(f"✅ Используем специализированный парсер: {trader_id}")
                else:
                    logger.info(f"⚠️ Специализированный парсер {trader_id} не может обработать этот текст")
            else:
                logger.warning(f"⚠️ Специализированный парсер для {trader_id} не найден!")
                logger.info(f"   Доступные парсеры: {list(self.parsers.keys())}")
            
            # Если специализированный не найден, пробуем подсказку источника
            if not best_parser and source_hint and source_hint in self.parsers:
                parser = self.parsers[source_hint]
                if parser.can_parse(raw_text):
                    best_parser = parser
                    best_parser_name = source_hint
            
            # Если ничего не сработало, используем приоритетный порядок
            if not best_parser:
                # Порядок приоритета парсеров
                priority_order = ['whales_crypto_guide', 'cryptoattack24', 
                                '2trade_premium', 'crypto_hub_vip']
                
                for parser_name in priority_order:
                    if parser_name in self.parsers:
                        parser = self.parsers[parser_name]
                        if parser.can_parse(raw_text):
                            best_parser = parser
                            best_parser_name = parser_name
                            break
                
                # Если приоритетные не сработали, пробуем остальные
                if not best_parser:
                    for parser_name, parser in self.parsers.items():
                        if parser_name not in priority_order and parser.can_parse(raw_text):
                            best_parser = parser
                            best_parser_name = parser_name
                            break
            
            if not best_parser:
                logger.warning(f"⚠️ No suitable parser found for signal from {trader_id}")
                self.stats['signals_failed'] += 1
                return None
            
            # Парсим сигнал
            signal = best_parser.parse_signal(raw_text, trader_id)
            
            if not signal:
                logger.warning(f"⚠️ Failed to parse signal with {best_parser_name}")
                self.stats['signals_failed'] += 1
                return None
            
            # Обновляем статистику парсера
            self.stats['parsers_used'][best_parser_name] += 1
            
            # Сохраняем ВСЕ сигналы в Supabase (включая невалидные)
            await self._save_parsed_signal_to_supabase(signal, best_parser_name, raw_text)
            
            # Для тестового канала ghostsignaltest также сохраняем в v_trades
            if trader_id in ['ghostsignaltest', 'ghost_test'] and isinstance(self.parsers.get(trader_id), GhostTestParser):
                await self._save_to_v_trades_table(signal, trader_id, raw_text)
            
            # Статистика зависит от валидности
            if signal.is_valid:
                self.stats['signals_saved'] += 1
                logger.info(f"✅ VALID signal parsed and saved: {signal.symbol} {signal.direction}")
            else:
                logger.warning(f"⚠️ INVALID signal parsed and saved: {signal.symbol} {signal.direction} | Errors: {signal.parse_errors}")
                
            return signal
            
        except Exception as e:
            logger.error(f"❌ Error processing signal: {e}")
            self.stats['signals_failed'] += 1
            return None
    
    async def _save_raw_signal_to_supabase(self, trader_id: str, raw_text: str):
        """Сохранение сырого сигнала в Supabase с дедупликацией"""
        try:
            if not self.supabase:
                logger.warning("⚠️ Supabase not available, skipping raw signal save")
                return

            # Проверяем дубликаты по трейдеру и тексту за последние 2 часа
            from datetime import timedelta
            two_hours_ago = (datetime.now() - timedelta(hours=2)).isoformat()

            # Исправлено: убираем select('id') так как колонки id нет в таблице
            existing = self.supabase.table('signals_raw').select('*').eq('trader_id', trader_id).eq('text', raw_text.strip()).gte('created_at', two_hours_ago).limit(1).execute()
            
            if existing.data:
                logger.info(f"🔄 Duplicate signal ignored from {trader_id} (text: {raw_text[:30]}...)")
                self.stats['duplicates_skipped'] = self.stats.get('duplicates_skipped', 0) + 1
                return
            
            # Подготавливаем данные для сохранения сырого сигнала
            raw_data = {
                'trader_id': trader_id,
                'text': raw_text,  # Исправлено: поле называется 'text' в Prisma схеме
                'posted_at': datetime.now().isoformat(),
                'processed': False
            }
            
            # Сохраняем в таблицу signals_raw
            result = self.supabase.table('signals_raw').insert(raw_data).execute()
            
            if result.data:
                logger.info(f"✅ Raw signal saved to Supabase from {trader_id}")
                self.stats['raw_signals_saved'] = self.stats.get('raw_signals_saved', 0) + 1
            else:
                logger.error(f"❌ Failed to save raw signal to Supabase")
                self.stats['supabase_errors'] += 1
                
        except Exception as e:
            logger.error(f"❌ Failed to save raw signal: {e}")
            self.stats['supabase_errors'] += 1
    
    async def _save_parsed_signal_to_supabase(self, signal: ParsedSignal, parser_name: str, raw_text: str):
        """Сохранение обработанного сигнала в Supabase"""
        try:
            if not self.supabase:
                logger.warning("⚠️ Supabase not available, skipping parsed signal save")
                return
            
            # Подготавливаем данные для сохранения в соответствии со схемой Prisma
            current_time = datetime.now().isoformat()
            
            signal_data = {
                'trader_id': signal.trader_id,
                'symbol': signal.symbol,
                'side': signal.direction.value if hasattr(signal, 'direction') else 'UNKNOWN',
                'entry_type': getattr(signal, 'entry_type', 'market'),
                'entry': float(signal.entry_price) if hasattr(signal, 'entry_price') and signal.entry_price else None,
                'range_low': float(min(signal.entry_zone)) if hasattr(signal, 'entry_zone') and signal.entry_zone else None,
                'range_high': float(max(signal.entry_zone)) if hasattr(signal, 'entry_zone') and signal.entry_zone else None,
                'tp1': float(signal.targets[0]) if hasattr(signal, 'targets') and signal.targets and len(signal.targets) > 0 else None,
                'tp2': float(signal.targets[1]) if hasattr(signal, 'targets') and signal.targets and len(signal.targets) > 1 else None,
                'tp3': float(signal.targets[2]) if hasattr(signal, 'targets') and signal.targets and len(signal.targets) > 2 else None,
                'tp4': float(signal.targets[3]) if hasattr(signal, 'targets') and signal.targets and len(signal.targets) > 3 else None,
                'sl': float(signal.stop_loss) if hasattr(signal, 'stop_loss') and signal.stop_loss else None,
                'leverage_hint': self._extract_leverage_number(getattr(signal, 'leverage', None)),
                'confidence': float(signal.confidence) if hasattr(signal, 'confidence') else 0.5,
                
                # Временные поля в соответствии со схемой Prisma
                'parsed_at': current_time,
                'posted_at': signal.timestamp.isoformat() if hasattr(signal, 'timestamp') else current_time,
                'created_at': current_time,  # Добавляем для совместимости с API
                
                # Метаданные
                'parse_version': 'v1.0',
                'is_valid': getattr(signal, 'is_valid', True),
                'validation_errors': getattr(signal, 'parse_errors', None),
                
                # Генерируем уникальный checksum для Prisma схемы (максимум 64 символа)
                'checksum': f"{signal.trader_id[:10]}_{signal.symbol[:10]}_{int(datetime.now().timestamp())}_{abs(hash(raw_text)) % 100000}"
            }
            
            # Сохраняем в таблицу signals_parsed
            result = self.supabase.table('signals_parsed').insert(signal_data).execute()
            
            if result.data:
                logger.info(f"✅ Parsed signal saved to Supabase: {signal.symbol}")
                self.stats['supabase_saves'] += 1
            else:
                logger.error(f"❌ Failed to save parsed signal to Supabase")
                self.stats['supabase_errors'] += 1
                
        except Exception as e:
            logger.error(f"❌ Failed to save parsed signal: {e}")
            self.stats['supabase_errors'] += 1
    
    async def _save_to_v_trades_table(self, signal: ParsedSignal, trader_id: str, raw_text: str):
        """Специальная функция для сохранения тестовых сигналов в таблицу v_trades"""
        try:
            if not self.supabase:
                logger.warning("⚠️ Supabase not available, skipping v_trades save")
                return
            
            import uuid
            from datetime import timezone
            
            # Генерируем уникальный ID для записи
            trade_id = str(uuid.uuid4())
            current_timestamp = datetime.now(timezone.utc)
            posted_timestamp = int(current_timestamp.timestamp())  # unix секунды (для совместимости с фронтендом)
            
            # Для ghostsignaltest извлекаем точные значения из исходного текста
            is_ghost_test = trader_id in ['ghostsignaltest', 'ghost_test']
            
            # Определяем цены входа
            entry_min = None
            entry_max = None
            
            if is_ghost_test and hasattr(self.parsers.get(trader_id), 'extract_entry_prices_exact'):
                # Используем точные строковые значения для ghostsignaltest
                parser = self.parsers.get(trader_id)
                exact_entries = parser.extract_entry_prices_exact(raw_text)
                if exact_entries:
                    # Преобразуем в float для БД, но используем оригинальные строки с запятыми
                    entry_values = [float(e.replace(',', '')) for e in exact_entries]
                    entry_min = min(entry_values)
                    entry_max = max(entry_values)
            else:
                # Стандартная логика для других парсеров
                if hasattr(signal, 'entry_zone') and signal.entry_zone:
                    entry_min = float(min(signal.entry_zone))
                    entry_max = float(max(signal.entry_zone))
                elif hasattr(signal, 'entry_single') and signal.entry_single:
                    entry_min = float(signal.entry_single)
                    entry_max = float(signal.entry_single)
            
            # Определяем цели с сохранением точности
            tp1, tp2, tp3 = None, None, None
            targets_json = '[]'
            
            if is_ghost_test and hasattr(self.parsers.get(trader_id), 'extract_targets_exact'):
                # Используем точные строковые значения для ghostsignaltest
                parser = self.parsers.get(trader_id)
                exact_targets = parser.extract_targets_exact(raw_text)
                if exact_targets:
                    # Преобразуем в float для полей tp1, tp2, tp3
                    target_values = [float(t.replace(',', '')) for t in exact_targets]
                    tp1 = target_values[0] if len(target_values) > 0 else None
                    tp2 = target_values[1] if len(target_values) > 1 else None
                    tp3 = target_values[2] if len(target_values) > 2 else None
                    # Сохраняем оригинальные строковые значения в JSON
                    targets_json = str(exact_targets)
            else:
                # Стандартная логика для других парсеров
                tp1 = float(signal.targets[0]) if hasattr(signal, 'targets') and signal.targets and len(signal.targets) > 0 else None
                tp2 = float(signal.targets[1]) if hasattr(signal, 'targets') and signal.targets and len(signal.targets) > 1 else None
                tp3 = float(signal.targets[2]) if hasattr(signal, 'targets') and signal.targets and len(signal.targets) > 2 else None
                targets_json = str(signal.targets) if hasattr(signal, 'targets') and signal.targets else '[]'
            
            # Определяем стоп-лосс с сохранением точности
            sl = None
            
            if is_ghost_test and hasattr(self.parsers.get(trader_id), 'extract_stop_loss_exact'):
                # Используем точное строковое значение для ghostsignaltest
                parser = self.parsers.get(trader_id)
                exact_sl = parser.extract_stop_loss_exact(raw_text)
                if exact_sl:
                    sl = float(exact_sl.replace(',', ''))
            else:
                # Стандартная логика для других парсеров
                sl = float(signal.stop_loss) if hasattr(signal, 'stop_loss') and signal.stop_loss else None
            
            # Подготавливаем данные для v_trades таблицы
            v_trades_data = {
                # Основные поля
                'id': trade_id,
                'signal_id': signal.signal_id if hasattr(signal, 'signal_id') else None,
                'source': f"tg_{trader_id}",
                'source_type': 'telegram',
                'source_name': 'Ghost Signal Test',
                'source_ref': f"tg://{trader_id}",
                'original_text': raw_text,
                'signal_reason': self._get_validation_info(signal),
                'posted_ts': posted_timestamp,
                
                # Торговые данные
                'symbol': signal.symbol,
                'side': 'LONG' if signal.direction.value in ['LONG', 'BUY'] else 'SHORT',
                'entry_type': 'zone' if (entry_min != entry_max and entry_max is not None) else 'exact',
                'entry_min': entry_min,
                'entry_max': entry_max,
                
                # Цели с сохранением точности
                'tp1': tp1,
                'tp2': tp2,
                'tp3': tp3,
                'targets_json': targets_json,
                
                # Стоп-лосс с сохранением точности
                'sl': sl,
                'sl_type': 'hard',
                
                # Параметры торговли
                'source_leverage': getattr(signal, 'leverage', '15x'),
                'strategy_id': 'S_A_TP1_BE_TP2',
                'strategy_version': '1',
                'fee_rate': 0.0005,
                'leverage': self._extract_leverage_number(getattr(signal, 'leverage', '15x')),
                'margin_usd': 100.0,
                'entry_timeout_sec': 172800,  # 48 часов
                
                # Статус
                'was_fillable': getattr(signal, 'is_valid', True),  # Только валидные сигналы fillable
                'status': 'cancelled' if not getattr(signal, 'is_valid', True) else 'sim_open',  # Невалидные помечаем как cancelled
                
                # Временные метки
                'created_at': current_timestamp.isoformat(),
                'updated_at': current_timestamp.isoformat()
            }
            
            # Сохраняем в таблицу v_trades
            result = self.supabase.table('v_trades').insert(v_trades_data).execute()
            
            if result.data:
                is_valid = getattr(signal, 'is_valid', True)
                status = 'cancelled' if not is_valid else 'sim_open'
                validation_info = ""
                
                if not is_valid:
                    validation_errors = getattr(signal, 'validation_errors', [])
                    validation_info = f" | INVALID: {'; '.join(validation_errors[:2])}"  # Первые 2 ошибки
                    
                logger.info(f"✅ Ghost test signal saved to v_trades: {signal.symbol} {signal.direction.value} [{status}]{validation_info}")
                self.stats['v_trades_saves'] = self.stats.get('v_trades_saves', 0) + 1
                
                # Создаем виртуальную позицию для валидных сигналов
                if is_valid and VIRTUAL_TRADING_AVAILABLE:
                    try:
                        position_id = await virtual_position_manager.create_position_from_signal(
                            signal=signal,
                            v_trade_id=trade_id,
                            position_size_usd=100.0,  # Размер позиции по умолчанию
                            leverage=10  # Плечо по умолчанию
                        )
                        
                        if position_id:
                            logger.info(f"🚀 Virtual position created: {signal.symbol} (ID: {position_id})")
                        else:
                            logger.warning(f"⚠️ Failed to create virtual position for {signal.symbol}")
                            
                    except Exception as e:
                        logger.error(f"❌ Error creating virtual position: {e}")
            else:
                logger.error(f"❌ Failed to save to v_trades table")
                self.stats['supabase_errors'] += 1
                
        except Exception as e:
            logger.error(f"❌ Failed to save to v_trades table: {e}")
            self.stats['supabase_errors'] += 1
    
    def _get_validation_info(self, signal) -> str:
        """Получает информацию о валидации сигнала для записи в базу"""
        # Проверяем наличие информации о валидности
        if not hasattr(signal, 'is_valid') or signal.is_valid:
            return 'Valid signal'  # Валидный сигнал
        
        # Для невалидных сигналов записываем ошибки
        validation_errors = getattr(signal, 'validation_errors', [])
        if validation_errors:
            return f"INVALID_SIGNAL: {'; '.join(validation_errors)}"
        else:
            return 'INVALID_SIGNAL: Unknown validation error'
    
    async def get_stats(self) -> Dict[str, Any]:
        """Получение статистики работы оркестратора"""
        uptime = datetime.now() - self.stats['started_at']
        
        return {
            **self.stats,
            'uptime_seconds': int(uptime.total_seconds()),
            'uptime_human': str(uptime),
            'supabase_connected': self.supabase is not None,
            'parsers_available': list(self.parsers.keys()),
            'success_rate': (self.stats['signals_saved'] / max(self.stats['signals_processed'], 1)) * 100
        }
    
    async def _ensure_trader_exists(self, trader_id: str, source_hint: str = None):
        """Убеждаемся что трейдер существует в trader_registry"""
        try:
            if not self.supabase:
                return
            
            # Проверяем существует ли трейдер
            result = self.supabase.table('trader_registry').select('trader_id').eq('trader_id', trader_id).execute()
            
            if not result.data:
                # Создаем нового трейдера
                trader_info = self._get_trader_info(trader_id, source_hint)
                
                insert_result = self.supabase.table('trader_registry').insert(trader_info).execute()
                
                if insert_result.data:
                    logger.info(f"✅ Создан новый трейдер: {trader_id}")
                else:
                    logger.error(f"❌ Ошибка создания трейдера: {trader_id}")
                    
        except Exception as e:
            logger.error(f"❌ Ошибка проверки трейдера: {e}")
    
    def _get_trader_info(self, trader_id: str, source_hint: str = None) -> Dict[str, Any]:
        """Получаем информацию о трейдере на основе ID"""
        trader_configs = {
            'whales_crypto_guide': {
                'name': 'Whales Crypto Guide',
                'source_handle': '@whalesguide',
                'source_id': '-1001288385100',
                'notes': 'English premium crypto signals with high accuracy',
                'parsing_profile': 'whales_crypto_parser'
            },
            'cryptoattack24': {
                'name': 'КриптоАтака 24',
                'source_handle': '@cryptoattack24',
                'source_id': '-1001263635145',
                'notes': 'Russian crypto news and pump signals with market analysis',
                'parsing_profile': 'cryptoattack24_parser'
            },
            '2trade_premium': {
                'name': '2Trade Premium',
                'source_handle': '@slivaeminfo',
                'source_id': '-1001234567890',
                'notes': 'Russian structured trading signals with clear entry/exit levels',
                'parsing_profile': 'two_trade_parser'
            },
            'crypto_hub_vip': {
                'name': 'Crypto Hub VIP',
                'source_handle': '@cryptohubvip',
                'source_id': '-1001345678901',
                'notes': 'VIP crypto signals with emoji formatting and quick calls',
                'parsing_profile': 'crypto_hub_parser'
            },
            'ghostsignaltest': {
                'name': 'Ghost Signal Test',
                'source_handle': '@ghostsignaltest',
                'source_id': '-1002974041293',
                'notes': 'Test channel for signal parsing to v_trades table',
                'parsing_profile': 'ghost_test_parser'
            }
        }
        
        config = trader_configs.get(trader_id, {
            'name': trader_id.replace('_', ' ').title(),
            'source_handle': f'@{trader_id}',
            'source_id': None,
            'notes': 'Auto-created trader',
            'parsing_profile': source_hint or 'standard_v1'
        })
        
        return {
            'trader_id': trader_id,
            'name': config['name'],
            'source_type': 'telegram',
            'source_id': config['source_id'],
            'source_handle': config['source_handle'],
            'mode': 'observe',
            'risk_profile': {'size_usd': 100, 'leverage': 10, 'risk_percent': 2},
            'parsing_profile': config['parsing_profile'],
            'is_active': True,
            'notes': config['notes']
        }
    
    def _extract_leverage_number(self, leverage_str: str) -> Optional[int]:
        """Извлекает число из строки плеча"""
        if not leverage_str:
            return None
        
        try:
            # Ищем число в строке типа "10x", "5x - 10x", "10"
            import re
            numbers = re.findall(r'(\d+)', str(leverage_str))
            if numbers:
                # Берем максимальное значение
                return max(int(num) for num in numbers)
        except:
            pass
        
        return None

    async def test_supabase_connection(self) -> bool:
        """Тест подключения к Supabase"""
        try:
            if not self.supabase:
                return False
            
            # Простой запрос для проверки подключения
            result = self.supabase.table('signals_raw').select('*').limit(1).execute()
            return True
            
        except Exception as e:
            logger.error(f"❌ Supabase connection test failed: {e}")
            return False

# Создаем глобальный экземпляр для использования в других модулях
orchestrator_with_supabase = SignalOrchestratorWithSupabase()

async def main():
    """Тестирование оркестратора"""
    logger.info("🚀 Testing SignalOrchestrator with Supabase...")
    
    # Тест подключения к Supabase
    if await orchestrator_with_supabase.test_supabase_connection():
        logger.info("✅ Supabase connection OK")
    else:
        logger.error("❌ Supabase connection failed")
    
    # Тестовый сигнал
    test_signal = """
    🚀🔥 #ALPINE запампили на +57% со вчерашнего вечера
    Сейчас коррекция и можно заходить в лонг
    Цели: 2.45, 2.60, 2.85
    """
    
    result = await orchestrator_with_supabase.process_raw_signal(test_signal, "cryptoattack24", "cryptoattack24")
    
    if result:
        logger.info(f"✅ Test signal processed: {result.symbol}")
    else:
        logger.error("❌ Test signal failed")
    
    # Статистика
    stats = await orchestrator_with_supabase.get_stats()
    logger.info(f"📊 Stats: {json.dumps(stats, indent=2, default=str)}")

if __name__ == "__main__":
    asyncio.run(main())
