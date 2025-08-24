#!/usr/bin/env python3
"""
Скрипт инициализации аналитики трейдеров
⚠️ НЕ трогает существующие данные
✅ Создает новые таблицы и заполняет базовыми метриками
"""

import os
import sys
import asyncio
from supabase import create_client, Client
from datetime import datetime, timedelta
import json
from typing import Dict, Any

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TraderAnalyticsInitializer:
    def __init__(self):
        # Получаем переменные окружения
        supabase_url = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_SECRET_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("❌ Необходимы переменные NEXT_PUBLIC_SUPABASE_URL и SUPABASE_SERVICE_ROLE_KEY")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        print(f"✅ Подключение к Supabase: {supabase_url}")
    
    def create_tables(self) -> bool:
        """Создает новые таблицы (если их нет)"""
        print("\n📋 Создание новых таблиц...")
        
        try:
            # Читаем SQL файл
            sql_file = os.path.join(os.path.dirname(__file__), '..', 'database', 'add_trader_analytics.sql')
            
            if not os.path.exists(sql_file):
                print(f"❌ Файл не найден: {sql_file}")
                return False
            
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            print("⚠️  ВАЖНО: SQL скрипт нужно выполнить в Supabase SQL Editor:")
            print("   1. Откройте https://supabase.com/dashboard")
            print("   2. Перейдите в SQL Editor")
            print(f"   3. Выполните содержимое файла: {sql_file}")
            print("\n📄 SQL для выполнения:")
            print("=" * 60)
            print(sql_content[:500] + "...")
            print("=" * 60)
            
            # Проверяем доступность таблиц
            return self._check_tables_exist()
            
        except Exception as e:
            print(f"❌ Ошибка создания таблиц: {e}")
            return False
    
    def _check_tables_exist(self) -> bool:
        """Проверяет существование новых таблиц"""
        required_tables = [
            'trader_analytics',
            'signal_errors', 
            'trader_time_stats',
            'trader_behavior_flags'
        ]
        
        print("\n🔍 Проверка существования таблиц...")
        
        for table_name in required_tables:
            try:
                # Пробуем сделать простой запрос к таблице
                result = self.supabase.table(table_name).select("*").limit(1).execute()
                print(f"✅ Таблица {table_name}: найдена")
            except Exception as e:
                print(f"❌ Таблица {table_name}: не найдена ({e})")
                return False
        
        return True
    
    def calculate_basic_analytics(self) -> bool:
        """Вычисляет базовую аналитику для существующих трейдеров"""
        print("\n📊 Расчет базовой аналитики...")
        
        try:
            # Получаем всех активных трейдеров
            traders_result = self.supabase.table('trader_registry').select('*').eq('is_active', True).execute()
            traders = traders_result.data
            
            if not traders:
                print("⚠️ Активные трейдеры не найдены")
                return True
            
            print(f"🎯 Найдено {len(traders)} активных трейдеров")
            
            for trader in traders:
                trader_id = trader['trader_id']
                print(f"\n📈 Обработка трейдера: {trader_id}")
                
                # Получаем сигналы трейдера из v_trades
                signals_result = self.supabase.table('v_trades').select('*').eq('source', trader_id).execute()
                signals = signals_result.data
                
                if not signals:
                    print(f"   ⚠️ Сигналы для {trader_id} не найдены")
                    continue
                
                # Вычисляем метрики
                analytics = self._calculate_trader_metrics(signals)
                analytics['trader_id'] = trader_id
                
                # Сохраняем в trader_analytics (upsert)
                self.supabase.table('trader_analytics').upsert(analytics, on_conflict='trader_id').execute()
                
                # Создаем базовую запись в behavior_flags
                behavior_flags = {
                    'trader_id': trader_id,
                    'has_duplicates': False,
                    'has_contradictions': False,
                    'suspected_copy_paste': False
                }
                self.supabase.table('trader_behavior_flags').upsert(behavior_flags, on_conflict='trader_id').execute()
                
                print(f"   ✅ Trust Index: {analytics['trust_index']:.1f}, Grade: {analytics['grade']}")
            
            # Обновляем рейтинги
            self._update_rankings()
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка расчета аналитики: {e}")
            return False
    
    def _calculate_trader_metrics(self, signals: list) -> Dict[str, Any]:
        """Вычисляет метрики для трейдера на основе сигналов"""
        total_signals = len(signals)
        
        if total_signals == 0:
            return {
                'total_signals': 0,
                'trust_index': 50,
                'grade': 'C',
                'risk_score': 50
            }
        
        # Базовая статистика
        executed_signals = [s for s in signals if s.get('status') == 'sim_open']
        executed_count = len(executed_signals)
        
        # Подсчет побед (TP1 или TP2)
        wins = [s for s in executed_signals if s.get('tp1_hit') or s.get('tp2_hit')]
        win_count = len(wins)
        
        # Финансовые метрики
        total_pnl = sum(float(s.get('pnl_gross', 0) or 0) for s in executed_signals)
        
        # Расчет производных метрик
        winrate = (win_count / executed_count * 100) if executed_count > 0 else 0
        avg_roi = (total_pnl / executed_count) if executed_count > 0 else 0
        
        # Простой расчет Trust Index (0-100)
        trust_index = min(100, max(0,
            winrate * 0.4 +                          # 40% winrate
            min(100, max(0, avg_roi + 50)) * 0.3 +   # 30% ROI (центрируем)
            min(100, total_signals) * 0.2 +          # 20% activity
            10                                        # 10% base
        ))
        
        # Присваиваем Grade
        if trust_index >= 80:
            grade = 'A'
        elif trust_index >= 60:
            grade = 'B' 
        elif trust_index >= 40:
            grade = 'C'
        else:
            grade = 'D'
        
        # Risk Score (простая версия)
        risk_score = max(0, min(100, 100 - trust_index))
        
        return {
            'total_signals': total_signals,
            'valid_signals': total_signals,  # пока считаем все валидными
            'executed_signals': executed_count,
            'winrate': round(winrate, 2),
            'tp1_rate': 0,  # TODO: детальный расчет
            'tp2_rate': 0,  # TODO: детальный расчет
            'sl_rate': 0,   # TODO: детальный расчет
            'total_pnl': round(total_pnl, 2),
            'avg_roi': round(avg_roi, 2),
            'best_roi': 0,  # TODO: расчет
            'worst_roi': 0, # TODO: расчет
            'avg_rrr': 0,   # TODO: расчет
            'max_drawdown': 0, # TODO: расчет
            'consistency_score': round(trust_index * 0.8, 2),
            'trust_index': round(trust_index, 2),
            'grade': grade,
            'risk_score': round(risk_score, 2),
            'overall_rank': 999,  # будет обновлено в _update_rankings
            'rank_change': 0
        }
    
    def _update_rankings(self):
        """Обновляет рейтинги трейдеров"""
        print("\n🏆 Обновление рейтингов...")
        
        try:
            # Получаем всех трейдеров с аналитикой, отсортированных по trust_index
            result = self.supabase.table('trader_analytics').select('trader_id, trust_index').order('trust_index', desc=True).execute()
            analytics = result.data
            
            # Обновляем рейтинги
            for i, trader in enumerate(analytics):
                new_rank = i + 1
                self.supabase.table('trader_analytics').update({
                    'overall_rank': new_rank
                }).eq('trader_id', trader['trader_id']).execute()
            
            print(f"✅ Рейтинги обновлены для {len(analytics)} трейдеров")
            
        except Exception as e:
            print(f"❌ Ошибка обновления рейтингов: {e}")
    
    def test_api_endpoints(self):
        """Тестирует новые API endpoints"""
        print("\n🧪 Тестирование API endpoints...")
        
        # Тест не делаем, так как нужно запустить Next.js сервер
        print("⚠️ Для тестирования API endpoints запустите:")
        print("   npm run dev")
        print("   Затем откройте: http://localhost:3000/test-table")
    
    def run(self):
        """Основной метод запуска"""
        print("🚀 Инициализация аналитики трейдеров")
        print("=" * 50)
        
        # Шаг 1: Создание таблиц
        if not self.create_tables():
            print("\n❌ ОСТАНОВКА: Необходимо создать таблицы в Supabase")
            return False
        
        # Шаг 2: Расчет аналитики  
        if not self.calculate_basic_analytics():
            print("\n❌ ОСТАНОВКА: Ошибка расчета аналитики")
            return False
        
        # Шаг 3: Тест API
        self.test_api_endpoints()
        
        print("\n🎉 ИНИЦИАЛИЗАЦИЯ ЗАВЕРШЕНА!")
        print("\n📋 Следующие шаги:")
        print("   1. Запустите: npm run dev")
        print("   2. Откройте: http://localhost:3000/test-table")
        print("   3. Проверьте новые колонки Trust Index и Grade")
        print("   4. Посмотрите summary блок с аналитикой трейдеров")
        
        return True

def main():
    try:
        initializer = TraderAnalyticsInitializer()
        success = initializer.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Остановлено пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
