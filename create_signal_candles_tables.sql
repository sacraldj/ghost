-- SQL схема для системы графиков и отслеживания свечей по сигналам
-- Создание таблиц в Supabase для хранения 1-секундных свечей

-- 1. Таблица для хранения 1-секундных свечей по сигналам
CREATE TABLE IF NOT EXISTS signal_candles_1s (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id TEXT NOT NULL,           -- связь с v_trades.id
    symbol TEXT NOT NULL,              -- BTCUSDT, APTUSDT, etc.
    timestamp INTEGER NOT NULL,        -- unix timestamp (секунды)
    open REAL NOT NULL,
    high REAL NOT NULL, 
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume REAL NOT NULL,
    quote_volume REAL,                 -- объем в валюте котировки  
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Уникальность по signal_id + timestamp
    UNIQUE(signal_id, timestamp)
);

-- 2. Таблица для отслеживания активных подписок WebSocket
CREATE TABLE IF NOT EXISTS signal_websocket_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id TEXT NOT NULL UNIQUE,   -- связь с v_trades.id
    symbol TEXT NOT NULL,              -- торговая пара
    start_time INTEGER NOT NULL,       -- unix timestamp когда начали
    end_time INTEGER,                  -- unix timestamp когда закончили (NULL = активно)
    status TEXT DEFAULT 'active',     -- active, stopped, completed, error
    error_message TEXT,               -- сообщение об ошибке если есть
    candles_collected INTEGER DEFAULT 0, -- количество собранных свечей
    last_candle_time INTEGER,         -- время последней полученной свечи
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 3. Индексы для быстрого поиска и сортировки
CREATE INDEX IF NOT EXISTS idx_signal_candles_signal_id ON signal_candles_1s(signal_id);
CREATE INDEX IF NOT EXISTS idx_signal_candles_timestamp ON signal_candles_1s(timestamp);
CREATE INDEX IF NOT EXISTS idx_signal_candles_symbol ON signal_candles_1s(symbol);
CREATE INDEX IF NOT EXISTS idx_signal_candles_composite ON signal_candles_1s(signal_id, timestamp);

CREATE INDEX IF NOT EXISTS idx_signal_subscriptions_signal_id ON signal_websocket_subscriptions(signal_id);
CREATE INDEX IF NOT EXISTS idx_signal_subscriptions_status ON signal_websocket_subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_signal_subscriptions_symbol ON signal_websocket_subscriptions(symbol);

-- 4. Функция для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггер для автоматического обновления updated_at в signal_websocket_subscriptions
CREATE TRIGGER update_signal_subscriptions_updated_at 
BEFORE UPDATE ON signal_websocket_subscriptions 
FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- 5. Функция для получения статистики по сигналу
CREATE OR REPLACE FUNCTION get_signal_candles_stats(p_signal_id TEXT)
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'signal_id', p_signal_id,
        'total_candles', COUNT(*),
        'first_candle', MIN(timestamp),
        'last_candle', MAX(timestamp),
        'duration_hours', ROUND(EXTRACT(EPOCH FROM (
            to_timestamp(MAX(timestamp)) - to_timestamp(MIN(timestamp))
        )) / 3600, 2),
        'price_range', json_build_object(
            'min', MIN(low),
            'max', MAX(high),
            'first_open', (SELECT open FROM signal_candles_1s WHERE signal_id = p_signal_id ORDER BY timestamp LIMIT 1),
            'last_close', (SELECT close FROM signal_candles_1s WHERE signal_id = p_signal_id ORDER BY timestamp DESC LIMIT 1)
        )
    ) INTO result
    FROM signal_candles_1s 
    WHERE signal_id = p_signal_id;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- 6. Политики безопасности (RLS)
ALTER TABLE signal_candles_1s ENABLE ROW LEVEL SECURITY;
ALTER TABLE signal_websocket_subscriptions ENABLE ROW LEVEL SECURITY;

-- Разрешаем все операции для аутентифицированных пользователей
CREATE POLICY "Allow all operations for authenticated users on signal_candles_1s" 
ON signal_candles_1s FOR ALL 
TO authenticated 
USING (true)
WITH CHECK (true);

CREATE POLICY "Allow all operations for authenticated users on signal_websocket_subscriptions" 
ON signal_websocket_subscriptions FOR ALL 
TO authenticated 
USING (true)
WITH CHECK (true);

-- 7. Комментарии к таблицам
COMMENT ON TABLE signal_candles_1s IS 'Хранение 1-секундных свечей для каждого сигнала из v_trades';
COMMENT ON TABLE signal_websocket_subscriptions IS 'Отслеживание активных WebSocket подписок для сбора свечей';

COMMENT ON COLUMN signal_candles_1s.signal_id IS 'ID сигнала из таблицы v_trades';
COMMENT ON COLUMN signal_candles_1s.symbol IS 'Торговая пара (BTCUSDT, APTUSDT, etc.)';
COMMENT ON COLUMN signal_candles_1s.timestamp IS 'Unix timestamp в секундах';

COMMENT ON COLUMN signal_websocket_subscriptions.signal_id IS 'ID сигнала из таблицы v_trades';
COMMENT ON COLUMN signal_websocket_subscriptions.status IS 'Статус подписки: active, stopped, completed, error';
COMMENT ON COLUMN signal_websocket_subscriptions.candles_collected IS 'Количество собранных свечей для контроля';

-- 8. Дополнительные функции для работы с системой

-- Функция для получения общей статистики отслеживания
CREATE OR REPLACE FUNCTION get_tracking_statistics()
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'total_subscriptions', COUNT(*),
        'active_subscriptions', COUNT(*) FILTER (WHERE status = 'active'),
        'completed_subscriptions', COUNT(*) FILTER (WHERE status = 'completed'),
        'stopped_subscriptions', COUNT(*) FILTER (WHERE status = 'stopped'),
        'error_subscriptions', COUNT(*) FILTER (WHERE status = 'error'),
        'unique_symbols', COUNT(DISTINCT symbol),
        'total_candles_collected', COALESCE(SUM(candles_collected), 0),
        'avg_candles_per_signal', ROUND(AVG(candles_collected), 2),
        'longest_running_signal', (
            SELECT signal_id 
            FROM signal_websocket_subscriptions 
            WHERE status = 'active' 
            ORDER BY start_time 
            LIMIT 1
        ),
        'most_candles_signal', (
            SELECT signal_id 
            FROM signal_websocket_subscriptions 
            ORDER BY candles_collected DESC 
            LIMIT 1
        ),
        'last_update', NOW()
    ) INTO result
    FROM signal_websocket_subscriptions;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Функция для инкремента счетчика свечей (используется в API)
CREATE OR REPLACE FUNCTION increment_candles_collected(p_signal_id TEXT)
RETURNS INTEGER AS $$
DECLARE
    new_count INTEGER;
BEGIN
    UPDATE signal_websocket_subscriptions 
    SET candles_collected = candles_collected + 1,
        updated_at = NOW()
    WHERE signal_id = p_signal_id
    RETURNING candles_collected INTO new_count;
    
    RETURN COALESCE(new_count, 0);
END;
$$ LANGUAGE plpgsql;

-- Функция для получения статистики по конкретному символу
CREATE OR REPLACE FUNCTION get_symbol_statistics(p_symbol TEXT)
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'symbol', p_symbol,
        'total_signals', COUNT(DISTINCT signal_id),
        'active_signals', COUNT(DISTINCT signal_id) FILTER (WHERE status = 'active'),
        'total_candles', COALESCE(SUM(candles_collected), 0),
        'avg_duration_hours', ROUND(AVG(
            CASE 
                WHEN end_time IS NOT NULL 
                THEN (end_time - start_time) / 3600.0 
                ELSE (EXTRACT(EPOCH FROM NOW()) - start_time) / 3600.0 
            END
        ), 2),
        'first_signal_time', MIN(start_time),
        'last_signal_time', MAX(start_time),
        'active_since', MIN(start_time) FILTER (WHERE status = 'active')
    ) INTO result
    FROM signal_websocket_subscriptions 
    WHERE symbol = p_symbol;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Функция для очистки старых записей свечей (для обслуживания)
CREATE OR REPLACE FUNCTION cleanup_old_candles(days_to_keep INTEGER DEFAULT 30)
RETURNS JSON AS $$
DECLARE
    cutoff_time INTEGER;
    deleted_count INTEGER;
    result JSON;
BEGIN
    cutoff_time := EXTRACT(EPOCH FROM NOW() - INTERVAL '1 day' * days_to_keep);
    
    -- Удаляем старые свечи
    WITH deleted AS (
        DELETE FROM signal_candles_1s 
        WHERE timestamp < cutoff_time
        RETURNING *
    )
    SELECT COUNT(*) INTO deleted_count FROM deleted;
    
    -- Также удаляем завершенные подписки старше указанного периода
    UPDATE signal_websocket_subscriptions 
    SET status = 'cleaned'
    WHERE status IN ('completed', 'stopped') 
    AND end_time < cutoff_time;
    
    SELECT json_build_object(
        'candles_deleted', deleted_count,
        'cutoff_timestamp', cutoff_time,
        'cutoff_date', to_timestamp(cutoff_time),
        'cleanup_date', NOW()
    ) INTO result;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Функция для получения активных подписок с их статистикой
CREATE OR REPLACE FUNCTION get_active_subscriptions_with_stats()
RETURNS TABLE (
    signal_id TEXT,
    symbol TEXT,
    status TEXT,
    start_time INTEGER,
    candles_collected INTEGER,
    duration_hours NUMERIC,
    last_candle_time INTEGER,
    candles_in_last_hour INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sws.signal_id,
        sws.symbol,
        sws.status,
        sws.start_time,
        sws.candles_collected,
        ROUND((EXTRACT(EPOCH FROM NOW()) - sws.start_time) / 3600.0, 2) as duration_hours,
        sws.last_candle_time,
        COALESCE((
            SELECT COUNT(*)::INTEGER
            FROM signal_candles_1s sc
            WHERE sc.signal_id = sws.signal_id
            AND sc.timestamp > EXTRACT(EPOCH FROM NOW() - INTERVAL '1 hour')
        ), 0) as candles_in_last_hour
    FROM signal_websocket_subscriptions sws
    WHERE sws.status = 'active'
    ORDER BY sws.start_time DESC;
END;
$$ LANGUAGE plpgsql;

-- Функция для получения топ символов по активности
CREATE OR REPLACE FUNCTION get_top_symbols_by_activity(limit_count INTEGER DEFAULT 10)
RETURNS TABLE (
    symbol TEXT,
    total_signals INTEGER,
    total_candles BIGINT,
    avg_candles_per_signal NUMERIC,
    first_activity TIMESTAMP,
    last_activity TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sws.symbol,
        COUNT(DISTINCT sws.signal_id)::INTEGER as total_signals,
        COALESCE(SUM(sws.candles_collected), 0) as total_candles,
        ROUND(AVG(sws.candles_collected), 2) as avg_candles_per_signal,
        to_timestamp(MIN(sws.start_time)) as first_activity,
        to_timestamp(MAX(COALESCE(sws.end_time, sws.last_candle_time, sws.start_time))) as last_activity
    FROM signal_websocket_subscriptions sws
    GROUP BY sws.symbol
    ORDER BY total_candles DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- 9. Представления (Views) для удобного доступа к данным

-- Представление активных подписок с расширенной информацией
CREATE OR REPLACE VIEW v_active_tracking AS
SELECT 
    sws.signal_id,
    sws.symbol,
    sws.status,
    sws.start_time,
    to_timestamp(sws.start_time) as start_time_formatted,
    sws.candles_collected,
    ROUND((EXTRACT(EPOCH FROM NOW()) - sws.start_time) / 3600.0, 2) as duration_hours,
    sws.last_candle_time,
    to_timestamp(sws.last_candle_time) as last_candle_time_formatted,
    vt.side,
    vt.entry_min,
    vt.entry_max,
    vt.tp1,
    vt.tp2,
    vt.sl,
    vt.source_name
FROM signal_websocket_subscriptions sws
LEFT JOIN v_trades vt ON sws.signal_id = vt.id
WHERE sws.status = 'active';

-- Представление для обзора системы
CREATE OR REPLACE VIEW v_system_overview AS
SELECT 
    COUNT(DISTINCT sws.signal_id) as total_signals,
    COUNT(DISTINCT sws.signal_id) FILTER (WHERE sws.status = 'active') as active_signals,
    COUNT(DISTINCT sws.symbol) as unique_symbols,
    COALESCE(SUM(sws.candles_collected), 0) as total_candles_collected,
    COUNT(*) FILTER (WHERE sc.timestamp > EXTRACT(EPOCH FROM NOW() - INTERVAL '1 hour')) as candles_last_hour,
    COUNT(*) FILTER (WHERE sc.timestamp > EXTRACT(EPOCH FROM NOW() - INTERVAL '1 day')) as candles_last_day
FROM signal_websocket_subscriptions sws
LEFT JOIN signal_candles_1s sc ON sws.signal_id = sc.signal_id;
