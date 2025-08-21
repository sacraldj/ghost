-- Создание таблиц для виртуального трейдинга
-- Исправленная версия без синтаксических ошибок

-- 1. ВИРТУАЛЬНЫЕ ПОЗИЦИИ
CREATE TABLE IF NOT EXISTS virtual_positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id UUID,
    v_trade_id UUID,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(5) NOT NULL CHECK (side IN ('LONG', 'SHORT')),
    strategy_id VARCHAR(50) DEFAULT 'S_A_TP1_BE_TP2',
    position_size_usd DECIMAL(12,4) NOT NULL,
    leverage INTEGER DEFAULT 10,
    margin_usd DECIMAL(12,4) NOT NULL,
    signal_entry_min DECIMAL(20,8),
    signal_entry_max DECIMAL(20,8),
    signal_tp1 DECIMAL(20,8),
    signal_tp2 DECIMAL(20,8),
    signal_tp3 DECIMAL(20,8),
    signal_sl DECIMAL(20,8),
    avg_entry_price DECIMAL(20,8),
    current_price DECIMAL(20,8),
    current_pnl_usd DECIMAL(12,4) DEFAULT 0,
    current_pnl_percent DECIMAL(8,4) DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN (
        'PENDING', 'PARTIAL_FILL', 'FILLED', 'TP1_HIT', 'TP2_HIT', 'TP3_HIT', 'SL_HIT', 'CLOSED', 'EXPIRED'
    )),
    filled_percent DECIMAL(5,2) DEFAULT 0,
    tp1_filled_percent DECIMAL(5,2) DEFAULT 0,
    tp2_filled_percent DECIMAL(5,2) DEFAULT 0,
    tp3_filled_percent DECIMAL(5,2) DEFAULT 0,
    remaining_percent DECIMAL(5,2) DEFAULT 100,
    signal_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    entry_timeout TIMESTAMPTZ,
    first_entry_time TIMESTAMPTZ,
    last_update_time TIMESTAMPTZ,
    close_time TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. ВХОДЫ В ПОЗИЦИЮ
CREATE TABLE IF NOT EXISTS position_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    position_id UUID NOT NULL,
    entry_price DECIMAL(20,8) NOT NULL,
    entry_size_usd DECIMAL(12,4) NOT NULL,
    entry_percent DECIMAL(5,2) NOT NULL,
    entry_type VARCHAR(20) DEFAULT 'MARKET' CHECK (entry_type IN ('MARKET', 'LIMIT', 'DCA')),
    entry_reason VARCHAR(100),
    entry_time TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. ВЫХОДЫ ИЗ ПОЗИЦИИ
CREATE TABLE IF NOT EXISTS position_exits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    position_id UUID NOT NULL,
    exit_price DECIMAL(20,8) NOT NULL,
    exit_size_usd DECIMAL(12,4) NOT NULL,
    exit_percent DECIMAL(5,2) NOT NULL,
    pnl_usd DECIMAL(12,4) NOT NULL,
    pnl_percent DECIMAL(8,4) NOT NULL,
    exit_type VARCHAR(20) NOT NULL CHECK (exit_type IN ('TP1', 'TP2', 'TP3', 'SL', 'MANUAL', 'TIMEOUT')),
    exit_reason VARCHAR(100),
    exit_time TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. ИСТОРИЧЕСКИЕ ДАННЫЕ СВЕЧЕЙ
CREATE TABLE IF NOT EXISTS position_candles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    position_id UUID NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) DEFAULT '1m',
    open_time TIMESTAMPTZ NOT NULL,
    close_time TIMESTAMPTZ NOT NULL,
    open_price DECIMAL(20,8) NOT NULL,
    high_price DECIMAL(20,8) NOT NULL,
    low_price DECIMAL(20,8) NOT NULL,
    close_price DECIMAL(20,8) NOT NULL,
    volume DECIMAL(20,8),
    sma_20 DECIMAL(20,8),
    ema_12 DECIMAL(20,8),
    rsi_14 DECIMAL(5,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. СОБЫТИЯ ПОЗИЦИИ
CREATE TABLE IF NOT EXISTS position_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    position_id UUID NOT NULL,
    event_type VARCHAR(30) NOT NULL CHECK (event_type IN (
        'POSITION_CREATED', 'ENTRY_FILLED', 'PRICE_UPDATE', 'TP1_REACHED', 'TP2_REACHED', 
        'TP3_REACHED', 'SL_REACHED', 'PARTIAL_CLOSE', 'POSITION_CLOSED', 'TIMEOUT', 'ERROR', 'MANUAL_ACTION'
    )),
    event_description TEXT,
    price_at_event DECIMAL(20,8),
    pnl_at_event DECIMAL(12,4),
    event_data JSONB,
    event_time TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ИНДЕКСЫ
CREATE INDEX IF NOT EXISTS idx_virtual_positions_symbol ON virtual_positions(symbol);
CREATE INDEX IF NOT EXISTS idx_virtual_positions_status ON virtual_positions(status);
CREATE INDEX IF NOT EXISTS idx_virtual_positions_created_at ON virtual_positions(created_at);
CREATE INDEX IF NOT EXISTS idx_position_entries_position_id ON position_entries(position_id);
CREATE INDEX IF NOT EXISTS idx_position_exits_position_id ON position_exits(position_id);
CREATE INDEX IF NOT EXISTS idx_position_candles_position_id ON position_candles(position_id);
CREATE INDEX IF NOT EXISTS idx_position_events_position_id ON position_events(position_id);

-- ФУНКЦИЯ ДЛЯ ОБНОВЛЕНИЯ updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- ТРИГГЕР (правильный синтаксис)
DROP TRIGGER IF EXISTS update_virtual_positions_updated_at ON virtual_positions;
CREATE TRIGGER update_virtual_positions_updated_at 
    BEFORE UPDATE ON virtual_positions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
