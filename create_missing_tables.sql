-- 🔧 Создание недостающих таблиц в Supabase
-- Выполнить в Supabase Dashboard -> SQL Editor

-- 1. Таблица инструментов
CREATE TABLE IF NOT EXISTS instruments (
  id SERIAL PRIMARY KEY,
  ticker_symbol TEXT NOT NULL UNIQUE,
  instrument_name TEXT,
  instrument_type TEXT DEFAULT 'Crypto',
  base_currency TEXT,
  quote_currency TEXT,
  exchange_code TEXT DEFAULT 'BINANCE',
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 2. Таблица бирж
CREATE TABLE IF NOT EXISTS exchanges (
  id SERIAL PRIMARY KEY,
  exchange_code TEXT NOT NULL UNIQUE,
  exchange_name TEXT NOT NULL,
  timezone TEXT DEFAULT 'UTC',
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 3. Таблица снимков рынка
CREATE TABLE IF NOT EXISTS market_snapshots (
  id SERIAL PRIMARY KEY,
  signal_id INTEGER REFERENCES signals_parsed(signal_id),
  symbol TEXT NOT NULL,
  snapshot_timestamp TIMESTAMP DEFAULT NOW(),
  current_price DECIMAL(20,8),
  volume_24h DECIMAL(30,8),
  rsi_14 DECIMAL(5,2),
  created_at TIMESTAMP DEFAULT NOW()
);

-- 4. Таблица фундаментальных данных
CREATE TABLE IF NOT EXISTS fundamental_data (
  id SERIAL PRIMARY KEY,
  signal_id INTEGER REFERENCES signals_parsed(signal_id),
  symbol TEXT NOT NULL,
  market_cap DECIMAL(30,2),
  social_sentiment_score DECIMAL(3,2),
  data_timestamp TIMESTAMP DEFAULT NOW(),
  created_at TIMESTAMP DEFAULT NOW()
);

-- 5. Таблица аналитики производительности
CREATE TABLE IF NOT EXISTS performance_analytics (
  id SERIAL PRIMARY KEY,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  total_trades INTEGER DEFAULT 0,
  win_rate DECIMAL(5,2),
  total_pnl DECIMAL(20,8),
  analysis_period_start TIMESTAMP,
  analysis_period_end TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 6. Таблица алертов
CREATE TABLE IF NOT EXISTS alerts (
  id SERIAL PRIMARY KEY,
  alert_type TEXT NOT NULL,
  priority TEXT DEFAULT 'MEDIUM',
  title TEXT NOT NULL,
  message TEXT NOT NULL,
  signal_id INTEGER REFERENCES signals_parsed(signal_id),
  status TEXT DEFAULT 'PENDING',
  created_at TIMESTAMP DEFAULT NOW()
);

-- Добавляем начальные данные

-- Биржи
INSERT INTO exchanges (exchange_code, exchange_name) VALUES
('BINANCE', 'Binance Futures'),
('BYBIT', 'Bybit Derivatives'),
('OKX', 'OKX Futures')
ON CONFLICT (exchange_code) DO NOTHING;

-- Популярные инструменты
INSERT INTO instruments (ticker_symbol, instrument_name, base_currency, quote_currency) VALUES
('BTCUSDT', 'Bitcoin USDT Perpetual', 'BTC', 'USDT'),
('ETHUSDT', 'Ethereum USDT Perpetual', 'ETH', 'USDT'),
('ORDIUSDT', 'Ordinals USDT Perpetual', 'ORDI', 'USDT'),
('SOLUSDT', 'Solana USDT Perpetual', 'SOL', 'USDT'),
('ADAUSDT', 'Cardano USDT Perpetual', 'ADA', 'USDT')
ON CONFLICT (ticker_symbol) DO NOTHING;

-- Создаем индексы для производительности
CREATE INDEX IF NOT EXISTS idx_market_snapshots_signal_id ON market_snapshots(signal_id);
CREATE INDEX IF NOT EXISTS idx_fundamental_data_signal_id ON fundamental_data(signal_id);
CREATE INDEX IF NOT EXISTS idx_alerts_signal_id ON alerts(signal_id);
CREATE INDEX IF NOT EXISTS idx_performance_analytics_entity ON performance_analytics(entity_type, entity_id);

COMMENT ON TABLE instruments IS 'Торговые инструменты (криптовалютные пары)';
COMMENT ON TABLE exchanges IS 'Криптовалютные биржи';
COMMENT ON TABLE market_snapshots IS 'Снимки рыночных данных на момент сигнала';
COMMENT ON TABLE fundamental_data IS 'Фундаментальные и on-chain данные';
COMMENT ON TABLE performance_analytics IS 'Аналитика производительности источников сигналов';
COMMENT ON TABLE alerts IS 'Система уведомлений о сигналах и событиях';