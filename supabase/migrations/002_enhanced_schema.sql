-- GHOST Enhanced Schema Migration
-- Добавление новых таблиц и атрибутов

-- 1. Добавление новых атрибутов к существующим таблицам

-- Добавляем поля к таблице trades
ALTER TABLE trades ADD COLUMN IF NOT EXISTS strategy_id UUID REFERENCES strategies(id);
ALTER TABLE trades ADD COLUMN IF NOT EXISTS portfolio_id UUID REFERENCES portfolios(id);
ALTER TABLE trades ADD COLUMN IF NOT EXISTS risk_reward_ratio DECIMAL(10,4);
ALTER TABLE trades ADD COLUMN IF NOT EXISTS max_drawdown DECIMAL(10,4);
ALTER TABLE trades ADD COLUMN IF NOT EXISTS time_in_trade INTEGER; -- в секундах
ALTER TABLE trades ADD COLUMN IF NOT EXISTS exit_reason TEXT CHECK (exit_reason IN ('TP1', 'TP2', 'SL', 'MANUAL', 'BREAKEVEN'));
ALTER TABLE trades ADD COLUMN IF NOT EXISTS market_conditions JSONB;
ALTER TABLE trades ADD COLUMN IF NOT EXISTS news_impact_score DECIMAL(3,2);
ALTER TABLE trades ADD COLUMN IF NOT EXISTS ai_confidence_score DECIMAL(3,2);

-- Добавляем поля к таблице signals
ALTER TABLE signals ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS strategy_id UUID REFERENCES strategies(id);
ALTER TABLE signals ADD COLUMN IF NOT EXISTS news_event_id UUID REFERENCES news_events(id);
ALTER TABLE signals ADD COLUMN IF NOT EXISTS ai_generated BOOLEAN DEFAULT false;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS execution_priority INTEGER DEFAULT 1;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS market_context JSONB;

-- Добавляем поля к таблице news_events
ALTER TABLE news_events ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE news_events ADD COLUMN IF NOT EXISTS category TEXT;
ALTER TABLE news_events ADD COLUMN IF NOT EXISTS sentiment_score DECIMAL(3,2);
ALTER TABLE news_events ADD COLUMN IF NOT EXISTS urgency_score DECIMAL(3,2);
ALTER TABLE news_events ADD COLUMN IF NOT EXISTS reach_score DECIMAL(3,2);
ALTER TABLE news_events ADD COLUMN IF NOT EXISTS credibility_score DECIMAL(3,2);
ALTER TABLE news_events ADD COLUMN IF NOT EXISTS keywords TEXT[];
ALTER TABLE news_events ADD COLUMN IF NOT EXISTS entities TEXT[];
ALTER TABLE news_events ADD COLUMN IF NOT EXISTS summary TEXT;
ALTER TABLE news_events ADD COLUMN IF NOT EXISTS is_important BOOLEAN DEFAULT false;
ALTER TABLE news_events ADD COLUMN IF NOT EXISTS priority_level INTEGER DEFAULT 1;

-- 2. Создание новых таблиц

-- Таблица влиятельных твитов
CREATE TABLE IF NOT EXISTS influential_tweets (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  tweet_id TEXT UNIQUE NOT NULL,
  author TEXT NOT NULL,
  author_name TEXT,
  text TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL,
  
  -- Анализ влияния
  influence_score DECIMAL(3,2) DEFAULT 0,
  sentiment_score DECIMAL(3,2) DEFAULT 0,
  keyword_score DECIMAL(3,2) DEFAULT 0,
  engagement_score DECIMAL(3,2) DEFAULT 0,
  
  -- Метрики
  retweet_count INTEGER DEFAULT 0,
  like_count INTEGER DEFAULT 0,
  reply_count INTEGER DEFAULT 0,
  quote_count INTEGER DEFAULT 0,
  
  -- Классификация
  categories TEXT[],
  keywords TEXT[],
  
  processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица рыночных данных
CREATE TABLE IF NOT EXISTS market_data (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  symbol TEXT NOT NULL,
  price DECIMAL(20,8) NOT NULL,
  volume DECIMAL(20,8) NOT NULL,
  market_cap DECIMAL(20,8),
  
  -- Технические индикаторы
  rsi DECIMAL(10,4),
  macd DECIMAL(10,4),
  bollinger_upper DECIMAL(20,8),
  bollinger_lower DECIMAL(20,8),
  
  -- Настроения
  sentiment_score DECIMAL(3,2) DEFAULT 0,
  news_count INTEGER DEFAULT 0,
  positive_news INTEGER DEFAULT 0,
  negative_news INTEGER DEFAULT 0,
  
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица истории анализа
CREATE TABLE IF NOT EXISTS analysis_history (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  symbol TEXT NOT NULL,
  analysis_type TEXT NOT NULL CHECK (analysis_type IN ('NEWS', 'TECHNICAL', 'SENTIMENT', 'AI')),
  result TEXT NOT NULL,
  recommendation TEXT CHECK (recommendation IN ('BUY', 'SELL', 'HOLD')),
  confidence_score DECIMAL(3,2) DEFAULT 0,
  related_news TEXT[],
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица закладок новостей
CREATE TABLE IF NOT EXISTS news_bookmarks (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  news_event_id UUID REFERENCES news_events(id) ON DELETE CASCADE,
  notes TEXT,
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  UNIQUE(user_id, news_event_id)
);

-- Таблица настроек пользователя
CREATE TABLE IF NOT EXISTS user_settings (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
  
  -- Торговые настройки
  risk_tolerance TEXT DEFAULT 'MEDIUM' CHECK (risk_tolerance IN ('LOW', 'MEDIUM', 'HIGH')),
  preferred_pairs TEXT[] DEFAULT '{}',
  max_position_size DECIMAL(10,4) DEFAULT 100,
  default_leverage INTEGER DEFAULT 20,
  
  -- Уведомления
  email_notifications BOOLEAN DEFAULT true,
  telegram_notifications BOOLEAN DEFAULT false,
  telegram_chat_id TEXT,
  
  -- Интерфейс
  theme TEXT DEFAULT 'DARK' CHECK (theme IN ('LIGHT', 'DARK', 'AUTO')),
  language TEXT DEFAULT 'RU',
  timezone TEXT DEFAULT 'UTC',
  
  -- Торговые предпочтения
  auto_execute_signals BOOLEAN DEFAULT false,
  confirm_trades BOOLEAN DEFAULT true,
  max_open_positions INTEGER DEFAULT 5,
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица торговых сессий
CREATE TABLE IF NOT EXISTS trading_sessions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  session_name TEXT NOT NULL,
  start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  end_time TIMESTAMP WITH TIME ZONE,
  
  -- Статистика сессии
  trades_count INTEGER DEFAULT 0,
  winning_trades INTEGER DEFAULT 0,
  losing_trades INTEGER DEFAULT 0,
  total_pnl DECIMAL(20,8) DEFAULT 0,
  max_drawdown DECIMAL(10,4) DEFAULT 0,
  
  -- Настройки сессии
  strategy_id UUID REFERENCES strategies(id),
  risk_per_trade DECIMAL(5,4) DEFAULT 0.02,
  max_positions INTEGER DEFAULT 5,
  
  notes TEXT,
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица торговых паттернов
CREATE TABLE IF NOT EXISTS trading_patterns (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  pattern_name TEXT NOT NULL,
  pattern_type TEXT NOT NULL CHECK (pattern_type IN ('ENTRY', 'EXIT', 'RISK_MANAGEMENT')),
  
  -- Условия паттерна
  conditions JSONB NOT NULL,
  actions JSONB NOT NULL,
  
  -- Статистика
  success_rate DECIMAL(5,2) DEFAULT 0,
  total_uses INTEGER DEFAULT 0,
  is_active BOOLEAN DEFAULT true,
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица торговых целей
CREATE TABLE IF NOT EXISTS trading_goals (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  goal_name TEXT NOT NULL,
  goal_type TEXT NOT NULL CHECK (goal_type IN ('PROFIT', 'WIN_RATE', 'TRADES_COUNT', 'DRAWDOWN_LIMIT')),
  
  -- Параметры цели
  target_value DECIMAL(20,8) NOT NULL,
  current_value DECIMAL(20,8) DEFAULT 0,
  start_date DATE NOT NULL,
  end_date DATE,
  
  -- Статус
  status TEXT DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'COMPLETED', 'FAILED', 'CANCELLED')),
  progress_percentage DECIMAL(5,2) DEFAULT 0,
  
  notes TEXT,
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Создание индексов для новых таблиц

CREATE INDEX IF NOT EXISTS idx_trades_strategy_id ON trades(strategy_id);
CREATE INDEX IF NOT EXISTS idx_trades_portfolio_id ON trades(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_trades_exit_reason ON trades(exit_reason);

CREATE INDEX IF NOT EXISTS idx_signals_user_id ON signals(user_id);
CREATE INDEX IF NOT EXISTS idx_signals_strategy_id ON signals(strategy_id);
CREATE INDEX IF NOT EXISTS idx_signals_ai_generated ON signals(ai_generated);

CREATE INDEX IF NOT EXISTS idx_news_events_user_id ON news_events(user_id);
CREATE INDEX IF NOT EXISTS idx_news_events_category ON news_events(category);
CREATE INDEX IF NOT EXISTS idx_news_events_is_important ON news_events(is_important);

CREATE INDEX IF NOT EXISTS idx_influential_tweets_author ON influential_tweets(author);
CREATE INDEX IF NOT EXISTS idx_influential_tweets_created_at ON influential_tweets(created_at);
CREATE INDEX IF NOT EXISTS idx_influential_tweets_influence_score ON influential_tweets(influence_score);

CREATE INDEX IF NOT EXISTS idx_market_data_symbol ON market_data(symbol);
CREATE INDEX IF NOT EXISTS idx_market_data_timestamp ON market_data(timestamp);

CREATE INDEX IF NOT EXISTS idx_analysis_history_user_id ON analysis_history(user_id);
CREATE INDEX IF NOT EXISTS idx_analysis_history_symbol ON analysis_history(symbol);
CREATE INDEX IF NOT EXISTS idx_analysis_history_analysis_type ON analysis_history(analysis_type);

CREATE INDEX IF NOT EXISTS idx_news_bookmarks_user_id ON news_bookmarks(user_id);

CREATE INDEX IF NOT EXISTS idx_trading_sessions_user_id ON trading_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_trading_sessions_start_time ON trading_sessions(start_time);

CREATE INDEX IF NOT EXISTS idx_trading_patterns_user_id ON trading_patterns(user_id);
CREATE INDEX IF NOT EXISTS idx_trading_patterns_pattern_type ON trading_patterns(pattern_type);

CREATE INDEX IF NOT EXISTS idx_trading_goals_user_id ON trading_goals(user_id);
CREATE INDEX IF NOT EXISTS idx_trading_goals_status ON trading_goals(status);

-- 4. Включение RLS для новых таблиц

ALTER TABLE influential_tweets ENABLE ROW LEVEL SECURITY;
ALTER TABLE market_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE analysis_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE news_bookmarks ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE trading_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE trading_patterns ENABLE ROW LEVEL SECURITY;
ALTER TABLE trading_goals ENABLE ROW LEVEL SECURITY;

-- 5. Создание политик безопасности для новых таблиц

CREATE POLICY "All users can view influential tweets" ON influential_tweets
  FOR SELECT USING (true);

CREATE POLICY "All users can view market data" ON market_data
  FOR SELECT USING (true);

CREATE POLICY "Users can view own analysis history" ON analysis_history
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own analysis history" ON analysis_history
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can manage own news bookmarks" ON news_bookmarks
  FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own settings" ON user_settings
  FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own trading sessions" ON trading_sessions
  FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own trading patterns" ON trading_patterns
  FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own trading goals" ON trading_goals
  FOR ALL USING (auth.uid() = user_id);

-- 6. Создание триггеров для обновления updated_at

CREATE TRIGGER update_user_settings_updated_at BEFORE UPDATE ON user_settings
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_trading_patterns_updated_at BEFORE UPDATE ON trading_patterns
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_trading_goals_updated_at BEFORE UPDATE ON trading_goals
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 7. Создание функций для автоматических вычислений

-- Функция для обновления статистики портфолио
CREATE OR REPLACE FUNCTION update_portfolio_stats()
RETURNS TRIGGER AS $$
BEGIN
  -- Обновляем статистику портфолио при изменении сделок
  UPDATE portfolios 
  SET 
    total_trades = (
      SELECT COUNT(*) FROM trades 
      WHERE trades.portfolio_id = NEW.portfolio_id
    ),
    win_rate = (
      SELECT 
        CASE 
          WHEN COUNT(*) = 0 THEN 0 
          ELSE ROUND((COUNT(*) FILTER (WHERE pnl_net > 0)::DECIMAL / COUNT(*) * 100), 2)
        END
      FROM trades 
      WHERE trades.portfolio_id = NEW.portfolio_id AND status = 'CLOSED'
    ),
    total_pnl = (
      SELECT COALESCE(SUM(pnl_net), 0) 
      FROM trades 
      WHERE trades.portfolio_id = NEW.portfolio_id
    )
  WHERE id = NEW.portfolio_id;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер для обновления статистики портфолио
CREATE TRIGGER update_portfolio_stats_trigger
  AFTER INSERT OR UPDATE ON trades
  FOR EACH ROW
  EXECUTE FUNCTION update_portfolio_stats();

-- Функция для вычисления времени в сделке
CREATE OR REPLACE FUNCTION calculate_time_in_trade()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.closed_at IS NOT NULL AND NEW.opened_at IS NOT NULL THEN
    NEW.time_in_trade = EXTRACT(EPOCH FROM (NEW.closed_at - NEW.opened_at))::INTEGER;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер для вычисления времени в сделке
CREATE TRIGGER calculate_time_in_trade_trigger
  BEFORE UPDATE ON trades
  FOR EACH ROW
  EXECUTE FUNCTION calculate_time_in_trade();
