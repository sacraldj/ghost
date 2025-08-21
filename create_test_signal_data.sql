-- Создание тестовых данных для проверки системы графиков
-- Выполнить в Supabase SQL Editor

-- 1. Создаем тестовый сигнал в v_trades (если еще нет)
INSERT INTO v_trades (
    id,
    signal_id,
    source,
    source_type,
    source_name,
    original_text,
    posted_ts,
    symbol,
    side,
    entry_type,
    entry_min,
    entry_max,
    tp1,
    tp2,
    sl,
    leverage,
    margin_usd,
    status
) VALUES (
    'test_signal_chart_001',
    'test_chart_signal_001',
    'test_channel',
    'manual',
    'Test Chart Signal',
    'Testing #BTC LONG Entry: 43000-43500 TP1: 44000 TP2: 45000 SL: 42000',
    EXTRACT(EPOCH FROM NOW() - INTERVAL '1 hour')::INTEGER,
    'BTCUSDT',
    'LONG',
    'zone',
    43000.0,
    43500.0,
    44000.0,
    45000.0,
    42000.0,
    15.0,
    100.0,
    'sim_open'
) ON CONFLICT (id) DO NOTHING;

-- 2. Создаем запись отслеживания для этого сигнала
INSERT INTO signal_websocket_subscriptions (
    signal_id,
    symbol,
    start_time,
    status,
    candles_collected
) VALUES (
    'test_signal_chart_001',
    'BTCUSDT',
    EXTRACT(EPOCH FROM NOW() - INTERVAL '1 hour')::INTEGER,
    'active',
    100
) ON CONFLICT (signal_id) DO UPDATE SET
    status = 'active',
    candles_collected = 100;

-- 3. Создаем тестовые свечи (симуляция движения цены)
DO $$
DECLARE
    i INTEGER;
    base_time INTEGER;
    current_price REAL := 43200.0;
    price_change REAL;
    volume_val REAL;
BEGIN
    base_time := EXTRACT(EPOCH FROM NOW() - INTERVAL '1 hour')::INTEGER;
    
    -- Создаем 100 свечей (по одной в минуту за последний час)
    FOR i IN 0..99 LOOP
        -- Случайное изменение цены (±0.5%)
        price_change := (random() - 0.5) * 0.01 * current_price;
        current_price := current_price + price_change;
        
        -- Случайный объем
        volume_val := 0.1 + random() * 2.0;
        
        INSERT INTO signal_candles_1s (
            signal_id,
            symbol,
            timestamp,
            open,
            high,
            low,
            close,
            volume,
            quote_volume
        ) VALUES (
            'test_signal_chart_001',
            'BTCUSDT',
            base_time + (i * 60), -- каждую минуту
            current_price,
            current_price + (random() * 50), -- high
            current_price - (random() * 50), -- low
            current_price + (random() - 0.5) * 20, -- close
            volume_val,
            volume_val * current_price
        ) ON CONFLICT (signal_id, timestamp) DO NOTHING;
        
        -- Обновляем цену для следующей итерации
        current_price := current_price + (random() - 0.5) * 20;
        
        -- Ограничиваем диапазон цены
        IF current_price < 41000 THEN current_price := 41000; END IF;
        IF current_price > 46000 THEN current_price := 46000; END IF;
    END LOOP;
END $$;

-- 4. Создаем еще один тестовый сигнал SHORT
INSERT INTO v_trades (
    id,
    signal_id,
    source,
    source_type,
    source_name,
    original_text,
    posted_ts,
    symbol,
    side,
    entry_type,
    entry_min,
    entry_max,
    tp1,
    tp2,
    sl,
    leverage,
    margin_usd,
    status
) VALUES (
    'test_signal_chart_002',
    'test_chart_signal_002',
    'test_channel',
    'manual',
    'Test Chart Signal SHORT',
    'Testing #ETH SHORT Entry: 2800-2850 TP1: 2700 TP2: 2600 SL: 2900',
    EXTRACT(EPOCH FROM NOW() - INTERVAL '30 minutes')::INTEGER,
    'ETHUSDT',
    'SHORT',
    'zone',
    2800.0,
    2850.0,
    2700.0,
    2600.0,
    2900.0,
    15.0,
    100.0,
    'sim_open'
) ON CONFLICT (id) DO NOTHING;

-- 5. Подписка для ETH сигнала
INSERT INTO signal_websocket_subscriptions (
    signal_id,
    symbol,
    start_time,
    status,
    candles_collected
) VALUES (
    'test_signal_chart_002',
    'ETHUSDT',
    EXTRACT(EPOCH FROM NOW() - INTERVAL '30 minutes')::INTEGER,
    'active',
    30
) ON CONFLICT (signal_id) DO UPDATE SET
    status = 'active',
    candles_collected = 30;

-- 6. Тестовые свечи для ETH
DO $$
DECLARE
    i INTEGER;
    base_time INTEGER;
    current_price REAL := 2825.0;
    price_change REAL;
    volume_val REAL;
BEGIN
    base_time := EXTRACT(EPOCH FROM NOW() - INTERVAL '30 minutes')::INTEGER;
    
    -- Создаем 30 свечей за последние 30 минут
    FOR i IN 0..29 LOOP
        price_change := (random() - 0.5) * 0.02 * current_price;
        current_price := current_price + price_change;
        volume_val := 1.0 + random() * 5.0;
        
        INSERT INTO signal_candles_1s (
            signal_id,
            symbol,
            timestamp,
            open,
            high,
            low,
            close,
            volume,
            quote_volume
        ) VALUES (
            'test_signal_chart_002',
            'ETHUSDT',
            base_time + (i * 60),
            current_price,
            current_price + (random() * 20),
            current_price - (random() * 20),
            current_price + (random() - 0.5) * 10,
            volume_val,
            volume_val * current_price
        ) ON CONFLICT (signal_id, timestamp) DO NOTHING;
        
        current_price := current_price + (random() - 0.5) * 15;
        
        IF current_price < 2500 THEN current_price := 2500; END IF;
        IF current_price > 3000 THEN current_price := 3000; END IF;
    END LOOP;
END $$;

-- 7. Проверяем созданные данные
SELECT 
    'v_trades test signals' as table_name,
    COUNT(*) as count
FROM v_trades 
WHERE id LIKE 'test_signal_chart_%'

UNION ALL

SELECT 
    'signal_websocket_subscriptions' as table_name,
    COUNT(*) as count
FROM signal_websocket_subscriptions 
WHERE signal_id LIKE 'test_signal_chart_%'

UNION ALL

SELECT 
    'signal_candles_1s' as table_name,
    COUNT(*) as count
FROM signal_candles_1s 
WHERE signal_id LIKE 'test_signal_chart_%';

-- 8. Показываем тестовые сигналы
SELECT 
    id,
    symbol,
    side,
    entry_min,
    entry_max,
    tp1,
    tp2,
    sl,
    to_timestamp(posted_ts) as signal_time
FROM v_trades 
WHERE id LIKE 'test_signal_chart_%'
ORDER BY posted_ts DESC;
