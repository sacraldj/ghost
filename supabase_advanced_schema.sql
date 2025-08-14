-- 🏆 GHOST Advanced Trading Database Schema
-- Основано на лучших практиках Renaissance Technologies, Jane Street, Citadel
-- Максимальный набор полей для профессионального анализа сигналов и сделок

-- =====================================
-- 1. ИНСТРУМЕНТЫ И АКТИВЫ
-- =====================================

CREATE TABLE IF NOT EXISTS instruments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  ticker_symbol TEXT NOT NULL UNIQUE, -- ORDIUSDT
  instrument_name TEXT, -- Ordinals USDT Perpetual
  instrument_type TEXT NOT NULL, -- Crypto, Stock, Future, Option
  sector TEXT, -- Crypto, Tech, Finance
  industry TEXT, -- Blockchain, DeFi, Layer1
  base_currency TEXT, -- ORDI
  quote_currency TEXT, -- USDT
  settlement_currency TEXT, -- USDT
  exchange_code TEXT NOT NULL, -- BINANCE
  tick_size DECIMAL(20,8), -- 0.001
  contract_size DECIMAL(20,8), -- 1.0
    multiplier INTEGER DEFAULT 1,
  margin_requirements JSONB, -- {"initial": 0.1, "maintenance": 0.05}
  listing_date TIMESTAMP,
  delisting_date TIMESTAMP,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- =====================================
-- 2. БИРЖИ И ТОРГОВЫЕ ПЛОЩАДКИ
-- =====================================

CREATE TABLE IF NOT EXISTS exchanges (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  exchange_code TEXT NOT NULL UNIQUE, -- BINANCE
  exchange_name TEXT NOT NULL, -- Binance Futures
  timezone TEXT DEFAULT 'UTC',
  trading_hours JSONB, -- {"open": "00:00", "close": "23:59", "24_7": true}
  api_endpoints JSONB, -- {"rest": "api.binance.com", "ws": "stream.binance.com"}
  fees_structure JSONB, -- {"maker": 0.0002, "taker": 0.0004}
  created_at TIMESTAMP DEFAULT NOW()
);

-- =====================================
-- 3. ИСТОЧНИКИ СИГНАЛОВ (TELEGRAM КАНАЛЫ)
-- =====================================

CREATE TABLE IF NOT EXISTS signal_sources (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  source_code TEXT NOT NULL UNIQUE, -- whales_crypto_guide
  source_name TEXT NOT NULL, -- Whales Crypto Guide
  source_type TEXT NOT NULL, -- telegram, discord, twitter, internal
  channel_id TEXT, -- -1001288385100
  trader_id TEXT, -- crypto_hub_vip
  reliability_score DECIMAL(3,2) DEFAULT 0.5, -- 0.0-1.0
  win_rate DECIMAL(5,2), -- Исторический винрейт
  avg_roi DECIMAL(10,4), -- Средний ROI
  total_signals INTEGER DEFAULT 0,
  successful_signals INTEGER DEFAULT 0,
  is_active BOOLEAN DEFAULT true,
  subscription_cost DECIMAL(10,2), -- Стоимость подписки
  risk_rating TEXT, -- LOW, MEDIUM, HIGH
  specialization TEXT[], -- ["scalping", "swing", "futures"]
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- =====================================
-- 4. СЫРЫЕ TELEGRAM СИГНАЛЫ
-- =====================================

CREATE TABLE IF NOT EXISTS signals_raw (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  source_id UUID REFERENCES signal_sources(id),
  message_id TEXT, -- Telegram message ID
  channel_id TEXT NOT NULL,
  raw_text TEXT NOT NULL, -- Полный текст сообщения
  message_timestamp TIMESTAMP NOT NULL,
  received_timestamp TIMESTAMP DEFAULT NOW(),
  sender_username TEXT,
  sender_id TEXT,
  message_type TEXT, -- text, photo, document
  forwarded_from TEXT,
  reply_to_message_id TEXT,
  has_media BOOLEAN DEFAULT false,
  media_urls TEXT[],
  hashtags TEXT[], -- ["#ORDIUSDT", "#LONG"]
  mentions TEXT[], -- ["@username"]
  language TEXT DEFAULT 'en',
  character_count INTEGER,
  word_count INTEGER,
  sentiment_score DECIMAL(3,2), -- -1.0 to 1.0
  urgency_indicators TEXT[], -- ["BREAKING", "URGENT", "NOW"]
  processing_status TEXT DEFAULT 'pending', -- pending, processed, failed, ignored
  error_message TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- =====================================
-- 5. ОБРАБОТАННЫЕ СИГНАЛЫ (PARSED)
-- =====================================

CREATE TABLE IF NOT EXISTS signals_parsed (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  raw_signal_id UUID REFERENCES signals_raw(id),
  source_id UUID REFERENCES signal_sources(id),
    instrument_id UUID REFERENCES instruments(id),
  
  -- Основная информация о сигнале
  signal_type TEXT NOT NULL, -- LONG, SHORT, CLOSE, UPDATE
  symbol TEXT NOT NULL, -- ORDIUSDT
  direction TEXT NOT NULL, -- BUY, SELL
  
  -- Цены и уровни
  entry_price DECIMAL(20,8), -- 10.456
  entry_levels DECIMAL(20,8)[], -- [10.565, 10.617, 10.716]
  stop_loss DECIMAL(20,8), -- 9.800
  take_profit_levels DECIMAL(20,8)[], -- [11.500, 12.000, 12.500]
  
  -- Управление рисками
  leverage INTEGER, -- 10
  position_size_percent DECIMAL(5,2), -- % от депозита
  risk_reward_ratio DECIMAL(10,4), -- 2.5
  confidence_score DECIMAL(3,2), -- 0.0-1.0
  
  -- Временные параметры
  signal_timestamp TIMESTAMP NOT NULL,
  expiry_timestamp TIMESTAMP,
  timeframe TEXT, -- 1m, 5m, 1h, 1d
  holding_period TEXT, -- scalp, intraday, swing, position
  
  -- Технический анализ
  technical_reason TEXT, -- "RSI oversold + EMA crossover"
  support_resistance_levels DECIMAL(20,8)[],
  chart_pattern TEXT, -- "ascending triangle", "head_and_shoulders"
  
  -- Фундаментальные факторы
  fundamental_reason TEXT,
  news_catalyst TEXT,
  event_driven BOOLEAN DEFAULT false,
  
  -- Качество парсинга
  parsing_confidence DECIMAL(3,2), -- Уверенность парсера
  parsing_method TEXT, -- manual, regex, ai, ml
  parser_version TEXT, -- v1.2.3
  validation_status TEXT, -- valid, invalid, suspicious
  validation_errors TEXT[],
  
  -- Метаданные
  is_update BOOLEAN DEFAULT false, -- Обновление предыдущего сигнала
  parent_signal_id UUID REFERENCES signals_parsed(id),
  priority_level INTEGER DEFAULT 1, -- 1-10
  tags TEXT[], -- ["breakout", "momentum", "reversal"]
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- =====================================
-- 6. РЫНОЧНЫЕ ДАННЫЕ НА МОМЕНТ СИГНАЛА
-- =====================================

CREATE TABLE IF NOT EXISTS market_snapshots (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  signal_id UUID REFERENCES signals_parsed(id),
  instrument_id UUID REFERENCES instruments(id),
  snapshot_timestamp TIMESTAMP NOT NULL,
  
  -- OHLCV данные
  current_price DECIMAL(20,8),
    open_price DECIMAL(20,8),
    high_price DECIMAL(20,8),
    low_price DECIMAL(20,8),
    close_price DECIMAL(20,8),
  volume_24h DECIMAL(30,8),
  volume_1h DECIMAL(30,8),
  
  -- Order Book
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
-- 7. ON-CHAIN И ФУНДАМЕНТАЛЬНЫЕ ДАННЫЕ
-- =====================================

CREATE TABLE IF NOT EXISTS fundamental_data (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  signal_id UUID REFERENCES signals_parsed(id),
  instrument_id UUID REFERENCES instruments(id),
  data_timestamp TIMESTAMP NOT NULL,
  
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
-- 8. ИСПОЛНЕНИЕ СИГНАЛОВ (TRADES)
-- =====================================

CREATE TABLE IF NOT EXISTS trades (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  signal_id UUID REFERENCES signals_parsed(id),
  instrument_id UUID REFERENCES instruments(id),
  source_id UUID REFERENCES signal_sources(id),
  
  -- Основная информация
  trade_type TEXT NOT NULL, -- SIGNAL_FOLLOW, MANUAL, AUTOMATED
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
  portfolio_id UUID, -- Ссылка на портфель
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- =====================================
-- 9. АНАЛИЗ ПРОИЗВОДИТЕЛЬНОСТИ
-- =====================================

CREATE TABLE IF NOT EXISTS performance_analytics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  entity_type TEXT NOT NULL, -- SIGNAL_SOURCE, TRADER, STRATEGY, INSTRUMENT
  entity_id UUID NOT NULL, -- ID источника/трейдера/стратегии
  analysis_period_start TIMESTAMP NOT NULL,
  analysis_period_end TIMESTAMP NOT NULL,
  
  -- Основные метрики
  total_trades INTEGER,
  winning_trades INTEGER,
  losing_trades INTEGER,
  win_rate DECIMAL(5,2),
  
  -- Финансовые метрики
  total_pnl DECIMAL(20,8),
  avg_win DECIMAL(20,8),
  avg_loss DECIMAL(20,8),
  largest_win DECIMAL(20,8),
  largest_loss DECIMAL(20,8),
  profit_factor DECIMAL(10,4), -- Gross profit / Gross loss
  
  -- Риск-метрики
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
-- 10. СИСТЕМА УВЕДОМЛЕНИЙ И АЛЕРТОВ
-- =====================================

CREATE TABLE IF NOT EXISTS alerts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  alert_type TEXT NOT NULL, -- SIGNAL_RECEIVED, TRADE_OPENED, TP_HIT, SL_HIT, SYSTEM_ERROR
  priority TEXT DEFAULT 'MEDIUM', -- LOW, MEDIUM, HIGH, CRITICAL
  title TEXT NOT NULL,
  message TEXT NOT NULL,
  
  -- Связанные объекты
  signal_id UUID REFERENCES signals_parsed(id),
  trade_id UUID REFERENCES trades(id),
  source_id UUID REFERENCES signal_sources(id),
  
  -- Статус обработки
  status TEXT DEFAULT 'PENDING', -- PENDING, SENT, DELIVERED, FAILED
  delivery_channels TEXT[], -- ["telegram", "email", "webhook", "dashboard"]
  
  -- Метаданные
  created_at TIMESTAMP DEFAULT NOW(),
  processed_at TIMESTAMP,
  delivered_at TIMESTAMP
);

-- =====================================
-- ИНДЕКСЫ ДЛЯ ПРОИЗВОДИТЕЛЬНОСТИ
-- =====================================

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_signals_raw_channel_timestamp ON signals_raw(channel_id, message_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_signals_parsed_symbol_timestamp ON signals_parsed(symbol, signal_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_trades_status_opened ON trades(status, position_opened_at DESC);
CREATE INDEX IF NOT EXISTS idx_market_snapshots_signal_timestamp ON market_snapshots(signal_id, snapshot_timestamp);
CREATE INDEX IF NOT EXISTS idx_alerts_status_priority ON alerts(status, priority, created_at DESC);

-- Индексы для аналитики
CREATE INDEX IF NOT EXISTS idx_trades_source_performance ON trades(source_id, position_closed_at, net_pnl);
CREATE INDEX IF NOT EXISTS idx_signals_parsed_source_success ON signals_parsed(source_id, validation_status, signal_timestamp);

-- =====================================
-- ТРИГГЕРЫ ДЛЯ АВТОМАТИЧЕСКОГО ОБНОВЛЕНИЯ
-- =====================================

-- Автоматическое обновление updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Применяем триггер к нужным таблицам
CREATE TRIGGER update_instruments_updated_at BEFORE UPDATE ON instruments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_signal_sources_updated_at BEFORE UPDATE ON signal_sources FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_signals_parsed_updated_at BEFORE UPDATE ON signals_parsed FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_trades_updated_at BEFORE UPDATE ON trades FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================
-- НАЧАЛЬНЫЕ ДАННЫЕ
-- =====================================

-- Добавляем основные биржи
INSERT INTO exchanges (exchange_code, exchange_name, timezone, trading_hours, api_endpoints, fees_structure) VALUES
('BINANCE', 'Binance Futures', 'UTC', '{"24_7": true}', '{"rest": "fapi.binance.com", "ws": "fstream.binance.com"}', '{"maker": 0.0002, "taker": 0.0004}'),
('BYBIT', 'Bybit Derivatives', 'UTC', '{"24_7": true}', '{"rest": "api.bybit.com", "ws": "stream.bybit.com"}', '{"maker": 0.0001, "taker": 0.0006}'),
('OKX', 'OKX Futures', 'UTC', '{"24_7": true}', '{"rest": "www.okx.com", "ws": "ws.okx.com"}', '{"maker": 0.0002, "taker": 0.0005}')
ON CONFLICT (exchange_code) DO NOTHING;

-- Добавляем источник Telegram
INSERT INTO signal_sources (source_code, source_name, source_type, channel_id, trader_id, reliability_score, specialization) VALUES
('whales_crypto_guide', 'Whales Crypto Guide', 'telegram', '-1001288385100', 'whales_guide', 0.75, ARRAY['futures', 'swing', 'crypto'])
ON CONFLICT (source_code) DO NOTHING;

COMMENT ON TABLE signals_raw IS 'Сырые сообщения из Telegram каналов - каждое сообщение сохраняется как есть';
COMMENT ON TABLE signals_parsed IS 'Обработанные торговые сигналы с извлеченными параметрами (цены, стопы, таргеты)';
COMMENT ON TABLE trades IS 'Фактические сделки, исполненные по сигналам с полной аналитикой результатов';
COMMENT ON TABLE market_snapshots IS 'Снимки рынка на момент получения сигнала для последующего анализа';
COMMENT ON TABLE performance_analytics IS 'Аггрегированная аналитика производительности источников сигналов и стратегий';
