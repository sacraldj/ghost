-- Migration: Add unified signal system tables
-- Добавляет новые таблицы для unified signal system

-- 1. Таблица источников сигналов (для ChannelManager)
CREATE TABLE IF NOT EXISTS signal_sources (
    source_id VARCHAR(100) PRIMARY KEY,
    source_type VARCHAR(50) NOT NULL, -- telegram_channel, discord, rss, api
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

-- 2. Таблица unified сигналов (дополнительная к signals_parsed)
CREATE TABLE IF NOT EXISTS unified_signals (
    signal_id VARCHAR(100) PRIMARY KEY,
    raw_id VARCHAR(100),
    trader_id VARCHAR(100) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    raw_text TEXT NOT NULL,
    original_message_id VARCHAR(100),
    
    -- Временные метки
    received_at TIMESTAMP WITH TIME ZONE NOT NULL,
    parsed_at TIMESTAMP WITH TIME ZONE,
    
    -- Торговые данные
    symbol VARCHAR(20) NOT NULL,
    raw_symbol VARCHAR(20),
    side VARCHAR(10) NOT NULL, -- LONG/SHORT
    
    -- Вход
    entry_type VARCHAR(20) DEFAULT 'range', -- range, market, limit
    entry_single DECIMAL(20,8),
    entry_min DECIMAL(20,8),
    entry_max DECIMAL(20,8),
    entry_zone DECIMAL(20,8)[],
    avg_entry_price DECIMAL(20,8),
    
    -- Цели (до 7 уровней)
    targets DECIMAL(20,8)[],
    tp1 DECIMAL(20,8),
    tp2 DECIMAL(20,8),
    tp3 DECIMAL(20,8),
    tp4 DECIMAL(20,8),
    tp5 DECIMAL(20,8),
    tp6 DECIMAL(20,8),
    tp7 DECIMAL(20,8),
    
    -- Риск-менеджмент
    sl DECIMAL(20,8),
    sl_type VARCHAR(20) DEFAULT 'fixed', -- fixed, trailing, be
    
    -- Плечо и объем
    leverage VARCHAR(20),
    source_leverage VARCHAR(20),
    volume_split VARCHAR(50),
    
    -- Метаданные парсинга
    parser_type VARCHAR(50) DEFAULT 'unknown',
    parsing_method VARCHAR(30) DEFAULT 'rule_based', -- rule_based, ai_assisted, hybrid
    confidence DECIMAL(5,2) DEFAULT 0.0,
    
    -- AI-ассистированный парсинг
    ai_used BOOLEAN DEFAULT false,
    ai_model VARCHAR(50),
    ai_confidence DECIMAL(5,2),
    ai_explanation TEXT,
    
    -- Детекция трейдера
    detected_trader_style VARCHAR(100),
    detection_confidence DECIMAL(5,2),
    
    -- Статус и валидация
    status VARCHAR(20) DEFAULT 'raw', -- raw, parsed, ai_parsed, failed, validated
    is_valid BOOLEAN DEFAULT false,
    validation_errors TEXT[],
    
    -- Дополнительная информация
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
    
    -- Счетчики
    total_attempts INTEGER DEFAULT 0,
    successful_parses INTEGER DEFAULT 0,
    failed_parses INTEGER DEFAULT 0,
    ai_fallback_used INTEGER DEFAULT 0,
    
    -- Метрики качества
    avg_confidence DECIMAL(5,2),
    avg_processing_time_ms INTEGER,
    
    -- Источники
    sources_processed TEXT[],
    traders_detected TEXT[],
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(parser_type, date)
);

-- 4. Таблица конфигурации AI парсеров
CREATE TABLE IF NOT EXISTS ai_parser_config (
    id SERIAL PRIMARY KEY,
    ai_provider VARCHAR(20) NOT NULL, -- openai, gemini, claude
    model_name VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    
    -- Настройки модели
    temperature DECIMAL(3,2) DEFAULT 0.1,
    max_tokens INTEGER DEFAULT 500,
    system_prompt TEXT,
    
    -- Метрики использования
    requests_today INTEGER DEFAULT 0,
    successful_parses_today INTEGER DEFAULT 0,
    cost_today_usd DECIMAL(10,4) DEFAULT 0.0,
    
    -- Лимиты
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
    
    -- Дополнительные метрики
    active_sources INTEGER DEFAULT 0,
    recent_traders INTEGER DEFAULT 0,
    memory_usage_mb INTEGER,
    cpu_usage_percent DECIMAL(5,2),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. Расширение trader_registry с дополнительными полями
ALTER TABLE trader_registry ADD COLUMN IF NOT EXISTS signal_count_total INTEGER DEFAULT 0;
ALTER TABLE trader_registry ADD COLUMN IF NOT EXISTS signal_count_valid INTEGER DEFAULT 0;
ALTER TABLE trader_registry ADD COLUMN IF NOT EXISTS last_signal_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE trader_registry ADD COLUMN IF NOT EXISTS avg_confidence DECIMAL(5,2);
ALTER TABLE trader_registry ADD COLUMN IF NOT EXISTS detection_accuracy DECIMAL(5,2);
ALTER TABLE trader_registry ADD COLUMN IF NOT EXISTS preferred_parser VARCHAR(50);

-- Индексы для оптимизации
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

-- Обновляем trader_registry с функцией auto-update
CREATE OR REPLACE FUNCTION update_trader_registry_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Обновляем статистику трейдера при добавлении нового сигнала
    UPDATE trader_registry 
    SET 
        signal_count_total = signal_count_total + 1,
        signal_count_valid = signal_count_valid + CASE WHEN NEW.is_valid THEN 1 ELSE 0 END,
        last_signal_at = NEW.received_at,
        avg_confidence = (
            SELECT AVG(confidence) 
            FROM unified_signals 
            WHERE trader_id = NEW.trader_id 
            AND confidence IS NOT NULL
        ),
        updated_at = NOW()
    WHERE trader_id = NEW.trader_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Создаем триггер для автообновления статистики
DROP TRIGGER IF EXISTS trigger_update_trader_stats ON unified_signals;
CREATE TRIGGER trigger_update_trader_stats
    AFTER INSERT ON unified_signals
    FOR EACH ROW
    EXECUTE FUNCTION update_trader_registry_stats();

-- Функция для очистки старых данных
CREATE OR REPLACE FUNCTION cleanup_old_signals(days_to_keep INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Удаляем старые сырые сигналы
    DELETE FROM signals_raw 
    WHERE created_at < NOW() - INTERVAL '1 day' * days_to_keep;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Удаляем старую системную статистику
    DELETE FROM system_stats 
    WHERE created_at < NOW() - INTERVAL '1 day' * (days_to_keep / 3);
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Комментарии к таблицам
COMMENT ON TABLE signal_sources IS 'Конфигурация источников сигналов для ChannelManager';
COMMENT ON TABLE unified_signals IS 'Унифицированные сигналы от UnifiedSignalSystem';
COMMENT ON TABLE parser_stats IS 'Статистика работы парсеров по дням';
COMMENT ON TABLE ai_parser_config IS 'Конфигурация и метрики AI парсеров';
COMMENT ON TABLE system_stats IS 'Системная статистика компонентов';

-- Вставляем базовые данные для AI конфигурации
INSERT INTO ai_parser_config (ai_provider, model_name, system_prompt) VALUES 
('openai', 'gpt-4o', 'You are a professional crypto trading signal parser. Extract structured data from trading signals. Return JSON only.'),
('gemini', 'gemini-1.5-pro', 'Parse crypto trading signals and return structured JSON data only.')
ON CONFLICT DO NOTHING;

-- Создаем базовые источники сигналов
INSERT INTO signal_sources (source_id, source_type, name, connection_params, parser_type, keywords_filter) VALUES
('whales_guide_test', 'telegram_channel', 'Whales Guide Test', '{"channel_id": "-1001234567890"}', 'whales_crypto_parser', ARRAY['longing', 'entry', 'targets']),
('test_channel_2trade', 'telegram_channel', '2Trade Test', '{"channel_id": "-1001234567891"}', '2trade_parser', ARRAY['long', 'short', 'вход', 'стоп']),
('test_channel_crypto_hub', 'telegram_channel', 'Crypto Hub Test', '{"channel_id": "-1001234567892"}', 'crypto_hub_parser', ARRAY['entry', 'tp1', 'tp2', 'sl'])
ON CONFLICT DO NOTHING;
