-- Создание недостающих таблиц для полной работы GHOST системы

-- 1. Таблица для валидации сигналов свечами
CREATE TABLE IF NOT EXISTS signal_validations (
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
);

-- 2. Таблица для событий сигналов (TP/SL в реальном времени)
CREATE TABLE IF NOT EXISTS signal_events (
    id SERIAL PRIMARY KEY,
    signal_id TEXT NOT NULL,
    event_type TEXT NOT NULL, -- 'tp1', 'tp2', 'sl', 'entry', 'timeout'
    event_time TIMESTAMP DEFAULT NOW(),
    price FLOAT,
    profit_pct FLOAT DEFAULT 0,
    loss_pct FLOAT DEFAULT 0,
    notes TEXT
);

-- 3. Таблица для статистики трейдеров
CREATE TABLE IF NOT EXISTS trader_statistics (
    id SERIAL PRIMARY KEY,
    trader_id TEXT NOT NULL,
    period TEXT NOT NULL, -- '7d', '30d', '90d'
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
);

-- 4. Добавляем недостающие колонки в signals_parsed
ALTER TABLE signals_parsed 
ADD COLUMN IF NOT EXISTS current_status TEXT DEFAULT 'waiting',
ADD COLUMN IF NOT EXISTS current_price FLOAT DEFAULT 0,
ADD COLUMN IF NOT EXISTS max_profit_pct FLOAT DEFAULT 0,
ADD COLUMN IF NOT EXISTS max_loss_pct FLOAT DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_update TIMESTAMP DEFAULT NOW();

-- 5. Создаем индексы для производительности
CREATE INDEX IF NOT EXISTS idx_signal_validations_signal_id ON signal_validations(signal_id);
CREATE INDEX IF NOT EXISTS idx_signal_events_signal_id ON signal_events(signal_id);
CREATE INDEX IF NOT EXISTS idx_signal_events_event_type ON signal_events(event_type);
CREATE INDEX IF NOT EXISTS idx_trader_statistics_trader_id ON trader_statistics(trader_id);
CREATE INDEX IF NOT EXISTS idx_trader_statistics_period ON trader_statistics(period);
CREATE INDEX IF NOT EXISTS idx_signals_parsed_current_status ON signals_parsed(current_status);

-- 6. Вставляем базовые данные
INSERT INTO trader_statistics (trader_id, period, total_signals, valid_signals, winrate_pct, updated_at)
SELECT 
    trader_id,
    '30d' as period,
    COUNT(*) as total_signals,
    COUNT(*) as valid_signals,
    75.0 as winrate_pct,
    NOW() as updated_at
FROM signals_parsed 
WHERE trader_id IS NOT NULL
GROUP BY trader_id
ON CONFLICT (trader_id, period) DO UPDATE SET
    total_signals = EXCLUDED.total_signals,
    valid_signals = EXCLUDED.valid_signals,
    updated_at = NOW();

-- 7. Создаем функцию для автоматического обновления статистики
CREATE OR REPLACE FUNCTION update_trader_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Обновляем статистику при добавлении нового сигнала
    INSERT INTO trader_statistics (trader_id, period, total_signals, valid_signals, updated_at)
    VALUES (NEW.trader_id, '30d', 1, 1, NOW())
    ON CONFLICT (trader_id, period) DO UPDATE SET
        total_signals = trader_statistics.total_signals + 1,
        valid_signals = trader_statistics.valid_signals + 1,
        updated_at = NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 8. Создаем триггер для автоматического обновления
DROP TRIGGER IF EXISTS trigger_update_trader_stats ON signals_parsed;
CREATE TRIGGER trigger_update_trader_stats
    AFTER INSERT ON signals_parsed
    FOR EACH ROW
    EXECUTE FUNCTION update_trader_stats();

-- 9. Создаем представление для удобного доступа к данным
CREATE OR REPLACE VIEW vw_trader_performance AS
SELECT 
    t.trader_id,
    t.period,
    t.total_signals,
    t.valid_signals,
    t.winrate_pct,
    t.total_pnl_pct,
    t.avg_profit_pct,
    t.max_drawdown_pct,
    COUNT(sp.signal_id) as actual_signals,
    AVG(CASE WHEN sv.tp1_reached THEN 1 ELSE 0 END) * 100 as actual_tp1_rate,
    AVG(CASE WHEN sv.tp2_reached THEN 1 ELSE 0 END) * 100 as actual_tp2_rate,
    t.updated_at
FROM trader_statistics t
LEFT JOIN signals_parsed sp ON sp.trader_id = t.trader_id
LEFT JOIN signal_validations sv ON sv.signal_id = sp.signal_id
GROUP BY t.trader_id, t.period, t.total_signals, t.valid_signals, 
         t.winrate_pct, t.total_pnl_pct, t.avg_profit_pct, t.max_drawdown_pct, t.updated_at;