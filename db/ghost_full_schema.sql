-- 🏆 GHOST FULL DATABASE SCHEMA v1.1
-- Полная схема после аудита сигналов согласно спецификации Дарэна
-- Единая БД: ghost.db
-- Слои: signals • candles_cache • trades • trade_events • trade_audits • strategies • strategy_results • traders • trader_stats • scenarios • scenario_results
-- Методология ROI/PNL/комиссий: строго как в position_exit_tracker.py
-- Нотация типов: SQLite; JSON храним как TEXT с валидным JSON

-- =====================================
-- 1) SIGNALS — первичная «правда» сигнала (immutable)
-- =====================================

CREATE TABLE IF NOT EXISTS signals (
    id TEXT PRIMARY KEY,                        -- UUID сигнала
    received_at INTEGER NOT NULL,               -- Время получения (unix ms)
    source_name TEXT NOT NULL,                  -- Канал/источник (e.g. Whales Crypto Guide)
    source_id TEXT,                            -- Внутренний ID источника
    raw_text TEXT NOT NULL,                    -- Исходный текст поста
    symbol_raw TEXT NOT NULL,                  -- Как в посте
    symbol TEXT NOT NULL,                      -- Нормализованный (e.g. BELUSDT)
    side TEXT NOT NULL CHECK (side IN ('Buy', 'Sell')), -- Long/Short
    entry_low REAL NOT NULL,                   -- Нижняя граница входа
    entry_high REAL NOT NULL,                  -- Верхняя граница входа
    targets_json TEXT NOT NULL,                -- [tp1,tp2,...,tpN] (цены) JSON array
    stoploss REAL NOT NULL,                    -- SL из поста
    leverage_hint_min REAL,                    -- Мин. плечо
    leverage_hint_max REAL,                    -- Макс. плечо
    reason_text TEXT,                          -- Комментарий автора
    parse_version TEXT NOT NULL,               -- Версия парсера
    parsed_ok INTEGER NOT NULL DEFAULT 1 CHECK (parsed_ok IN (0,1)), -- Флаг успеха парсинга
    precision_hint_json TEXT,                  -- Точность/тик-сайз/мин.шаг JSON
    dedupe_hash TEXT,                          -- Антидубль (индекс)
    created_at INTEGER DEFAULT (strftime('%s', 'now') * 1000)
);

-- Индексы для signals
CREATE INDEX IF NOT EXISTS idx_signals_source_received ON signals(source_name, received_at);
CREATE INDEX IF NOT EXISTS idx_signals_symbol_received ON signals(symbol, received_at);
CREATE UNIQUE INDEX IF NOT EXISTS idx_signals_dedupe ON signals(dedupe_hash);

-- =====================================
-- 2) CANDLES_CACHE — рынок/свечи (контекст и поток)
-- =====================================

CREATE TABLE IF NOT EXISTS candles_cache (
    symbol TEXT NOT NULL,                      -- Тикер
    timeframe TEXT NOT NULL,                   -- ТФ (1m,5m,...)
    ts INTEGER NOT NULL,                       -- Метка времени свечи (unix ms, open time)
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume REAL,
    load_source TEXT,                          -- rest/ws
    quality_flags TEXT,                        -- Признаки качества/латч JSON
    created_at INTEGER DEFAULT (strftime('%s', 'now') * 1000),
    
    UNIQUE(symbol, timeframe, ts)
);

-- Индексы для candles_cache
CREATE INDEX IF NOT EXISTS idx_candles_symbol_timeframe_ts ON candles_cache(symbol, timeframe, ts DESC);

-- =====================================
-- 3) TRADES — сделки (реальные и бумажные)
-- =====================================

CREATE TABLE IF NOT EXISTS trades (
    id TEXT PRIMARY KEY,                       -- UUID
    signal_id TEXT REFERENCES signals(id),     -- Связь с сигналом
    mode TEXT NOT NULL CHECK (mode IN ('paper', 'real')), -- Режим
    status TEXT NOT NULL CHECK (status IN ('paper_open', 'open', 'closed')), -- Статус
    symbol TEXT NOT NULL,                      -- Тикер
    side TEXT NOT NULL CHECK (side IN ('Buy', 'Sell')), -- Направление
    opened_at INTEGER NOT NULL,                -- Время открытия (вирт./факт)
    entry_type TEXT,                          -- zone_mid/market/limit
    entry_exec_price REAL,                   -- Факт входа (real)
    entry_price_virtual REAL,                -- Виртуальный вход (paper)
    entry_low REAL,                          -- Копия зоны
    entry_high REAL,                         -- Копия зоны
    tp_prices_json TEXT NOT NULL,            -- [tp1,tp2,...] JSON
    sl_price REAL NOT NULL,                  -- SL
    be_after_tp1 INTEGER DEFAULT 0 CHECK (be_after_tp1 IN (0,1)), -- BE после TP1 (план)
    margin_usd REAL,                         -- Нормализация (paper=100)
    leverage_plan REAL,                      -- План плеча
    real_leverage REAL,                      -- Факт плеча (real)
    qty REAL,                               -- Кол-во (real)
    exit_time INTEGER,                       -- Время закрытия
    exit_reason TEXT,                        -- tp2/tp1_be/sl/manual/timeout
    exit_price REAL,                         -- Факт/вирт. выход
    tp1_hit INTEGER DEFAULT 0 CHECK (tp1_hit IN (0,1)), -- Факт касания TP1
    tp2_hit INTEGER DEFAULT 0 CHECK (tp2_hit IN (0,1)), -- Факт касания TP2
    tpN_hits_json TEXT,                      -- { "tp3":true, ... } JSON
    sl_hit INTEGER DEFAULT 0 CHECK (sl_hit IN (0,1)), -- Факт касания SL
    duration_sec INTEGER,                    -- Длительность
    bybit_fee_open REAL,                     -- Комиссия вход
    bybit_fee_close REAL,                    -- Комиссия выход
    bybit_fee_total REAL,                    -- Комиссии всего
    bybit_pnl_net_api REAL,                  -- Истинный PnL из API
    pnl_tp1_net REAL,                        -- Net PnL ноги TP1
    pnl_tp2_net REAL,                        -- Net PnL ноги TP2/BE
    pnl_final_real REAL,                     -- Итоговый PnL (fallback)
    roi_tp1_real REAL,                       -- ROI TP1 от маржи
    roi_tp2_real REAL,                       -- ROI TP2/BE от маржи
    roi_final_real REAL,                     -- Итоговый ROI от маржи
    roi_ui REAL,                            -- UI-ROI (по методике)
    algo_version TEXT,                       -- Версия формул
    created_at INTEGER DEFAULT (strftime('%s', 'now') * 1000),
    updated_at INTEGER DEFAULT (strftime('%s', 'now') * 1000)
);

-- Индексы для trades
CREATE INDEX IF NOT EXISTS idx_trades_symbol_opened ON trades(symbol, opened_at);
CREATE INDEX IF NOT EXISTS idx_trades_exit_time ON trades(exit_time);
CREATE INDEX IF NOT EXISTS idx_trades_mode_status ON trades(mode, status);
CREATE INDEX IF NOT EXISTS idx_trades_signal_id ON trades(signal_id);

-- =====================================
-- 4) TRADE_EVENTS — нормализованная лента событий по сделке
-- =====================================

CREATE TABLE IF NOT EXISTS trade_events (
    id TEXT PRIMARY KEY,                       -- UUID события
    trade_id TEXT NOT NULL REFERENCES trades(id), -- Сделка
    ts INTEGER NOT NULL,                       -- Время события
    event_type TEXT NOT NULL,                  -- tp1/tp2/.../sl/be_move/timeout
    event_price REAL NOT NULL,                 -- Цена срабатывания
    event_note TEXT,                          -- Доп. инфо
    snapshot_json TEXT,                        -- Срез позиции/параметров JSON
    created_at INTEGER DEFAULT (strftime('%s', 'now') * 1000)
);

-- Индексы для trade_events
CREATE INDEX IF NOT EXISTS idx_trade_events_trade_ts ON trade_events(trade_id, ts);
CREATE INDEX IF NOT EXISTS idx_trade_events_type ON trade_events(event_type);

-- =====================================
-- 5) TRADE_AUDITS — агрегированный аудит сделки
-- =====================================

CREATE TABLE IF NOT EXISTS trade_audits (
    trade_id TEXT PRIMARY KEY REFERENCES trades(id),
    tp_hits_json TEXT NOT NULL,               -- {tp1:{hit,time,price}, ...} JSON
    tp_sequence_json TEXT NOT NULL,           -- События по времени (["TP1","TP2","BE","SL"]) JSON
    tp_first_hit_time INTEGER,               -- Время первого TP
    tp_depth INTEGER,                        -- Максимально достигнутый TP-номер
    sl_hit_time INTEGER,                     -- Время SL (если было)
    mae_pct REAL NOT NULL,                   -- Max adverse excursion % маржи
    mae_time INTEGER,                        -- Когда случился MAE
    mfe_pct REAL NOT NULL,                   -- Max favorable excursion % маржи
    mfe_time INTEGER,                        -- Когда случился MFE
    t_to_tp_map_json TEXT,                   -- {tp1:sec,tp2:sec,...} JSON
    fake_tp_flags_json TEXT,                 -- {tp1:false,tp2:true,...} (high/low check) JSON
    audit_version TEXT NOT NULL,             -- Версия аудита
    updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now') * 1000)
);

-- Индексы для trade_audits
CREATE INDEX IF NOT EXISTS idx_trade_audits_tp_depth ON trade_audits(tp_depth);
CREATE INDEX IF NOT EXISTS idx_trade_audits_mae ON trade_audits(mae_pct);
CREATE INDEX IF NOT EXISTS idx_trade_audits_mfe ON trade_audits(mfe_pct);

-- =====================================
-- 6) STRATEGIES — каталог стратегий исполнения
-- =====================================

CREATE TABLE IF NOT EXISTS strategies (
    strategy_id TEXT PRIMARY KEY,             -- ID
    name TEXT NOT NULL,                       -- Читабельное имя
    description TEXT,                         -- Описание
    params_json TEXT NOT NULL,                -- Доли/BE/трейлинг/timeout и т.п. JSON
    version TEXT NOT NULL,                    -- Версия
    enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0,1)), -- Активна
    created_at INTEGER DEFAULT (strftime('%s', 'now') * 1000),
    updated_at INTEGER DEFAULT (strftime('%s', 'now') * 1000)
);

-- Индекс для strategies
CREATE INDEX IF NOT EXISTS idx_strategies_enabled ON strategies(enabled);

-- =====================================
-- 7) STRATEGY_RESULTS — кэш результата по каждой сделке и стратегии
-- =====================================

CREATE TABLE IF NOT EXISTS strategy_results (
    trade_id TEXT NOT NULL REFERENCES trades(id),
    strategy_id TEXT NOT NULL REFERENCES strategies(strategy_id),
    computed_at INTEGER NOT NULL,             -- Когда посчитали
    algo_version TEXT NOT NULL,               -- Версия симулятора
    pnl_usdt REAL NOT NULL,                  -- Итоговый PnL (net)
    roi_pct REAL NOT NULL,                   -- Итоговый ROI% от маржи
    win_flag INTEGER NOT NULL CHECK (win_flag IN (0,1)), -- Win/Loss по стратегии
    tp_depth INTEGER,                        -- Достигнутый TPn в модели
    mae_pct REAL,                           -- MAE в модели
    mfe_pct REAL,                           -- MFE в модели
    t_to_tp_map_json TEXT,                  -- Тайминги до целей JSON
    fees_est REAL,                          -- Комиссии (методика как в трекере)
    created_at INTEGER DEFAULT (strftime('%s', 'now') * 1000),
    
    UNIQUE(trade_id, strategy_id)
);

-- Индексы для strategy_results
CREATE INDEX IF NOT EXISTS idx_strategy_results_strategy ON strategy_results(strategy_id);
CREATE INDEX IF NOT EXISTS idx_strategy_results_roi ON strategy_results(roi_pct);
CREATE INDEX IF NOT EXISTS idx_strategy_results_pnl ON strategy_results(pnl_usdt);

-- =====================================
-- 8) TRADERS — справочник трейдеров/каналов
-- =====================================

CREATE TABLE IF NOT EXISTS traders (
    trader_id TEXT PRIMARY KEY,              -- ID/slug
    name TEXT NOT NULL,                      -- Имя/псевдоним
    source_type TEXT,                        -- telegram/discord/ai
    is_traded INTEGER NOT NULL DEFAULT 0 CHECK (is_traded IN (0,1)), -- В реальном портфеле?
    trust_score REAL,                        -- Индекс доверия
    status TEXT,                             -- 🔥/🟡/🔴/🛑/⚪
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now') * 1000),
    updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now') * 1000)
);

-- Индекс для traders
CREATE INDEX IF NOT EXISTS idx_traders_status ON traders(status);
CREATE INDEX IF NOT EXISTS idx_traders_traded ON traders(is_traded);

-- =====================================
-- 9) TRADER_STATS — агрегаты по трейдеру (по периоду и стратегии)
-- =====================================

CREATE TABLE IF NOT EXISTS trader_stats (
    trader_id TEXT NOT NULL REFERENCES traders(trader_id),
    period_key TEXT NOT NULL,                -- 7d/30d/ytd/all
    strategy_id TEXT NOT NULL,               -- Для честного сравнения
    trades_cnt INTEGER NOT NULL,             -- Кол-во сделок
    winrate_pct REAL NOT NULL,              -- % побед
    roi_avg_pct REAL NOT NULL,              -- Ср. ROI%
    pnl_usdt REAL NOT NULL,                 -- Суммарный PnL
    max_dd_pct REAL,                        -- Макс. просадка
    tp1_pct REAL,                           -- Доля TP1-касаний
    tp2_pct REAL,                           -- Доля TP2-касаний
    tp3_pct REAL,                           -- Доля TP3-касаний
    avg_t_to_tp1 REAL,                      -- Ср. время до TP1 (сек)
    avg_t_to_tp2 REAL,                      -- Ср. время до TP2 (сек)
    avg_mae_pct REAL,                       -- Ср. MAE %
    avg_mfe_pct REAL,                       -- Ср. MFE %
    roi_trend_sign INTEGER CHECK (roi_trend_sign IN (-1,0,1)), -- Тренд ROI
    updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now') * 1000),
    
    UNIQUE(trader_id, period_key, strategy_id)
);

-- Индексы для trader_stats
CREATE INDEX IF NOT EXISTS idx_trader_stats_trader_period ON trader_stats(trader_id, period_key);
CREATE INDEX IF NOT EXISTS idx_trader_stats_strategy ON trader_stats(strategy_id);

-- =====================================
-- 10) SCENARIOS & SCENARIO_RESULTS — what-if фильтры (опционально)
-- =====================================

CREATE TABLE IF NOT EXISTS scenarios (
    scenario_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    json_filter TEXT NOT NULL,               -- JSON filter
    created_at INTEGER DEFAULT (strftime('%s', 'now') * 1000)
);

CREATE TABLE IF NOT EXISTS scenario_results (
    scenario_id TEXT NOT NULL REFERENCES scenarios(scenario_id),
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
-- 11) VIEWS под UI (колонки результирующих представлений)
-- =====================================

-- vw_kpi_summary - общие KPI
CREATE VIEW IF NOT EXISTS vw_kpi_summary AS
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
CREATE VIEW IF NOT EXISTS vw_trader_ranking AS
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

-- Тестовый трейдер
INSERT OR IGNORE INTO traders (trader_id, name, source_type, status) VALUES
('ZTrade', 'ZTrade', 'telegram', '🔥'),
('whales_guide', 'Whales Crypto Guide', 'telegram', '🔥'),
('test_trader', 'Test Trader', 'telegram', '⚪');

-- =====================================
-- ЗАВЕРШЕНИЕ
-- =====================================

-- Включаем внешние ключи
PRAGMA foreign_keys = ON;

SELECT 
    'GHOST Full Database Schema v1.1 создана успешно! 🎉' as status,
    'Таблиц создано: 11 основных + 2 VIEW' as tables_info,
    'Готова для полного цикла сбора/аудита сигналов' as ready_status;
