-- Исправление SQL функций для системы графиков
-- Убираем проблемные функции и оставляем только рабочие

-- 1. Обновляем функцию get_tracking_statistics (упрощенная версия)
CREATE OR REPLACE FUNCTION get_tracking_statistics()
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'total_subscriptions', COUNT(*),
        'active_subscriptions', COUNT(*) FILTER (WHERE status = 'active'),
        'completed_subscriptions', COUNT(*) FILTER (WHERE status = 'completed'),
        'unique_symbols', COUNT(DISTINCT symbol),
        'total_candles_collected', COALESCE(SUM(candles_collected), 0),
        'last_update', NOW()
    ) INTO result
    FROM signal_websocket_subscriptions;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- 2. Упрощенная функция для получения статистики по сигналу
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
        'price_range', json_build_object(
            'min', MIN(low),
            'max', MAX(high),
            'first_open', MIN(open) FILTER (WHERE timestamp = (SELECT MIN(timestamp) FROM signal_candles_1s WHERE signal_id = p_signal_id)),
            'last_close', MAX(close) FILTER (WHERE timestamp = (SELECT MAX(timestamp) FROM signal_candles_1s WHERE signal_id = p_signal_id))
        )
    ) INTO result
    FROM signal_candles_1s 
    WHERE signal_id = p_signal_id;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- 3. Функция для получения активных подписок (упрощенная)
CREATE OR REPLACE FUNCTION get_active_subscriptions()
RETURNS TABLE (
    signal_id TEXT,
    symbol TEXT,
    status TEXT,
    start_time INTEGER,
    candles_collected INTEGER,
    duration_hours NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sws.signal_id,
        sws.symbol,
        sws.status,
        sws.start_time,
        sws.candles_collected,
        ROUND((EXTRACT(EPOCH FROM NOW()) - sws.start_time) / 3600.0, 2) as duration_hours
    FROM signal_websocket_subscriptions sws
    WHERE sws.status = 'active'
    ORDER BY sws.start_time DESC;
END;
$$ LANGUAGE plpgsql;

-- 4. Проверяем, что функции работают
SELECT 'Testing get_tracking_statistics' as test_name, get_tracking_statistics() as result

UNION ALL

SELECT 'Active subscriptions count', 
       json_build_object('count', COUNT(*)) as result
FROM signal_websocket_subscriptions 
WHERE status = 'active';

-- 5. Показываем статус системы
SELECT 
    'System Status' as info,
    json_build_object(
        'tables_created', (
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_name IN ('signal_candles_1s', 'signal_websocket_subscriptions')
        ),
        'functions_created', (
            SELECT COUNT(*) 
            FROM information_schema.routines 
            WHERE routine_name IN ('get_tracking_statistics', 'get_signal_candles_stats')
        ),
        'test_signals_available', (
            SELECT COUNT(*) 
            FROM v_trades 
            WHERE id LIKE 'test_signal_chart_%'
        )
    ) as status;
