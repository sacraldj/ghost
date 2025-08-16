# 📊 GHOST Database Schema - Columns After Signal Full Audit

**Статус:** 🟢 ready-to-build  
**Версия:** v1.1  
**Единая БД:** ghost.db  
**Методология:** Строго как в position_exit_tracker.py

## 🔍 Анализ текущего состояния

### ✅ Что УЖЕ ЕСТЬ в системе:
1. **signals_parsed** - частично соответствует signals
2. **trades** - базовая версия, нужно расширить
3. **trader_registry** - частично соответствует traders
4. **candles_cache** - отсутствует, нужно создать
5. **market_snapshots** - есть в Supabase схеме
6. **performance_analytics** - есть в Supabase схеме

### ❌ Что ОТСУТСТВУЕТ и нужно доделать:

#### 1. **trade_events** - Критически важно!
- Нормализованная лента событий по сделке
- Для отслеживания касаний TP1, TP2, SL, BE
- Нужно для корректного аудита

#### 2. **trade_audits** - Критически важно!
- Агрегированный аудит каждой сделки
- MAE/MFE анализ
- Последовательность событий TP

#### 3. **strategies** - Отсутствует полностью
- Каталог торговых стратегий
- Параметры для каждой стратегии

#### 4. **strategy_results** - Отсутствует полностью
- Кэш результатов по стратегиям
- Пересчёт ROI для каждой стратегии

#### 5. **trader_stats** - Отсутствует полностью
- Агрегированная статистика по трейдерам
- По периодам и стратегиям

#### 6. **candles_cache** - Отсутствует полностью
- Кэш свечей для анализа
- Нужно для симуляции сделок

## 🚀 План доработки

### Шаг 1: Создание недостающих таблиц
```bash
# Выполнить миграцию
sqlite3 ghost.db < db/migrate_to_ghost_full_schema.sql
```

### Шаг 2: Обновление API endpoints
- Обновить `/api/traders-analytics/list` для работы с новой схемой
- Добавить поддержку strategy_id в запросах
- Интегрировать с trader_stats таблицей

### Шаг 3: Создание модулей для заполнения данных

#### 3.1 Signal Processor (обновить существующий)
```python
# core/signal_processor_v2.py
class SignalProcessorV2:
    def process_raw_signal(self, raw_message):
        # Парсинг в новую таблицу signals
        # С полями согласно спецификации
        pass
```

#### 3.2 Trade Executor (новый)
```python
# core/trade_executor.py
class TradeExecutor:
    def execute_paper_trade(self, signal_id, strategy_id):
        # Создание записи в trades
        # С правильным mode='paper'
        pass
    
    def record_trade_event(self, trade_id, event_type, price):
        # Запись в trade_events
        pass
```

#### 3.3 Trade Auditor (новый)
```python
# core/trade_auditor.py
class TradeAuditor:
    def audit_trade(self, trade_id):
        # Анализ всех событий из trade_events
        # Расчёт MAE/MFE
        # Запись в trade_audits
        pass
```

#### 3.4 Strategy Simulator (новый)
```python
# core/strategy_simulator.py
class StrategySimulator:
    def simulate_strategy(self, trade_id, strategy_id):
        # Симуляция торговли по стратегии
        # Запись результата в strategy_results
        pass
```

#### 3.5 Stats Aggregator (новый)
```python
# core/stats_aggregator.py
class StatsAggregator:
    def update_trader_stats(self, trader_id, period_key, strategy_id):
        # Агрегация данных из strategy_results
        # Обновление trader_stats
        pass
```

### Шаг 4: Обновление UI компонентов

#### 4.1 TradersAnalyticsDashboard
- Интегрировать с новыми VIEW
- Использовать vw_trader_ranking
- Поддержка фильтрации по стратегиям

#### 4.2 API Endpoints
```typescript
// Обновить существующие endpoints
GET /api/traders-analytics/list?strategy_id=tp2_sl_be
GET /api/traders-analytics/summary?strategy_id=scalping
GET /api/traders-analytics/chart?strategy_id=swing
```

## 📋 Приоритеты реализации

### 🔥 Критический приоритет:
1. **trade_events** - без этого невозможен корректный аудит
2. **trade_audits** - нужно для расчёта MAE/MFE
3. **strategies** - база для всей системы стратегий

### ⚡ Высокий приоритет:
4. **strategy_results** - кэш для быстрого доступа к результатам
5. **trader_stats** - агрегированная статистика
6. **candles_cache** - данные для симуляции

### 📊 Средний приоритет:
7. **scenarios/scenario_results** - what-if анализ
8. Обновление VIEW для оптимизации запросов

## 🔧 Технические детали

### Формат JSON полей:
```json
// targets_json
["45000", "46000", "47000"]

// tp_hits_json
{
  "tp1": {"hit": true, "time": 1692168000000, "price": "45000"},
  "tp2": {"hit": false, "time": null, "price": "46000"}
}

// params_json для стратегий
{
  "tp1_portion": 0.5,
  "tp2_portion": 0.5,
  "be_after_tp1": true,
  "max_duration": 86400
}
```

### Расчёт ROI (как в position_exit_tracker.py):
```python
def calculate_roi(pnl_net, margin_used):
    return (pnl_net / margin_used) * 100 if margin_used > 0 else 0
```

## 🎯 Ожидаемый результат

После завершения доработки система будет:

1. ✅ **Полностью соответствовать спецификации Дарэна**
2. ✅ **Корректно рассчитывать ROI по разным стратегиям**
3. ✅ **Предоставлять детальный аудит каждой сделки**
4. ✅ **Поддерживать симуляцию $100 маржи на сигнал**
5. ✅ **Показывать разное ROI в зависимости от стратегии**
6. ✅ **Агрегировать статистику по трейдерам и периодам**

## 🚀 Команды для запуска

```bash
# 1. Создать полную схему
sqlite3 ghost.db < db/ghost_full_schema.sql

# 2. Или мигрировать существующую
sqlite3 ghost.db < db/migrate_to_ghost_full_schema.sql

# 3. Проверить результат
sqlite3 ghost.db ".tables"
sqlite3 ghost.db "SELECT * FROM strategies;"
```

**Готово к реализации! 🎉**
