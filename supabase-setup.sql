-- GHOST Supabase Setup SQL
-- Выполните этот код в SQL Editor в Supabase Dashboard

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

-- 2. Таблица торговых сделок
CREATE TABLE IF NOT EXISTS trades (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL CHECK (side IN ('LONG', 'SHORT')),
  status TEXT DEFAULT 'OPEN',
  entry_price DECIMAL(20,8) NOT NULL,
  exit_price DECIMAL(20,8),
  quantity DECIMAL(20,8) NOT NULL,
  leverage INTEGER NOT NULL,
  margin_used DECIMAL(20,8) NOT NULL,
  pnl_net DECIMAL(20,8),
  roi_percent DECIMAL(10,4),
  opened_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  closed_at TIMESTAMP WITH TIME ZONE
);

-- 3. Таблица истории чатов
CREATE TABLE IF NOT EXISTS chat_history (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  message TEXT NOT NULL,
  response TEXT NOT NULL,
  context JSONB,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Таблица новостных событий
CREATE TABLE IF NOT EXISTS news_events (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  cluster TEXT NOT NULL,
  title TEXT NOT NULL,
  content TEXT,
  source TEXT NOT NULL,
  published_at TIMESTAMP WITH TIME ZONE NOT NULL,
  price_change_1h DECIMAL(10,4),
  reaction_type TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Таблица ИИ-анализа
CREATE TABLE IF NOT EXISTS ai_analysis (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  news_event_id UUID REFERENCES news_events(id),
  gpt_analysis JSONB,
  gpt_confidence DECIMAL(3,2),
  gpt_reasoning TEXT,
  final_verdict TEXT,
  confidence DECIMAL(3,2),
  reasoning TEXT,
  patterns TEXT[],
  similar_cases INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Включение Row Level Security (RLS)
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE news_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_analysis ENABLE ROW LEVEL SECURITY;

-- Создание политик безопасности
CREATE POLICY "Users can view own profile" ON profiles
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can view own trades" ON trades
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can view own chat history" ON chat_history
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "All users can view news events" ON news_events
  FOR SELECT USING (true);

CREATE POLICY "All users can view AI analysis" ON ai_analysis
  FOR SELECT USING (true);

-- Создание индексов для производительности
CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trades(user_id);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);
CREATE INDEX IF NOT EXISTS idx_trades_opened_at ON trades(opened_at);

CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_timestamp ON chat_history(timestamp);

CREATE INDEX IF NOT EXISTS idx_news_events_cluster ON news_events(cluster);
CREATE INDEX IF NOT EXISTS idx_news_events_published_at ON news_events(published_at);

-- Создание триггера для обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON profiles
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column(); 