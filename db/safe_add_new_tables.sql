-- GHOST Database Safe Migration: Only Add New Tables
-- This script ONLY creates new tables and views, does NOT modify existing ones
-- Safe to run in production - no data loss risk

-- ================================================
-- 1. NEW TABLES (safe creation with IF NOT EXISTS)
-- ================================================

-- Trade Events - normalized event stream for trades
CREATE TABLE IF NOT EXISTS trade_events (
    id TEXT PRIMARY KEY,
    trade_id TEXT NOT NULL,
    ts INTEGER NOT NULL,
    event_type TEXT NOT NULL, -- tp1/tp2/.../sl/be_move/timeout
    event_price REAL NOT NULL,
    event_note TEXT,
    snapshot_json TEXT, -- JSON snapshot of position/params
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trade Audits - aggregated trade audit (hit facts, MAE/MFE)
CREATE TABLE IF NOT EXISTS trade_audits (
    trade_id TEXT PRIMARY KEY,
    tp_hits_json TEXT NOT NULL, -- {tp1:{hit,time,price}, ...}
    tp_sequence_json TEXT NOT NULL, -- Events by time (["TP1","TP2","BE","SL"])
    tp_first_hit_time INTEGER,
    tp_depth INTEGER, -- Max achieved TP number
    sl_hit_time INTEGER,
    mae_pct REAL NOT NULL, -- Max adverse excursion % of margin
    mae_time INTEGER,
    mfe_pct REAL NOT NULL, -- Max favorable excursion % of margin
    mfe_time INTEGER,
    t_to_tp_map_json TEXT, -- {tp1:sec,tp2:sec,...}
    fake_tp_flags_json TEXT, -- {tp1:false,tp2:true,...} (high/low check)
    audit_version TEXT NOT NULL,
    updated_at INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Strategies catalog
CREATE TABLE IF NOT EXISTS strategies (
    strategy_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    params_json TEXT NOT NULL, -- Shares/BE/trailing/timeout etc.
    version TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1, -- 0/1
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Strategy Results - cache of result per trade and strategy
CREATE TABLE IF NOT EXISTS strategy_results (
    trade_id TEXT NOT NULL,
    strategy_id TEXT NOT NULL,
    computed_at INTEGER NOT NULL,
    algo_version TEXT NOT NULL,
    pnl_usdt REAL NOT NULL,
    roi_pct REAL NOT NULL,
    win_flag INTEGER NOT NULL, -- 0/1
    tp_depth INTEGER,
    mae_pct REAL,
    mfe_pct REAL,
    t_to_tp_map_json TEXT,
    fees_est REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (trade_id, strategy_id)
);

-- Trader Stats - aggregates per trader (by period and strategy)
CREATE TABLE IF NOT EXISTS trader_stats (
    trader_id TEXT NOT NULL,
    period_key TEXT NOT NULL, -- 7d/30d/ytd/all
    strategy_id TEXT NOT NULL,
    trades_cnt INTEGER NOT NULL,
    winrate_pct REAL NOT NULL,
    roi_avg_pct REAL NOT NULL,
    pnl_usdt REAL NOT NULL,
    max_dd_pct REAL,
    tp1_pct REAL, -- Share of TP1 hits
    tp2_pct REAL, -- Share of TP2 hits
    tp3_pct REAL, -- Share of TP3 hits
    avg_t_to_tp1 REAL, -- Avg time to TP1 (sec)
    avg_t_to_tp2 REAL, -- Avg time to TP2 (sec)
    avg_mae_pct REAL, -- Avg MAE %
    avg_mfe_pct REAL, -- Avg MFE %
    roi_trend_sign INTEGER, -- -1/0/1
    updated_at INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (trader_id, period_key, strategy_id)
);

-- Candles Cache - market/candles (context and stream)
CREATE TABLE IF NOT EXISTS candles_cache (
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL, -- 1m,5m,...
    ts INTEGER NOT NULL, -- unix ms, open time
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume REAL,
    load_source TEXT, -- rest/ws
    quality_flags TEXT, -- JSON - quality signs/latch
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (symbol, timeframe, ts)
);

-- Scenarios (optional) - what-if filters
CREATE TABLE IF NOT EXISTS scenarios (
    scenario_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    json_filter TEXT NOT NULL, -- JSON filter conditions
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scenario Results (optional)
CREATE TABLE IF NOT EXISTS scenario_results (
    scenario_id TEXT NOT NULL,
    trader_id TEXT NOT NULL,
    period_key TEXT NOT NULL,
    pnl_usdt REAL NOT NULL,
    roi_pct REAL NOT NULL,
    winrate REAL NOT NULL,
    trades_cnt INTEGER NOT NULL,
    computed_at INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (scenario_id, trader_id, period_key)
);

-- ================================================
-- 2. INDEXES for performance (safe creation)
-- ================================================

-- Trade Events indexes
CREATE INDEX IF NOT EXISTS idx_trade_events_trade_id ON trade_events(trade_id, ts);
CREATE INDEX IF NOT EXISTS idx_trade_events_type ON trade_events(event_type);

-- Trade Audits indexes
CREATE INDEX IF NOT EXISTS idx_trade_audits_depth ON trade_audits(tp_depth);
CREATE INDEX IF NOT EXISTS idx_trade_audits_mae ON trade_audits(mae_pct);
CREATE INDEX IF NOT EXISTS idx_trade_audits_mfe ON trade_audits(mfe_pct);

-- Strategy Results indexes
CREATE INDEX IF NOT EXISTS idx_strategy_results_strategy ON strategy_results(strategy_id);
CREATE INDEX IF NOT EXISTS idx_strategy_results_roi ON strategy_results(roi_pct);
CREATE INDEX IF NOT EXISTS idx_strategy_results_pnl ON strategy_results(pnl_usdt);

-- Candles Cache indexes
CREATE INDEX IF NOT EXISTS idx_candles_symbol_time ON candles_cache(symbol, ts);
CREATE INDEX IF NOT EXISTS idx_candles_timeframe ON candles_cache(timeframe, ts);

-- ================================================
-- 3. VIEWS for UI (safe creation)
-- ================================================

-- KPI Summary View
CREATE OR REPLACE VIEW vw_kpi_summary AS
SELECT 
    'all' as scope,
    '30d' as period,
    'all' as strategy_id,
    COALESCE(SUM(pnl_usdt), 0) as total_pnl_usdt,
    COUNT(*) as total_trades,
    COALESCE(AVG(CASE WHEN win_flag = 1 THEN 100.0 ELSE 0.0 END), 0) as winrate_pct,
    COALESCE(SUM(CASE WHEN pnl_usdt > 0 THEN pnl_usdt ELSE 0 END), 0) as pnl_long,
    COALESCE(SUM(CASE WHEN pnl_usdt < 0 THEN pnl_usdt ELSE 0 END), 0) as pnl_short,
    MAX(computed_at) as updated_at
FROM strategy_results 
WHERE strategy_id = 'tp2_sl_be';

-- Trader Ranking View
CREATE OR REPLACE VIEW vw_trader_ranking AS
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
    COALESCE(t.trust_score, 0.5) as trust_score,
    ts.roi_trend_sign,
    COALESCE(t.status, '⚪') as status,
    ts.updated_at
FROM trader_stats ts
LEFT JOIN traders t ON ts.trader_id = t.trader_id
WHERE ts.period_key = '30d' AND ts.strategy_id = 'tp2_sl_be';

-- P&L Series View
CREATE OR REPLACE VIEW vw_pnl_series AS
SELECT 
    sr.computed_at as ts,
    SUM(sr.pnl_usdt) OVER (ORDER BY sr.computed_at) as pnl_cum_norm,
    sr.pnl_usdt as pnl_step_norm,
    NULL as symbol_opt
FROM strategy_results sr
WHERE sr.strategy_id = 'tp2_sl_be'
ORDER BY sr.computed_at;

-- ================================================
-- 4. INSERT DEFAULT STRATEGIES (safe with ON CONFLICT)
-- ================================================

INSERT INTO strategies (strategy_id, name, description, params_json, version, enabled) VALUES
('tp2_sl_be', 'TP2 & SL → BE', 'Take 50% at TP1, move SL to BE, exit remainder at TP2', '{"tp1_share": 0.5, "be_after_tp1": true, "tp2_exit": true}', '1.0', 1),
('scalping', 'Scalping', 'Quick entries and exits, small profits', '{"tp1_share": 0.8, "be_after_tp1": false, "timeout_sec": 300}', '1.0', 1),
('swing', 'Swing Trading', 'Hold positions longer, target higher TPs', '{"tp1_share": 0.3, "tp2_share": 0.4, "tp3_target": true}', '1.0', 1),
('all', 'All Strategies', 'Combined view of all strategies', '{"combined": true}', '1.0', 1)
ON CONFLICT (strategy_id) DO NOTHING;

-- ================================================
-- SUCCESS MESSAGE
-- ================================================

-- This script has safely added new tables and views to your database
-- without modifying any existing data or structures.
-- 
-- Next steps:
-- 1. Your existing data in signals_parsed, trader_registry, etc. remains untouched
-- 2. New features will use the new tables
-- 3. You can gradually migrate data using separate scripts if needed
