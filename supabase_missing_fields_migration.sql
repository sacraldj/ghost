-- GHOST Supabase Missing Fields Migration
-- Добавление недостающих полей из схемы Дарэна
-- Выполните этот код в SQL Editor в Supabase Dashboard

-- Добавляем недостающие поля в таблицу trades
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS tp_hit TEXT,
ADD COLUMN IF NOT EXISTS exit_detail TEXT,
ADD COLUMN IF NOT EXISTS roi_ui DECIMAL(10,4),
ADD COLUMN IF NOT EXISTS pnl_net_initial DECIMAL(20,8),
ADD COLUMN IF NOT EXISTS roi_percent_initial DECIMAL(10,4),
ADD COLUMN IF NOT EXISTS roi_bybit_style DECIMAL(10,4);

-- Обновляем существующие поля если нужно
-- Некоторые поля могут уже существовать, но с другими типами данных

-- Создаем дополнительные индексы для новых полей
CREATE INDEX IF NOT EXISTS idx_trades_tp_hit ON trades(tp_hit);
CREATE INDEX IF NOT EXISTS idx_trades_exit_detail ON trades(exit_detail);
CREATE INDEX IF NOT EXISTS idx_trades_roi_ui ON trades(roi_ui);
CREATE INDEX IF NOT EXISTS idx_trades_pnl_net_initial ON trades(pnl_net_initial);
CREATE INDEX IF NOT EXISTS idx_trades_roi_percent_initial ON trades(roi_percent_initial);
CREATE INDEX IF NOT EXISTS idx_trades_roi_bybit_style ON trades(roi_bybit_style);

-- Проверяем и обновляем существующие поля если нужно
-- Это безопасная операция, которая не изменит существующие данные

-- Добавляем комментарии к таблице для документации
COMMENT ON TABLE trades IS 'Extended trades table with all fields from Darrin schema';
COMMENT ON COLUMN trades.tp_hit IS 'Which take profit was hit (TP1, TP2, etc.)';
COMMENT ON COLUMN trades.exit_detail IS 'Detailed exit information';
COMMENT ON COLUMN trades.roi_ui IS 'ROI for UI display';
COMMENT ON COLUMN trades.pnl_net_initial IS 'Initial net P&L';
COMMENT ON COLUMN trades.roi_percent_initial IS 'Initial ROI percentage';
COMMENT ON COLUMN trades.roi_bybit_style IS 'ROI calculated in Bybit style';

-- Создаем представление для проверки всех полей
CREATE OR REPLACE VIEW trades_schema_check AS
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'trades' 
ORDER BY ordinal_position;

-- Проверяем что все поля добавлены
SELECT 'Migration completed successfully. Total columns in trades table: ' || 
       COUNT(*)::TEXT as migration_status
FROM information_schema.columns 
WHERE table_name = 'trades';
