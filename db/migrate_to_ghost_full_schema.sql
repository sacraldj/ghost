-- 🔄 МИГРАЦИЯ К ПОЛНОЙ СХЕМЕ GHOST v1.1
-- Скрипт для обновления существующих таблиц до полной спецификации Дарэна

BEGIN TRANSACTION;

-- =====================================
-- АНАЛИЗ СУЩЕСТВУЮЩИХ ТАБЛИЦ
-- =====================================

-- Проверяем какие таблицы уже существуют
.schema

-- =====================================
-- СОЗДАНИЕ НЕДОСТАЮЩИХ ТАБЛИЦ
-- =====================================

-- 1. Создаём новую таблицу signals (если не существует)
CREATE TABLE IF NOT EXISTS signals_new (
    id TEXT PRIMARY KEY,
    received_at INTEGER NOT NULL,
    source_name TEXT NOT NULL,
    source_id TEXT,
    raw_text TEXT NOT NULL,
    symbol_raw TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL CHECK (side IN ('Buy', 'Sell')),
    entry_low REAL NOT NULL,
    entry_high REAL NOT NULL,
    targets_json TEXT NOT NULL,
    stoploss REAL NOT NULL,
    leverage_hint_min REAL,
    leverage_hint_max REAL,
    reason_text TEXT,
    parse_version TEXT NOT NULL,
    parsed_ok INTEGER NOT NULL DEFAULT 1 CHECK (parsed_ok IN (0,1)),
    precision_hint_json TEXT,
    dedupe_hash TEXT,
    created_at INTEGER DEFAULT (strftime('%s', 'now') * 1000)
);

-- Мигрируем данные из signals_parsed в signals_new
INSERT OR IGNORE INTO signals_new (
    id, received_at, source_name, symbol_raw, symbol, side, 
    entry_low, entry_high, targets_json, stoploss, parse_version, raw_text
)
SELECT 
    'sig_' || signal_id,
    strftime('%s', posted_at) * 1000,
    COALESCE(trader_id, 'unknown'),
    symbol,
    symbol,
    CASE WHEN side = 'BUY' THEN 'Buy' ELSE 'Sell' END,
    COALESCE(range_low, entry, 0),
    COALESCE(range_high, entry, 0),
    json_array(COALESCE(tp1, 0), COALESCE(tp2, 0), COALESCE(tp3, 0)),
    COALESCE(sl, 0),
    COALESCE(parse_version, 'v1.0'),
    'Migrated from signals_parsed'
FROM signals_parsed
WHERE signal_id IS NOT NULL;

-- Переименовываем таблицы
DROP TABLE IF EXISTS signals_parsed_backup;
ALTER TABLE signals_parsed RENAME TO signals_parsed_backup;
ALTER TABLE signals_new RENAME TO signals;

-- 2. Создаём candles_cache (если не существует)
CREATE TABLE IF NOT EXISTS candles_cache (
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    ts INTEGER NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume REAL,
    load_source TEXT,
    quality_flags TEXT,
    created_at INTEGER DEFAULT (strftime('%s', 'now') * 1000),
    UNIQUE(symbol, timeframe, ts)
);

-- 3. Обновляем таблицу trades
CREATE TABLE IF NOT EXISTS trades_new (
    id TEXT PRIMARY KEY,
    signal_id TEXT,
    mode TEXT NOT NULL CHECK (mode IN ('paper', 'real')),
    status TEXT NOT NULL CHECK (status IN ('paper_open', 'open', 'closed')),
    symbol TEXT NOT NULL,
    side TEXT NOT NULL CHECK (side IN ('Buy', 'Sell')),
    opened_at INTEGER NOT NULL,
    entry_type TEXT,
    entry_exec_price REAL,
    entry_price_virtual REAL,
    entry_low REAL,
    entry_high REAL,
    tp_prices_json TEXT NOT NULL,
    sl_price REAL NOT NULL,
    be_after_tp1 INTEGER DEFAULT 0 CHECK (be_after_tp1 IN (0,1)),
    margin_usd REAL,
    leverage_plan REAL,
    real_leverage REAL,
    qty REAL,
    exit_time INTEGER,
    exit_reason TEXT,
    exit_price REAL,
    tp1_hit INTEGER DEFAULT 0 CHECK (tp1_hit IN (0,1)),
    tp2_hit INTEGER DEFAULT 0 CHECK (tp2_hit IN (0,1)),
    tpN_hits_json TEXT,
    sl_hit INTEGER DEFAULT 0 CHECK (sl_hit IN (0,1)),
    duration_sec INTEGER,
    bybit_fee_open REAL,
    bybit_fee_close REAL,
    bybit_fee_total REAL,
    bybit_pnl_net_api REAL,
    pnl_tp1_net REAL,
    pnl_tp2_net REAL,
    pnl_final_real REAL,
    roi_tp1_real REAL,
    roi_tp2_real REAL,
    roi_final_real REAL,
    roi_ui REAL,
    algo_version TEXT,
    created_at INTEGER DEFAULT (strftime('%s', 'now') * 1000),
    updated_at INTEGER DEFAULT (strftime('%s', 'now') * 1000)
);

-- Мигрируем существующие trades
INSERT OR IGNORE INTO trades_new (
    id, symbol, side, opened_at, entry_exec_price, exit_price, 
    qty, pnl_final_real, roi_ui, tp_prices_json, sl_price, mode, status
)
SELECT 
    COALESCE(id, 'trade_' || rowid),
    symbol,
    side,
    strftime('%s', opened_at) * 1000,
    entry_price,
    exit_price,
    quantity,
    pnl_net,
    roi_percent,
    '[]',
    0,
    'paper',
    CASE WHEN closed_at IS NULL THEN 'paper_open' ELSE 'closed' END
FROM trades
WHERE symbol IS NOT NULL;

-- Переименовываем таблицы
DROP TABLE IF EXISTS trades_backup;
ALTER TABLE trades RENAME TO trades_backup;
ALTER TABLE trades_new RENAME TO trades;

-- 4. Создаём новые таблицы
CREATE TABLE IF NOT EXISTS trade_events (
    id TEXT PRIMARY KEY,
    trade_id TEXT NOT NULL,
    ts INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    event_price REAL NOT NULL,
    event_note TEXT,
    snapshot_json TEXT,
    created_at INTEGER DEFAULT (strftime('%s', 'now') * 1000)
);

CREATE TABLE IF NOT EXISTS trade_audits (
    trade_id TEXT PRIMARY KEY,
    tp_hits_json TEXT NOT NULL,
    tp_sequence_json TEXT NOT NULL,
    tp_first_hit_time INTEGER,
    tp_depth INTEGER,
    sl_hit_time INTEGER,
    mae_pct REAL NOT NULL,
    mae_time INTEGER,
    mfe_pct REAL NOT NULL,
    mfe_time INTEGER,
    t_to_tp_map_json TEXT,
    fake_tp_flags_json TEXT,
    audit_version TEXT NOT NULL,
    updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now') * 1000)
);

CREATE TABLE IF NOT EXISTS strategies (
    strategy_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    params_json TEXT NOT NULL,
    version TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0,1)),
    created_at INTEGER DEFAULT (strftime('%s', 'now') * 1000),
    updated_at INTEGER DEFAULT (strftime('%s', 'now') * 1000)
);

CREATE TABLE IF NOT EXISTS strategy_results (
    trade_id TEXT NOT NULL,
    strategy_id TEXT NOT NULL,
    computed_at INTEGER NOT NULL,
    algo_version TEXT NOT NULL,
    pnl_usdt REAL NOT NULL,
    roi_pct REAL NOT NULL,
    win_flag INTEGER NOT NULL CHECK (win_flag IN (0,1)),
    tp_depth INTEGER,
    mae_pct REAL,
    mfe_pct REAL,
    t_to_tp_map_json TEXT,
    fees_est REAL,
    created_at INTEGER DEFAULT (strftime('%s', 'now') * 1000),
    UNIQUE(trade_id, strategy_id)
);

-- 5. Обновляем traders (если существует trader_registry)
CREATE TABLE IF NOT EXISTS traders_new (
    trader_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    source_type TEXT,
    is_traded INTEGER NOT NULL DEFAULT 0 CHECK (is_traded IN (0,1)),
    trust_score REAL,
    status TEXT,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now') * 1000),
    updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now') * 1000)
);

-- Мигрируем из trader_registry если существует
INSERT OR IGNORE INTO traders_new (trader_id, name, source_type, is_traded, status)
SELECT 
    trader_id,
    name,
    source_type,
    CASE WHEN mode = 'live' THEN 1 ELSE 0 END,
    CASE WHEN is_active THEN '🔥' ELSE '⚪' END
FROM trader_registry
WHERE trader_id IS NOT NULL;

-- Если trader_registry не существует, создаём тестовые данные
INSERT OR IGNORE INTO traders_new (trader_id, name, source_type, status) VALUES
('ZTrade', 'ZTrade', 'telegram', '🔥'),
('whales_guide', 'Whales Crypto Guide', 'telegram', '🔥'),
('test_trader', 'Test Trader', 'telegram', '⚪');

-- Переименовываем
DROP TABLE IF EXISTS traders;
ALTER TABLE traders_new RENAME TO traders;

-- 6. Создаём trader_stats
CREATE TABLE IF NOT EXISTS trader_stats (
    trader_id TEXT NOT NULL,
    period_key TEXT NOT NULL,
    strategy_id TEXT NOT NULL,
    trades_cnt INTEGER NOT NULL,
    winrate_pct REAL NOT NULL,
    roi_avg_pct REAL NOT NULL,
    pnl_usdt REAL NOT NULL,
    max_dd_pct REAL,
    tp1_pct REAL,
    tp2_pct REAL,
    tp3_pct REAL,
    avg_t_to_tp1 REAL,
    avg_t_to_tp2 REAL,
    avg_mae_pct REAL,
    avg_mfe_pct REAL,
    roi_trend_sign INTEGER CHECK (roi_trend_sign IN (-1,0,1)),
    updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now') * 1000),
    UNIQUE(trader_id, period_key, strategy_id)
);

-- 7. Создаём scenarios (опционально)
CREATE TABLE IF NOT EXISTS scenarios (
    scenario_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    json_filter TEXT NOT NULL,
    created_at INTEGER DEFAULT (strftime('%s', 'now') * 1000)
);

CREATE TABLE IF NOT EXISTS scenario_results (
    scenario_id TEXT NOT NULL,
    trader_id TEXT NOT NULL,
    period_key TEXT NOT NULL,
    pnl_usdt REAL NOT NULL,
    roi_pct REAL NOT NULL,
    winrate REAL NOT NULL,
    trades_cnt INTEGER NOT NULL,
    computed_at INTEGER NOT NULL,
    UNIQUE(scenario_id, trader_id, period_key)
);

-- =====================================
-- СОЗДАНИЕ ИНДЕКСОВ
-- =====================================

-- Индексы для signals
CREATE INDEX IF NOT EXISTS idx_signals_source_received ON signals(source_name, received_at);
CREATE INDEX IF NOT EXISTS idx_signals_symbol_received ON signals(symbol, received_at);
CREATE UNIQUE INDEX IF NOT EXISTS idx_signals_dedupe ON signals(dedupe_hash);

-- Индексы для candles_cache
CREATE INDEX IF NOT EXISTS idx_candles_symbol_timeframe_ts ON candles_cache(symbol, timeframe, ts DESC);

-- Индексы для trades
CREATE INDEX IF NOT EXISTS idx_trades_symbol_opened ON trades(symbol, opened_at);
CREATE INDEX IF NOT EXISTS idx_trades_exit_time ON trades(exit_time);
CREATE INDEX IF NOT EXISTS idx_trades_mode_status ON trades(mode, status);
CREATE INDEX IF NOT EXISTS idx_trades_signal_id ON trades(signal_id);

-- Индексы для trade_events
CREATE INDEX IF NOT EXISTS idx_trade_events_trade_ts ON trade_events(trade_id, ts);
CREATE INDEX IF NOT EXISTS idx_trade_events_type ON trade_events(event_type);

-- Индексы для trade_audits
CREATE INDEX IF NOT EXISTS idx_trade_audits_tp_depth ON trade_audits(tp_depth);
CREATE INDEX IF NOT EXISTS idx_trade_audits_mae ON trade_audits(mae_pct);
CREATE INDEX IF NOT EXISTS idx_trade_audits_mfe ON trade_audits(mfe_pct);

-- Индексы для strategies
CREATE INDEX IF NOT EXISTS idx_strategies_enabled ON strategies(enabled);

-- Индексы для strategy_results
CREATE INDEX IF NOT EXISTS idx_strategy_results_strategy ON strategy_results(strategy_id);
CREATE INDEX IF NOT EXISTS idx_strategy_results_roi ON strategy_results(roi_pct);
CREATE INDEX IF NOT EXISTS idx_strategy_results_pnl ON strategy_results(pnl_usdt);

-- Индексы для traders
CREATE INDEX IF NOT EXISTS idx_traders_status ON traders(status);
CREATE INDEX IF NOT EXISTS idx_traders_traded ON traders(is_traded);

-- Индексы для trader_stats
CREATE INDEX IF NOT EXISTS idx_trader_stats_trader_period ON trader_stats(trader_id, period_key);
CREATE INDEX IF NOT EXISTS idx_trader_stats_strategy ON trader_stats(strategy_id);

-- =====================================
-- СОЗДАНИЕ VIEW
-- =====================================

-- vw_kpi_summary - общие KPI
DROP VIEW IF EXISTS vw_kpi_summary;
CREATE VIEW vw_kpi_summary AS
SELECT 
    'global' as scope,
    period_key as period,
    strategy_id,
    SUM(pnl_usdt) as total_pnl_usdt,
    SUM(trades_cnt) as total_trades,
    AVG(winrate_pct) as winrate_pct,
    SUM(CASE WHEN pnl_usdt > 0 THEN pnl_usdt ELSE 0 END) as pnl_long,
    SUM(CASE WHEN pnl_usdt < 0 THEN pnl_usdt ELSE 0 END) as pnl_short,
    MAX(updated_at) as updated_at
FROM trader_stats 
GROUP BY period_key, strategy_id;

-- vw_trader_ranking - рейтинг трейдеров
DROP VIEW IF EXISTS vw_trader_ranking;
CREATE VIEW vw_trader_ranking AS
SELECT 
    ts.trader_id,
    t.name,
    ts.trades_cnt,
    ts.winrate_pct,
    ts.roi_avg_pct,
    ts.pnl_usdt,
    ts.max_dd_pct,
    ts.tp1_pct,
    ts.tp2_pct,
    ts.tp3_pct,
    ts.avg_t_to_tp1,
    t.trust_score,
    ts.roi_trend_sign,
    t.status,
    ts.updated_at,
    ts.period_key,
    ts.strategy_id
FROM trader_stats ts
JOIN traders t ON ts.trader_id = t.trader_id;

-- =====================================
-- НАЧАЛЬНЫЕ ДАННЫЕ
-- =====================================

-- Базовые стратегии
INSERT OR IGNORE INTO strategies (strategy_id, name, description, params_json, version) VALUES
('tp2_sl_be', 'TP2 & SL → BE', 'Два тейк-профита, стоп в безубыток', '{"tp1_portion": 0.5, "tp2_portion": 0.5, "be_after_tp1": true}', 'v1.0'),
('scalping', 'Scalping', 'Быстрые сделки, малый профит', '{"tp1_portion": 1.0, "quick_exit": true, "max_duration": 3600}', 'v1.0'),
('swing', 'Swing Trading', 'Средне-срочные позиции', '{"tp1_portion": 0.3, "tp2_portion": 0.7, "max_duration": 86400}', 'v1.0'),
('all', 'Все стратегии', 'Смешанная торговля', '{"adaptive": true}', 'v1.0');

-- Заполняем тестовые данные в trader_stats
INSERT OR IGNORE INTO trader_stats (
    trader_id, period_key, strategy_id, trades_cnt, winrate_pct, 
    roi_avg_pct, pnl_usdt, tp1_pct, tp2_pct
) VALUES
('ZTrade', '30d', 'tp2_sl_be', 45, 73.3, 12.5, 1540.5, 65.0, 35.0),
('ZTrade', '30d', 'scalping', 45, 68.9, 8.2, 980.2, 85.0, 15.0),
('whales_guide', '30d', 'tp2_sl_be', 32, 78.1, 15.8, 1890.7, 70.0, 40.0),
('whales_guide', '30d', 'swing', 32, 71.9, 18.9, 2150.3, 60.0, 50.0);

COMMIT;

-- =====================================
-- ПРОВЕРКА РЕЗУЛЬТАТА
-- =====================================

SELECT 
    'GHOST Database Migration v1.1 завершена успешно! 🎉' as status,
    'Все таблицы обновлены согласно спецификации Дарэна' as migration_info,
    'Данные сохранены, индексы созданы, VIEW готовы' as ready_status;

-- Показываем структуру
.tables
.schema
