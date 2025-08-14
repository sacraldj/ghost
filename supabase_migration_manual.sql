-- GHOST Unified Signal System Migration
-- Применить вручную в Supabase SQL Editor

-- 1. Таблица источников сигналов
CREATE TABLE IF NOT EXISTS signal_sources (
    source_id VARCHAR(100) PRIMARY KEY,
    source_type VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    connection_params JSONB DEFAULT '{}',
    parser_type VARCHAR(50) DEFAULT 'default',
    is_active BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 5,
    min_confidence DECIMAL(3,2) DEFAULT 0.7,
    keywords_filter TEXT[],
    exclude_keywords TEXT[],
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Таблица unified сигналов
CREATE TABLE IF NOT EXISTS unified_signals (
    signal_id VARCHAR(100) PRIMARY KEY,
    raw_id VARCHAR(100),
    trader_id VARCHAR(100) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    raw_text TEXT NOT NULL,
    original_message_id VARCHAR(100),
    received_at TIMESTAMP WITH TIME ZONE NOT NULL,
    parsed_at TIMESTAMP WITH TIME ZONE,
    symbol VARCHAR(20) NOT NULL,
    raw_symbol VARCHAR(20),
    side VARCHAR(10) NOT NULL,
    entry_type VARCHAR(20) DEFAULT 'range',
    entry_single DECIMAL(20,8),
    entry_min DECIMAL(20,8),
    entry_max DECIMAL(20,8),
    entry_zone DECIMAL(20,8)[],
    avg_entry_price DECIMAL(20,8),
    targets DECIMAL(20,8)[],
    tp1 DECIMAL(20,8),
    tp2 DECIMAL(20,8),
    tp3 DECIMAL(20,8),
    tp4 DECIMAL(20,8),
    tp5 DECIMAL(20,8),
    tp6 DECIMAL(20,8),
    tp7 DECIMAL(20,8),
    sl DECIMAL(20,8),
    sl_type VARCHAR(20) DEFAULT 'fixed',
    leverage VARCHAR(20),
    source_leverage VARCHAR(20),
    volume_split VARCHAR(50),
    parser_type VARCHAR(50) DEFAULT 'unknown',
    parsing_method VARCHAR(30) DEFAULT 'rule_based',
    confidence DECIMAL(5,2) DEFAULT 0.0,
    ai_used BOOLEAN DEFAULT false,
    ai_model VARCHAR(50),
    ai_confidence DECIMAL(5,2),
    ai_explanation TEXT,
    detected_trader_style VARCHAR(100),
    detection_confidence DECIMAL(5,2),
    status VARCHAR(20) DEFAULT 'raw',
    is_valid BOOLEAN DEFAULT false,
    validation_errors TEXT[],
    reason TEXT,
    note TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Таблица статистики парсеров
CREATE TABLE IF NOT EXISTS parser_stats (
    id SERIAL PRIMARY KEY,
    parser_type VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    total_attempts INTEGER DEFAULT 0,
    successful_parses INTEGER DEFAULT 0,
    failed_parses INTEGER DEFAULT 0,
    ai_fallback_used INTEGER DEFAULT 0,
    avg_confidence DECIMAL(5,2),
    avg_processing_time_ms INTEGER,
    sources_processed TEXT[],
    traders_detected TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(parser_type, date)
);

-- 4. Таблица конфигурации AI парсеров
CREATE TABLE IF NOT EXISTS ai_parser_config (
    id SERIAL PRIMARY KEY,
    ai_provider VARCHAR(20) NOT NULL,
    model_name VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    temperature DECIMAL(3,2) DEFAULT 0.1,
    max_tokens INTEGER DEFAULT 500,
    system_prompt TEXT,
    requests_today INTEGER DEFAULT 0,
    successful_parses_today INTEGER DEFAULT 0,
    cost_today_usd DECIMAL(10,4) DEFAULT 0.0,
    daily_request_limit INTEGER DEFAULT 1000,
    cost_limit_usd DECIMAL(10,2) DEFAULT 50.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Таблица системной статистики
CREATE TABLE IF NOT EXISTS system_stats (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    component VARCHAR(50) NOT NULL,
    stats JSONB NOT NULL,
    active_sources INTEGER DEFAULT 0,
    recent_traders INTEGER DEFAULT 0,
    memory_usage_mb INTEGER,
    cpu_usage_percent DECIMAL(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ИНДЕКСЫ для оптимизации
CREATE INDEX IF NOT EXISTS idx_unified_signals_trader_time ON unified_signals(trader_id, received_at);
CREATE INDEX IF NOT EXISTS idx_unified_signals_symbol_time ON unified_signals(symbol, received_at);
CREATE INDEX IF NOT EXISTS idx_unified_signals_status ON unified_signals(status);
CREATE INDEX IF NOT EXISTS idx_unified_signals_is_valid ON unified_signals(is_valid);
CREATE INDEX IF NOT EXISTS idx_unified_signals_parsing_method ON unified_signals(parsing_method);

CREATE INDEX IF NOT EXISTS idx_signal_sources_type_active ON signal_sources(source_type, is_active);
CREATE INDEX IF NOT EXISTS idx_signal_sources_active ON signal_sources(is_active);

CREATE INDEX IF NOT EXISTS idx_parser_stats_date ON parser_stats(date);
CREATE INDEX IF NOT EXISTS idx_parser_stats_type_date ON parser_stats(parser_type, date);

CREATE INDEX IF NOT EXISTS idx_system_stats_timestamp ON system_stats(timestamp);
CREATE INDEX IF NOT EXISTS idx_system_stats_component_time ON system_stats(component, timestamp);

-- БАЗОВЫЕ ДАННЫЕ
INSERT INTO ai_parser_config (ai_provider, model_name, system_prompt) VALUES 
('openai', 'gpt-4o', 'You are a professional crypto trading signal parser. Extract structured data from trading signals. Return JSON only.'),
('gemini', 'gemini-1.5-pro', 'Parse crypto trading signals and return structured JSON data only.')
ON CONFLICT DO NOTHING;

INSERT INTO signal_sources (source_id, source_type, name, connection_params, parser_type, keywords_filter) VALUES
('whales_guide_main', 'telegram_channel', 'Whales Guide Main', '{"channel_id": "-1001234567890"}', 'whales_crypto_parser', ARRAY['longing', 'entry', 'targets']),
('2trade_slivaem', 'telegram_channel', '2Trade - slivaeminfo', '{"channel_id": "-1001234567891"}', '2trade_parser', ARRAY['long', 'short', 'вход', 'стоп']),
('crypto_hub_vip', 'telegram_channel', 'Crypto Hub VIP', '{"channel_id": "-1001234567892"}', 'crypto_hub_parser', ARRAY['entry', 'tp1', 'tp2', 'sl'])
ON CONFLICT (source_id) DO NOTHING;

-- Создаем таблицу для анализа сигналов как у Дарена
CREATE TABLE IF NOT EXISTS signal_analysis (
    analysis_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id TEXT NOT NULL,
    trader_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    
    -- Предсказания вероятностей (как у Дарена)
    tp1_probability DECIMAL(5,2) NOT NULL,
    tp2_probability DECIMAL(5,2) NOT NULL,
    sl_probability DECIMAL(5,2) NOT NULL,
    confidence_score DECIMAL(5,2) NOT NULL,
    
    -- Структурные показатели
    rr_ratio_tp1 DECIMAL(8,2),
    rr_ratio_tp2 DECIMAL(8,2),
    risk_distance DECIMAL(8,2),
    
    -- Рыночные условия
    market_conditions JSONB,
    
    -- Факторы уверенности и риска
    confidence_factors TEXT[],
    risk_factors TEXT[],
    
    -- Исторический контекст
    similar_signals_count INTEGER,
    similar_signals_success_rate DECIMAL(5,2),
    
    -- Метаданные
    analysis_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Создаем индексы для signal_analysis отдельно
CREATE INDEX IF NOT EXISTS idx_signal_analysis_signal_id ON signal_analysis (signal_id);
CREATE INDEX IF NOT EXISTS idx_signal_analysis_trader_id ON signal_analysis (trader_id);
CREATE INDEX IF NOT EXISTS idx_signal_analysis_symbol ON signal_analysis (symbol);
CREATE INDEX IF NOT EXISTS idx_signal_analysis_tp1_prob ON signal_analysis (tp1_probability DESC);
CREATE INDEX IF NOT EXISTS idx_signal_analysis_confidence ON signal_analysis (confidence_score DESC);

-- Комментарии
COMMENT ON TABLE signal_sources IS 'Конфигурация источников сигналов';
COMMENT ON TABLE unified_signals IS 'Унифицированные торговые сигналы';
COMMENT ON TABLE parser_stats IS 'Статистика работы парсеров';
COMMENT ON TABLE ai_parser_config IS 'Конфигурация AI парсеров';
COMMENT ON TABLE system_stats IS 'Системная статистика компонентов';
COMMENT ON TABLE signal_analysis IS 'Анализ сигналов с предсказанием вероятностей как у Дарена';
