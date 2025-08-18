-- GHOST Virtual Trades Table
-- Версия: v1.0
-- Назначение: Хранить виртуальные сделки изолированно от реальных trades
-- Стратегия: TP1(50%) → SL в BE → TP2(50%)

-- Создаем ENUM типы для строгой типизации
CREATE TYPE trade_side AS ENUM ('LONG', 'SHORT');
CREATE TYPE entry_type AS ENUM ('zone', 'exact');
CREATE TYPE virtual_status AS ENUM ('sim_open', 'sim_closed', 'sim_skipped');
CREATE TYPE source_type AS ENUM ('telegram', 'manual', 'api');

-- Основная таблица виртуальных сделок
CREATE TABLE IF NOT EXISTS v_trades (
  -- 1) Идентификация/Источник
  id                TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  signal_id         TEXT,                    -- UUID исходного сообщения (если есть)
  source            TEXT,                    -- канал/трейдер (e.g. tg_binance_killers)
  source_type       source_type DEFAULT 'telegram',
  source_name       TEXT,                    -- человекочитаемое имя канала
  source_ref        TEXT,                    -- ссылка/ID в источнике
  original_text     TEXT,                    -- сырой текст сигнала
  signal_reason     TEXT,                    -- причина (из текста, опционально)
  posted_ts         BIGINT,                  -- unix ms, время публикации сигнала

  -- 2) Паспорт сигнала
  symbol            TEXT NOT NULL,           -- YGGUSDT
  side              trade_side NOT NULL,     -- LONG/SHORT
  entry_type        entry_type DEFAULT 'zone',
  entry_min         NUMERIC(20, 8),          -- нижняя граница зоны (или = entry_exact)
  entry_max         NUMERIC(20, 8),          -- верхняя граница зоны (или = entry_exact)
  tp1               NUMERIC(20, 8),          
  tp2               NUMERIC(20, 8),
  tp3               NUMERIC(20, 8),          -- на будущее; сейчас считаем по 2 TP
  targets_json      JSONB,                   -- все цели списком (JSON)
  sl                NUMERIC(20, 8),
  sl_type           TEXT DEFAULT 'hard',
  source_leverage   TEXT,                    -- как в тексте сигнала (например "5-10")

  -- 3) Параметры симуляции
  strategy_id       TEXT DEFAULT 'S_A_TP1_BE_TP2',
  strategy_version  TEXT DEFAULT '1',
  fee_rate          NUMERIC(10, 6) DEFAULT 0.00055,  -- 0.055% taker
  leverage          NUMERIC(10, 2) DEFAULT 15,
  margin_usd        NUMERIC(10, 2) DEFAULT 100,
  entry_timeout_sec INTEGER DEFAULT 172800,  -- 48ч

  -- 4) Виртуальный вход
  was_fillable      BOOLEAN DEFAULT FALSE,   -- 0/1 (вход достижим)
  entry_ts          BIGINT,                  -- unix ms (когда «вошли»)
  entry_price       NUMERIC(20, 8),          -- цена входа
  position_qty      NUMERIC(20, 8),          -- qty = margin*lev/entry_price

  -- 5) События по ходу сделки
  tp1_hit           BOOLEAN DEFAULT FALSE,
  tp1_ts            BIGINT,
  be_hit            BOOLEAN DEFAULT FALSE,
  be_ts             BIGINT,
  be_price          NUMERIC(20, 8),          -- = entry_price при переносе SL в BE
  tp2_hit           BOOLEAN DEFAULT FALSE,
  tp2_ts            BIGINT,
  sl_hit            BOOLEAN DEFAULT FALSE,
  sl_ts             BIGINT,

  -- 6) Финансы (виртуальные)
  fee_open          NUMERIC(20, 8),          -- комиссия входа
  fee_close         NUMERIC(20, 8),          -- суммарные комиссии выходов
  fee_total         NUMERIC(20, 8),          -- fee_open + fee_close
  pnl_tp1           NUMERIC(20, 8),          -- gross по ноге TP1 (без комиссий)
  pnl_tp2           NUMERIC(20, 8),          -- gross по ноге TP2 (без комиссий; 0 при BE)
  pnl_gross         NUMERIC(20, 8),          -- суммарно по ногам (или SL)
  pnl_net           NUMERIC(20, 8),          -- после комиссий
  roi_percent       NUMERIC(10, 4),          -- pnl_net / margin_usd * 100

  -- 7) Длительности/итоги
  closed_ts         BIGINT,                  -- unix ms финального выхода
  duration_sec      INTEGER,                 -- closed_ts - entry_ts
  tp1_duration_sec  INTEGER,
  tp2_duration_sec  INTEGER,
  sl_duration_sec   INTEGER,
  status            virtual_status DEFAULT 'sim_open',
  exit_reason       TEXT,                    -- 'tp2' | 'tp1_be' | 'sl' | 'skipped' | 'timeout'
  tp_hit            TEXT,                    -- 'tp1,tp2' | 'tp1,be' | '' (для удобства отчетов)
  tp_count_hit      INTEGER DEFAULT 0,       -- 0/1/2

  -- 8) Аналитика фондового уровня
  mfe_pct           NUMERIC(10, 4),          -- максимум «в плюс» от входа (% к entry_price)
  mae_pct           NUMERIC(10, 4),          -- максимум «в минус» от входа
  reached_after_exit JSONB,                 -- JSON: TP, которых рынок достиг уже после выхода

  -- 9) Служебное
  created_at        TIMESTAMPTZ DEFAULT NOW(),
  updated_at        TIMESTAMPTZ DEFAULT NOW()
);

-- Индексы под симулятор и отчеты
CREATE INDEX IF NOT EXISTS idx_vtrades_status ON v_trades(status);
CREATE INDEX IF NOT EXISTS idx_vtrades_symbol_ts ON v_trades(symbol, posted_ts);
CREATE INDEX IF NOT EXISTS idx_vtrades_strategy ON v_trades(strategy_id, posted_ts);
CREATE INDEX IF NOT EXISTS idx_vtrades_created_at ON v_trades(created_at);
CREATE INDEX IF NOT EXISTS idx_vtrades_side_symbol ON v_trades(side, symbol);
CREATE INDEX IF NOT EXISTS idx_vtrades_source ON v_trades(source_type, source);

-- Добавляем RLS (Row Level Security) если нужно
ALTER TABLE v_trades ENABLE ROW LEVEL SECURITY;

-- Политика доступа (для admin/authenticated users)
CREATE POLICY "Enable read access for authenticated users" ON v_trades
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Enable insert access for authenticated users" ON v_trades
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Enable update access for authenticated users" ON v_trades
    FOR UPDATE USING (auth.role() = 'authenticated');

-- Trigger для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_vtrades_updated_at BEFORE UPDATE ON v_trades
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Комментарии к таблице и ключевым полям
COMMENT ON TABLE v_trades IS 'Virtual trades table for signal simulation with TP1→BE→TP2 strategy';
COMMENT ON COLUMN v_trades.strategy_id IS 'Trading strategy identifier (S_A_TP1_BE_TP2 = Strategy A: TP1 then move SL to BE then TP2)';
COMMENT ON COLUMN v_trades.status IS 'Simulation status: sim_open (running), sim_closed (finished), sim_skipped (not processed)';
COMMENT ON COLUMN v_trades.tp_count_hit IS 'Number of take profits hit: 0, 1, or 2';
