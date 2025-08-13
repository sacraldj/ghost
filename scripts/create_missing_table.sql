-- Создание недостающей таблицы trader_candles в Supabase
-- Выполнить в Supabase SQL Editor

-- Создаем таблицу свечей для trader observation system
CREATE TABLE IF NOT EXISTS trader_candles (
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL, -- 1m, 5m, 15m, 1h
    open_time TIMESTAMP NOT NULL,
    open_price DECIMAL(20,8) NOT NULL,
    high_price DECIMAL(20,8) NOT NULL,
    low_price DECIMAL(20,8) NOT NULL,
    close_price DECIMAL(20,8) NOT NULL,
    volume DECIMAL(20,8),
    vwap DECIMAL(20,8),
    trades_count INTEGER,
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (symbol, timeframe, open_time)
);

-- Создаем индексы
CREATE INDEX IF NOT EXISTS idx_trader_candles_symbol_tf_time ON trader_candles(symbol, timeframe, open_time);

-- Включение RLS
ALTER TABLE trader_candles ENABLE ROW LEVEL SECURITY;

-- Политика доступа
CREATE POLICY "Allow authenticated users" ON trader_candles FOR ALL TO authenticated USING (true);

-- Комментарий
COMMENT ON TABLE trader_candles IS 'Свечи для симуляции исходов сигналов в Trader Observation System';

-- Проверка создания
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'trader_candles') as column_count
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name = 'trader_candles';
