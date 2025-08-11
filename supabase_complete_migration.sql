-- GHOST Supabase Complete Migration
-- Полная миграция таблицы trades на основе схемы Дарэна
-- Выполните этот код в SQL Editor в Supabase Dashboard

-- Сначала удаляем существующую таблицу если она есть
DROP TABLE IF EXISTS trades CASCADE;

-- Создаем полную таблицу trades со всеми полями из схемы Дарэна
CREATE TABLE trades (
    -- Основные идентификаторы
    id TEXT PRIMARY KEY,
    trade_id TEXT,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Информация о сделке
    symbol TEXT,
    side TEXT CHECK (side IN ('LONG', 'SHORT')),
    leverage INTEGER,
    source TEXT,
    source_type TEXT,
    source_name TEXT,
    source_id INTEGER,
    
    -- Вход в позицию
    entry_zone TEXT,
    entry_type TEXT,
    entry_exec_price DECIMAL(20,8),
    entry DECIMAL(20,8),
    fill_type TEXT,
    
    -- Целевые цены и стоп-лосс
    tp1 DECIMAL(20,8),
    tp2 DECIMAL(20,8),
    tp3 DECIMAL(20,8),
    sl DECIMAL(20,8),
    tp1_price DECIMAL(20,8),
    tp2_price DECIMAL(20,8),
    sl_price DECIMAL(20,8),
    
    -- Автоматические расчеты
    tp1_auto_calc DECIMAL(20,8),
    sl_auto_calc DECIMAL(20,8),
    sl_type TEXT,
    
    -- Реальные цены исполнения
    real_entry_price DECIMAL(20,8),
    position_qty DECIMAL(20,8),
    margin_usd DECIMAL(20,8),
    
    -- Анализ и решения
    verdict_reason TEXT,
    signal_reason TEXT,
    note TEXT,
    gpt_comment TEXT,
    
    -- Временные метки
    opened_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    exit_time TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    
    -- Расчеты и метрики
    real_leverage DECIMAL(20,8),
    margin_used DECIMAL(20,8),
    entry_min DECIMAL(20,8),
    entry_max DECIMAL(20,8),
    avg_entry_price DECIMAL(20,8),
    entry_method TEXT,
    risk_pct DECIMAL(10,4),
    source_leverage TEXT,
    raw_symbol TEXT,
    
    -- Цели и веса
    targets TEXT,
    tp_weights TEXT,
    original_text TEXT,
    
    -- Выход из позиции
    exit_reason TEXT,
    roi_percent DECIMAL(10,4),
    verdict TEXT,
    exit_trigger_type TEXT,
    exit_trigger_value TEXT,
    ghost_exit_score DECIMAL(10,4),
    
    -- Исполнение ордеров
    order_id TEXT,
    execution_type TEXT,
    fill_status TEXT,
    avg_fill_price DECIMAL(20,8),
    fee_rate DECIMAL(10,4),
    fee_paid DECIMAL(20,8),
    
    -- Стратегия и консенсус
    model_id TEXT,
    strategy_version TEXT,
    strategy_id TEXT,
    signal_sequence INTEGER,
    consensus_score DECIMAL(10,4),
    consensus_sources TEXT,
    status TEXT,
    
    -- P&L и ROI
    realized_pnl DECIMAL(20,8),
    exit DECIMAL(20,8),
    finalized BOOLEAN DEFAULT FALSE,
    roi_planned DECIMAL(10,4),
    pnl_gross DECIMAL(20,8),
    pnl_net DECIMAL(20,8),
    roi_gross DECIMAL(10,4),
    
    -- Bybit данные
    entry_price_bybit DECIMAL(20,8),
    exit_price_bybit DECIMAL(20,8),
    exit_price_fallback DECIMAL(20,8),
    roi_percent_bybit DECIMAL(10,4),
    roi_estimated DECIMAL(10,4),
    
    -- Проскальзывание и задержки
    entry_slippage DECIMAL(10,4),
    exit_slippage DECIMAL(10,4),
    entry_latency_ms INTEGER,
    exit_latency_ms INTEGER,
    
    -- Источники данных
    data_source_mode TEXT,
    weekday INTEGER,
    weekday_name TEXT,
    opened_at_full TEXT,
    
    -- Комиссии
    bybit_fee_open DECIMAL(20,8),
    bybit_fee_close DECIMAL(20,8),
    bybit_fee_total DECIMAL(20,8),
    bybit_pnl_net DECIMAL(20,8),
    commission_over_roi DECIMAL(10,4),
    
    -- Анализ и флаги
    loss_type TEXT,
    anomaly_flag BOOLEAN DEFAULT FALSE,
    bybit_pnl_net_api DECIMAL(20,8),
    bybit_pnl_net_fallback DECIMAL(20,8),
    
    -- ID ордеров
    order_id_exit TEXT,
    signal_id TEXT,
    tp1_order_id TEXT,
    tp2_order_id TEXT,
    sl_order_id TEXT,
    
    -- Управление стоп-лоссом
    sl_be_moved BOOLEAN DEFAULT FALSE,
    sl_be_method TEXT,
    sl_be_price DECIMAL(20,8),
    sl_to_be INTEGER DEFAULT 0,
    
    -- Восстановление TP2
    tp2_restore_attempted BOOLEAN DEFAULT FALSE,
    tp2_restore_attempts INTEGER DEFAULT 0,
    tp2_order_id_current TEXT,
    tp2_order_id_history TEXT,
    tp2_exit_type TEXT,
    
    -- Текущие ID ордеров
    sl_order_id_current TEXT,
    sl_order_id_history TEXT,
    
    -- P&L по целям
    pnl_tp1 DECIMAL(20,8),
    pnl_tp2 DECIMAL(20,8),
    roi_tp1 DECIMAL(10,4),
    roi_tp2 DECIMAL(10,4),
    roi_final_real DECIMAL(10,4),
    pnl_final_real DECIMAL(20,8),
    
    -- Прибыль по целям
    profit_tp1_real DECIMAL(20,8),
    profit_tp2_real DECIMAL(20,8),
    expected_profit_tp1 DECIMAL(20,8),
    expected_profit_tp2 DECIMAL(20,8),
    expected_profit_total DECIMAL(20,8),
    
    -- Комиссии по целям
    fee_tp1 DECIMAL(20,8),
    fee_tp2 DECIMAL(20,8),
    pnl_tp1_net DECIMAL(20,8),
    pnl_tp2_net DECIMAL(20,8),
    
    -- ROI по целям
    roi_tp1_real DECIMAL(10,4),
    roi_tp2_real DECIMAL(10,4),
    roi_sl_real DECIMAL(10,4),
    roi_sl_expected DECIMAL(10,4),
    
    -- Время достижения целей
    tp1_hit_time TIMESTAMPTZ,
    tp2_hit_time TIMESTAMPTZ,
    sl_hit_time TIMESTAMPTZ,
    
    -- Длительность
    duration_sec INTEGER,
    tp1_duration_sec INTEGER,
    tp2_duration_sec INTEGER,
    sl_duration_sec INTEGER,
    
    -- Флаги достижения целей
    tp1_hit BOOLEAN DEFAULT FALSE,
    tp2_hit BOOLEAN DEFAULT FALSE,
    sl_hit BOOLEAN DEFAULT FALSE,
    tp_count_hit INTEGER DEFAULT 0,
    
    -- Ранний выход
    early_exit BOOLEAN DEFAULT FALSE,
    early_exit_reason TEXT,
    exit_explanation TEXT,
    exit_ai_score DECIMAL(10,4),
    
    -- Ручное управление
    manual_exit INTEGER DEFAULT 0,
    manual_exit_type TEXT,
    
    -- Источники P&L
    pnl_source TEXT,
    roi_source TEXT,
    
    -- Fills данные
    raw_fills_count INTEGER,
    fills_legA TEXT,
    fills_legB TEXT,
    fills_legA_vwap DECIMAL(20,8),
    fills_legB_vwap DECIMAL(20,8),
    fills_legA_qty DECIMAL(20,8),
    fills_legB_qty DECIMAL(20,8),
    fills_legA_fee DECIMAL(20,8),
    fills_legB_fee DECIMAL(20,8),
    fills_legA_fee_in DECIMAL(20,8),
    fills_legB_fee_in DECIMAL(20,8),
    
    -- Дополнительные поля
    leverage_used_expected DECIMAL(20,8),
    
    -- Дополнительные поля из схемы Дарэна
    tp_hit TEXT,
    exit_detail TEXT,
    roi_ui DECIMAL(10,4),
    pnl_net_initial DECIMAL(20,8),
    roi_percent_initial DECIMAL(10,4),
    roi_bybit_style DECIMAL(10,4),
    
    -- Недостающие поля для полного покрытия
    expected_loss_sl DECIMAL(20,8),
    order_id_exit_fallback TEXT,
    
    -- Временные метки создания/обновления
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Создание индексов для оптимизации
CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trades(user_id);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);
CREATE INDEX IF NOT EXISTS idx_trades_opened_at ON trades(opened_at);
CREATE INDEX IF NOT EXISTS idx_trades_trade_id ON trades(trade_id);
CREATE INDEX IF NOT EXISTS idx_trades_source ON trades(source);
CREATE INDEX IF NOT EXISTS idx_trades_source_name ON trades(source_name);
CREATE INDEX IF NOT EXISTS idx_trades_side ON trades(side);
CREATE INDEX IF NOT EXISTS idx_trades_leverage ON trades(leverage);
CREATE INDEX IF NOT EXISTS idx_trades_entry_price ON trades(entry);
CREATE INDEX IF NOT EXISTS idx_trades_exit_price ON trades(exit);
CREATE INDEX IF NOT EXISTS idx_trades_roi_percent ON trades(roi_percent);
CREATE INDEX IF NOT EXISTS idx_trades_pnl_net ON trades(pnl_net);
CREATE INDEX IF NOT EXISTS idx_trades_verdict ON trades(verdict);
CREATE INDEX IF NOT EXISTS idx_trades_strategy_id ON trades(strategy_id);
CREATE INDEX IF NOT EXISTS idx_trades_model_id ON trades(model_id);
CREATE INDEX IF NOT EXISTS idx_trades_weekday ON trades(weekday);
CREATE INDEX IF NOT EXISTS idx_trades_anomaly_flag ON trades(anomaly_flag);
CREATE INDEX IF NOT EXISTS idx_trades_tp1_hit ON trades(tp1_hit);
CREATE INDEX IF NOT EXISTS idx_trades_tp2_hit ON trades(tp2_hit);
CREATE INDEX IF NOT EXISTS idx_trades_sl_hit ON trades(sl_hit);
CREATE INDEX IF NOT EXISTS idx_trades_early_exit ON trades(early_exit);
CREATE INDEX IF NOT EXISTS idx_trades_manual_exit ON trades(manual_exit);
CREATE INDEX IF NOT EXISTS idx_trades_tp_hit ON trades(tp_hit);
CREATE INDEX IF NOT EXISTS idx_trades_exit_detail ON trades(exit_detail);
CREATE INDEX IF NOT EXISTS idx_trades_roi_ui ON trades(roi_ui);
CREATE INDEX IF NOT EXISTS idx_trades_pnl_net_initial ON trades(pnl_net_initial);
CREATE INDEX IF NOT EXISTS idx_trades_roi_percent_initial ON trades(roi_percent_initial);
CREATE INDEX IF NOT EXISTS idx_trades_roi_bybit_style ON trades(roi_bybit_style);
CREATE INDEX IF NOT EXISTS idx_trades_expected_loss_sl ON trades(expected_loss_sl);
CREATE INDEX IF NOT EXISTS idx_trades_order_id_exit_fallback ON trades(order_id_exit_fallback);

-- Включение Row Level Security (RLS)
ALTER TABLE trades ENABLE ROW LEVEL SECURITY;

-- Создание политик безопасности
CREATE POLICY "Users can view own trades" ON trades
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own trades" ON trades
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own trades" ON trades
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own trades" ON trades
    FOR DELETE USING (auth.uid() = user_id);

-- Создание триггера для обновления updated_at
CREATE OR REPLACE FUNCTION update_trades_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_trades_updated_at 
    BEFORE UPDATE ON trades 
    FOR EACH ROW EXECUTE FUNCTION update_trades_updated_at();

-- Создание представлений
CREATE OR REPLACE VIEW active_positions AS
SELECT * FROM trades 
WHERE status != 'CLOSED' AND finalized = FALSE;

CREATE OR REPLACE VIEW closed_trades AS
SELECT * FROM trades 
WHERE status = 'CLOSED' OR finalized = TRUE;

-- Создание функции для статистики по символам
CREATE OR REPLACE FUNCTION get_symbol_stats(symbol_param TEXT)
RETURNS TABLE(
    total_trades BIGINT,
    winning_trades BIGINT,
    losing_trades BIGINT,
    avg_roi DECIMAL,
    total_pnl DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_trades,
        COUNT(CASE WHEN roi_percent > 0 THEN 1 END)::BIGINT as winning_trades,
        COUNT(CASE WHEN roi_percent < 0 THEN 1 END)::BIGINT as losing_trades,
        AVG(roi_percent) as avg_roi,
        SUM(pnl_net) as total_pnl
    FROM trades 
    WHERE symbol = symbol_param AND finalized = TRUE;
END;
$$ LANGUAGE plpgsql;

-- Создание функции для поиска сделок
CREATE OR REPLACE FUNCTION search_trades(search_query TEXT, user_id_param UUID DEFAULT NULL)
RETURNS TABLE(
    id TEXT,
    symbol TEXT,
    side TEXT,
    roi_percent DECIMAL,
    pnl_net DECIMAL,
    status TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.id,
        t.symbol,
        t.side,
        t.roi_percent,
        t.pnl_net,
        t.status
    FROM trades t
    WHERE (
        t.symbol ILIKE '%' || search_query || '%' OR
        t.note ILIKE '%' || search_query || '%' OR
        t.verdict_reason ILIKE '%' || search_query || '%'
    )
    AND (user_id_param IS NULL OR t.user_id = user_id_param)
    ORDER BY t.opened_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Создание полнотекстового поиска
CREATE INDEX IF NOT EXISTS idx_trades_fts ON trades USING gin(
    to_tsvector('english', 
        COALESCE(symbol, '') || ' ' ||
        COALESCE(note, '') || ' ' ||
        COALESCE(verdict_reason, '') || ' ' ||
        COALESCE(signal_reason, '')
    )
);

-- Добавляем комментарии к таблице
COMMENT ON TABLE trades IS 'Complete trades table with all fields from Darrin schema';
COMMENT ON COLUMN trades.tp_hit IS 'Which take profit was hit (TP1, TP2, etc.)';
COMMENT ON COLUMN trades.exit_detail IS 'Detailed exit information';
COMMENT ON COLUMN trades.roi_ui IS 'ROI for UI display';
COMMENT ON COLUMN trades.pnl_net_initial IS 'Initial net P&L';
COMMENT ON COLUMN trades.roi_percent_initial IS 'Initial ROI percentage';
COMMENT ON COLUMN trades.roi_bybit_style IS 'ROI calculated in Bybit style';

-- Проверяем что все поля созданы
SELECT 'Migration completed successfully. Total columns in trades table: ' || 
       COUNT(*)::TEXT as migration_status
FROM information_schema.columns 
WHERE table_name = 'trades';
