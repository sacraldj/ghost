#!/usr/bin/env python3
"""
Скрипт для проверки совместимости схемы базы данных
Сравнивает поля из схемы Дарэна с нашими схемами Prisma и Supabase
"""

import re
from typing import Set, Dict, List

# Поля из схемы Дарэна (SQLite)
DARRIN_FIELDS = {
    'id', 'trade_id', 'symbol', 'side', 'leverage', 'source', 'source_type', 'source_name', 'source_id',
    'entry_zone', 'entry_type', 'entry_exec_price', 'entry', 'fill_type', 'tp1', 'tp2', 'tp3', 'sl',
    'tp1_price', 'tp2_price', 'sl_price', 'tp1_auto_calc', 'sl_auto_calc', 'sl_type', 'real_entry_price',
    'position_qty', 'margin_usd', 'verdict_reason', 'opened_at', 'updated_at', 'real_leverage',
    'margin_used', 'entry_min', 'entry_max', 'avg_entry_price', 'entry_method', 'risk_pct',
    'source_leverage', 'raw_symbol', 'targets', 'tp_weights', 'original_text', 'exit_time',
    'exit_reason', 'roi_percent', 'verdict', 'gpt_comment', 'exit_trigger_type', 'exit_trigger_value',
    'ghost_exit_score', 'order_id', 'execution_type', 'fill_status', 'avg_fill_price', 'fee_rate',
    'fee_paid', 'model_id', 'strategy_version', 'signal_sequence', 'consensus_score',
    'consensus_sources', 'status', 'closed_at', 'realized_pnl', 'exit', 'finalized', 'roi_planned',
    'pnl_gross', 'pnl_net', 'roi_gross', 'entry_price_bybit', 'exit_price_bybit', 'exit_price_fallback',
    'roi_percent_bybit', 'roi_estimated', 'entry_slippage', 'exit_slippage', 'entry_latency_ms',
    'exit_latency_ms', 'data_source_mode', 'weekday', 'roi_bybit_style', 'bybit_fee_open',
    'bybit_fee_close', 'bybit_fee_total', 'bybit_pnl_net', 'weekday_name', 'opened_at_full',
    'commission_over_roi', 'loss_type', 'anomaly_flag', 'bybit_pnl_net_api', 'order_id_exit',
    'signal_id', 'bybit_pnl_net_fallback', 'order_id_exit_fallback', 'roi_source', 'tp_hit',
    'exit_detail', 'roi_ui', 'pnl_net_initial', 'roi_percent_initial', 'tp1_hit', 'tp2_hit',
    'sl_hit', 'early_exit', 'early_exit_reason', 'exit_explanation', 'exit_ai_score',
    'tp_count_hit', 'roi_sl_expected', 'expected_profit_tp1', 'expected_loss_sl', 'duration_sec',
    'leverage_used_expected', 'strategy_id', 'tp1_order_id', 'tp2_order_id', 'sl_order_id',
    'sl_be_moved', 'sl_be_method', 'tp2_restore_attempted', 'tp2_order_id_current',
    'tp2_order_id_history', 'sl_order_id_current', 'sl_order_id_history', 'tp2_restore_attempts',
    'pnl_tp1', 'pnl_tp2', 'roi_tp1', 'roi_tp2', 'roi_final_real', 'pnl_final_real',
    'profit_tp1_real', 'profit_tp2_real', 'fee_tp1', 'fee_tp2', 'pnl_tp1_net', 'pnl_tp2_net',
    'roi_tp1_real', 'roi_tp2_real', 'roi_sl_real', 'tp2_exit_type', 'tp1_hit_time',
    'tp2_hit_time', 'sl_hit_time', 'tp1_duration_sec', 'tp2_duration_sec', 'sl_duration_sec',
    'expected_profit_tp2', 'expected_profit_total', 'manual_exit', 'manual_exit_type',
    'sl_to_be', 'sl_be_price', 'pnl_source', 'raw_fills_count', 'fills_legA', 'fills_legB',
    'fills_legA_vwap', 'fills_legB_vwap', 'fills_legA_qty', 'fills_legB_qty', 'fills_legA_fee',
    'fills_legB_fee', 'fills_legA_fee_in', 'fills_legB_fee_in'
}

def extract_prisma_fields(prisma_file: str) -> Set[str]:
    """Извлекает поля из Prisma схемы"""
    try:
        with open(prisma_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Ищем поля в модели Trade
        trade_model_match = re.search(r'model Trade\s*\{([^}]+)\}', content, re.DOTALL)
        if not trade_model_match:
            return set()
        
        trade_content = trade_model_match.group(1)
        
        # Извлекаем имена полей
        field_pattern = r'(\w+)\s+[\w<>\[\]?]+'
        fields = set()
        
        for line in trade_content.split('\n'):
            line = line.strip()
            if line and not line.startswith('//') and not line.startswith('@@'):
                match = re.search(field_pattern, line)
                if match:
                    field_name = match.group(1)
                    if field_name not in ['profile', 'Profile']:  # Исключаем связи
                        fields.add(field_name)
        
        return fields
    except FileNotFoundError:
        print(f"❌ Файл {prisma_file} не найден")
        return set()
    except Exception as e:
        print(f"❌ Ошибка при чтении {prisma_file}: {e}")
        return set()

def extract_supabase_fields(sql_file: str) -> Set[str]:
    """Извлекает поля из SQL миграции Supabase"""
    try:
        with open(sql_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Ищем CREATE TABLE trades
        create_table_match = re.search(r'CREATE TABLE trades\s*\(([\s\S]*?)\);', content, re.IGNORECASE)
        if not create_table_match:
            print(f"❌ CREATE TABLE trades не найден в {sql_file}")
            return set()
        
        table_content = create_table_match.group(1)
        
        # Извлекаем имена полей
        fields = set()
        lines = table_content.split('\n')
        
        for line in lines:
            line = line.strip()
            # Пропускаем пустые строки и комментарии
            if not line or line.startswith('--') or line.startswith('@@'):
                continue
            
            # Убираем комментарии в конце строки
            line = re.sub(r'--.*$', '', line)
            line = line.strip()
            
            # Пропускаем строки с комментариями
            if not line or line.startswith('--'):
                continue
            
            # Ищем имя поля (первое слово в строке)
            field_match = re.search(r'^(\w+)', line)
            if field_match:
                field_name = field_match.group(1)
                # Исключаем SQL ключевые слова и специальные конструкции
                if field_name not in ['PRIMARY', 'KEY', 'REFERENCES', 'ON', 'DELETE', 'CASCADE', 'CHECK', 'IN', 'LONG', 'SHORT', 'DEFAULT', 'NOT', 'NULL', 'UNIQUE', 'CONSTRAINT']:
                    fields.add(field_name)
        
        return fields
    except FileNotFoundError:
        print(f"❌ Файл {sql_file} не найден")
        return set()
    except Exception as e:
        print(f"❌ Ошибка при чтении {sql_file}: {e}")
        return set()

def check_compatibility():
    """Проверяет совместимость схем"""
    print("🔍 Проверка совместимости схемы базы данных")
    print("=" * 50)
    
    # Проверяем Prisma схему
    print("\n📋 Prisma Schema (prisma/schema.prisma):")
    prisma_fields = extract_prisma_fields('prisma/schema.prisma')
    if prisma_fields:
        print(f"✅ Найдено полей: {len(prisma_fields)}")
        
        # Проверяем недостающие поля
        missing_in_prisma = DARRIN_FIELDS - prisma_fields
        if missing_in_prisma:
            print(f"❌ Недостающие поля ({len(missing_in_prisma)}):")
            for field in sorted(missing_in_prisma):
                print(f"   - {field}")
        else:
            print("✅ Все поля из схемы Дарэна присутствуют")
    else:
        print("❌ Не удалось извлечь поля из Prisma схемы")
    
    # Проверяем Supabase миграцию
    print("\n🗄️ Supabase Migration (supabase_complete_migration.sql):")
    supabase_fields = extract_supabase_fields('supabase_complete_migration.sql')
    if supabase_fields:
        print(f"✅ Найдено полей: {len(supabase_fields)}")
        
        # Проверяем недостающие поля
        missing_in_supabase = DARRIN_FIELDS - supabase_fields
        if missing_in_supabase:
            print(f"❌ Недостающие поля ({len(missing_in_supabase)}):")
            for field in sorted(missing_in_supabase):
                print(f"   - {field}")
        else:
            print("✅ Все поля из схемы Дарэна присутствуют")
    else:
        print("❌ Не удалось извлечь поля из Supabase миграции")
    
    # Общая статистика
    print("\n📊 Общая статистика:")
    print(f"   - Всего полей в схеме Дарэна: {len(DARRIN_FIELDS)}")
    print(f"   - Поля в Prisma: {len(prisma_fields)}")
    print(f"   - Поля в Supabase: {len(supabase_fields)}")
    
    # Проверяем полное покрытие
    if prisma_fields and supabase_fields:
        total_coverage = len(prisma_fields.union(supabase_fields))
        coverage_percentage = (total_coverage / len(DARRIN_FIELDS)) * 100
        print(f"   - Общее покрытие: {coverage_percentage:.1f}%")
        
        if coverage_percentage >= 95:
            print("🎉 Отличное покрытие схемы!")
        elif coverage_percentage >= 80:
            print("👍 Хорошее покрытие схемы")
        else:
            print("⚠️ Низкое покрытие схемы")

if __name__ == "__main__":
    check_compatibility()
