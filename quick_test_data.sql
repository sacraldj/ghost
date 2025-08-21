-- Быстрое создание тестового сигнала для проверки графика
-- Выполни в Supabase SQL Editor если еще нет тестовых данных

INSERT INTO v_trades (
    id, symbol, side, entry_min, entry_max, tp1, tp2, sl, 
    posted_ts, status, source, source_type
) VALUES (
    'quick_test_001', 'BTCUSDT', 'LONG', 43000, 43500, 44000, 45000, 42000,
    EXTRACT(EPOCH FROM NOW())::INTEGER, 'sim_open', 'test', 'manual'
) ON CONFLICT (id) DO UPDATE SET posted_ts = EXTRACT(EPOCH FROM NOW())::INTEGER;

-- Создаем несколько тестовых свечей
INSERT INTO signal_candles_1s (signal_id, symbol, timestamp, open, high, low, close, volume)
SELECT 
    'quick_test_001',
    'BTCUSDT',
    EXTRACT(EPOCH FROM NOW())::INTEGER - (i * 60),
    43200 + (random() - 0.5) * 100,
    43200 + random() * 200,
    43200 - random() * 200,
    43200 + (random() - 0.5) * 150,
    random() * 2
FROM generate_series(1, 20) i
ON CONFLICT (signal_id, timestamp) DO NOTHING;
