-- GHOST Initial Schema Migration
-- Создание всех необходимых таблиц

-- 1. Таблица профилей пользователей
CREATE TABLE IF NOT EXISTS profiles (
  id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  email TEXT UNIQUE,
  name TEXT,
  avatar TEXT,
  role TEXT DEFAULT 'USER',
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Таблица API ключей
CREATE TABLE IF NOT EXISTS api_keys (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT NOT NULL,
  key TEXT UNIQUE NOT NULL,
  is_active BOOLEAN DEFAULT true,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_used TIMESTAMP WITH TIME ZONE
);

-- 3. Таблица торговых сигналов
CREATE TABLE IF NOT EXISTS signals (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  source TEXT NOT NULL,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL CHECK (side IN ('LONG', 'SHORT')),
  entry_price DECIMAL(20,8) NOT NULL,
  tp1_price DECIMAL(20,8),
  tp2_price DECIMAL(20,8),
  sl_price DECIMAL(20,8),
  leverage INTEGER DEFAULT 20,
  risk DECIMAL(5,4) DEFAULT 0.02,
  confidence DECIMAL(3,2) DEFAULT 0.5,
  status TEXT DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'EXECUTED', 'EXPIRED', 'CANCELLED')),
  raw_message TEXT,
  parsed_data JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  expires_at TIMESTAMP WITH TIME ZONE
);

-- 4. Таблица торговых сделок
CREATE TABLE IF NOT EXISTS trades (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  signal_id UUID REFERENCES signals(id),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL CHECK (side IN ('LONG', 'SHORT')),
  status TEXT DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'CLOSED', 'CANCELLED', 'ERROR')),
  
  -- Цены
  entry_price DECIMAL(20,8) NOT NULL,
  exit_price DECIMAL(20,8),
  tp1_price DECIMAL(20,8),
  tp2_price DECIMAL(20,8),
  sl_price DECIMAL(20,8),
  
  -- Размеры
  quantity DECIMAL(20,8) NOT NULL,
  leverage INTEGER NOT NULL,
  margin_used DECIMAL(20,8) NOT NULL,
  
  -- Результаты
  pnl_gross DECIMAL(20,8),
  pnl_net DECIMAL(20,8),
  roi_percent DECIMAL(10,4),
  fees DECIMAL(20,8),
  
  -- Временные метки
  opened_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  closed_at TIMESTAMP WITH TIME ZONE,
  duration INTEGER,
  
  -- Детали исполнения
  entry_order_id TEXT,
  exit_order_id TEXT,
  slippage DECIMAL(10,4),
  latency INTEGER,
  
  -- Аналитика
  before_candles JSONB,
  after_candles JSONB,
  market_context JSONB,
  
  -- Вердикт
  verdict TEXT CHECK (verdict IN ('SUCCESS', 'FAILURE', 'BREAKEVEN', 'PARTIAL_SUCCESS')),
  verdict_reason TEXT
);

-- 5. Таблица новостных событий
CREATE TABLE IF NOT EXISTS news_events (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  trade_id UUID REFERENCES trades(id),
  cluster TEXT NOT NULL,
  title TEXT NOT NULL,
  content TEXT,
  source TEXT NOT NULL,
  published_at TIMESTAMP WITH TIME ZONE NOT NULL,
  significance DECIMAL(3,2) DEFAULT 0.5,
  
  -- Ценовые данные
  price_at_event DECIMAL(20,8),
  price_1h DECIMAL(20,8),
  price_4h DECIMAL(20,8),
  price_24h DECIMAL(20,8),
  price_change_1h DECIMAL(10,4),
  price_change_4h DECIMAL(10,4),
  price_change_24h DECIMAL(10,4),
  
  -- Реакция
  reaction_type TEXT CHECK (reaction_type IN ('PUMP', 'DUMP', 'NEUTRAL', 'SHORT_PUMP_THEN_FADE', 'MODERATE_MOVE')),
  volume_change DECIMAL(10,4),
  
  -- Контекст
  market_context JSONB,
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. Таблица ИИ-анализа
CREATE TABLE IF NOT EXISTS ai_analysis (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  trade_id UUID REFERENCES trades(id),
  news_event_id UUID REFERENCES news_events(id),
  
  -- GPT анализ
  gpt_analysis JSONB,
  gpt_confidence DECIMAL(3,2),
  gpt_reasoning TEXT,
  
  -- Gemini анализ
  gemini_analysis JSONB,
  gemini_confidence DECIMAL(3,2),
  gemini_reasoning TEXT,
  
  -- Финальный вердикт
  final_verdict TEXT,
  confidence DECIMAL(3,2),
  reasoning TEXT,
  
  -- Паттерны
  patterns TEXT[],
  similar_cases INTEGER DEFAULT 0,
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. Таблица аномалий событий
CREATE TABLE IF NOT EXISTS event_anomalies (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  event_type TEXT NOT NULL CHECK (event_type IN ('NEWS_WITHOUT_REACTION', 'REACTION_WITHOUT_NEWS', 'UNEXPECTED_MOVEMENT', 'MANIPULATION')),
  news_event_id UUID REFERENCES news_events(id),
  
  -- Данные события
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
  price_before DECIMAL(20,8),
  price_after DECIMAL(20,8),
  price_change DECIMAL(10,4),
  volume_change DECIMAL(10,4),
  
  -- Анализ
  anomaly_score DECIMAL(3,2) DEFAULT 0.5,
  possible_causes TEXT[],
  market_context JSONB,
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 8. Таблица манипуляций рынка
CREATE TABLE IF NOT EXISTS market_manipulations (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
  symbol TEXT NOT NULL,
  manipulation_type TEXT NOT NULL CHECK (manipulation_type IN ('PUMP', 'DUMP', 'SQUEEZE', 'LIQUIDATION')),
  price_before DECIMAL(20,8) NOT NULL,
  price_after DECIMAL(20,8) NOT NULL,
  volume_spike DECIMAL(10,4),
  funding_rate_change DECIMAL(10,6),
  open_interest_change DECIMAL(10,4),
  confidence_score DECIMAL(3,2),
  evidence JSONB,
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 9. Таблица стратегий
CREATE TABLE IF NOT EXISTS strategies (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  type TEXT NOT NULL CHECK (type IN ('MANUAL', 'AUTOMATED', 'AI_ASSISTED')),
  settings JSONB,
  is_active BOOLEAN DEFAULT true,
  performance_metrics JSONB,
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 10. Таблица портфелей
CREATE TABLE IF NOT EXISTS portfolios (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  balance DECIMAL(20,8) DEFAULT 0,
  total_pnl DECIMAL(20,8) DEFAULT 0,
  win_rate DECIMAL(5,2) DEFAULT 0,
  total_trades INTEGER DEFAULT 0,
  settings JSONB,
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 11. Таблица уведомлений
CREATE TABLE IF NOT EXISTS notifications (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  type TEXT NOT NULL CHECK (type IN ('SIGNAL', 'TRADE_UPDATE', 'SYSTEM_ALERT', 'NEWS_ALERT')),
  title TEXT NOT NULL,
  message TEXT,
  data JSONB,
  is_read BOOLEAN DEFAULT false,
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 12. Таблица истории чатов
CREATE TABLE IF NOT EXISTS chat_history (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  message TEXT NOT NULL,
  response TEXT NOT NULL,
  context JSONB,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 13. Таблица временной шкалы сделок
CREATE TABLE IF NOT EXISTS trade_timeline (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  trade_id UUID REFERENCES trades(id) ON DELETE CASCADE,
  event_type TEXT NOT NULL CHECK (event_type IN ('OPENED', 'TP1_HIT', 'TP2_HIT', 'SL_HIT', 'CLOSED', 'CANCELLED')),
  description TEXT NOT NULL,
  data JSONB,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 14. Таблица ценовых данных
CREATE TABLE IF NOT EXISTS price_feed (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  symbol TEXT NOT NULL,
  interval TEXT NOT NULL,
  timestamp BIGINT NOT NULL,
  open_price DECIMAL(20,8) NOT NULL,
  high_price DECIMAL(20,8) NOT NULL,
  low_price DECIMAL(20,8) NOT NULL,
  close_price DECIMAL(20,8) NOT NULL,
  volume DECIMAL(20,8) NOT NULL,
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  UNIQUE(symbol, interval, timestamp)
);

-- Создание индексов для производительности
CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trades(user_id);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);
CREATE INDEX IF NOT EXISTS idx_trades_opened_at ON trades(opened_at);

CREATE INDEX IF NOT EXISTS idx_signals_source ON signals(source);
CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol);
CREATE INDEX IF NOT EXISTS idx_signals_status ON signals(status);

CREATE INDEX IF NOT EXISTS idx_news_events_cluster ON news_events(cluster);
CREATE INDEX IF NOT EXISTS idx_news_events_published_at ON news_events(published_at);

CREATE INDEX IF NOT EXISTS idx_price_feed_symbol_timestamp ON price_feed(symbol, timestamp);
CREATE INDEX IF NOT EXISTS idx_price_feed_interval ON price_feed(interval);

CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_timestamp ON chat_history(timestamp);

-- Включение Row Level Security (RLS)
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE news_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE event_anomalies ENABLE ROW LEVEL SECURITY;
ALTER TABLE market_manipulations ENABLE ROW LEVEL SECURITY;
ALTER TABLE strategies ENABLE ROW LEVEL SECURITY;
ALTER TABLE portfolios ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE trade_timeline ENABLE ROW LEVEL SECURITY;
ALTER TABLE price_feed ENABLE ROW LEVEL SECURITY;

-- Создание политик безопасности
CREATE POLICY "Users can view own profile" ON profiles
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON profiles
  FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can manage own API keys" ON api_keys
  FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "All users can view signals" ON signals
  FOR SELECT USING (true);

CREATE POLICY "Users can view own trades" ON trades
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own trades" ON trades
  FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "All users can view news events" ON news_events
  FOR SELECT USING (true);

CREATE POLICY "All users can view AI analysis" ON ai_analysis
  FOR SELECT USING (true);

CREATE POLICY "All users can view anomalies" ON event_anomalies
  FOR SELECT USING (true);

CREATE POLICY "All users can view manipulations" ON market_manipulations
  FOR SELECT USING (true);

CREATE POLICY "Users can manage own strategies" ON strategies
  FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own portfolios" ON portfolios
  FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view own notifications" ON notifications
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update own notifications" ON notifications
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own chat history" ON chat_history
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own chat messages" ON chat_history
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view own trade timeline" ON trade_timeline
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM trades 
      WHERE trades.id = trade_timeline.trade_id 
      AND trades.user_id = auth.uid()
    )
  );

CREATE POLICY "All users can view price feed" ON price_feed
  FOR SELECT USING (true);

-- Создание триггеров для обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON profiles
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_strategies_updated_at BEFORE UPDATE ON strategies
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_portfolios_updated_at BEFORE UPDATE ON portfolios
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column(); 