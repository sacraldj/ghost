-- GHOST Supabase Complete Safe Migration
-- Безопасное добавление ВСЕХ недостающих полей из схемы Дарэна
-- Выполните этот код в SQL Editor в Supabase Dashboard

-- Сначала проверяем текущую схему
SELECT 'Current schema check - Total columns: ' || 
       COUNT(*)::TEXT as current_status
FROM information_schema.columns 
WHERE table_name = 'trades';

-- ========================================
-- ДОБАВЛЯЕМ ВСЕ ПОЛЯ ИЗ СХЕМЫ ДАРЭНА
-- ========================================

-- Основные идентификаторы и информация о сделке
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS trade_id TEXT,
ADD COLUMN IF NOT EXISTS source_type TEXT,
ADD COLUMN IF NOT EXISTS source_name TEXT,
ADD COLUMN IF NOT EXISTS source_id INTEGER;

-- Вход в позицию
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS entry_zone TEXT,
ADD COLUMN IF NOT EXISTS entry_type TEXT,
ADD COLUMN IF NOT EXISTS entry_exec_price DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS fill_type TEXT;

-- Целевые цены и стоп-лосс
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS tp1 DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS tp2 DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS tp3 DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS sl DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS tp1_price DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS tp2_price DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS sl_price DECIMAL(20,8);

-- Автоматические расчеты
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS tp1_auto_calc DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS sl_auto_calc DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS sl_type TEXT;

-- Реальные цены исполнения
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS real_entry_price DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS position_qty DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS margin_usd DECIMAL(20,8);

-- Анализ и решения
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS verdict_reason TEXT,
ADD COLUMN IF NOT EXISTS signal_reason TEXT,
ADD COLUMN IF NOT EXISTS gpt_comment TEXT;

-- Временные метки
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS opened_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS exit_time TIMESTAMP,
ADD COLUMN IF NOT EXISTS closed_at TIMESTAMP;

-- Расчеты и метрики
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS real_leverage DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS margin_used DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS entry_min DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS entry_max DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS avg_entry_price DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS entry_method TEXT,
ADD COLUMN IF NOT EXISTS risk_pct DECIMAL(10,4),
ADD COLUMN IF NOT EXISTS source_leverage TEXT,
ADD COLUMN IF NOT EXISTS raw_symbol TEXT;

-- Цели и веса
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS targets TEXT,
ADD COLUMN IF NOT EXISTS tp_weights TEXT,
ADD COLUMN IF NOT EXISTS original_text TEXT;

-- Выход из позиции
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS exit_reason TEXT,
ADD COLUMN IF NOT EXISTS roi_percent DECIMAL(10,4),
ADD COLUMN IF NOT EXISTS verdict TEXT,
ADD COLUMN IF NOT EXISTS exit_trigger_type TEXT,
ADD COLUMN IF NOT EXISTS exit_trigger_value TEXT,
ADD COLUMN IF NOT EXISTS ghost_exit_score DECIMAL(10,4);

-- Исполнение ордеров
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS order_id TEXT,
ADD COLUMN IF NOT EXISTS execution_type TEXT,
ADD COLUMN IF NOT EXISTS fill_status TEXT,
ADD COLUMN IF NOT EXISTS avg_fill_price DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS fee_rate DECIMAL(10,4),
ADD COLUMN IF NOT EXISTS fee_paid DECIMAL(20,8);

-- Стратегия и консенсус
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS model_id TEXT,
ADD COLUMN IF NOT EXISTS strategy_version TEXT,
ADD COLUMN IF NOT EXISTS strategy_id TEXT,
ADD COLUMN IF NOT EXISTS signal_sequence INTEGER,
ADD COLUMN IF NOT EXISTS consensus_score DECIMAL(10,4),
ADD COLUMN IF NOT EXISTS consensus_sources TEXT,
ADD COLUMN IF NOT EXISTS status TEXT;

-- P&L и ROI
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS realized_pnl DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS finalized BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS roi_planned DECIMAL(10,4),
ADD COLUMN IF NOT EXISTS pnl_gross DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS pnl_net DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS roi_gross DECIMAL(10,4);

-- Bybit данные
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS entry_price_bybit DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS exit_price_bybit DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS exit_price_fallback DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS roi_percent_bybit DECIMAL(10,4),
ADD COLUMN IF NOT EXISTS roi_estimated DECIMAL(10,4);

-- Проскальзывание и задержки
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS entry_slippage DECIMAL(10,4),
ADD COLUMN IF NOT EXISTS exit_slippage DECIMAL(10,4),
ADD COLUMN IF NOT EXISTS entry_latency_ms INTEGER,
ADD COLUMN IF NOT EXISTS exit_latency_ms INTEGER;

-- Источники данных
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS data_source_mode TEXT,
ADD COLUMN IF NOT EXISTS weekday INTEGER,
ADD COLUMN IF NOT EXISTS weekday_name TEXT,
ADD COLUMN IF NOT EXISTS opened_at_full TEXT;

-- Комиссии
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS bybit_fee_open DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS bybit_fee_close DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS bybit_fee_total DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS bybit_pnl_net DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS commission_over_roi DECIMAL(10,4);

-- Анализ и флаги
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS loss_type TEXT,
ADD COLUMN IF NOT EXISTS anomaly_flag BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS bybit_pnl_net_api DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS bybit_pnl_net_fallback DECIMAL(20,8);

-- ID ордеров
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS order_id_exit TEXT,
ADD COLUMN IF NOT EXISTS signal_id TEXT,
ADD COLUMN IF NOT EXISTS tp1_order_id TEXT,
ADD COLUMN IF NOT EXISTS tp2_order_id TEXT,
ADD COLUMN IF NOT EXISTS sl_order_id TEXT;

-- Управление стоп-лоссом
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS sl_be_moved BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS sl_be_method TEXT,
ADD COLUMN IF NOT EXISTS sl_be_price DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS sl_to_be INTEGER DEFAULT 0;

-- Восстановление TP2
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS tp2_restore_attempted BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS tp2_restore_attempts INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS tp2_order_id_current TEXT,
ADD COLUMN IF NOT EXISTS tp2_order_id_history TEXT,
ADD COLUMN IF NOT EXISTS tp2_exit_type TEXT;

-- Текущие ID ордеров
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS sl_order_id_current TEXT,
ADD COLUMN IF NOT EXISTS sl_order_id_history TEXT;

-- P&L по целям
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS pnl_tp1 DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS pnl_tp2 DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS roi_tp1 DECIMAL(10,4),
ADD COLUMN IF NOT EXISTS roi_tp2 DECIMAL(10,4),
ADD COLUMN IF NOT EXISTS roi_final_real DECIMAL(10,4),
ADD COLUMN IF NOT EXISTS pnl_final_real DECIMAL(20,8);

-- Прибыль по целям
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS profit_tp1_real DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS profit_tp2_real DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS expected_profit_tp1 DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS expected_profit_tp2 DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS expected_profit_total DECIMAL(20,8);

-- Комиссии по целям
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS fee_tp1 DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS fee_tp2 DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS pnl_tp1_net DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS pnl_tp2_net DECIMAL(20,8);

-- ROI по целям
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS roi_tp1_real DECIMAL(10,4),
ADD COLUMN IF NOT EXISTS roi_tp2_real DECIMAL(10,4),
ADD COLUMN IF NOT EXISTS roi_sl_real DECIMAL(10,4),
ADD COLUMN IF NOT EXISTS roi_sl_expected DECIMAL(10,4);

-- Время достижения целей
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS tp1_hit_time TIMESTAMP,
ADD COLUMN IF NOT EXISTS tp2_hit_time TIMESTAMP,
ADD COLUMN IF NOT EXISTS sl_hit_time TIMESTAMP;

-- Длительность
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS duration_sec INTEGER,
ADD COLUMN IF NOT EXISTS tp1_duration_sec INTEGER,
ADD COLUMN IF NOT EXISTS tp2_duration_sec INTEGER,
ADD COLUMN IF NOT EXISTS sl_duration_sec INTEGER;

-- Флаги достижения целей
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS tp1_hit BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS tp2_hit BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS sl_hit BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS tp_count_hit INTEGER DEFAULT 0;

-- Ранний выход
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS early_exit BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS early_exit_reason TEXT,
ADD COLUMN IF NOT EXISTS exit_explanation TEXT,
ADD COLUMN IF NOT EXISTS exit_ai_score DECIMAL(10,4);

-- Ручное управление
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS manual_exit INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS manual_exit_type TEXT;

-- Источники P&L
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS pnl_source TEXT,
ADD COLUMN IF NOT EXISTS roi_source TEXT;

-- Fills данные
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS raw_fills_count INTEGER,
ADD COLUMN IF NOT EXISTS fills_legA TEXT,
ADD COLUMN IF NOT EXISTS fills_legB TEXT,
ADD COLUMN IF NOT EXISTS fills_legA_vwap DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS fills_legB_vwap DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS fills_legA_qty DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS fills_legB_qty DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS fills_legA_fee DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS fills_legB_fee DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS fills_legA_fee_in DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS fills_legB_fee_in DECIMAL(20,8);

-- Дополнительные поля
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS leverage_used_expected DECIMAL(20,8);

-- Дополнительные поля из схемы Дарэна
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS tp_hit TEXT,
ADD COLUMN IF NOT EXISTS exit_detail TEXT,
ADD COLUMN IF NOT EXISTS roi_ui DECIMAL(10,4),
ADD COLUMN IF NOT EXISTS pnl_net_initial DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS roi_percent_initial DECIMAL(10,4),
ADD COLUMN IF NOT EXISTS roi_bybit_style DECIMAL(10,4),
ADD COLUMN IF NOT EXISTS expected_loss_sl DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS order_id_exit_fallback TEXT;

-- ========================================
-- СОЗДАЕМ ИНДЕКСЫ ДЛЯ ВСЕХ НОВЫХ ПОЛЕЙ
-- ========================================

-- Основные индексы
CREATE INDEX IF NOT EXISTS idx_trades_trade_id ON trades(trade_id);
CREATE INDEX IF NOT EXISTS idx_trades_source_type ON trades(source_type);
CREATE INDEX IF NOT EXISTS idx_trades_entry_zone ON trades(entry_zone);
CREATE INDEX IF NOT EXISTS idx_trades_tp1 ON trades(tp1);
CREATE INDEX IF NOT EXISTS idx_trades_tp2 ON trades(tp2);
CREATE INDEX IF NOT EXISTS idx_trades_sl ON trades(sl);
CREATE INDEX IF NOT EXISTS idx_trades_real_entry_price ON trades(real_entry_price);
CREATE INDEX IF NOT EXISTS idx_trades_opened_at ON trades(opened_at);
CREATE INDEX IF NOT EXISTS idx_trades_exit_time ON trades(exit_time);
CREATE INDEX IF NOT EXISTS idx_trades_closed_at ON trades(closed_at);
CREATE INDEX IF NOT EXISTS idx_trades_real_leverage ON trades(real_leverage);
CREATE INDEX IF NOT EXISTS idx_trades_margin_used ON trades(margin_used);
CREATE INDEX IF NOT EXISTS idx_trades_risk_pct ON trades(risk_pct);
CREATE INDEX IF NOT EXISTS idx_trades_roi_percent ON trades(roi_percent);
CREATE INDEX IF NOT EXISTS idx_trades_pnl_net ON trades(pnl_net);
CREATE INDEX IF NOT EXISTS idx_trades_bybit_pnl_net ON trades(bybit_pnl_net);
CREATE INDEX IF NOT EXISTS idx_trades_tp1_hit ON trades(tp1_hit);
CREATE INDEX IF NOT EXISTS idx_trades_tp2_hit ON trades(tp2_hit);
CREATE INDEX IF NOT EXISTS idx_trades_sl_hit ON trades(sl_hit);
CREATE INDEX IF NOT EXISTS idx_trades_early_exit ON trades(early_exit);
CREATE INDEX IF NOT EXISTS idx_trades_manual_exit ON trades(manual_exit);
CREATE INDEX IF NOT EXISTS idx_trades_fills_legA ON trades(fills_legA);
CREATE INDEX IF NOT EXISTS idx_trades_fills_legB ON trades(fills_legB);

-- ========================================
-- ДОБАВЛЯЕМ КОММЕНТАРИИ
-- ========================================

COMMENT ON TABLE trades IS 'Complete trades table with all fields from Darrin schema';
COMMENT ON COLUMN trades.tp_hit IS 'Which take profit was hit (TP1, TP2, etc.)';
COMMENT ON COLUMN trades.exit_detail IS 'Detailed exit information';
COMMENT ON COLUMN trades.roi_ui IS 'ROI for UI display';
COMMENT ON COLUMN trades.pnl_net_initial IS 'Initial net P&L';
COMMENT ON COLUMN trades.roi_percent_initial IS 'Initial ROI percentage';
COMMENT ON COLUMN trades.roi_bybit_style IS 'ROI calculated in Bybit style';
COMMENT ON COLUMN trades.fills_legA IS 'Fills data for leg A';
COMMENT ON COLUMN trades.fills_legB IS 'Fills data for leg B';

-- ========================================
-- СОЗДАЕМ ПРЕДСТАВЛЕНИЕ ДЛЯ ПРОВЕРКИ
-- ========================================

CREATE OR REPLACE VIEW trades_schema_check AS
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'trades' 
ORDER BY ordinal_position;

-- ========================================
-- ПРОВЕРЯЕМ РЕЗУЛЬТАТ
-- ========================================

-- Проверяем что все поля добавлены
SELECT 'Migration completed successfully. Total columns in trades table: ' || 
       COUNT(*)::TEXT as migration_status
FROM information_schema.columns 
WHERE table_name = 'trades';

-- Показываем все поля для проверки
SELECT column_name, data_type, is_nullable
FROM trades_schema_check
ORDER BY column_name;
