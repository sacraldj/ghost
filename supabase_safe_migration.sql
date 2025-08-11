-- GHOST Supabase Safe Migration
-- Безопасное добавление недостающих полей из схемы Дарэна
-- Выполните этот код в SQL Editor в Supabase Dashboard

-- Сначала проверяем текущую схему
SELECT 'Current schema check - Total columns: ' || 
       COUNT(*)::TEXT as current_status
FROM information_schema.columns 
WHERE table_name = 'trades';

-- Добавляем недостающие поля из схемы Дарэна
-- Используем IF NOT EXISTS для безопасного добавления

-- Основные поля
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS tp_hit TEXT,
ADD COLUMN IF NOT EXISTS exit_detail TEXT,
ADD COLUMN IF NOT EXISTS roi_ui DECIMAL(10,4),
ADD COLUMN IF NOT EXISTS pnl_net_initial DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS roi_percent_initial DECIMAL(10,4),
ADD COLUMN IF NOT EXISTS roi_bybit_style DECIMAL(10,4),
ADD COLUMN IF NOT EXISTS expected_loss_sl DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS order_id_exit_fallback TEXT;

-- Fills поля
ALTER TABLE trades 
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
ADD COLUMN IF NOT EXISTS leverage_used_expected DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS raw_fills_count INTEGER;

-- Создаем индексы для новых полей
CREATE INDEX IF NOT EXISTS idx_trades_tp_hit ON trades(tp_hit);
CREATE INDEX IF NOT EXISTS idx_trades_exit_detail ON trades(exit_detail);
CREATE INDEX IF NOT EXISTS idx_trades_roi_ui ON trades(roi_ui);
CREATE INDEX IF NOT EXISTS idx_trades_pnl_net_initial ON trades(pnl_net_initial);
CREATE INDEX IF NOT EXISTS idx_trades_roi_percent_initial ON trades(roi_percent_initial);
CREATE INDEX IF NOT EXISTS idx_trades_roi_bybit_style ON trades(roi_bybit_style);
CREATE INDEX IF NOT EXISTS idx_trades_expected_loss_sl ON trades(expected_loss_sl);
CREATE INDEX IF NOT EXISTS idx_trades_order_id_exit_fallback ON trades(order_id_exit_fallback);
CREATE INDEX IF NOT EXISTS idx_trades_fills_legA ON trades(fills_legA);
CREATE INDEX IF NOT EXISTS idx_trades_fills_legB ON trades(fills_legB);

-- Добавляем комментарии
COMMENT ON TABLE trades IS 'Extended trades table with all fields from Darrin schema';
COMMENT ON COLUMN trades.tp_hit IS 'Which take profit was hit (TP1, TP2, etc.)';
COMMENT ON COLUMN trades.exit_detail IS 'Detailed exit information';
COMMENT ON COLUMN trades.roi_ui IS 'ROI for UI display';
COMMENT ON COLUMN trades.pnl_net_initial IS 'Initial net P&L';
COMMENT ON COLUMN trades.roi_percent_initial IS 'Initial ROI percentage';
COMMENT ON COLUMN trades.roi_bybit_style IS 'ROI calculated in Bybit style';
COMMENT ON COLUMN trades.fills_legA IS 'Fills data for leg A';
COMMENT ON COLUMN trades.fills_legB IS 'Fills data for leg B';

-- Создаем представление для проверки схемы
CREATE OR REPLACE VIEW trades_schema_check AS
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'trades' 
ORDER BY ordinal_position;

-- Проверяем результат
SELECT 'Migration completed successfully. Total columns in trades table: ' || 
       COUNT(*)::TEXT as migration_status
FROM information_schema.columns 
WHERE table_name = 'trades';

-- Показываем все поля для проверки
SELECT column_name, data_type, is_nullable
FROM trades_schema_check
ORDER BY column_name;
