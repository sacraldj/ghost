-- Проверка успешности миграции системы графиков
-- Выполнить в Supabase SQL Editor для проверки

-- 1. Проверяем созданные таблицы
SELECT 
    table_name, 
    table_type,
    is_insertable_into
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('signal_candles_1s', 'signal_websocket_subscriptions')
ORDER BY table_name;

-- 2. Проверяем структуру таблицы signal_candles_1s
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'signal_candles_1s'
ORDER BY ordinal_position;

-- 3. Проверяем структуру таблицы signal_websocket_subscriptions  
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'signal_websocket_subscriptions'
ORDER BY ordinal_position;

-- 4. Проверяем созданные индексы
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename IN ('signal_candles_1s', 'signal_websocket_subscriptions')
ORDER BY tablename, indexname;

-- 5. Проверяем созданные функции
SELECT 
    routine_name,
    routine_type,
    data_type as return_type
FROM information_schema.routines
WHERE routine_schema = 'public'
AND routine_name IN (
    'get_tracking_statistics',
    'get_signal_candles_stats', 
    'increment_candles_collected',
    'get_symbol_statistics',
    'cleanup_old_candles',
    'get_active_subscriptions_with_stats',
    'get_top_symbols_by_activity'
)
ORDER BY routine_name;

-- 6. Проверяем созданные представления (views)
SELECT 
    table_name,
    view_definition
FROM information_schema.views
WHERE table_schema = 'public'
AND table_name IN ('v_active_tracking', 'v_system_overview');

-- 7. Тестируем функцию статистики
SELECT get_tracking_statistics() as system_stats;

-- 8. Проверяем RLS политики
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual
FROM pg_policies
WHERE tablename IN ('signal_candles_1s', 'signal_websocket_subscriptions');

-- 9. Проверяем триггеры
SELECT 
    trigger_name,
    table_name,
    action_timing,
    event_manipulation
FROM information_schema.triggers
WHERE table_name IN ('signal_candles_1s', 'signal_websocket_subscriptions');

-- 10. Тестовая вставка для проверки работоспособности
-- (Можно раскомментировать для теста)
/*
-- Тестовая запись в signal_websocket_subscriptions
INSERT INTO signal_websocket_subscriptions (
    signal_id, 
    symbol, 
    start_time, 
    status
) VALUES (
    'test_signal_123',
    'BTCUSDT', 
    EXTRACT(EPOCH FROM NOW())::INTEGER,
    'active'
);

-- Тестовая запись в signal_candles_1s  
INSERT INTO signal_candles_1s (
    signal_id,
    symbol,
    timestamp,
    open,
    high, 
    low,
    close,
    volume
) VALUES (
    'test_signal_123',
    'BTCUSDT',
    EXTRACT(EPOCH FROM NOW())::INTEGER,
    45000.0,
    45100.0,
    44900.0,
    45050.0,
    1.5
);

-- Проверяем вставленные данные
SELECT * FROM signal_websocket_subscriptions WHERE signal_id = 'test_signal_123';
SELECT * FROM signal_candles_1s WHERE signal_id = 'test_signal_123';

-- Очищаем тестовые данные
DELETE FROM signal_candles_1s WHERE signal_id = 'test_signal_123';
DELETE FROM signal_websocket_subscriptions WHERE signal_id = 'test_signal_123';
*/
