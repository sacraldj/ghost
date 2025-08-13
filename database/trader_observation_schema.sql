-- ============================================
-- GHOST TRADER OBSERVATION SYSTEM
-- Database Schema для системы наблюдения за трейдерами
-- ============================================

-- 1. Реестр трейдеров и режимов
CREATE TABLE trader_registry (
    trader_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    source_type VARCHAR(20) NOT NULL, -- telegram, discord, twitter, rss
    source_id VARCHAR(100), -- chat_id, handle, etc
    source_handle VARCHAR(100), -- @username
    mode VARCHAR(10) DEFAULT 'observe', -- observe | paper | live
    risk_profile JSONB, -- {size_usd: 100, leverage: 10, max_concurrent: 3, sl_cap: 5}
    parsing_profile VARCHAR(50), -- ссылка на профиль парсинга
    is_active BOOLEAN DEFAULT true,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 2. Сырые сигналы (необработанные)
CREATE TABLE signals_raw (
    raw_id SERIAL PRIMARY KEY,
    trader_id VARCHAR(50) REFERENCES trader_registry(trader_id),
    source_msg_id VARCHAR(100), -- ID сообщения в источнике
    posted_at TIMESTAMP NOT NULL,
    text TEXT NOT NULL,
    meta JSONB, -- {chat_title, message_type, forwarded_from, etc}
    processed BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. Обработанные сигналы (нормализованные)
CREATE TABLE signals_parsed (
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
    timeframe_hint VARCHAR(10), -- 15m, 1h, 4h, 1d
    confidence DECIMAL(5,2), -- 0-100 скор качества парсинга
    parsed_at TIMESTAMP DEFAULT NOW(),
    parse_version VARCHAR(10) DEFAULT 'v1.0',
    checksum VARCHAR(64) UNIQUE, -- для анти-дубликатов
    is_valid BOOLEAN DEFAULT true
);

-- 4. Свечи для проверки исходов
CREATE TABLE candles (
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL, -- 1m, 5m, 15m, 1h, 4h, 1d
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

-- 5. Исходы сигналов (результаты симуляции)
CREATE TABLE signal_outcomes (
    signal_id INTEGER PRIMARY KEY REFERENCES signals_parsed(signal_id),
    trader_id VARCHAR(50) REFERENCES trader_registry(trader_id),
    entry_exec_price_sim DECIMAL(20,8),
    tp1_hit_at TIMESTAMP,
    tp2_hit_at TIMESTAMP,
    tp3_hit_at TIMESTAMP,
    sl_hit_at TIMESTAMP,
    max_favorable DECIMAL(20,8), -- максимальный профит
    max_adverse DECIMAL(20,8), -- максимальный убыток
    duration_to_tp1_min INTEGER,
    duration_to_tp2_min INTEGER,
    final_result VARCHAR(20), -- TP1_ONLY, TP2_FULL, SL, BE, TIMEOUT, NOFILL
    pnl_sim DECIMAL(20,8),
    roi_sim DECIMAL(10,4), -- в процентах
    fee_sim DECIMAL(20,8),
    calc_mode VARCHAR(10) DEFAULT 'candles', -- candles, ticks, mixed
    simulation_version VARCHAR(10) DEFAULT 'v1.0',
    calculated_at TIMESTAMP DEFAULT NOW()
);

-- 6. Paper торги (симуляция исполнения)
CREATE TABLE paper_trades (
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
    closes_json JSONB, -- [{type: 'tp1', price: X, qty: Y, at: timestamp}, ...]
    pnl_sim_final DECIMAL(20,8),
    roi_sim_final DECIMAL(10,4),
    status VARCHAR(20) DEFAULT 'open', -- open, partial, closed
    closed_at TIMESTAMP
);

-- 7. Дневная статистика трейдеров
CREATE TABLE trader_stats_daily (
    date DATE NOT NULL,
    trader_id VARCHAR(50) REFERENCES trader_registry(trader_id),
    signals_count INTEGER DEFAULT 0,
    valid_signals INTEGER DEFAULT 0,
    executed_signals INTEGER DEFAULT 0, -- кол-во исполненных (не NOFILL)
    winrate DECIMAL(5,2), -- процент выигрышных
    tp1_rate DECIMAL(5,2), -- процент достигших TP1
    tp2_rate DECIMAL(5,2), -- процент достигших TP2
    sl_rate DECIMAL(5,2), -- процент по стопу
    avg_rr DECIMAL(10,4), -- средний Risk/Reward
    avg_duration_to_tp1_min INTEGER,
    avg_duration_to_tp2_min INTEGER,
    pnl_sim_sum DECIMAL(20,8),
    max_drawdown_sim DECIMAL(20,8),
    sharpe_like DECIMAL(10,4), -- sharpe-подобный показатель
    expectancy DECIMAL(10,4), -- математическое ожидание
    stability_index DECIMAL(5,2), -- индекс стабильности (0-100)
    last_30d_perf DECIMAL(10,4), -- перформанс за 30 дней
    last_90d_perf DECIMAL(10,4), -- перформанс за 90 дней
    PRIMARY KEY (date, trader_id)
);

-- 8. Агрегированная статистика трейдеров (материализованное представление)
CREATE MATERIALIZED VIEW trader_stats AS
SELECT 
    t.trader_id,
    t.name,
    t.source_type,
    t.mode,
    t.is_active,
    
    -- Общие метрики
    COUNT(sp.signal_id) as total_signals,
    COUNT(CASE WHEN sp.is_valid THEN 1 END) as valid_signals,
    COUNT(so.signal_id) as analyzed_signals,
    
    -- Текущая производительность (последние 30 дней)
    AVG(CASE WHEN tsd.date >= CURRENT_DATE - INTERVAL '30 days' 
             THEN tsd.winrate END) as winrate_30d,
    AVG(CASE WHEN tsd.date >= CURRENT_DATE - INTERVAL '30 days' 
             THEN tsd.avg_rr END) as avg_rr_30d,
    SUM(CASE WHEN tsd.date >= CURRENT_DATE - INTERVAL '30 days' 
             THEN tsd.pnl_sim_sum END) as pnl_30d,
    
    -- Общая производительность
    AVG(tsd.winrate) as winrate_total,
    AVG(tsd.avg_rr) as avg_rr_total,
    SUM(tsd.pnl_sim_sum) as pnl_total,
    AVG(tsd.sharpe_like) as sharpe_avg,
    AVG(tsd.stability_index) as stability_avg,
    
    -- Последняя активность
    MAX(sp.posted_at) as last_signal_at,
    COUNT(CASE WHEN sp.posted_at >= CURRENT_DATE - INTERVAL '7 days' 
               THEN 1 END) as signals_7d,
    
    -- Качество сигналов
    AVG(sp.confidence) as avg_confidence,
    COUNT(DISTINCT sp.symbol) as symbols_traded
    
FROM trader_registry t
LEFT JOIN signals_parsed sp ON t.trader_id = sp.trader_id
LEFT JOIN signal_outcomes so ON sp.signal_id = so.signal_id
LEFT JOIN trader_stats_daily tsd ON t.trader_id = tsd.trader_id
GROUP BY t.trader_id, t.name, t.source_type, t.mode, t.is_active;

-- 9. Индексы для производительности
CREATE INDEX idx_signals_raw_trader_posted ON signals_raw(trader_id, posted_at);
CREATE INDEX idx_signals_parsed_trader_symbol ON signals_parsed(trader_id, symbol, posted_at);
CREATE INDEX idx_signals_parsed_checksum ON signals_parsed(checksum);
CREATE INDEX idx_candles_symbol_tf_time ON candles(symbol, timeframe, open_time);
CREATE INDEX idx_signal_outcomes_trader ON signal_outcomes(trader_id, calculated_at);
CREATE INDEX idx_trader_stats_daily_trader_date ON trader_stats_daily(trader_id, date);

-- 10. Функции для обновления статистики
CREATE OR REPLACE FUNCTION refresh_trader_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW trader_stats;
END;
$$ LANGUAGE plpgsql;

-- 11. Триггеры для автообновления timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_trader_registry_updated_at 
    BEFORE UPDATE ON trader_registry 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 12. Начальные данные (примеры трейдеров)
INSERT INTO trader_registry (trader_id, name, source_type, source_id, mode, risk_profile, parsing_profile) VALUES
('slivaeminfo', 'Slivaem Info', 'telegram', '-1001234567890', 'observe', 
 '{"size_usd": 100, "leverage": 10, "max_concurrent": 3, "sl_cap": 5}', 'standard_v1'),
('cryptoexpert', 'Crypto Expert', 'telegram', '-1001234567891', 'observe',
 '{"size_usd": 200, "leverage": 15, "max_concurrent": 5, "sl_cap": 10}', 'standard_v1'),
('tradingpro', 'Trading Pro', 'telegram', '-1001234567892', 'paper',
 '{"size_usd": 150, "leverage": 12, "max_concurrent": 4, "sl_cap": 7}', 'advanced_v1');

-- 13. Представления для быстрых запросов
CREATE VIEW active_traders AS
SELECT * FROM trader_registry WHERE is_active = true;

CREATE VIEW live_traders AS
SELECT * FROM trader_registry WHERE mode = 'live' AND is_active = true;

CREATE VIEW top_performers AS
SELECT 
    trader_id,
    name,
    winrate_30d,
    pnl_30d,
    avg_rr_30d,
    signals_7d
FROM trader_stats
WHERE winrate_30d > 60 AND signals_7d > 0
ORDER BY pnl_30d DESC;

-- Комментарии
COMMENT ON TABLE trader_registry IS 'Реестр всех отслеживаемых трейдеров';
COMMENT ON TABLE signals_raw IS 'Сырые сигналы от всех источников';
COMMENT ON TABLE signals_parsed IS 'Обработанные и нормализованные сигналы';
COMMENT ON TABLE candles IS 'Свечи для проверки исходов сигналов';
COMMENT ON TABLE signal_outcomes IS 'Результаты симуляции сигналов';
COMMENT ON TABLE paper_trades IS 'Симуляция торговли (paper trading)';
COMMENT ON TABLE trader_stats_daily IS 'Ежедневная статистика по трейдерам';
COMMENT ON MATERIALIZED VIEW trader_stats IS 'Агрегированная статистика трейдеров';
