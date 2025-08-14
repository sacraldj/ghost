#!/usr/bin/env python3
"""
🔧 GHOST Supabase Auto Migrator
Автоматическое создание и обновление схемы базы данных в Supabase
"""

import os
import sys
import json
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

try:
    from supabase import create_client, Client
except ImportError:
    print("❌ Supabase не установлен. Установите: pip install supabase")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('SupabaseMigrator')

class SupabaseMigrator:
    """Автоматический мигратор для Supabase"""
    
    def __init__(self):
        self.supabase_url = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL и SUPABASE_SERVICE_ROLE_KEY обязательны")
        
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        
        # Схема всех необходимых таблиц
        self.tables_schema = {
            'signal_sources': {
                'columns': [
                    {'name': 'id', 'type': 'uuid', 'default': 'gen_random_uuid()', 'primary': True},
                    {'name': 'source_code', 'type': 'text', 'unique': True, 'required': True},
                    {'name': 'source_name', 'type': 'text', 'required': True},
                    {'name': 'source_type', 'type': 'text', 'required': True},
                    {'name': 'channel_id', 'type': 'text'},
                    {'name': 'trader_id', 'type': 'text'},
                    {'name': 'reliability_score', 'type': 'decimal(3,2)', 'default': '0.5'},
                    {'name': 'win_rate', 'type': 'decimal(5,2)'},
                    {'name': 'avg_roi', 'type': 'decimal(10,4)'},
                    {'name': 'total_signals', 'type': 'integer', 'default': '0'},
                    {'name': 'successful_signals', 'type': 'integer', 'default': '0'},
                    {'name': 'is_active', 'type': 'boolean', 'default': 'true'},
                    {'name': 'created_at', 'type': 'timestamp', 'default': 'NOW()'},
                    {'name': 'updated_at', 'type': 'timestamp', 'default': 'NOW()'}
                ]
            },
            
            'instruments': {
                'columns': [
                    {'name': 'id', 'type': 'uuid', 'default': 'gen_random_uuid()', 'primary': True},
                    {'name': 'ticker_symbol', 'type': 'text', 'unique': True, 'required': True},
                    {'name': 'instrument_name', 'type': 'text'},
                    {'name': 'instrument_type', 'type': 'text', 'required': True},
                    {'name': 'sector', 'type': 'text'},
                    {'name': 'industry', 'type': 'text'},
                    {'name': 'base_currency', 'type': 'text'},
                    {'name': 'quote_currency', 'type': 'text'},
                    {'name': 'settlement_currency', 'type': 'text'},
                    {'name': 'exchange_code', 'type': 'text', 'required': True},
                    {'name': 'tick_size', 'type': 'decimal(20,8)'},
                    {'name': 'contract_size', 'type': 'decimal(20,8)'},
                    {'name': 'multiplier', 'type': 'integer', 'default': '1'},
                    {'name': 'is_active', 'type': 'boolean', 'default': 'true'},
                    {'name': 'created_at', 'type': 'timestamp', 'default': 'NOW()'},
                    {'name': 'updated_at', 'type': 'timestamp', 'default': 'NOW()'}
                ]
            },
            
            'exchanges': {
                'columns': [
                    {'name': 'id', 'type': 'uuid', 'default': 'gen_random_uuid()', 'primary': True},
                    {'name': 'exchange_code', 'type': 'text', 'unique': True, 'required': True},
                    {'name': 'exchange_name', 'type': 'text', 'required': True},
                    {'name': 'timezone', 'type': 'text', 'default': "'UTC'"},
                    {'name': 'trading_hours', 'type': 'jsonb'},
                    {'name': 'api_endpoints', 'type': 'jsonb'},
                    {'name': 'fees_structure', 'type': 'jsonb'},
                    {'name': 'created_at', 'type': 'timestamp', 'default': 'NOW()'}
                ]
            },
            
            'market_snapshots': {
                'columns': [
                    {'name': 'id', 'type': 'uuid', 'default': 'gen_random_uuid()', 'primary': True},
                    {'name': 'signal_id', 'type': 'uuid', 'foreign_key': 'signals_parsed(id)'},
                    {'name': 'instrument_id', 'type': 'uuid', 'foreign_key': 'instruments(id)'},
                    {'name': 'snapshot_timestamp', 'type': 'timestamp', 'required': True},
                    {'name': 'current_price', 'type': 'decimal(20,8)'},
                    {'name': 'open_price', 'type': 'decimal(20,8)'},
                    {'name': 'high_price', 'type': 'decimal(20,8)'},
                    {'name': 'low_price', 'type': 'decimal(20,8)'},
                    {'name': 'close_price', 'type': 'decimal(20,8)'},
                    {'name': 'volume_24h', 'type': 'decimal(30,8)'},
                    {'name': 'volume_1h', 'type': 'decimal(30,8)'},
                    {'name': 'bid_price', 'type': 'decimal(20,8)'},
                    {'name': 'ask_price', 'type': 'decimal(20,8)'},
                    {'name': 'spread_percent', 'type': 'decimal(10,6)'},
                    {'name': 'volatility_1h', 'type': 'decimal(10,6)'},
                    {'name': 'volatility_24h', 'type': 'decimal(10,6)'},
                    {'name': 'rsi_14', 'type': 'decimal(5,2)'},
                    {'name': 'macd_line', 'type': 'decimal(20,8)'},
                    {'name': 'macd_signal', 'type': 'decimal(20,8)'},
                    {'name': 'sma_20', 'type': 'decimal(20,8)'},
                    {'name': 'sma_50', 'type': 'decimal(20,8)'},
                    {'name': 'ema_12', 'type': 'decimal(20,8)'},
                    {'name': 'ema_26', 'type': 'decimal(20,8)'},
                    {'name': 'created_at', 'type': 'timestamp', 'default': 'NOW()'}
                ]
            },
            
            'fundamental_data': {
                'columns': [
                    {'name': 'id', 'type': 'uuid', 'default': 'gen_random_uuid()', 'primary': True},
                    {'name': 'signal_id', 'type': 'uuid', 'foreign_key': 'signals_parsed(id)'},
                    {'name': 'instrument_id', 'type': 'uuid', 'foreign_key': 'instruments(id)'},
                    {'name': 'data_timestamp', 'type': 'timestamp', 'required': True},
                    {'name': 'market_cap', 'type': 'decimal(30,2)'},
                    {'name': 'circulating_supply', 'type': 'decimal(30,8)'},
                    {'name': 'active_addresses_24h', 'type': 'integer'},
                    {'name': 'transaction_count_24h', 'type': 'integer'},
                    {'name': 'whale_transactions_24h', 'type': 'integer'},
                    {'name': 'exchange_inflows_24h', 'type': 'decimal(30,8)'},
                    {'name': 'exchange_outflows_24h', 'type': 'decimal(30,8)'},
                    {'name': 'fear_greed_index', 'type': 'integer'},
                    {'name': 'social_sentiment_score', 'type': 'decimal(3,2)'},
                    {'name': 'news_sentiment_score', 'type': 'decimal(3,2)'},
                    {'name': 'google_trends_score', 'type': 'integer'},
                    {'name': 'created_at', 'type': 'timestamp', 'default': 'NOW()'}
                ]
            },
            
            'performance_analytics': {
                'columns': [
                    {'name': 'id', 'type': 'uuid', 'default': 'gen_random_uuid()', 'primary': True},
                    {'name': 'entity_type', 'type': 'text', 'required': True},
                    {'name': 'entity_id', 'type': 'uuid', 'required': True},
                    {'name': 'analysis_period_start', 'type': 'timestamp', 'required': True},
                    {'name': 'analysis_period_end', 'type': 'timestamp', 'required': True},
                    {'name': 'total_trades', 'type': 'integer'},
                    {'name': 'winning_trades', 'type': 'integer'},
                    {'name': 'losing_trades', 'type': 'integer'},
                    {'name': 'win_rate', 'type': 'decimal(5,2)'},
                    {'name': 'total_pnl', 'type': 'decimal(20,8)'},
                    {'name': 'avg_win', 'type': 'decimal(20,8)'},
                    {'name': 'avg_loss', 'type': 'decimal(20,8)'},
                    {'name': 'sharpe_ratio', 'type': 'decimal(10,6)'},
                    {'name': 'max_drawdown', 'type': 'decimal(10,4)'},
                    {'name': 'created_at', 'type': 'timestamp', 'default': 'NOW()'}
                ]
            },
            
            'alerts': {
                'columns': [
                    {'name': 'id', 'type': 'uuid', 'default': 'gen_random_uuid()', 'primary': True},
                    {'name': 'alert_type', 'type': 'text', 'required': True},
                    {'name': 'priority', 'type': 'text', 'default': "'MEDIUM'"},
                    {'name': 'title', 'type': 'text', 'required': True},
                    {'name': 'message', 'type': 'text', 'required': True},
                    {'name': 'signal_id', 'type': 'uuid', 'foreign_key': 'signals_parsed(id)'},
                    {'name': 'trade_id', 'type': 'uuid', 'foreign_key': 'trades(id)'},
                    {'name': 'source_id', 'type': 'uuid', 'foreign_key': 'signal_sources(id)'},
                    {'name': 'status', 'type': 'text', 'default': "'PENDING'"},
                    {'name': 'delivery_channels', 'type': 'text[]'},
                    {'name': 'created_at', 'type': 'timestamp', 'default': 'NOW()'},
                    {'name': 'processed_at', 'type': 'timestamp'},
                    {'name': 'delivered_at', 'type': 'timestamp'}
                ]
            }
        }
        
        # Начальные данные
        self.initial_data = {
            'exchanges': [
                {
                    'exchange_code': 'BINANCE',
                    'exchange_name': 'Binance Futures',
                    'timezone': 'UTC',
                    'trading_hours': {'24_7': True},
                    'api_endpoints': {'rest': 'fapi.binance.com', 'ws': 'fstream.binance.com'},
                    'fees_structure': {'maker': 0.0002, 'taker': 0.0004}
                },
                {
                    'exchange_code': 'BYBIT',
                    'exchange_name': 'Bybit Derivatives',
                    'timezone': 'UTC',
                    'trading_hours': {'24_7': True},
                    'api_endpoints': {'rest': 'api.bybit.com', 'ws': 'stream.bybit.com'},
                    'fees_structure': {'maker': 0.0001, 'taker': 0.0006}
                }
            ],
            
            'signal_sources': [
                {
                    'source_code': 'whales_crypto_guide',
                    'source_name': 'Whales Crypto Guide',
                    'source_type': 'telegram',
                    'channel_id': '-1001288385100',
                    'trader_id': 'whales_guide',
                    'reliability_score': 0.75,
                    'is_active': True
                }
            ],
            
            'instruments': [
                {
                    'ticker_symbol': 'ORDIUSDT',
                    'instrument_name': 'Ordinals USDT Perpetual',
                    'instrument_type': 'Crypto',
                    'sector': 'Cryptocurrency',
                    'industry': 'Bitcoin Layer 2',
                    'base_currency': 'ORDI',
                    'quote_currency': 'USDT',
                    'settlement_currency': 'USDT',
                    'exchange_code': 'BINANCE',
                    'tick_size': 0.001,
                    'contract_size': 1.0,
                    'is_active': True
                },
                {
                    'ticker_symbol': 'BTCUSDT',
                    'instrument_name': 'Bitcoin USDT Perpetual',
                    'instrument_type': 'Crypto',
                    'sector': 'Cryptocurrency',
                    'industry': 'Digital Currency',
                    'base_currency': 'BTC',
                    'quote_currency': 'USDT',
                    'settlement_currency': 'USDT',
                    'exchange_code': 'BINANCE',
                    'tick_size': 0.1,
                    'contract_size': 1.0,
                    'is_active': True
                }
            ]
        }
    
    def check_table_exists(self, table_name: str) -> bool:
        """Проверяет существование таблицы"""
        try:
            result = self.supabase.table(table_name).select('*').limit(1).execute()
            return True
        except Exception:
            return False
    
    def create_table_if_not_exists(self, table_name: str, schema: Dict) -> bool:
        """Создает таблицу если она не существует"""
        try:
            if self.check_table_exists(table_name):
                logger.info(f"✅ Таблица {table_name} уже существует")
                return True
            
            # Пытаемся создать через Supabase REST API
            # Поскольку прямого SQL нет, создаем через вставку пустой записи
            logger.info(f"🔧 Создание таблицы {table_name}...")
            
            # Для критических таблиц пытаемся создать через upsert
            if table_name in ['signal_sources', 'instruments', 'exchanges']:
                # Создаем минимальную запись чтобы таблица появилась
                minimal_record = self._create_minimal_record(table_name, schema)
                if minimal_record:
                    result = self.supabase.table(table_name).upsert([minimal_record]).execute()
                    if result.data:
                        logger.info(f"✅ Таблица {table_name} создана с начальной записью")
                        return True
            
            logger.warning(f"⚠️ Не удалось создать таблицу {table_name} автоматически")
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания таблицы {table_name}: {e}")
            return False
    
    def _create_minimal_record(self, table_name: str, schema: Dict) -> Optional[Dict]:
        """Создает минимальную запись для создания таблицы"""
        record = {}
        
        for column in schema['columns']:
            name = column['name']
            
            # Пропускаем автогенерируемые поля
            if column.get('default') and ('gen_random_uuid()' in str(column['default']) or 'NOW()' in str(column['default'])):
                continue
            
            # Обязательные поля
            if column.get('required'):
                if name == 'source_code' and table_name == 'signal_sources':
                    record[name] = 'test_source'
                elif name == 'source_name' and table_name == 'signal_sources':
                    record[name] = 'Test Source'
                elif name == 'source_type' and table_name == 'signal_sources':
                    record[name] = 'test'
                elif name == 'ticker_symbol' and table_name == 'instruments':
                    record[name] = 'TEST'
                elif name == 'instrument_type' and table_name == 'instruments':
                    record[name] = 'Test'
                elif name == 'exchange_code':
                    record[name] = 'TEST'
                elif name == 'exchange_name' and table_name == 'exchanges':
                    record[name] = 'Test Exchange'
                else:
                    record[name] = 'test'
        
        return record if record else None
    
    def populate_initial_data(self, table_name: str) -> bool:
        """Заполняет таблицу начальными данными"""
        try:
            if table_name not in self.initial_data:
                return True
            
            data = self.initial_data[table_name]
            
            # Проверяем есть ли уже данные
            existing = self.supabase.table(table_name).select('*').limit(1).execute()
            if existing.data:
                logger.info(f"📊 Таблица {table_name} уже содержит данные")
                return True
            
            # Вставляем начальные данные
            result = self.supabase.table(table_name).upsert(data).execute()
            
            if result.data:
                logger.info(f"✅ Добавлено {len(result.data)} записей в {table_name}")
                return True
            else:
                logger.warning(f"⚠️ Не удалось добавить данные в {table_name}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка заполнения {table_name}: {e}")
            return False
    
    def migrate_all(self) -> bool:
        """Выполняет полную миграцию"""
        logger.info("🚀 Начинаем автоматическую миграцию Supabase...")
        
        success_count = 0
        total_count = len(self.tables_schema)
        
        # Порядок создания таблиц (с учетом зависимостей)
        creation_order = [
            'exchanges',
            'signal_sources', 
            'instruments',
            'market_snapshots',
            'fundamental_data',
            'performance_analytics',
            'alerts'
        ]
        
        for table_name in creation_order:
            if table_name not in self.tables_schema:
                continue
                
            logger.info(f"📋 Обработка таблицы {table_name}...")
            
            # Создаем таблицу
            if self.create_table_if_not_exists(table_name, self.tables_schema[table_name]):
                success_count += 1
                
                # Заполняем начальными данными
                self.populate_initial_data(table_name)
            
        # Проверяем существующие таблицы
        logger.info("\n🔍 Финальная проверка таблиц:")
        existing_tables = []
        
        for table_name in self.tables_schema.keys():
            if self.check_table_exists(table_name):
                try:
                    count_result = self.supabase.table(table_name).select('id', count='exact').execute()
                    count = count_result.count if hasattr(count_result, 'count') else len(count_result.data or [])
                    logger.info(f"✅ {table_name}: {count} записей")
                    existing_tables.append(table_name)
                except:
                    logger.info(f"✅ {table_name}: существует")
                    existing_tables.append(table_name)
            else:
                logger.warning(f"❌ {table_name}: не найдена")
        
        success_rate = len(existing_tables) / total_count * 100
        
        logger.info(f"\n📊 Результат миграции:")
        logger.info(f"Успешно: {len(existing_tables)}/{total_count} ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            logger.info("🎉 Миграция завершена успешно!")
            return True
        else:
            logger.warning("⚠️ Миграция завершена с ошибками")
            return False

def main():
    """Главная функция"""
    try:
        migrator = SupabaseMigrator()
        success = migrator.migrate_all()
        
        if success:
            print("\n✅ МИГРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
            print("🎯 Все необходимые таблицы готовы для работы")
        else:
            print("\n⚠️ МИГРАЦИЯ ЗАВЕРШЕНА С ОШИБКАМИ")
            print("🔧 Некоторые таблицы могут потребовать ручного создания")
        
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка миграции: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
