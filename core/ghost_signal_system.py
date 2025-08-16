#!/usr/bin/env python3
"""
GHOST Signal System - Полная система сбора и анализа торговых сигналов
Объединяет все модули: парсинг, валидацию, отслеживание, статистику
"""

import asyncio
import logging
import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

# Импортируем наши модули
from candle_analyzer import CandleAnalyzer
from realtime_tracker import RealtimeTracker
from statistics_calculator import StatisticsCalculator

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ghost_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class GhostSignalSystem:
    """Главная система GHOST для сигналов"""
    
    def __init__(self):
        load_dotenv()
        
        # Инициализация Supabase
        self.supabase = create_client(
            os.getenv('NEXT_PUBLIC_SUPABASE_URL'),
            os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        )
        
        # Инициализация модулей
        self.candle_analyzer = CandleAnalyzer(self.supabase)
        self.realtime_tracker = RealtimeTracker(self.supabase)
        self.statistics_calculator = StatisticsCalculator(self.supabase)
        
        self.running = False
        
    async def create_required_tables(self):
        """Создание необходимых таблиц если их нет"""
        try:
            # Таблица для валидаций сигналов
            self.supabase.rpc('create_table_if_not_exists', {
                'table_name': 'signal_validations',
                'columns': '''
                    id SERIAL PRIMARY KEY,
                    signal_id TEXT UNIQUE NOT NULL,
                    is_valid BOOLEAN DEFAULT FALSE,
                    entry_confirmed BOOLEAN DEFAULT FALSE,
                    tp1_reached BOOLEAN DEFAULT FALSE,
                    tp2_reached BOOLEAN DEFAULT FALSE,
                    sl_hit BOOLEAN DEFAULT FALSE,
                    max_profit_pct FLOAT DEFAULT 0,
                    max_loss_pct FLOAT DEFAULT 0,
                    duration_hours FLOAT DEFAULT 0,
                    validation_time TIMESTAMP DEFAULT NOW(),
                    notes TEXT
                '''
            }).execute()
            
            # Таблица для событий сигналов
            self.supabase.rpc('create_table_if_not_exists', {
                'table_name': 'signal_events',
                'columns': '''
                    id SERIAL PRIMARY KEY,
                    signal_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_time TIMESTAMP DEFAULT NOW(),
                    price FLOAT,
                    profit_pct FLOAT DEFAULT 0,
                    loss_pct FLOAT DEFAULT 0,
                    notes TEXT
                '''
            }).execute()
            
            # Таблица для статистики трейдеров
            self.supabase.rpc('create_table_if_not_exists', {
                'table_name': 'trader_statistics',
                'columns': '''
                    id SERIAL PRIMARY KEY,
                    trader_id TEXT NOT NULL,
                    period TEXT NOT NULL,
                    total_signals INTEGER DEFAULT 0,
                    valid_signals INTEGER DEFAULT 0,
                    tp1_hits INTEGER DEFAULT 0,
                    tp2_hits INTEGER DEFAULT 0,
                    sl_hits INTEGER DEFAULT 0,
                    winrate_pct FLOAT DEFAULT 0,
                    avg_profit_pct FLOAT DEFAULT 0,
                    avg_loss_pct FLOAT DEFAULT 0,
                    total_pnl_pct FLOAT DEFAULT 0,
                    max_drawdown_pct FLOAT DEFAULT 0,
                    avg_duration_hours FLOAT DEFAULT 0,
                    best_signal_pct FLOAT DEFAULT 0,
                    worst_signal_pct FLOAT DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(trader_id, period)
                '''
            }).execute()
            
            print("✅ Таблицы созданы/проверены")
            
        except Exception as e:
            logger.warning(f"Не удалось создать таблицы через RPC: {e}")
            print("⚠️ Создание таблиц пропущено (возможно, они уже существуют)")
    
    async def run_initial_validation(self):
        """Запуск первичной валидации существующих сигналов"""
        print("🔍 ЗАПУСК ПЕРВИЧНОЙ ВАЛИДАЦИИ СИГНАЛОВ")
        print("=" * 50)
        
        try:
            await self.candle_analyzer.validate_pending_signals()
            print("✅ Первичная валидация завершена")
        except Exception as e:
            logger.error(f"Ошибка первичной валидации: {e}")
    
    async def run_initial_statistics(self):
        """Запуск первичного расчета статистики"""
        print("📊 ЗАПУСК ПЕРВИЧНОГО РАСЧЕТА СТАТИСТИКИ")
        print("=" * 50)
        
        try:
            await self.statistics_calculator.calculate_all_traders_stats()
            print("✅ Первичная статистика рассчитана")
        except Exception as e:
            logger.error(f"Ошибка первичной статистики: {e}")
    
    async def start_system(self):
        """Запуск полной системы"""
        self.running = True
        
        print("🚀 ЗАПУСК GHOST SIGNAL SYSTEM")
        print("=" * 60)
        print(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Создаем необходимые таблицы
        await self.create_required_tables()
        
        # Запускаем первичную обработку
        await self.run_initial_validation()
        await self.run_initial_statistics()
        
        print("\n🔄 ЗАПУСК РЕАЛЬНОГО ВРЕМЕНИ")
        print("=" * 60)
        
        # Создаем задачи для всех компонентов
        tasks = [
            # Реальное отслеживание сигналов
            asyncio.create_task(
                self.realtime_tracker.start_tracking(),
                name="realtime_tracker"
            ),
            
            # Периодическая валидация новых сигналов
            asyncio.create_task(
                self.periodic_validation(),
                name="periodic_validation"
            ),
            
            # Периодический расчет статистики
            asyncio.create_task(
                self.statistics_calculator.run_periodic_calculation(interval_hours=1),
                name="periodic_statistics"
            ),
            
            # Мониторинг системы
            asyncio.create_task(
                self.system_monitor(),
                name="system_monitor"
            )
        ]
        
        try:
            # Запускаем все задачи
            await asyncio.gather(*tasks)
            
        except KeyboardInterrupt:
            print("\n⏹️ ОСТАНОВКА СИСТЕМЫ...")
            self.running = False
            
            # Останавливаем все задачи
            for task in tasks:
                task.cancel()
                
            # Ждем завершения задач
            await asyncio.gather(*tasks, return_exceptions=True)
            
            print("✅ Система остановлена")
    
    async def periodic_validation(self):
        """Периодическая валидация новых сигналов"""
        while self.running:
            try:
                await asyncio.sleep(1800)  # Каждые 30 минут
                print("🔍 Валидация новых сигналов...")
                await self.candle_analyzer.validate_pending_signals()
                
            except Exception as e:
                logger.error(f"Ошибка периодической валидации: {e}")
                await asyncio.sleep(300)  # Ждем 5 минут при ошибке
    
    async def system_monitor(self):
        """Мониторинг состояния системы"""
        while self.running:
            try:
                await asyncio.sleep(3600)  # Каждый час
                
                # Проверяем состояние компонентов
                print(f"\n📊 СОСТОЯНИЕ СИСТЕМЫ - {datetime.now().strftime('%H:%M:%S')}")
                print("-" * 40)
                
                # Количество активных сигналов
                active_signals = len(self.realtime_tracker.active_signals)
                print(f"🎯 Активных сигналов: {active_signals}")
                
                # Статистика за последний час
                # Здесь можно добавить дополнительные проверки
                
                print("-" * 40)
                
            except Exception as e:
                logger.error(f"Ошибка мониторинга системы: {e}")
                await asyncio.sleep(300)
    
    async def get_system_status(self) -> dict:
        """Получить статус системы"""
        try:
            # Количество сигналов в БД
            signals_count = self.supabase.table('signals_parsed').select('signal_id', count='exact').execute()
            
            # Количество валидаций
            validations_count = self.supabase.table('signal_validations').select('id', count='exact').execute()
            
            # Количество активных сигналов
            active_signals = len(self.realtime_tracker.active_signals)
            
            # Топ трейдеры
            top_traders = await self.statistics_calculator.get_top_traders(limit=5)
            
            return {
                'system_running': self.running,
                'total_signals': signals_count.count if signals_count else 0,
                'validated_signals': validations_count.count if validations_count else 0,
                'active_signals': active_signals,
                'top_traders': top_traders,
                'last_update': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статуса системы: {e}")
            return {
                'system_running': self.running,
                'error': str(e)
            }

async def main():
    """Главная функция запуска"""
    system = GhostSignalSystem()
    
    try:
        await system.start_system()
    except KeyboardInterrupt:
        print("👋 До свидания!")

if __name__ == "__main__":
    asyncio.run(main())
