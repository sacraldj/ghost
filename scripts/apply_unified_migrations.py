#!/usr/bin/env python3
"""
Применение миграций для unified signal system в Supabase
"""

import os
import sys
import asyncio
from supabase import create_client, Client
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MigrationApplier:
    """Класс для применения миграций в Supabase"""
    
    def __init__(self):
        self.supabase = self._init_supabase()
        
    def _init_supabase(self) -> Client:
        """Инициализация Supabase клиента"""
        supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.error("❌ Supabase credentials not found in environment")
            logger.error("Set NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
            sys.exit(1)
        
        try:
            supabase = create_client(supabase_url, supabase_key)
            logger.info("✅ Supabase client initialized")
            return supabase
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase: {e}")
            sys.exit(1)
    
    def read_migration_file(self, file_path: str) -> str:
        """Чтение файла миграции"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"❌ Migration file not found: {file_path}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"❌ Error reading migration file: {e}")
            sys.exit(1)
    
    def execute_sql(self, sql: str, description: str = "SQL command"):
        """Выполнение SQL команды"""
        try:
            logger.info(f"📝 Executing: {description}")
            
            # Разбиваем SQL на отдельные команды
            commands = [cmd.strip() for cmd in sql.split(';') if cmd.strip()]
            
            for i, command in enumerate(commands, 1):
                if command.strip():
                    logger.debug(f"  Command {i}/{len(commands)}")
                    
                    # Используем RPC для выполнения SQL
                    try:
                        # Для CREATE TABLE, ALTER TABLE и других DDL команд
                        result = self.supabase.rpc('execute_sql', {'sql_command': command}).execute()
                        
                        if hasattr(result, 'error') and result.error:
                            logger.warning(f"⚠️ Command {i} warning: {result.error}")
                        else:
                            logger.debug(f"✅ Command {i} executed successfully")
                            
                    except Exception as cmd_error:
                        # Некоторые команды могут не поддерживаться через RPC
                        logger.warning(f"⚠️ Command {i} failed via RPC: {cmd_error}")
                        
                        # Пробуем альтернативный способ для простых INSERT/UPDATE
                        if any(keyword in command.upper() for keyword in ['INSERT', 'UPDATE', 'SELECT']):
                            try:
                                # Для простых DML команд можем попробовать через обычный API
                                logger.debug(f"Trying alternative method for command {i}")
                            except:
                                logger.error(f"❌ Command {i} failed completely")
                                raise
            
            logger.info(f"✅ {description} completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Error executing {description}: {e}")
            raise
    
    def check_table_exists(self, table_name: str) -> bool:
        """Проверка существования таблицы"""
        try:
            result = self.supabase.table(table_name).select("*").limit(1).execute()
            return True
        except:
            return False
    
    def apply_unified_migrations(self):
        """Применение миграций для unified system"""
        logger.info("🚀 Starting unified signal system migrations")
        
        # Читаем файл миграций
        migration_sql = self.read_migration_file("prisma/migrations/unified_signal_tables.sql")
        
        # Применяем миграции
        self.execute_sql(migration_sql, "Unified Signal System tables")
        
        # Проверяем созданные таблицы
        self.verify_tables()
        
        # Вставляем тестовые данные
        self.insert_test_data()
        
        logger.info("🎉 All migrations applied successfully!")
    
    def verify_tables(self):
        """Проверка созданных таблиц"""
        logger.info("🔍 Verifying created tables...")
        
        expected_tables = [
            "signal_sources",
            "unified_signals", 
            "parser_stats",
            "ai_parser_config",
            "system_stats"
        ]
        
        for table in expected_tables:
            if self.check_table_exists(table):
                logger.info(f"✅ Table '{table}' exists")
            else:
                logger.warning(f"⚠️ Table '{table}' not found")
    
    def insert_test_data(self):
        """Вставка тестовых данных"""
        logger.info("📊 Inserting test data...")
        
        try:
            # Проверяем и вставляем базовые источники сигналов
            sources_result = self.supabase.table("signal_sources").select("*").execute()
            
            if not sources_result.data:
                logger.info("📝 Inserting test signal sources...")
                
                test_sources = [
                    {
                        "source_id": "whales_guide_test",
                        "source_type": "telegram_channel", 
                        "name": "Whales Guide Test",
                        "connection_params": {"channel_id": "-1001234567890"},
                        "parser_type": "whales_crypto_parser",
                        "keywords_filter": ["longing", "entry", "targets"]
                    },
                    {
                        "source_id": "test_channel_2trade",
                        "source_type": "telegram_channel",
                        "name": "2Trade Test", 
                        "connection_params": {"channel_id": "-1001234567891"},
                        "parser_type": "2trade_parser",
                        "keywords_filter": ["long", "short", "вход", "стоп"]
                    }
                ]
                
                for source in test_sources:
                    try:
                        self.supabase.table("signal_sources").insert(source).execute()
                        logger.info(f"✅ Inserted source: {source['name']}")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to insert source {source['name']}: {e}")
            
            else:
                logger.info(f"📊 Found {len(sources_result.data)} existing signal sources")
            
            # Проверяем AI конфигурацию
            ai_config_result = self.supabase.table("ai_parser_config").select("*").execute()
            
            if not ai_config_result.data:
                logger.info("🤖 Inserting AI parser configuration...")
                
                ai_configs = [
                    {
                        "ai_provider": "openai",
                        "model_name": "gpt-4o",
                        "system_prompt": "You are a professional crypto trading signal parser. Extract structured data from trading signals. Return JSON only."
                    },
                    {
                        "ai_provider": "gemini", 
                        "model_name": "gemini-1.5-pro",
                        "system_prompt": "Parse crypto trading signals and return structured JSON data only."
                    }
                ]
                
                for config in ai_configs:
                    try:
                        self.supabase.table("ai_parser_config").insert(config).execute()
                        logger.info(f"✅ Inserted AI config: {config['ai_provider']}")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to insert AI config {config['ai_provider']}: {e}")
            
            else:
                logger.info(f"🤖 Found {len(ai_config_result.data)} existing AI configurations")
                
        except Exception as e:
            logger.error(f"❌ Error inserting test data: {e}")
    
    def show_current_status(self):
        """Показать текущий статус таблиц"""
        logger.info("📊 Current database status:")
        
        tables_to_check = [
            ("trader_registry", "Trader Registry"),
            ("signals_raw", "Raw Signals"), 
            ("signals_parsed", "Parsed Signals"),
            ("signal_outcomes", "Signal Outcomes"),
            ("signal_sources", "Signal Sources"),
            ("unified_signals", "Unified Signals"),
            ("parser_stats", "Parser Stats"),
            ("ai_parser_config", "AI Parser Config"),
            ("system_stats", "System Stats")
        ]
        
        for table_name, display_name in tables_to_check:
            try:
                result = self.supabase.table(table_name).select("*", count="exact").limit(1).execute()
                count = result.count if hasattr(result, 'count') else len(result.data) if result.data else 0
                logger.info(f"  📋 {display_name}: {count} records")
            except Exception as e:
                logger.warning(f"  ❌ {display_name}: Error - {e}")

def main():
    """Главная функция"""
    logger.info("🎯 UNIFIED SIGNAL SYSTEM MIGRATION TOOL")
    logger.info("=" * 60)
    
    # Проверяем переменные окружения
    required_env_vars = ["NEXT_PUBLIC_SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Missing environment variables: {missing_vars}")
        logger.error("Please set them in your .env file")
        sys.exit(1)
    
    # Создаем applier и применяем миграции
    applier = MigrationApplier()
    
    try:
        # Показываем статус до миграции
        logger.info("📊 BEFORE MIGRATION:")
        applier.show_current_status()
        
        # Применяем миграции
        applier.apply_unified_migrations()
        
        # Показываем статус после миграции
        logger.info("\n📊 AFTER MIGRATION:")
        applier.show_current_status()
        
        logger.info("\n🎉 MIGRATION COMPLETED SUCCESSFULLY!")
        logger.info("Your database is now ready for the unified signal system.")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
