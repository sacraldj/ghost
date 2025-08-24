-- ДОПОЛНЕНИЕ СИСТЕМЫ: Добавляем аналитику трейдеров
-- ⚠️ НЕ ТРОГАЕМ СУЩЕСТВУЮЩИЕ ТАБЛИЦЫ!
-- ✅ Только ДОБАВЛЯЕМ новые для расширенной аналитики

-- =====================================================
-- 1. РАСШИРЕННАЯ СТАТИСТИКА ТРЕЙДЕРОВ (базовая)
-- =====================================================
CREATE TABLE IF NOT EXISTS trader_analytics (
  id SERIAL PRIMARY KEY,
  trader_id TEXT NOT NULL, -- ссылка на trader_registry.trader_id
  
  -- Основные метрики (на основе v_trades)
  total_signals INTEGER DEFAULT 0,
  valid_signals INTEGER DEFAULT 0,
  executed_signals INTEGER DEFAULT 0,
  
  -- Результативность
  winrate DECIMAL(10,4) DEFAULT 0,        -- %
  tp1_rate DECIMAL(10,4) DEFAULT 0,       -- %
  tp2_rate DECIMAL(10,4) DEFAULT 0,       -- %
  sl_rate DECIMAL(10,4) DEFAULT 0,        -- %
  
  -- Финансовые метрики
  total_pnl DECIMAL(20,8) DEFAULT 0,
  avg_roi DECIMAL(10,4) DEFAULT 0,        -- %
  best_roi DECIMAL(10,4) DEFAULT 0,       -- %
  worst_roi DECIMAL(10,4) DEFAULT 0,      -- %
  
  -- Риск-менеджмент
  avg_rrr DECIMAL(10,4) DEFAULT 0,        -- Risk/Reward Ratio
  max_drawdown DECIMAL(10,4) DEFAULT 0,   -- %
  consistency_score DECIMAL(10,4) DEFAULT 0, -- 0-100
  
  -- НОВЫЕ МЕТРИКИ: Trust Index и Grade
  trust_index DECIMAL(10,4) DEFAULT 0,    -- 0-100
  grade TEXT DEFAULT 'C',                 -- A, B, C, D
  risk_score DECIMAL(10,4) DEFAULT 50,    -- 0-100 (higher = riskier)
  
  -- Рейтинги
  overall_rank INTEGER DEFAULT 999,
  rank_change INTEGER DEFAULT 0,          -- +/- from previous period
  
  -- Периоды расчета
  period_start DATE DEFAULT CURRENT_DATE - INTERVAL '30 days',
  period_end DATE DEFAULT CURRENT_DATE,
  
  -- Метки времени
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  -- Уникальный constraint по trader_id (один record на трейдера)
  UNIQUE(trader_id)
);

-- =====================================================
-- 2. ОШИБКИ ВАЛИДАЦИИ (детальная классификация)  
-- =====================================================
CREATE TABLE IF NOT EXISTS signal_errors (
  id SERIAL PRIMARY KEY,
  trader_id TEXT NOT NULL,
  signal_id TEXT,                         -- ссылка на v_trades.id если есть
  
  -- Классификация ошибки
  error_category TEXT NOT NULL,           -- 'logic', 'technical', 'market', 'format'
  error_type TEXT NOT NULL,               -- 'tp_below_entry', 'missing_sl', 'invalid_symbol'
  error_message TEXT,
  severity TEXT DEFAULT 'medium',         -- 'low', 'medium', 'high', 'critical'
  
  -- Метки времени
  detected_at TIMESTAMPTZ DEFAULT NOW(),
  signal_posted_at TIMESTAMPTZ,
  
  -- Дополнительные данные
  meta_data JSONB                         -- любая дополнительная информация
);

-- =====================================================
-- 3. ВРЕМЕННЫЕ ПАТТЕРНЫ (для heatmap)
-- =====================================================
CREATE TABLE IF NOT EXISTS trader_time_stats (
  id SERIAL PRIMARY KEY,
  trader_id TEXT NOT NULL,
  
  -- Время публикации (UTC)
  hour_of_day INTEGER NOT NULL,           -- 0-23
  day_of_week INTEGER NOT NULL,           -- 1-7 (Monday=1)
  
  -- Статистика за этот временной слот
  signals_count INTEGER DEFAULT 0,
  avg_roi DECIMAL(10,4) DEFAULT 0,
  success_rate DECIMAL(10,4) DEFAULT 0,   -- % successful signals
  
  -- Период анализа
  analysis_period TEXT DEFAULT '30d',     -- '7d', '30d', '90d'
  last_updated TIMESTAMPTZ DEFAULT NOW(),
  
  -- Уникальный constraint
  UNIQUE(trader_id, hour_of_day, day_of_week, analysis_period)
);

-- =====================================================
-- 4. ПОВЕДЕНЧЕСКИЕ ФЛАГИ (простые)
-- =====================================================
CREATE TABLE IF NOT EXISTS trader_behavior_flags (
  id SERIAL PRIMARY KEY,
  trader_id TEXT NOT NULL,
  
  -- Флаги поведения
  has_duplicates BOOLEAN DEFAULT FALSE,
  has_contradictions BOOLEAN DEFAULT FALSE,
  suspected_copy_paste BOOLEAN DEFAULT FALSE,
  
  -- Скоры (0-100)
  duplicate_score INTEGER DEFAULT 0,
  contradiction_score INTEGER DEFAULT 0,
  copy_paste_score INTEGER DEFAULT 0,
  
  -- Детали (JSON)
  behavior_details JSONB,
  
  -- Метки времени
  last_analyzed TIMESTAMPTZ DEFAULT NOW(),
  detection_period TEXT DEFAULT '30d',
  
  UNIQUE(trader_id)
);

-- =====================================================
-- 5. ИНДЕКСЫ ДЛЯ ПРОИЗВОДИТЕЛЬНОСТИ
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_trader_analytics_trader_id ON trader_analytics(trader_id);
CREATE INDEX IF NOT EXISTS idx_trader_analytics_grade ON trader_analytics(grade);
CREATE INDEX IF NOT EXISTS idx_trader_analytics_trust_index ON trader_analytics(trust_index DESC);
CREATE INDEX IF NOT EXISTS idx_trader_analytics_rank ON trader_analytics(overall_rank);

CREATE INDEX IF NOT EXISTS idx_signal_errors_trader_id ON signal_errors(trader_id);
CREATE INDEX IF NOT EXISTS idx_signal_errors_category ON signal_errors(error_category);
CREATE INDEX IF NOT EXISTS idx_signal_errors_detected_at ON signal_errors(detected_at);

CREATE INDEX IF NOT EXISTS idx_time_stats_trader_id ON trader_time_stats(trader_id);
CREATE INDEX IF NOT EXISTS idx_time_stats_time ON trader_time_stats(hour_of_day, day_of_week);

CREATE INDEX IF NOT EXISTS idx_behavior_flags_trader_id ON trader_behavior_flags(trader_id);

-- =====================================================
-- 6. ИНИЦИАЛИЗАЦИЯ: Заполняем данные для существующих трейдеров
-- =====================================================

-- Создаем базовые записи для всех существующих трейдеров
INSERT INTO trader_analytics (trader_id, trust_index, grade, total_signals)
SELECT 
  trader_id,
  50 as trust_index,           -- начальное значение
  'C' as grade,                -- начальный grade
  0 as total_signals
FROM trader_registry 
WHERE is_active = true
ON CONFLICT (trader_id) DO NOTHING;

-- Создаем базовые поведенческие флаги
INSERT INTO trader_behavior_flags (trader_id)
SELECT trader_id
FROM trader_registry 
WHERE is_active = true
ON CONFLICT (trader_id) DO NOTHING;

-- =====================================================
-- 7. ФУНКЦИЯ ДЛЯ ПЕРЕСЧЕТА БАЗОВЫХ МЕТРИК
-- =====================================================
CREATE OR REPLACE FUNCTION update_trader_basic_analytics(target_trader_id TEXT DEFAULT NULL)
RETURNS void AS $$
DECLARE
    trader_record RECORD;
    total_signals_count INTEGER;
    valid_signals_count INTEGER;
    executed_count INTEGER;
    win_count INTEGER;
    total_pnl_sum DECIMAL(20,8);
    calculated_winrate DECIMAL(10,4);
    calculated_avg_roi DECIMAL(10,4);
    calculated_trust_index DECIMAL(10,4);
    calculated_grade TEXT;
BEGIN
    -- Обрабатываем либо конкретного трейдера, либо всех
    FOR trader_record IN 
        SELECT trader_id FROM trader_registry 
        WHERE is_active = true 
        AND (target_trader_id IS NULL OR trader_id = target_trader_id)
    LOOP
        -- Считаем статистику из v_trades
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN status = 'sim_open' THEN 1 END) as executed,
            COUNT(CASE WHEN tp1_hit = true OR tp2_hit = true THEN 1 END) as wins,
            COALESCE(SUM(pnl_gross), 0) as total_pnl
        INTO total_signals_count, executed_count, win_count, total_pnl_sum
        FROM v_trades 
        WHERE source = trader_record.trader_id;
        
        -- Рассчитываем метрики
        calculated_winrate := CASE 
            WHEN executed_count > 0 THEN (win_count::DECIMAL / executed_count::DECIMAL) * 100 
            ELSE 0 
        END;
        
        calculated_avg_roi := CASE 
            WHEN executed_count > 0 THEN total_pnl_sum / executed_count 
            ELSE 0 
        END;
        
        -- Простой расчет Trust Index (0-100)
        calculated_trust_index := LEAST(100, GREATEST(0, 
            (calculated_winrate * 0.4) +                    -- 40% winrate  
            (LEAST(100, calculated_avg_roi + 50) * 0.3) +   -- 30% ROI (центрируем вокруг 0)
            (LEAST(100, total_signals_count) * 0.2) +       -- 20% activity
            (10)                                             -- 10% base score
        ));
        
        -- Присваиваем Grade
        calculated_grade := CASE
            WHEN calculated_trust_index >= 80 THEN 'A'
            WHEN calculated_trust_index >= 60 THEN 'B' 
            WHEN calculated_trust_index >= 40 THEN 'C'
            ELSE 'D'
        END;
        
        -- Обновляем trader_analytics
        UPDATE trader_analytics 
        SET 
            total_signals = total_signals_count,
            executed_signals = executed_count,
            winrate = calculated_winrate,
            total_pnl = total_pnl_sum,
            avg_roi = calculated_avg_roi,
            trust_index = calculated_trust_index,
            grade = calculated_grade,
            updated_at = NOW()
        WHERE trader_id = trader_record.trader_id;
        
    END LOOP;
    
    -- Обновляем рейтинги
    WITH ranked_traders AS (
        SELECT trader_id, 
               ROW_NUMBER() OVER (ORDER BY trust_index DESC) as new_rank
        FROM trader_analytics
    )
    UPDATE trader_analytics ta
    SET overall_rank = rt.new_rank
    FROM ranked_traders rt
    WHERE ta.trader_id = rt.trader_id;
    
END;
$$ LANGUAGE plpgsql;

-- Запускаем первичный расчет для всех трейдеров
SELECT update_trader_basic_analytics();
