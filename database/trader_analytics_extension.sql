-- МАКСИМАЛЬНАЯ АНАЛИТИКА ТРЕЙДЕРОВ - РАСШИРЕНИЕ СИСТЕМЫ
-- Выполнить в Supabase SQL Editor

-- =====================================================
-- 1. ДЕТАЛЬНАЯ КЛАССИФИКАЦИЯ ОШИБОК
-- =====================================================
CREATE TABLE IF NOT EXISTS signal_validation_errors (
  id SERIAL PRIMARY KEY,
  signal_id INTEGER REFERENCES signals_parsed(signal_id),
  trader_id TEXT REFERENCES trader_registry(trader_id),
  error_category TEXT NOT NULL, -- 'logic', 'technical', 'market', 'format'  
  error_type TEXT NOT NULL,     -- 'tp_below_entry', 'missing_sl', 'invalid_symbol'
  error_message TEXT,
  severity TEXT DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- 2. ЕЖЕДНЕВНАЯ СТАТИСТИКА ТРЕЙДЕРОВ
-- =====================================================
CREATE TABLE IF NOT EXISTS trader_stats_daily (
  id SERIAL PRIMARY KEY,
  trader_id TEXT REFERENCES trader_registry(trader_id),
  date DATE NOT NULL,
  
  -- Основные метрики
  signals_count INTEGER DEFAULT 0,
  valid_signals INTEGER DEFAULT 0,
  executed_signals INTEGER DEFAULT 0,
  
  -- Результативность
  tp1_hits INTEGER DEFAULT 0,
  tp2_hits INTEGER DEFAULT 0,
  sl_hits INTEGER DEFAULT 0,
  be_hits INTEGER DEFAULT 0,
  no_fill INTEGER DEFAULT 0,
  
  -- Финансы
  pnl_gross DECIMAL(20,8) DEFAULT 0,
  pnl_net DECIMAL(20,8) DEFAULT 0,
  roi_avg DECIMAL(10,4) DEFAULT 0,
  best_signal_roi DECIMAL(10,4) DEFAULT 0,
  worst_signal_roi DECIMAL(10,4) DEFAULT 0,
  
  -- Риск-менеджмент  
  avg_rrr DECIMAL(10,4) DEFAULT 0,
  avg_tp1_distance_pct DECIMAL(10,4) DEFAULT 0,
  avg_sl_distance_pct DECIMAL(10,4) DEFAULT 0,
  
  -- Временные метрики
  avg_duration_to_tp1_sec INTEGER DEFAULT 0,
  avg_duration_to_tp2_sec INTEGER DEFAULT 0,
  avg_duration_to_sl_sec INTEGER DEFAULT 0,
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(trader_id, date)
);

-- =====================================================  
-- 3. ПОВЕДЕНЧЕСКИЕ ПАТТЕРНЫ
-- =====================================================
CREATE TABLE IF NOT EXISTS trader_behavioral_patterns (
  id SERIAL PRIMARY KEY,
  trader_id TEXT REFERENCES trader_registry(trader_id),
  pattern_type TEXT NOT NULL, -- 'duplicate', 'contradiction', 'frequency', 'timing'
  pattern_data JSONB NOT NULL,
  severity DECIMAL(5,2) DEFAULT 0, -- 0-100 score
  first_detected TIMESTAMPTZ DEFAULT NOW(),
  last_detected TIMESTAMPTZ DEFAULT NOW(),
  occurrence_count INTEGER DEFAULT 1,
  
  -- Примеры pattern_data:
  -- duplicate: {"signal_ids": [123, 124], "similarity": 0.95}
  -- contradiction: {"signal_1": 123, "signal_2": 124, "conflict": "LONG vs SHORT BTC"}  
  -- timing: {"hour": 14, "frequency": 0.8, "performance": {"roi": 2.5}}
  
  UNIQUE(trader_id, pattern_type, pattern_data)
);

-- =====================================================
-- 4. РАСШИРЕННЫЕ МЕТРИКИ ПРОИЗВОДИТЕЛЬНОСТИ  
-- =====================================================
CREATE TABLE IF NOT EXISTS trader_performance_metrics (
  id SERIAL PRIMARY KEY,
  trader_id TEXT REFERENCES trader_registry(trader_id),
  period_type TEXT NOT NULL, -- 'daily', 'weekly', 'monthly', 'all_time'
  period_start DATE NOT NULL,
  period_end DATE NOT NULL,
  
  -- Основная статистика
  total_signals INTEGER DEFAULT 0,
  valid_signals INTEGER DEFAULT 0,
  executed_signals INTEGER DEFAULT 0,
  invalid_rate DECIMAL(10,4) DEFAULT 0,
  
  -- Детальная результативность
  winrate DECIMAL(10,4) DEFAULT 0,
  tp1_rate DECIMAL(10,4) DEFAULT 0,
  tp2_rate DECIMAL(10,4) DEFAULT 0,
  sl_rate DECIMAL(10,4) DEFAULT 0,
  be_rate DECIMAL(10,4) DEFAULT 0,
  no_fill_rate DECIMAL(10,4) DEFAULT 0,
  
  -- Финансовые метрики
  total_pnl DECIMAL(20,8) DEFAULT 0,
  avg_roi DECIMAL(10,4) DEFAULT 0,
  median_roi DECIMAL(10,4) DEFAULT 0,
  best_roi DECIMAL(10,4) DEFAULT 0,
  worst_roi DECIMAL(10,4) DEFAULT 0,
  sharpe_ratio DECIMAL(10,4) DEFAULT 0,
  sortino_ratio DECIMAL(10,4) DEFAULT 0,
  max_drawdown DECIMAL(10,4) DEFAULT 0,
  
  -- Стрики и последовательности
  max_win_streak INTEGER DEFAULT 0,
  max_loss_streak INTEGER DEFAULT 0,
  current_streak INTEGER DEFAULT 0,
  current_streak_type TEXT, -- 'win', 'loss', 'neutral'
  
  -- Риск-менеджмент
  avg_rrr DECIMAL(10,4) DEFAULT 0,
  min_rrr DECIMAL(10,4) DEFAULT 0,
  max_rrr DECIMAL(10,4) DEFAULT 0,
  adequate_rrr_rate DECIMAL(10,4) DEFAULT 0, -- % signals with RRR > 1.5
  
  -- Временные паттерны  
  avg_signal_frequency_per_day DECIMAL(10,4) DEFAULT 0,
  best_day_of_week TEXT,
  best_hour_of_day INTEGER,
  avg_duration_minutes INTEGER DEFAULT 0,
  
  -- Символы и рынки
  symbols_traded_count INTEGER DEFAULT 0,
  most_profitable_symbol TEXT,
  symbols_data JSONB, -- {"BTCUSDT": {"count": 10, "winrate": 80, "roi": 5.2}}
  
  -- Рейтинг и классификация
  trust_index DECIMAL(10,4) DEFAULT 0, -- 0-100
  reliability_score DECIMAL(10,4) DEFAULT 0, -- 0-100  
  risk_score DECIMAL(10,4) DEFAULT 0, -- 0-100 (higher = riskier)
  trader_grade TEXT DEFAULT 'C', -- A, B, C, D
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  UNIQUE(trader_id, period_type, period_start, period_end)
);

-- =====================================================
-- 5. РЕЙТИНГИ И СРАВНИТЕЛЬНЫЙ АНАЛИЗ
-- =====================================================
CREATE TABLE IF NOT EXISTS trader_rankings (
  id SERIAL PRIMARY KEY,
  period_type TEXT NOT NULL, -- 'weekly', 'monthly', 'quarterly'
  period_start DATE NOT NULL,
  period_end DATE NOT NULL,
  
  trader_id TEXT REFERENCES trader_registry(trader_id),
  
  -- Позиции в рейтингах
  overall_rank INTEGER,
  roi_rank INTEGER, 
  winrate_rank INTEGER,
  consistency_rank INTEGER,
  risk_adjusted_rank INTEGER,
  
  -- Баллы по категориям (0-100)
  performance_score DECIMAL(10,4) DEFAULT 0,
  consistency_score DECIMAL(10,4) DEFAULT 0,
  risk_management_score DECIMAL(10,4) DEFAULT 0,
  reliability_score DECIMAL(10,4) DEFAULT 0,
  
  -- Итоговый композитный рейтинг
  composite_score DECIMAL(10,4) DEFAULT 0,
  grade TEXT DEFAULT 'C',
  
  -- Сравнение с предыдущим периодом
  rank_change INTEGER DEFAULT 0, -- +/- change from previous period
  score_change DECIMAL(10,4) DEFAULT 0,
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  
  UNIQUE(trader_id, period_type, period_start, period_end)
);

-- =====================================================
-- 6. ВРЕМЕННЫЕ ПАТТЕРНЫ И HEATMAP
-- =====================================================
CREATE TABLE IF NOT EXISTS trader_time_patterns (
  id SERIAL PRIMARY KEY,
  trader_id TEXT REFERENCES trader_registry(trader_id),
  
  -- Время публикации
  hour_of_day INTEGER NOT NULL, -- 0-23
  day_of_week INTEGER NOT NULL, -- 1-7 (Monday=1)
  
  -- Статистика за этот временной слот
  signals_count INTEGER DEFAULT 0,
  avg_roi DECIMAL(10,4) DEFAULT 0,
  winrate DECIMAL(10,4) DEFAULT 0,
  avg_duration_minutes INTEGER DEFAULT 0,
  
  -- Период анализа
  period_start DATE NOT NULL,
  period_end DATE NOT NULL,
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  UNIQUE(trader_id, hour_of_day, day_of_week, period_start, period_end)
);

-- =====================================================
-- ИНДЕКСЫ ДЛЯ ПРОИЗВОДИТЕЛЬНОСТИ
-- =====================================================

-- Validation errors
CREATE INDEX IF NOT EXISTS idx_validation_errors_trader_id ON signal_validation_errors(trader_id);
CREATE INDEX IF NOT EXISTS idx_validation_errors_category ON signal_validation_errors(error_category);
CREATE INDEX IF NOT EXISTS idx_validation_errors_type ON signal_validation_errors(error_type);

-- Daily stats
CREATE INDEX IF NOT EXISTS idx_daily_stats_trader_date ON trader_stats_daily(trader_id, date);
CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON trader_stats_daily(date);

-- Performance metrics
CREATE INDEX IF NOT EXISTS idx_performance_trader_period ON trader_performance_metrics(trader_id, period_type);
CREATE INDEX IF NOT EXISTS idx_performance_period_dates ON trader_performance_metrics(period_start, period_end);

-- Rankings
CREATE INDEX IF NOT EXISTS idx_rankings_period ON trader_rankings(period_type, period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_rankings_scores ON trader_rankings(composite_score DESC);

-- Time patterns
CREATE INDEX IF NOT EXISTS idx_time_patterns_trader ON trader_time_patterns(trader_id);
CREATE INDEX IF NOT EXISTS idx_time_patterns_time ON trader_time_patterns(hour_of_day, day_of_week);

-- Behavioral patterns
CREATE INDEX IF NOT EXISTS idx_behavioral_trader ON trader_behavioral_patterns(trader_id);
CREATE INDEX IF NOT EXISTS idx_behavioral_type ON trader_behavioral_patterns(pattern_type);
