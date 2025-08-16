-- Исправление схемы таблицы signals_parsed
-- Добавляем недостающие колонки для совместимости с API

-- Проверяем текущую структуру таблицы
-- \d signals_parsed;

-- Добавляем колонку created_at если её нет (для совместимости)
ALTER TABLE signals_parsed 
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Обновляем created_at на основе parsed_at для существующих записей
UPDATE signals_parsed 
SET created_at = parsed_at 
WHERE created_at IS NULL AND parsed_at IS NOT NULL;

-- Обновляем created_at на основе posted_at если parsed_at нет
UPDATE signals_parsed 
SET created_at = posted_at 
WHERE created_at IS NULL AND posted_at IS NOT NULL;

-- Добавляем индексы для производительности
CREATE INDEX IF NOT EXISTS idx_signals_parsed_created_at ON signals_parsed(created_at);
CREATE INDEX IF NOT EXISTS idx_signals_parsed_trader_created ON signals_parsed(trader_id, created_at);
CREATE INDEX IF NOT EXISTS idx_signals_parsed_symbol_created ON signals_parsed(symbol, created_at);

-- Проверяем что все поля есть для API совместимости
DO $$ 
BEGIN
    -- Проверяем наличие всех нужных колонок
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'signals_parsed' AND column_name = 'created_at') THEN
        RAISE NOTICE 'ERROR: created_at column is missing!';
    ELSE
        RAISE NOTICE 'SUCCESS: created_at column exists';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'signals_parsed' AND column_name = 'parsed_at') THEN
        RAISE NOTICE 'ERROR: parsed_at column is missing!';
    ELSE
        RAISE NOTICE 'SUCCESS: parsed_at column exists';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'signals_parsed' AND column_name = 'posted_at') THEN
        RAISE NOTICE 'ERROR: posted_at column is missing!';
    ELSE
        RAISE NOTICE 'SUCCESS: posted_at column exists';
    END IF;
END $$;

-- Показываем статистику таблицы
SELECT 
    COUNT(*) as total_signals,
    COUNT(created_at) as with_created_at,
    COUNT(parsed_at) as with_parsed_at,
    COUNT(posted_at) as with_posted_at,
    MIN(created_at) as earliest_signal,
    MAX(created_at) as latest_signal
FROM signals_parsed;
