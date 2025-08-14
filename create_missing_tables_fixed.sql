-- 🔧 ИСПРАВЛЕННЫЕ SQL команды для создания таблиц в Supabase
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

-- 3. Таблица снимков рынка (БЕЗ foreign key к signal_sources)
CREATE TABLE IF NOT EXISTS market_snapshots (
  id SERIAL PRIMARY KEY,
  signal_id INTEGER, -- БЕЗ REFERENCES, так как может ссылаться на signals_parsed.signal_id
  symbol TEXT NOT NULL,
  snapshot_timestamp TIMESTAMP DEFAULT NOW(),
  current_price DECIMAL(20,8),
  volume_24h DECIMAL(30,8),
  rsi_14 DECIMAL(5,2),
  macd_line DECIMAL(20,8),
  sma_20 DECIMAL(20,8),
  created_at TIMESTAMP DEFAULT NOW()
);

-- 4. Таблица фундаментальных данных (БЕЗ foreign key)
CREATE TABLE IF NOT EXISTS fundamental_data (
  id SERIAL PRIMARY KEY,
  signal_id INTEGER, -- БЕЗ REFERENCES
  symbol TEXT NOT NULL,
  market_cap DECIMAL(30,2),
  social_sentiment_score DECIMAL(3,2),
  news_sentiment_score DECIMAL(3,2),
  active_addresses_24h INTEGER,
  whale_transactions_24h INTEGER,
  data_timestamp TIMESTAMP DEFAULT NOW(),
  created_at TIMESTAMP DEFAULT NOW()
);

-- 5. Таблица аналитики производительности
CREATE TABLE IF NOT EXISTS performance_analytics (
  id SERIAL PRIMARY KEY,
  entity_type TEXT NOT NULL, -- 'SIGNAL_SOURCE', 'TRADER', 'STRATEGY'
  entity_id TEXT NOT NULL, -- source_id из signal_sources
  total_trades INTEGER DEFAULT 0,
  winning_trades INTEGER DEFAULT 0,
  losing_trades INTEGER DEFAULT 0,
  win_rate DECIMAL(5,2),
  total_pnl DECIMAL(20,8),
  avg_win DECIMAL(20,8),
  avg_loss DECIMAL(20,8),
  sharpe_ratio DECIMAL(10,6),
  max_drawdown DECIMAL(10,4),
  analysis_period_start TIMESTAMP,
  analysis_period_end TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 6. Таблица алертов (БЕЗ foreign key)
CREATE TABLE IF NOT EXISTS alerts (
  id SERIAL PRIMARY KEY,
  alert_type TEXT NOT NULL, -- 'SIGNAL_RECEIVED', 'TRADE_OPENED', 'TP_HIT', 'SL_HIT'
  priority TEXT DEFAULT 'MEDIUM', -- 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
  title TEXT NOT NULL,
  message TEXT NOT NULL,
  signal_id INTEGER, -- БЕЗ REFERENCES, может быть NULL
  trade_id INTEGER, -- БЕЗ REFERENCES, может быть NULL
  source_id TEXT, -- source_id из signal_sources
  status TEXT DEFAULT 'PENDING', -- 'PENDING', 'SENT', 'DELIVERED', 'FAILED'
  delivery_channels TEXT[], -- ['telegram', 'email', 'webhook', 'dashboard']
  created_at TIMESTAMP DEFAULT NOW(),
  processed_at TIMESTAMP,
  delivered_at TIMESTAMP
);

-- Добавляем начальные данные

-- Биржи
INSERT INTO exchanges (exchange_code, exchange_name) VALUES
('BINANCE', 'Binance Futures'),
('BYBIT', 'Bybit Derivatives'),
('OKX', 'OKX Futures'),
('MEXC', 'MEXC Global'),
('KUCOIN', 'KuCoin Futures')
ON CONFLICT (exchange_code) DO NOTHING;

-- Популярные криптовалютные инструменты
INSERT INTO instruments (ticker_symbol, instrument_name, base_currency, quote_currency) VALUES
('BTCUSDT', 'Bitcoin USDT Perpetual', 'BTC', 'USDT'),
('ETHUSDT', 'Ethereum USDT Perpetual', 'ETH', 'USDT'),
('ORDIUSDT', 'Ordinals USDT Perpetual', 'ORDI', 'USDT'),
('SOLUSDT', 'Solana USDT Perpetual', 'SOL', 'USDT'),
('ADAUSDT', 'Cardano USDT Perpetual', 'ADA', 'USDT'),
('DOGEUSDT', 'Dogecoin USDT Perpetual', 'DOGE', 'USDT'),
('BNBUSDT', 'Binance Coin USDT Perpetual', 'BNB', 'USDT'),
('XRPUSDT', 'XRP USDT Perpetual', 'XRP', 'USDT'),
('AVAXUSDT', 'Avalanche USDT Perpetual', 'AVAX', 'USDT'),
('LINKUSDT', 'Chainlink USDT Perpetual', 'LINK', 'USDT')
ON CONFLICT (ticker_symbol) DO NOTHING;

-- Создаем индексы для производительности
CREATE INDEX IF NOT EXISTS idx_market_snapshots_signal_id ON market_snapshots(signal_id);
CREATE INDEX IF NOT EXISTS idx_market_snapshots_symbol ON market_snapshots(symbol);
CREATE INDEX IF NOT EXISTS idx_fundamental_data_signal_id ON fundamental_data(signal_id);
CREATE INDEX IF NOT EXISTS idx_fundamental_data_symbol ON fundamental_data(symbol);
CREATE INDEX IF NOT EXISTS idx_alerts_signal_id ON alerts(signal_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_performance_analytics_entity ON performance_analytics(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_instruments_symbol ON instruments(ticker_symbol);

-- Комментарии к таблицам
COMMENT ON TABLE instruments IS 'Торговые инструменты (криптовалютные пары, акции, фьючерсы)';
COMMENT ON TABLE exchanges IS 'Криптовалютные биржи и торговые площадки';
COMMENT ON TABLE market_snapshots IS 'Снимки рыночных данных на момент получения сигнала';
COMMENT ON TABLE fundamental_data IS 'Фундаментальные данные, on-chain метрики и социальный sentiment';
COMMENT ON TABLE performance_analytics IS 'Аналитика производительности источников сигналов, трейдеров и стратегий';
COMMENT ON TABLE alerts IS 'Система уведомлений о торговых сигналах и важных событиях';

-- Пример создания тестового алерта
INSERT INTO alerts (alert_type, title, message, priority) VALUES
('SYSTEM_START', 'GHOST System Started', 'Торговая система GHOST успешно запущена и готова к работе', 'HIGH');

SELECT 'Все таблицы созданы успешно! 🎉' as result;
