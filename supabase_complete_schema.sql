-- 🏆 GHOST Complete Database Schema
-- Полная продвинутая схема + исправления для Supabase
-- Основано на лучших практиках торговых фондов: Renaissance Technologies, Jane Street, Citadel

-- =====================================
-- 1. БИРЖИ И ТОРГОВЫЕ ПЛОЩАДКИ
-- =====================================

CREATE TABLE IF NOT EXISTS exchanges (
  id SERIAL PRIMARY KEY,
  exchange_code TEXT NOT NULL UNIQUE, -- BINANCE, BYBIT, OKX
  exchange_name TEXT NOT NULL, -- Binance Futures
  timezone TEXT DEFAULT 'UTC',
  trading_hours JSONB DEFAULT '{"24_7": true}',
  api_endpoints JSONB, -- {"rest": "fapi.binance.com", "ws": "fstream.binance.com"}
  fees_structure JSONB, -- {"maker": 0.0002, "taker": 0.0004}
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW()
);

-- =====================================
-- 2. ТОРГОВЫЕ ИНСТРУМЕНТЫ
-- =====================================

CREATE TABLE IF NOT EXISTS instruments (
  id SERIAL PRIMARY KEY,
  ticker_symbol TEXT NOT NULL UNIQUE, -- ORDIUSDT, BTCUSDT
  instrument_name TEXT, -- Ordinals USDT Perpetual
  instrument_type TEXT NOT NULL DEFAULT 'Crypto', -- Crypto, Stock, Future, Option
  sector TEXT, -- Cryptocurrency, Tech, Finance
  industry TEXT, -- Blockchain, DeFi, Layer1
  base_currency TEXT, -- ORDI, BTC
  quote_currency TEXT, -- USDT, USD
  settlement_currency TEXT, -- USDT
  exchange_code TEXT NOT NULL DEFAULT 'BINANCE',
  tick_size DECIMAL(20,8) DEFAULT 0.001, -- Минимальный шаг цены
  contract_size DECIMAL(20,8) DEFAULT 1.0, -- Размер контракта
  multiplier INTEGER DEFAULT 1,
  margin_requirements JSONB, -- {"initial": 0.1, "maintenance": 0.05}
  listing_date TIMESTAMP,
  delisting_date TIMESTAMP,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- =====================================
-- 3. СНИМКИ РЫНКА НА МОМЕНТ СИГНАЛА
-- =====================================

CREATE TABLE IF NOT EXISTS market_snapshots (
  id SERIAL PRIMARY KEY,
  signal_id INTEGER, -- Ссылка на signals_parsed.signal_id (без FK constraint)
  instrument_id INTEGER, -- Ссылка на instruments.id (без FK constraint)
  symbol TEXT NOT NULL, -- Дублируем для быстрого поиска
  snapshot_timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
  
  -- OHLCV данные
  current_price DECIMAL(20,8),
  open_price DECIMAL(20,8),
  high_price DECIMAL(20,8),
  low_price DECIMAL(20,8),
  close_price DECIMAL(20,8),
  volume_24h DECIMAL(30,8),
  volume_1h DECIMAL(30,8),
  
  -- Order Book данные
  bid_price DECIMAL(20,8),
  ask_price DECIMAL(20,8),
  spread_percent DECIMAL(10,6),
  bid_volume DECIMAL(30,8),
  ask_volume DECIMAL(30,8),
  order_book_imbalance DECIMAL(10,6), -- (bid_vol - ask_vol) / (bid_vol + ask_vol)
  
  -- Волатильность
  volatility_1h DECIMAL(10,6),
  volatility_24h DECIMAL(10,6),
  volatility_7d DECIMAL(10,6),
  atr_14 DECIMAL(20,8), -- Average True Range
  
  -- Объемы и интерес
  open_interest DECIMAL(30,8), -- Для futures
  funding_rate DECIMAL(10,8), -- Для perpetual
  long_short_ratio DECIMAL(10,6),
  
  -- Технические индикаторы
  rsi_14 DECIMAL(5,2),
  rsi_7 DECIMAL(5,2),
  macd_line DECIMAL(20,8),
  macd_signal DECIMAL(20,8),
  macd_histogram DECIMAL(20,8),
  sma_20 DECIMAL(20,8),
  sma_50 DECIMAL(20,8),
  sma_200 DECIMAL(20,8),
  ema_12 DECIMAL(20,8),
  ema_26 DECIMAL(20,8),
  bollinger_upper DECIMAL(20,8),
  bollinger_middle DECIMAL(20,8),
  bollinger_lower DECIMAL(20,8),
  stochastic_k DECIMAL(5,2),
  stochastic_d DECIMAL(5,2),
  williams_r DECIMAL(5,2),
  cci DECIMAL(10,4),
  adx DECIMAL(5,2),
  
  -- Дополнительные индикаторы
  vwap DECIMAL(20,8), -- Volume Weighted Average Price
  pivot_point DECIMAL(20,8),
  resistance_1 DECIMAL(20,8),
  resistance_2 DECIMAL(20,8),
  support_1 DECIMAL(20,8),
  support_2 DECIMAL(20,8),
  
  created_at TIMESTAMP DEFAULT NOW()
);

-- =====================================
-- 4. ON-CHAIN И ФУНДАМЕНТАЛЬНЫЕ ДАННЫЕ
-- =====================================

CREATE TABLE IF NOT EXISTS fundamental_data (
  id SERIAL PRIMARY KEY,
  signal_id INTEGER, -- Ссылка на signals_parsed.signal_id
  instrument_id INTEGER, -- Ссылка на instruments.id
  symbol TEXT NOT NULL,
  data_timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
  
  -- Криптовалютные метрики
  market_cap DECIMAL(30,2),
  circulating_supply DECIMAL(30,8),
  max_supply DECIMAL(30,8),
  total_supply DECIMAL(30,8),
  
  -- On-chain данные
  active_addresses_24h INTEGER,
  transaction_count_24h INTEGER,
  transaction_volume_24h DECIMAL(30,8),
  hash_rate DECIMAL(30,8), -- Для Bitcoin и форков
  network_difficulty DECIMAL(30,8),
  
  -- Whale Activity
  whale_transactions_24h INTEGER, -- Транзакции >100k USD
  large_holder_concentration DECIMAL(5,2), -- % токенов у топ-100 адресов
  exchange_inflows_24h DECIMAL(30,8),
  exchange_outflows_24h DECIMAL(30,8),
  exchange_netflows_24h DECIMAL(30,8),
  
  -- DeFi метрики (если применимо)
  total_value_locked DECIMAL(30,2), -- TVL
  liquidity_pools_count INTEGER,
  yield_farming_apy DECIMAL(10,4),
  
  -- Социальные метрики
  twitter_followers INTEGER,
  telegram_members INTEGER,
  reddit_subscribers INTEGER,
  github_commits_30d INTEGER,
  developer_activity_score DECIMAL(5,2),
  
  -- Sentiment данные
  fear_greed_index INTEGER, -- 0-100
  social_sentiment_score DECIMAL(3,2), -- -1.0 to 1.0
  news_sentiment_score DECIMAL(3,2),
  google_trends_score INTEGER, -- 0-100
  
  created_at TIMESTAMP DEFAULT NOW()
);

-- =====================================
-- 5. АНАЛИЗ ПРОИЗВОДИТЕЛЬНОСТИ
-- =====================================

CREATE TABLE IF NOT EXISTS performance_analytics (
  id SERIAL PRIMARY KEY,
  entity_type TEXT NOT NULL, -- SIGNAL_SOURCE, TRADER, STRATEGY, INSTRUMENT
  entity_id TEXT NOT NULL, -- ID источника/трейдера/стратегии
  analysis_period_start TIMESTAMP NOT NULL,
  analysis_period_end TIMESTAMP NOT NULL,
  
  -- Основные метрики
  total_trades INTEGER DEFAULT 0,
  winning_trades INTEGER DEFAULT 0,
  losing_trades INTEGER DEFAULT 0,
  win_rate DECIMAL(5,2),
  
  -- Финансовые метрики
  total_pnl DECIMAL(20,8),
  avg_win DECIMAL(20,8),
  avg_loss DECIMAL(20,8),
  largest_win DECIMAL(20,8),
  largest_loss DECIMAL(20,8),
  profit_factor DECIMAL(10,4), -- Gross profit / Gross loss
  
  -- Риск-метрики уровня хедж-фондов
  sharpe_ratio DECIMAL(10,6),
  sortino_ratio DECIMAL(10,6),
  calmar_ratio DECIMAL(10,6),
  max_drawdown DECIMAL(10,4),
  max_drawdown_duration_days INTEGER,
  value_at_risk_95 DECIMAL(20,8), -- VaR 95%
  expected_shortfall DECIMAL(20,8),
  
  -- Временные метрики
  avg_trade_duration_hours DECIMAL(10,2),
  avg_time_between_trades_hours DECIMAL(10,2),
  
  -- Дополнительные метрики
  kelly_criterion DECIMAL(10,6), -- Оптимальный размер позиции
  ulcer_index DECIMAL(10,6),
  recovery_factor DECIMAL(10,4),
  
  created_at TIMESTAMP DEFAULT NOW()
);

-- =====================================
-- 6. СИСТЕМА УВЕДОМЛЕНИЙ И АЛЕРТОВ
-- =====================================

CREATE TABLE IF NOT EXISTS alerts (
  id SERIAL PRIMARY KEY,
  alert_type TEXT NOT NULL, -- SIGNAL_RECEIVED, TRADE_OPENED, TP_HIT, SL_HIT, SYSTEM_ERROR
  priority TEXT DEFAULT 'MEDIUM', -- LOW, MEDIUM, HIGH, CRITICAL
  title TEXT NOT NULL,
  message TEXT NOT NULL,
  
  -- Связанные объекты (без FK constraints)
  signal_id INTEGER, -- Ссылка на signals_parsed.signal_id
  trade_id INTEGER, -- Ссылка на trades.id
  source_id TEXT, -- Ссылка на signal_sources.source_id
  
  -- Статус обработки
  status TEXT DEFAULT 'PENDING', -- PENDING, SENT, DELIVERED, FAILED
  delivery_channels TEXT[] DEFAULT ARRAY['dashboard'], -- telegram, email, webhook, dashboard
  
  -- Дополнительные данные
  metadata JSONB, -- Любые дополнительные данные
  error_message TEXT,
  retry_count INTEGER DEFAULT 0,
  
  -- Временные метки
  created_at TIMESTAMP DEFAULT NOW(),
  processed_at TIMESTAMP,
  delivered_at TIMESTAMP,
  expires_at TIMESTAMP
);

-- =====================================
-- 7. РАСШИРЕННАЯ ТАБЛИЦА СДЕЛОК
-- =====================================

CREATE TABLE IF NOT EXISTS trades_extended (
  id SERIAL PRIMARY KEY,
  signal_id INTEGER, -- Ссылка на signals_parsed.signal_id
  instrument_id INTEGER, -- Ссылка на instruments.id
  source_id TEXT, -- Ссылка на signal_sources.source_id
  
  -- Основная информация
  trade_type TEXT NOT NULL DEFAULT 'SIGNAL_FOLLOW', -- SIGNAL_FOLLOW, MANUAL, AUTOMATED
  direction TEXT NOT NULL, -- LONG, SHORT
  status TEXT DEFAULT 'OPEN', -- OPEN, CLOSED, CANCELLED
  
  -- Планирование сделки
  planned_entry_price DECIMAL(20,8),
  planned_entry_levels DECIMAL(20,8)[],
  planned_stop_loss DECIMAL(20,8),
  planned_take_profits DECIMAL(20,8)[],
  planned_position_size DECIMAL(30,8),
  planned_leverage INTEGER,
  planned_risk_percent DECIMAL(5,2),
  planned_reward_risk_ratio DECIMAL(10,4),
  
  -- Фактическое исполнение
  actual_entry_price DECIMAL(20,8),
  actual_entry_quantity DECIMAL(30,8),
  actual_leverage INTEGER,
  actual_stop_loss DECIMAL(20,8),
  actual_take_profits DECIMAL(20,8)[],
  
  -- Выход из позиции
  exit_price DECIMAL(20,8),
  exit_quantity DECIMAL(30,8),
  exit_reason TEXT, -- TP_HIT, SL_HIT, MANUAL_CLOSE, TIMEOUT, SIGNAL_UPDATE
  
  -- Временные метки
  signal_received_at TIMESTAMP,
  order_placed_at TIMESTAMP,
  position_opened_at TIMESTAMP,
  position_closed_at TIMESTAMP,
  trade_duration_seconds INTEGER,
  
  -- Финансовые результаты
  entry_fees DECIMAL(20,8),
  exit_fees DECIMAL(20,8),
  total_fees DECIMAL(20,8),
  gross_pnl DECIMAL(20,8), -- До комиссий
  net_pnl DECIMAL(20,8), -- После комиссий
  pnl_percent DECIMAL(10,4),
  roi_percent DECIMAL(10,4),
  
  -- Риск-метрики
  max_drawdown_percent DECIMAL(10,4), -- Максимальная просадка во время сделки
  max_runup_percent DECIMAL(10,4), -- Максимальный плюс
  max_adverse_excursion DECIMAL(20,8), -- MAE
  max_favorable_excursion DECIMAL(20,8), -- MFE
  
  -- Исполнение
  slippage_percent DECIMAL(10,6),
  execution_latency_ms INTEGER, -- Задержка от сигнала до исполнения
  order_type TEXT, -- MARKET, LIMIT, STOP_LIMIT
  partial_fills JSONB, -- Массив частичных исполнений
  
  -- Качественные метрики
  trade_quality_score DECIMAL(3,2), -- Оценка качества исполнения
  signal_accuracy_score DECIMAL(3,2), -- Точность следования сигналу
  
  -- Метаданные
  notes TEXT,
  tags TEXT[],
  is_paper_trade BOOLEAN DEFAULT false,
  portfolio_id TEXT, -- ID портфеля
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- =====================================
-- ИНДЕКСЫ ДЛЯ ПРОИЗВОДИТЕЛЬНОСТИ
-- =====================================

-- Основные индексы
CREATE INDEX IF NOT EXISTS idx_market_snapshots_signal_id ON market_snapshots(signal_id);
CREATE INDEX IF NOT EXISTS idx_market_snapshots_symbol_timestamp ON market_snapshots(symbol, snapshot_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_fundamental_data_signal_id ON fundamental_data(signal_id);
CREATE INDEX IF NOT EXISTS idx_fundamental_data_symbol_timestamp ON fundamental_data(symbol, data_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_status_priority ON alerts(status, priority, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_signal_id ON alerts(signal_id);
CREATE INDEX IF NOT EXISTS idx_performance_analytics_entity ON performance_analytics(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_trades_extended_signal_id ON trades_extended(signal_id);
CREATE INDEX IF NOT EXISTS idx_trades_extended_status_opened ON trades_extended(status, position_opened_at DESC);
CREATE INDEX IF NOT EXISTS idx_instruments_symbol ON instruments(ticker_symbol);
CREATE INDEX IF NOT EXISTS idx_exchanges_code ON exchanges(exchange_code);

-- Композитные индексы для аналитики
CREATE INDEX IF NOT EXISTS idx_market_snapshots_analytics ON market_snapshots(symbol, snapshot_timestamp, rsi_14, current_price);
CREATE INDEX IF NOT EXISTS idx_trades_extended_performance ON trades_extended(source_id, position_closed_at, net_pnl);

-- =====================================
-- НАЧАЛЬНЫЕ ДАННЫЕ
-- =====================================

-- Биржи
INSERT INTO exchanges (exchange_code, exchange_name, timezone, trading_hours, api_endpoints, fees_structure) VALUES
('BINANCE', 'Binance Futures', 'UTC', '{"24_7": true}', '{"rest": "fapi.binance.com", "ws": "fstream.binance.com"}', '{"maker": 0.0002, "taker": 0.0004}'),
('BYBIT', 'Bybit Derivatives', 'UTC', '{"24_7": true}', '{"rest": "api.bybit.com", "ws": "stream.bybit.com"}', '{"maker": 0.0001, "taker": 0.0006}'),
('OKX', 'OKX Futures', 'UTC', '{"24_7": true}', '{"rest": "www.okx.com", "ws": "ws.okx.com"}', '{"maker": 0.0002, "taker": 0.0005}'),
('MEXC', 'MEXC Global', 'UTC', '{"24_7": true}', '{"rest": "api.mexc.com", "ws": "wbs.mexc.com"}', '{"maker": 0.0002, "taker": 0.0004}'),
('KUCOIN', 'KuCoin Futures', 'UTC', '{"24_7": true}', '{"rest": "api-futures.kucoin.com", "ws": "ws-api.kucoin.com"}', '{"maker": 0.0002, "taker": 0.0006}')
ON CONFLICT (exchange_code) DO NOTHING;

-- Популярные торговые инструменты
INSERT INTO instruments (ticker_symbol, instrument_name, base_currency, quote_currency, exchange_code, tick_size) VALUES
('BTCUSDT', 'Bitcoin USDT Perpetual', 'BTC', 'USDT', 'BINANCE', 0.1),
('ETHUSDT', 'Ethereum USDT Perpetual', 'ETH', 'USDT', 'BINANCE', 0.01),
('ORDIUSDT', 'Ordinals USDT Perpetual', 'ORDI', 'USDT', 'BINANCE', 0.001),
('SOLUSDT', 'Solana USDT Perpetual', 'SOL', 'USDT', 'BINANCE', 0.001),
('ADAUSDT', 'Cardano USDT Perpetual', 'ADA', 'USDT', 'BINANCE', 0.0001),
('DOGEUSDT', 'Dogecoin USDT Perpetual', 'DOGE', 'USDT', 'BINANCE', 0.00001),
('BNBUSDT', 'Binance Coin USDT Perpetual', 'BNB', 'USDT', 'BINANCE', 0.01),
('XRPUSDT', 'XRP USDT Perpetual', 'XRP', 'USDT', 'BINANCE', 0.0001),
('AVAXUSDT', 'Avalanche USDT Perpetual', 'AVAX', 'USDT', 'BINANCE', 0.001),
('LINKUSDT', 'Chainlink USDT Perpetual', 'LINK', 'USDT', 'BINANCE', 0.001),
('MATICUSDT', 'Polygon USDT Perpetual', 'MATIC', 'USDT', 'BINANCE', 0.0001),
('DOTUSDT', 'Polkadot USDT Perpetual', 'DOT', 'USDT', 'BINANCE', 0.001),
('LTCUSDT', 'Litecoin USDT Perpetual', 'LTC', 'USDT', 'BINANCE', 0.01),
('BCHUSDT', 'Bitcoin Cash USDT Perpetual', 'BCH', 'USDT', 'BINANCE', 0.01),
('UNIUSDT', 'Uniswap USDT Perpetual', 'UNI', 'USDT', 'BINANCE', 0.001)
ON CONFLICT (ticker_symbol) DO NOTHING;

-- Тестовый алерт о запуске системы
INSERT INTO alerts (alert_type, title, message, priority, status) VALUES
('SYSTEM_START', 'GHOST Advanced System Started', 'Продвинутая торговая система GHOST успешно запущена с полной схемой базы данных. Готова к обработке сигналов!', 'HIGH', 'DELIVERED');

-- =====================================
-- КОММЕНТАРИИ К ТАБЛИЦАМ
-- =====================================

COMMENT ON TABLE exchanges IS 'Криптовалютные биржи и торговые площадки с API endpoints и комиссиями';
COMMENT ON TABLE instruments IS 'Торговые инструменты: криптовалютные пары, акции, фьючерсы с детальными характеристиками';
COMMENT ON TABLE market_snapshots IS 'Снимки рыночных данных на момент получения сигнала с полным набором технических индикаторов';
COMMENT ON TABLE fundamental_data IS 'Фундаментальные данные, on-chain метрики, социальный sentiment и макроэкономические показатели';
COMMENT ON TABLE performance_analytics IS 'Профессиональная аналитика производительности уровня хедж-фондов с метриками Sharpe, Sortino, VaR';
COMMENT ON TABLE alerts IS 'Система уведомлений о торговых сигналах, исполнении сделок и системных событиях';
COMMENT ON TABLE trades_extended IS 'Расширенная таблица сделок с максимальной детализацией для анализа исполнения и производительности';

-- =====================================
-- ЗАВЕРШЕНИЕ
-- =====================================

SELECT 
  'GHOST Advanced Database Schema создана успешно! 🎉' as status,
  'Таблиц создано: 7 новых + существующие' as tables_info,
  'Готова для работы с профессиональными торговыми сигналами' as ready_status;
