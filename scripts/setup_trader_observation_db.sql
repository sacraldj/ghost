-- Создание таблиц для Trader Observation System в Supabase
-- Выполнить в Supabase SQL Editor

-- 1. Реестр трейдеров
CREATE TABLE IF NOT EXISTS trader_registry (
    trader_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    source_type VARCHAR(20) NOT NULL, -- telegram, discord, twitter, rss
    source_id VARCHAR(100), -- chat_id, handle, etc
    source_handle VARCHAR(100), -- @username
    mode VARCHAR(10) DEFAULT 'observe', -- observe | paper | live
    risk_profile JSONB, -- {size_usd: 100, leverage: 10, max_concurrent: 3}
    parsing_profile VARCHAR(50) DEFAULT 'standard_v1',
    is_active BOOLEAN DEFAULT true,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 2. Сырые сигналы
CREATE TABLE IF NOT EXISTS signals_raw (
    raw_id SERIAL PRIMARY KEY,
    trader_id VARCHAR(50) REFERENCES trader_registry(trader_id),
    source_msg_id VARCHAR(100),
    posted_at TIMESTAMP NOT NULL,
    text TEXT NOT NULL,
    meta JSONB,
    processed BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. Обработанные сигналы
CREATE TABLE IF NOT EXISTS signals_parsed (
    signal_id SERIAL PRIMARY KEY,
    trader_id VARCHAR(50) REFERENCES trader_registry(trader_id),
    raw_id INTEGER REFERENCES signals_raw(raw_id),
    posted_at TIMESTAMP NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL, -- BUY, SELL
    entry_type VARCHAR(10), -- market, limit, range
    entry DECIMAL(20,8),
    range_low DECIMAL(20,8),
    range_high DECIMAL(20,8),
    tp1 DECIMAL(20,8),
    tp2 DECIMAL(20,8),
    tp3 DECIMAL(20,8),
    tp4 DECIMAL(20,8),
    sl DECIMAL(20,8),
    leverage_hint INTEGER,
    timeframe_hint VARCHAR(10),
    confidence DECIMAL(5,2),
    parsed_at TIMESTAMP DEFAULT NOW(),
    parse_version VARCHAR(10) DEFAULT 'v1.0',
    checksum VARCHAR(64) UNIQUE,
    is_valid BOOLEAN DEFAULT true
);

-- 4. Свечи для симуляции
CREATE TABLE IF NOT EXISTS candles (
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL, -- 1m, 5m, 15m, 1h
    open_time TIMESTAMP NOT NULL,
    open_price DECIMAL(20,8) NOT NULL,
    high_price DECIMAL(20,8) NOT NULL,
    low_price DECIMAL(20,8) NOT NULL,
    close_price DECIMAL(20,8) NOT NULL,
    volume DECIMAL(20,8),
    vwap DECIMAL(20,8),
    trades_count INTEGER,
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (symbol, timeframe, open_time)
);

-- 5. Исходы сигналов
CREATE TABLE IF NOT EXISTS signal_outcomes (
    signal_id INTEGER PRIMARY KEY REFERENCES signals_parsed(signal_id),
    trader_id VARCHAR(50) REFERENCES trader_registry(trader_id),
    entry_exec_price_sim DECIMAL(20,8),
    tp1_hit_at TIMESTAMP,
    tp2_hit_at TIMESTAMP,
    tp3_hit_at TIMESTAMP,
    sl_hit_at TIMESTAMP,
    max_favorable DECIMAL(20,8),
    max_adverse DECIMAL(20,8),
    duration_to_tp1_min INTEGER,
    duration_to_tp2_min INTEGER,
    final_result VARCHAR(20), -- TP1_ONLY, TP2_FULL, SL, BE, TIMEOUT, NOFILL
    pnl_sim DECIMAL(20,8),
    roi_sim DECIMAL(10,4),
    fee_sim DECIMAL(20,8),
    calc_mode VARCHAR(10) DEFAULT 'candles',
    simulation_version VARCHAR(10) DEFAULT 'v1.0',
    calculated_at TIMESTAMP DEFAULT NOW()
);

-- 6. Paper торги
CREATE TABLE IF NOT EXISTS paper_trades (
    paper_trade_id SERIAL PRIMARY KEY,
    signal_id INTEGER REFERENCES signals_parsed(signal_id),
    trader_id VARCHAR(50) REFERENCES trader_registry(trader_id),
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    opened_at TIMESTAMP DEFAULT NOW(),
    entry_price_sim DECIMAL(20,8),
    position_size DECIMAL(20,8),
    margin_used DECIMAL(20,8),
    leverage INTEGER,
    tp1_price DECIMAL(20,8),
    tp2_price DECIMAL(20,8),
    sl_price DECIMAL(20,8),
    closes_json JSONB,
    pnl_sim_final DECIMAL(20,8),
    roi_sim_final DECIMAL(10,4),
    status VARCHAR(20) DEFAULT 'open',
    closed_at TIMESTAMP
);

-- 7. Дневная статистика
CREATE TABLE IF NOT EXISTS trader_stats_daily (
    date DATE NOT NULL,
    trader_id VARCHAR(50) REFERENCES trader_registry(trader_id),
    signals_count INTEGER DEFAULT 0,
    valid_signals INTEGER DEFAULT 0,
    executed_signals INTEGER DEFAULT 0,
    winrate DECIMAL(5,2),
    tp1_rate DECIMAL(5,2),
    tp2_rate DECIMAL(5,2),
    sl_rate DECIMAL(5,2),
    avg_rr DECIMAL(10,4),
    avg_duration_to_tp1_min INTEGER,
    avg_duration_to_tp2_min INTEGER,
    pnl_sim_sum DECIMAL(20,8),
    max_drawdown_sim DECIMAL(20,8),
    sharpe_like DECIMAL(10,4),
    expectancy DECIMAL(10,4),
    stability_index DECIMAL(5,2),
    last_30d_perf DECIMAL(10,4),
    last_90d_perf DECIMAL(10,4),
    PRIMARY KEY (date, trader_id)
);

-- Индексы для производительности
CREATE INDEX IF NOT EXISTS idx_signals_raw_trader_posted ON signals_raw(trader_id, posted_at);
CREATE INDEX IF NOT EXISTS idx_signals_parsed_trader_symbol ON signals_parsed(trader_id, symbol, posted_at);
CREATE INDEX IF NOT EXISTS idx_signals_parsed_checksum ON signals_parsed(checksum);
CREATE INDEX IF NOT EXISTS idx_candles_symbol_tf_time ON candles(symbol, timeframe, open_time);
CREATE INDEX IF NOT EXISTS idx_signal_outcomes_trader ON signal_outcomes(trader_id, calculated_at);
CREATE INDEX IF NOT EXISTS idx_trader_stats_daily_trader_date ON trader_stats_daily(trader_id, date);

-- Включение RLS (Row Level Security) для безопасности
ALTER TABLE trader_registry ENABLE ROW LEVEL SECURITY;
ALTER TABLE signals_raw ENABLE ROW LEVEL SECURITY;
ALTER TABLE signals_parsed ENABLE ROW LEVEL SECURITY;
ALTER TABLE candles ENABLE ROW LEVEL SECURITY;
ALTER TABLE signal_outcomes ENABLE ROW LEVEL SECURITY;
ALTER TABLE paper_trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE trader_stats_daily ENABLE ROW LEVEL SECURITY;

-- Политики доступа (можно настроить позже)
CREATE POLICY "Allow authenticated users" ON trader_registry FOR ALL TO authenticated USING (true);
CREATE POLICY "Allow authenticated users" ON signals_raw FOR ALL TO authenticated USING (true);
CREATE POLICY "Allow authenticated users" ON signals_parsed FOR ALL TO authenticated USING (true);
CREATE POLICY "Allow authenticated users" ON candles FOR ALL TO authenticated USING (true);
CREATE POLICY "Allow authenticated users" ON signal_outcomes FOR ALL TO authenticated USING (true);
CREATE POLICY "Allow authenticated users" ON paper_trades FOR ALL TO authenticated USING (true);
CREATE POLICY "Allow authenticated users" ON trader_stats_daily FOR ALL TO authenticated USING (true);

-- Тестовые данные
INSERT INTO trader_registry (trader_id, name, source_type, source_handle, mode, risk_profile) VALUES
('slivaeminfo', 'Slivaem Info', 'telegram', '@slivaeminfo', 'observe', 
 '{"size_usd": 100, "leverage": 10, "max_concurrent": 3, "sl_cap": 5}'),
('cryptoexpert', 'Crypto Expert Pro', 'telegram', '@cryptoexpert', 'paper',
 '{"size_usd": 200, "leverage": 15, "max_concurrent": 5, "sl_cap": 10}'),
('tradingpro', 'Trading Pro Master', 'telegram', '@tradingpro', 'live',
 '{"size_usd": 150, "leverage": 12, "max_concurrent": 4, "sl_cap": 7}'),
('signalmaster', 'Signal Master', 'telegram', '@signalmaster', 'observe',
 '{"size_usd": 75, "leverage": 8, "max_concurrent": 2, "sl_cap": 8}')
ON CONFLICT (trader_id) DO NOTHING;

-- Проверка создания таблиц
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
AND table_name IN ('trader_registry', 'signals_raw', 'signals_parsed', 'candles', 'signal_outcomes', 'paper_trades', 'trader_stats_daily')
ORDER BY table_name;
