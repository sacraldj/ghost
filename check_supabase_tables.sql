-- Проверяем какие таблицы есть в нашей Supabase базе данных
-- и какие данные в них находятся

-- 1. ОСНОВНЫЕ СИСТЕМНЫЕ ТАБЛИЦЫ
SELECT 'СИСТЕМНЫЕ ТАБЛИЦЫ' as category, '' as table_name, '' as count;

-- Проверяем все таблицы в базе
SELECT 
    'Все таблицы' as info,
    schemaname,
    tablename
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY tablename;

-- 2. ТАБЛИЦЫ ДЛЯ ТРЕЙДЕРОВ И СИГНАЛОВ
SELECT 'ТРЕЙДЕРЫ И СИГНАЛЫ' as category, '' as table_name, '' as count;

-- Проверяем trader_registry
SELECT 'trader_registry' as table_name, COUNT(*)::text as count 
FROM trader_registry;

-- Проверяем signals_raw
SELECT 'signals_raw' as table_name, COUNT(*)::text as count 
FROM signals_raw;

-- Проверяем signals_parsed  
SELECT 'signals_parsed' as table_name, COUNT(*)::text as count 
FROM signals_parsed;

-- Проверяем unified_signals
SELECT 'unified_signals' as table_name, COUNT(*)::text as count 
FROM unified_signals;

-- 3. НОВОСТНЫЕ ТАБЛИЦЫ
SELECT 'НОВОСТНЫЕ ТАБЛИЦЫ' as category, '' as table_name, '' as count;

-- Проверяем news_events
SELECT 'news_events' as table_name, COUNT(*)::text as count 
FROM news_events;

-- Проверяем critical_news
SELECT 'critical_news' as table_name, COUNT(*)::text as count 
FROM critical_news;

-- Проверяем news_items
SELECT 'news_items' as table_name, COUNT(*)::text as count 
FROM news_items;

-- 4. ТОРГОВЫЕ ТАБЛИЦЫ
SELECT 'ТОРГОВЫЕ ТАБЛИЦЫ' as category, '' as table_name, '' as count;

-- Проверяем trades
SELECT 'trades' as table_name, COUNT(*)::text as count 
FROM trades;

-- Проверяем trades_min
SELECT 'trades_min' as table_name, COUNT(*)::text as count 
FROM trades_min;

-- 5. ЦЕНОВЫЕ ДАННЫЕ
SELECT 'ЦЕНОВЫЕ ДАННЫЕ' as category, '' as table_name, '' as count;

-- Проверяем price_data
SELECT 'price_data' as table_name, COUNT(*)::text as count 
FROM price_data;

-- Проверяем market_data
SELECT 'market_data' as table_name, COUNT(*)::text as count 
FROM market_data;

-- 6. ДЕТАЛЬНАЯ ИНФОРМАЦИЯ О ТРЕЙДЕРАХ
SELECT 'ДЕТАЛИ ТРЕЙДЕРОВ' as category, '' as table_name, '' as count;

SELECT 
    trader_id,
    name,
    source_handle,
    is_active,
    signal_count_total,
    signal_count_valid,
    last_signal_at,
    created_at
FROM trader_registry 
ORDER BY name;

-- 7. ПОСЛЕДНИЕ СИГНАЛЫ
SELECT 'ПОСЛЕДНИЕ СИГНАЛЫ' as category, '' as table_name, '' as count;

-- Последние 5 сырых сигналов
SELECT 
    'RAW' as type,
    trader_id,
    LEFT(text, 50) || '...' as text_preview,
    posted_at,
    processed
FROM signals_raw 
ORDER BY posted_at DESC 
LIMIT 5;

-- Последние 5 обработанных сигналов
SELECT 
    'PARSED' as type,
    trader_id,
    symbol,
    side,
    entry,
    tp1,
    sl,
    confidence,
    is_valid,
    posted_at
FROM signals_parsed 
ORDER BY posted_at DESC 
LIMIT 5;

-- 8. СТАТИСТИКА ПО ТАБЛИЦАМ
SELECT 'ОБЩАЯ СТАТИСТИКА' as category, '' as table_name, '' as count;

SELECT 
    'Трейдеры' as metric,
    COUNT(*) as total,
    COUNT(CASE WHEN is_active = true THEN 1 END) as active
FROM trader_registry
UNION ALL
SELECT 
    'Сырые сигналы' as metric,
    COUNT(*) as total,
    COUNT(CASE WHEN processed = true THEN 1 END) as processed
FROM signals_raw
UNION ALL
SELECT 
    'Обработанные сигналы' as metric,
    COUNT(*) as total,
    COUNT(CASE WHEN is_valid = true THEN 1 END) as valid
FROM signals_parsed;
