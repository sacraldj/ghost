-- GHOST Supabase Migrations
-- Создание таблиц для новостей в Supabase

-- Таблица критических новостей
CREATE TABLE IF NOT EXISTS critical_news (
    id BIGSERIAL PRIMARY KEY,
    local_id INTEGER, -- ID из локальной SQLite
    source_name TEXT,
    title TEXT,
    content TEXT,
    url TEXT,
    published_at TIMESTAMPTZ,
    sentiment REAL DEFAULT 0.0,
    urgency REAL DEFAULT 1.0,
    is_critical BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 1,
    market_impact REAL DEFAULT 0.0,
    synced_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Таблица обычных новостей
CREATE TABLE IF NOT EXISTS news_items (
    id BIGSERIAL PRIMARY KEY,
    local_id INTEGER, -- ID из локальной SQLite
    source_name TEXT,
    title TEXT,
    content TEXT,
    url TEXT,
    published_at TIMESTAMPTZ,
    sentiment REAL DEFAULT 0.0,
    urgency REAL DEFAULT 0.5,
    is_important BOOLEAN DEFAULT FALSE,
    priority_level INTEGER DEFAULT 3,
    synced_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Таблица рыночных данных
CREATE TABLE IF NOT EXISTS market_data (
    id BIGSERIAL PRIMARY KEY,
    symbol TEXT,
    price REAL,
    change_24h REAL,
    volume REAL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Таблица критических алертов
CREATE TABLE IF NOT EXISTS critical_alerts (
    id BIGSERIAL PRIMARY KEY,
    alert_type TEXT,
    message TEXT,
    severity INTEGER DEFAULT 1,
    is_processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Индексы для оптимизации
CREATE INDEX IF NOT EXISTS idx_critical_news_published_at ON critical_news(published_at);
CREATE INDEX IF NOT EXISTS idx_critical_news_source ON critical_news(source_name);
CREATE INDEX IF NOT EXISTS idx_critical_news_local_id ON critical_news(local_id);
CREATE INDEX IF NOT EXISTS idx_critical_news_synced_at ON critical_news(synced_at);

CREATE INDEX IF NOT EXISTS idx_news_items_published_at ON news_items(published_at);
CREATE INDEX IF NOT EXISTS idx_news_items_source ON news_items(source_name);
CREATE INDEX IF NOT EXISTS idx_news_items_local_id ON news_items(local_id);
CREATE INDEX IF NOT EXISTS idx_news_items_synced_at ON news_items(synced_at);

CREATE INDEX IF NOT EXISTS idx_market_data_symbol ON market_data(symbol);
CREATE INDEX IF NOT EXISTS idx_market_data_timestamp ON market_data(timestamp);

CREATE INDEX IF NOT EXISTS idx_critical_alerts_created_at ON critical_alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_critical_alerts_severity ON critical_alerts(severity);

-- RLS (Row Level Security) политики
ALTER TABLE critical_news ENABLE ROW LEVEL SECURITY;
ALTER TABLE news_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE market_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE critical_alerts ENABLE ROW LEVEL SECURITY;

-- Политики для чтения (все пользователи могут читать)
CREATE POLICY "Allow read access to critical_news" ON critical_news
    FOR SELECT USING (true);

CREATE POLICY "Allow read access to news_items" ON news_items
    FOR SELECT USING (true);

CREATE POLICY "Allow read access to market_data" ON market_data
    FOR SELECT USING (true);

CREATE POLICY "Allow read access to critical_alerts" ON critical_alerts
    FOR SELECT USING (true);

-- Политики для записи (только аутентифицированные пользователи)
CREATE POLICY "Allow insert access to critical_news" ON critical_news
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Allow insert access to news_items" ON news_items
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Allow insert access to market_data" ON market_data
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Allow insert access to critical_alerts" ON critical_alerts
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- Функция для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггеры для автоматического обновления updated_at
CREATE TRIGGER update_critical_news_updated_at 
    BEFORE UPDATE ON critical_news 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_news_items_updated_at 
    BEFORE UPDATE ON news_items 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Функция для получения критических новостей
CREATE OR REPLACE FUNCTION get_critical_news(
    p_limit INTEGER DEFAULT 10,
    p_minutes INTEGER DEFAULT 5
)
RETURNS TABLE (
    id BIGINT,
    source_name TEXT,
    title TEXT,
    content TEXT,
    url TEXT,
    published_at TIMESTAMPTZ,
    sentiment REAL,
    urgency REAL,
    is_critical BOOLEAN,
    priority INTEGER,
    market_impact REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        cn.id,
        cn.source_name,
        cn.title,
        cn.content,
        cn.url,
        cn.published_at,
        cn.sentiment,
        cn.urgency,
        cn.is_critical,
        cn.priority,
        cn.market_impact
    FROM critical_news cn
    WHERE cn.published_at >= NOW() - INTERVAL '1 minute' * p_minutes
    ORDER BY cn.published_at DESC, cn.priority ASC, cn.urgency DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Функция для получения обычных новостей
CREATE OR REPLACE FUNCTION get_news_items(
    p_limit INTEGER DEFAULT 50,
    p_minutes INTEGER DEFAULT 60
)
RETURNS TABLE (
    id BIGINT,
    source_name TEXT,
    title TEXT,
    content TEXT,
    url TEXT,
    published_at TIMESTAMPTZ,
    sentiment REAL,
    urgency REAL,
    is_important BOOLEAN,
    priority_level INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ni.id,
        ni.source_name,
        ni.title,
        ni.content,
        ni.url,
        ni.published_at,
        ni.sentiment,
        ni.urgency,
        ni.is_important,
        ni.priority_level
    FROM news_items ni
    WHERE ni.published_at >= NOW() - INTERVAL '1 minute' * p_minutes
    ORDER BY ni.published_at DESC, ni.priority_level DESC, ni.urgency DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;
