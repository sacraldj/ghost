#!/usr/bin/env python3
"""
Проверка подключения к Supabase и анализ структуры базы данных
"""

import os
import sys
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

try:
    from supabase import create_client, Client
    import json
except ImportError as e:
    print(f"❌ Отсутствуют зависимости: {e}")
    print("Установите: pip install supabase python-dotenv")
    sys.exit(1)

class SupabaseChecker:
    def __init__(self):
        # Получаем переменные окружения
        self.supabase_url = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            print("❌ Отсутствуют переменные окружения:")
            print("   NEXT_PUBLIC_SUPABASE_URL")
            print("   SUPABASE_SERVICE_ROLE_KEY")
            sys.exit(1)
        
        print(f"🔗 Supabase URL: {self.supabase_url}")
        print(f"🔑 Service Key: {self.supabase_key[:20]}...")
        
        # Создаем клиент
        try:
            self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
            print("✅ Supabase клиент создан")
        except Exception as e:
            print(f"❌ Ошибка создания клиента: {e}")
            sys.exit(1)
    
    def check_connection(self):
        """Проверка базового подключения"""
        try:
            # Простой запрос для проверки подключения
            result = self.supabase.table('information_schema.tables').select('table_name').limit(1).execute()
            print("✅ Подключение к Supabase успешно!")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False
    
    def get_all_tables(self):
        """Получение списка всех таблиц"""
        try:
            print("\n📋 СПИСОК ВСЕХ ТАБЛИЦ:")
            print("=" * 50)
            
            # Получаем список таблиц через SQL
            query = """
            SELECT table_name, table_type 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
            """
            
            # Выполняем через RPC если доступно, иначе через прямой SQL
            try:
                result = self.supabase.rpc('exec_sql', {'sql': query}).execute()
                tables = result.data
            except:
                # Альтернативный способ - попробуем получить через отдельные запросы
                tables = self.get_tables_alternative()
            
            if tables:
                for table in tables:
                    print(f"  📄 {table.get('table_name', 'unknown')}")
                return [t.get('table_name') for t in tables]
            else:
                print("⚠️ Не удалось получить список таблиц")
                return []
                
        except Exception as e:
            print(f"❌ Ошибка получения таблиц: {e}")
            return []
    
    def get_tables_alternative(self):
        """Альтернативный способ получения таблиц"""
        # Список ожидаемых таблиц из нашей схемы
        expected_tables = [
            'profiles', 'trades', 'chat_history', 'news_events', 'ai_analysis',
            'critical_news', 'news_items', 'market_data', 'critical_alerts',
            'price_data', 'trader_registry', 'signals_raw', 'signals_parsed',
            'unified_signals', 'signal_sources', 'trades_min'
        ]
        
        existing_tables = []
        
        for table_name in expected_tables:
            try:
                # Пробуем сделать простой запрос к таблице
                result = self.supabase.table(table_name).select('*').limit(1).execute()
                existing_tables.append({'table_name': table_name})
                print(f"  ✅ {table_name}")
            except Exception:
                print(f"  ❌ {table_name} (не существует)")
        
        return existing_tables
    
    def check_key_tables(self):
        """Проверка ключевых таблиц для нашей системы"""
        print("\n🎯 ПРОВЕРКА КЛЮЧЕВЫХ ТАБЛИЦ:")
        print("=" * 50)
        
        key_tables = {
            'trader_registry': 'Реестр трейдеров',
            'signals_raw': 'Сырые сигналы',
            'signals_parsed': 'Обработанные сигналы',
            'unified_signals': 'Unified сигналы'
        }
        
        table_status = {}
        
        for table_name, description in key_tables.items():
            try:
                result = self.supabase.table(table_name).select('*', count='exact').limit(0).execute()
                count = result.count or 0
                table_status[table_name] = count
                print(f"  ✅ {table_name}: {count} записей - {description}")
            except Exception as e:
                table_status[table_name] = None
                print(f"  ❌ {table_name}: ОТСУТСТВУЕТ - {description}")
        
        return table_status
    
    def check_trader_data(self):
        """Проверка данных трейдеров"""
        print("\n👥 ДАННЫЕ ТРЕЙДЕРОВ:")
        print("=" * 50)
        
        try:
            result = self.supabase.table('trader_registry').select('*').execute()
            
            if result.data:
                print(f"📊 Найдено {len(result.data)} трейдеров:")
                for trader in result.data:
                    print(f"  🤖 {trader.get('name', 'Unnamed')} ({trader.get('trader_id')})")
                    print(f"     📱 {trader.get('source_handle', 'No handle')}")
                    print(f"     🟢 Активен: {trader.get('is_active', False)}")
            else:
                print("⚠️ Трейдеры не найдены")
                
        except Exception as e:
            print(f"❌ Ошибка получения данных трейдеров: {e}")
    
    def check_signals_data(self):
        """Проверка данных сигналов"""
        print("\n📡 ДАННЫЕ СИГНАЛОВ:")
        print("=" * 50)
        
        # Проверяем сырые сигналы
        try:
            result = self.supabase.table('signals_raw').select('*').order('created_at', desc=True).limit(5).execute()
            
            if result.data:
                print(f"📥 Последние {len(result.data)} сырых сигналов:")
                for signal in result.data:
                    text_preview = signal.get('text', '')[:50] + '...' if len(signal.get('text', '')) > 50 else signal.get('text', '')
                    print(f"  📝 {signal.get('trader_id')}: {text_preview}")
            else:
                print("⚠️ Сырые сигналы не найдены")
                
        except Exception as e:
            print(f"❌ Ошибка получения сырых сигналов: {e}")
        
        # Проверяем обработанные сигналы
        try:
            result = self.supabase.table('signals_parsed').select('*').order('parsed_at', desc=True).limit(5).execute()
            
            if result.data:
                print(f"\n📊 Последние {len(result.data)} обработанных сигналов:")
                for signal in result.data:
                    print(f"  💹 {signal.get('trader_id')}: {signal.get('symbol')} {signal.get('side')} @ {signal.get('entry')}")
            else:
                print("\n⚠️ Обработанные сигналы не найдены")
                
        except Exception as e:
            print(f"❌ Ошибка получения обработанных сигналов: {e}")
    
    def generate_report(self):
        """Генерация полного отчета"""
        print(f"\n📋 ПОЛНЫЙ ОТЧЕТ О БАЗЕ ДАННЫХ")
        print("=" * 60)
        print(f"🕒 Время проверки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔗 URL: {self.supabase_url}")
        
        # Проверяем подключение
        if not self.check_connection():
            return False
        
        # Получаем список таблиц
        tables = self.get_all_tables()
        
        # Проверяем ключевые таблицы
        table_status = self.check_key_tables()
        
        # Проверяем данные
        self.check_trader_data()
        self.check_signals_data()
        
        # Итоговый статус
        print(f"\n🎯 ИТОГОВЫЙ СТАТУС:")
        print("=" * 50)
        
        missing_tables = [table for table, count in table_status.items() if count is None]
        empty_tables = [table for table, count in table_status.items() if count == 0]
        
        if missing_tables:
            print(f"❌ Отсутствующие таблицы: {', '.join(missing_tables)}")
            print("   Нужно выполнить миграции!")
        
        if empty_tables:
            print(f"⚠️ Пустые таблицы: {', '.join(empty_tables)}")
            print("   Нужно добавить начальные данные!")
        
        if not missing_tables and not empty_tables:
            print("✅ База данных готова к работе!")
        
        return True

def main():
    print("🚀 ПРОВЕРКА БАЗЫ ДАННЫХ SUPABASE")
    print("=" * 60)
    
    checker = SupabaseChecker()
    success = checker.generate_report()
    
    if success:
        print(f"\n✅ Проверка завершена успешно!")
    else:
        print(f"\n❌ Проверка завершена с ошибками!")
        sys.exit(1)

if __name__ == "__main__":
    main()
