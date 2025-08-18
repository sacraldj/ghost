-- GHOST Virtual Trades Table Creation Script
-- Выполните этот SQL в Supabase SQL Editor

-- 1. Создаем ENUM типы
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'trade_side') THEN
        CREATE TYPE trade_side AS ENUM ('LONG', 'SHORT');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'entry_type') THEN
        CREATE TYPE entry_type AS ENUM ('zone', 'exact');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'virtual_status') THEN
        CREATE TYPE virtual_status AS ENUM ('sim_open', 'sim_closed', 'sim_skipped');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'source_type') THEN
        CREATE TYPE source_type AS ENUM ('telegram', 'manual', 'api');
    END IF;
END $$;

-- 2. Создаем основную таблицу
CREATE TABLE IF NOT EXISTS v_trades (
  -- 1) Идентификация/Источник
  id                TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  signal_id         TEXT,
  source            TEXT,
  source_type       source_type DEFAULT 'telegram',
  source_name       TEXT,
  source_ref        TEXT,
  original_text     TEXT,
  signal_reason     TEXT,
  posted_ts         BIGINT,

  -- 2) Паспорт сигнала
  symbol            TEXT NOT NULL,
  side              trade_side NOT NULL,
  entry_type        entry_type DEFAULT 'zone',
  entry_min         NUMERIC(20, 8),
  entry_max         NUMERIC(20, 8),
  tp1               NUMERIC(20, 8),
  tp2               NUMERIC(20, 8),
  tp3               NUMERIC(20, 8),
  targets_json      JSONB,
  sl                NUMERIC(20, 8),
  sl_type           TEXT DEFAULT 'hard',
  source_leverage   TEXT,

  -- 3) Параметры симуляции
  strategy_id       TEXT DEFAULT 'S_A_TP1_BE_TP2',
  strategy_version  TEXT DEFAULT '1',
  fee_rate          NUMERIC(10, 6) DEFAULT 0.00055,
  leverage          NUMERIC(10, 2) DEFAULT 15,
  margin_usd        NUMERIC(10, 2) DEFAULT 100,
  entry_timeout_sec INTEGER DEFAULT 172800,

  -- 4) Виртуальный вход
  was_fillable      BOOLEAN DEFAULT FALSE,
  entry_ts          BIGINT,
  entry_price       NUMERIC(20, 8),
  position_qty      NUMERIC(20, 8),

  -- 5) События по ходу сделки
  tp1_hit           BOOLEAN DEFAULT FALSE,
  tp1_ts            BIGINT,
  be_hit            BOOLEAN DEFAULT FALSE,
  be_ts             BIGINT,
  be_price          NUMERIC(20, 8),
  tp2_hit           BOOLEAN DEFAULT FALSE,
  tp2_ts            BIGINT,
  sl_hit            BOOLEAN DEFAULT FALSE,
  sl_ts             BIGINT,

  -- 6) Финансы (виртуальные)
  fee_open          NUMERIC(20, 8),
  fee_close         NUMERIC(20, 8),
  fee_total         NUMERIC(20, 8),
  pnl_tp1           NUMERIC(20, 8),
  pnl_tp2           NUMERIC(20, 8),
  pnl_gross         NUMERIC(20, 8),
  pnl_net           NUMERIC(20, 8),
  roi_percent       NUMERIC(10, 4),

  -- 7) Длительности/итоги
  closed_ts         BIGINT,
  duration_sec      INTEGER,
  tp1_duration_sec  INTEGER,
  tp2_duration_sec  INTEGER,
  sl_duration_sec   INTEGER,
  status            virtual_status DEFAULT 'sim_open',
  exit_reason       TEXT,
  tp_hit            TEXT,
  tp_count_hit      INTEGER DEFAULT 0,

  -- 8) Аналитика фондового уровня
  mfe_pct           NUMERIC(10, 4),
  mae_pct           NUMERIC(10, 4),
  reached_after_exit JSONB,

  -- 9) Служебное
  created_at        TIMESTAMPTZ DEFAULT NOW(),
  updated_at        TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Создаем индексы
CREATE INDEX IF NOT EXISTS idx_vtrades_status ON v_trades(status);
CREATE INDEX IF NOT EXISTS idx_vtrades_symbol_ts ON v_trades(symbol, posted_ts);
CREATE INDEX IF NOT EXISTS idx_vtrades_strategy ON v_trades(strategy_id, posted_ts);
CREATE INDEX IF NOT EXISTS idx_vtrades_created_at ON v_trades(created_at);
CREATE INDEX IF NOT EXISTS idx_vtrades_side_symbol ON v_trades(side, symbol);
CREATE INDEX IF NOT EXISTS idx_vtrades_source ON v_trades(source_type, source);

-- 4. Включаем RLS
ALTER TABLE v_trades ENABLE ROW LEVEL SECURITY;

-- 5. Создаем политики доступа
CREATE POLICY "Enable read access for authenticated users" ON v_trades
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Enable insert access for authenticated users" ON v_trades
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Enable update access for authenticated users" ON v_trades
    FOR UPDATE USING (auth.role() = 'authenticated');

-- 6. Trigger для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_vtrades_updated_at BEFORE UPDATE ON v_trades
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 7. Комментарии
COMMENT ON TABLE v_trades IS 'Virtual trades for signal simulation with TP1→BE→TP2 strategy';
COMMENT ON COLUMN v_trades.strategy_id IS 'Trading strategy: S_A_TP1_BE_TP2 = TP1 then move SL to BE then TP2';
COMMENT ON COLUMN v_trades.status IS 'sim_open (running), sim_closed (finished), sim_skipped (not processed)';

-- 8. Вставляем тестовую запись
INSERT INTO v_trades (
  symbol, side, entry_type, entry_min, entry_max, tp1, tp2, sl,
  source, source_type, source_name, original_text, posted_ts,
  strategy_id, leverage, margin_usd
) VALUES (
  'TESTUSDT', 'LONG', 'zone', 100.0, 102.0, 110.0, 120.0, 95.0,
  'ghost_test', 'manual', 'GHOST Test Signal', 
  'Test signal for virtual trades table creation', 
  EXTRACT(epoch FROM NOW()) * 1000,
  'S_A_TP1_BE_TP2', 10, 100
);

-- Проверяем что данные вставились
SELECT 
  id, symbol, side, status, 
  entry_min, entry_max, tp1, tp2, sl,
  strategy_id, created_at
FROM v_trades 
WHERE symbol = 'TESTUSDT'
LIMIT 1;
