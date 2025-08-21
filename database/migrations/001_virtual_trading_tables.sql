-- =========================================================================
-- МИГРАЦИЯ: Создание таблиц для виртуального трейдинга
-- Дата: 2025-08-21
-- Описание: Добавляет 5 новых таблиц поверх существующих v_trades
-- =========================================================================

-- 1. ВИРТУАЛЬНЫЕ ПОЗИЦИИ (основная таблица открытых позиций)
CREATE TABLE IF NOT EXISTS virtual_positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Связи с сигналами
    signal_id UUID, -- REFERENCES signals_parsed(id) - убрали FK для гибкости
    v_trade_id UUID, -- REFERENCES v_trades(id) - убрали FK для гибкости  
    
    -- Основная информация
    symbol VARCHAR(20) NOT NULL,                    -- DOGEUSDT, BTCUSDT, etc.
    side VARCHAR(5) NOT NULL CHECK (side IN ('LONG', 'SHORT')),
    strategy_id VARCHAR(50) DEFAULT 'S_A_TP1_BE_TP2',
    
    -- Параметры позиции
    position_size_usd DECIMAL(12,4) NOT NULL,      -- Размер позиции в USD
    leverage INTEGER DEFAULT 10,                    -- Плечо
    margin_usd DECIMAL(12,4) NOT NULL,             -- Используемая маржа
    
    -- Цены из сигнала
    signal_entry_min DECIMAL(20,8),                 -- Минимальная цена входа из сигнала
    signal_entry_max DECIMAL(20,8),                 -- Максимальная цена входа из сигнала
    signal_tp1 DECIMAL(20,8),                       -- Take Profit 1
    signal_tp2 DECIMAL(20,8),                       -- Take Profit 2
    signal_tp3 DECIMAL(20,8),                       -- Take Profit 3
    signal_sl DECIMAL(20,8),                        -- Stop Loss
    
    -- Текущие параметры позиции
    avg_entry_price DECIMAL(20,8),                  -- Средняя цена входа (рыночная)
    current_price DECIMAL(20,8),                    -- Текущая цена
    current_pnl_usd DECIMAL(12,4) DEFAULT 0,       -- Текущий PnL в USD
    current_pnl_percent DECIMAL(8,4) DEFAULT 0,    -- Текущий PnL в процентах
    
    -- Статус позиции
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN (
        'PENDING',      -- Ожидает входа
        'PARTIAL_FILL', -- Частично заполнена
        'FILLED',       -- Полностью заполнена
        'TP1_HIT',      -- Достигнут TP1
        'TP2_HIT',      -- Достигнут TP2
        'TP3_HIT',      -- Достигнут TP3
        'SL_HIT',       -- Достигнут Stop Loss
        'CLOSED',       -- Закрыта вручную
        'EXPIRED'       -- Истекла по времени
    )),
    
    -- Прогресс закрытия позиции
    filled_percent DECIMAL(5,2) DEFAULT 0,         -- Процент заполнения входа (0-100%)
    tp1_filled_percent DECIMAL(5,2) DEFAULT 0,     -- Процент закрытия по TP1
    tp2_filled_percent DECIMAL(5,2) DEFAULT 0,     -- Процент закрытия по TP2
    tp3_filled_percent DECIMAL(5,2) DEFAULT 0,     -- Процент закрытия по TP3
    remaining_percent DECIMAL(5,2) DEFAULT 100,    -- Остающийся процент позиции
    
    -- Временные метки
    signal_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),-- Время получения сигнала
    entry_timeout TIMESTAMPTZ,                     -- Время истечения входа
    first_entry_time TIMESTAMPTZ,                  -- Время первого входа
    last_update_time TIMESTAMPTZ,                  -- Последнее обновление цены
    close_time TIMESTAMPTZ,                        -- Время закрытия позиции
    
    -- Метаданные
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. ВХОДЫ В ПОЗИЦИЮ (может быть несколько частичных входов)
CREATE TABLE IF NOT EXISTS position_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    position_id UUID NOT NULL, -- REFERENCES virtual_positions(id) ON DELETE CASCADE
    
    -- Детали входа
    entry_price DECIMAL(20,8) NOT NULL,            -- Цена входа (рыночная)
    entry_size_usd DECIMAL(12,4) NOT NULL,         -- Размер входа в USD
    entry_percent DECIMAL(5,2) NOT NULL,           -- Процент от общей позиции (0-100%)
    
    -- Источник входа
    entry_type VARCHAR(20) DEFAULT 'MARKET' CHECK (entry_type IN (
        'MARKET',       -- По рыночной цене
        'LIMIT',        -- По лимитному ордеру
        'DCA'           -- Усреднение позиции
    )),
    
    entry_reason VARCHAR(100),                      -- Причина входа
    
    -- Временная метка
    entry_time TIMESTAMPTZ DEFAULT NOW(),
    
    -- Метаданные
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. ВЫХОДЫ ИЗ ПОЗИЦИИ (частичные закрытия, TP, SL)
CREATE TABLE IF NOT EXISTS position_exits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    position_id UUID NOT NULL, -- REFERENCES virtual_positions(id) ON DELETE CASCADE
    
    -- Детали выхода
    exit_price DECIMAL(20,8) NOT NULL,             -- Цена выхода
    exit_size_usd DECIMAL(12,4) NOT NULL,          -- Размер выхода в USD
    exit_percent DECIMAL(5,2) NOT NULL,            -- Процент закрытия позиции (0-100%)
    
    -- Результат
    pnl_usd DECIMAL(12,4) NOT NULL,                -- PnL в USD
    pnl_percent DECIMAL(8,4) NOT NULL,             -- PnL в процентах
    
    -- Тип выхода
    exit_type VARCHAR(20) NOT NULL CHECK (exit_type IN (
        'TP1',          -- Take Profit 1
        'TP2',          -- Take Profit 2  
        'TP3',          -- Take Profit 3
        'SL',           -- Stop Loss
        'MANUAL',       -- Ручное закрытие
        'TIMEOUT'       -- По истечении времени
    )),
    
    exit_reason VARCHAR(100),                       -- Причина выхода
    
    -- Временная метка
    exit_time TIMESTAMPTZ DEFAULT NOW(),
    
    -- Метаданные
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. ИСТОРИЧЕСКИЕ ДАННЫЕ СВЕЧЕЙ (для каждой позиции)
CREATE TABLE IF NOT EXISTS position_candles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    position_id UUID NOT NULL, -- REFERENCES virtual_positions(id) ON DELETE CASCADE
    
    -- OHLCV данные
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) DEFAULT '1m',            -- 1m, 5m, 15m, 1h, 4h, 1d
    open_time TIMESTAMPTZ NOT NULL,
    close_time TIMESTAMPTZ NOT NULL,
    
    open_price DECIMAL(20,8) NOT NULL,
    high_price DECIMAL(20,8) NOT NULL,
    low_price DECIMAL(20,8) NOT NULL,
    close_price DECIMAL(20,8) NOT NULL,
    volume DECIMAL(20,8),
    
    -- Индикаторы (расчетные)
    sma_20 DECIMAL(20,8),                          -- Простая скользящая средняя 20
    ema_12 DECIMAL(20,8),                          -- Экспоненциальная скользящая средняя 12
    rsi_14 DECIMAL(5,2),                           -- RSI 14
    
    -- Метаданные
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. СОБЫТИЯ ПОЗИЦИИ (логирование всех важных событий)
CREATE TABLE IF NOT EXISTS position_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    position_id UUID NOT NULL, -- REFERENCES virtual_positions(id) ON DELETE CASCADE
    
    -- Детали события
    event_type VARCHAR(30) NOT NULL CHECK (event_type IN (
        'POSITION_CREATED',     -- Позиция создана
        'ENTRY_FILLED',         -- Вход заполнен
        'PRICE_UPDATE',         -- Обновление цены
        'TP1_REACHED',          -- Достигнут TP1
        'TP2_REACHED',          -- Достигнут TP2
        'TP3_REACHED',          -- Достигнут TP3
        'SL_REACHED',           -- Достигнут SL
        'PARTIAL_CLOSE',        -- Частичное закрытие
        'POSITION_CLOSED',      -- Позиция закрыта
        'TIMEOUT',              -- Истечение времени
        'ERROR',                -- Ошибка
        'MANUAL_ACTION'         -- Ручное действие
    )),
    
    event_description TEXT,                         -- Описание события
    
    -- Контекст
    price_at_event DECIMAL(20,8),                  -- Цена на момент события
    pnl_at_event DECIMAL(12,4),                    -- PnL на момент события
    
    -- Дополнительные данные (JSON)
    event_data JSONB,                              -- Дополнительные данные события
    
    -- Временная метка
    event_time TIMESTAMPTZ DEFAULT NOW(),
    
    -- Метаданные
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =========================================================================
-- ИНДЕКСЫ для быстрых запросов
-- =========================================================================

CREATE INDEX IF NOT EXISTS idx_virtual_positions_symbol ON virtual_positions(symbol);
CREATE INDEX IF NOT EXISTS idx_virtual_positions_status ON virtual_positions(status);
CREATE INDEX IF NOT EXISTS idx_virtual_positions_signal_time ON virtual_positions(signal_time);
CREATE INDEX IF NOT EXISTS idx_virtual_positions_created_at ON virtual_positions(created_at);

CREATE INDEX IF NOT EXISTS idx_position_entries_position_id ON position_entries(position_id);
CREATE INDEX IF NOT EXISTS idx_position_entries_entry_time ON position_entries(entry_time);

CREATE INDEX IF NOT EXISTS idx_position_exits_position_id ON position_exits(position_id);
CREATE INDEX IF NOT EXISTS idx_position_exits_exit_time ON position_exits(exit_time);
CREATE INDEX IF NOT EXISTS idx_position_exits_exit_type ON position_exits(exit_type);

CREATE INDEX IF NOT EXISTS idx_position_candles_position_id ON position_candles(position_id);
CREATE INDEX IF NOT EXISTS idx_position_candles_symbol ON position_candles(symbol);
CREATE INDEX IF NOT EXISTS idx_position_candles_open_time ON position_candles(open_time);

CREATE INDEX IF NOT EXISTS idx_position_events_position_id ON position_events(position_id);
CREATE INDEX IF NOT EXISTS idx_position_events_event_time ON position_events(event_time);
CREATE INDEX IF NOT EXISTS idx_position_events_event_type ON position_events(event_type);

-- =========================================================================
-- ТРИГГЕРЫ для автообновления updated_at
-- =========================================================================

-- Функция для обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггер для virtual_positions (удаляем существующий если есть)
DROP TRIGGER IF EXISTS update_virtual_positions_updated_at ON virtual_positions;
CREATE TRIGGER update_virtual_positions_updated_at 
    BEFORE UPDATE ON virtual_positions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- =========================================================================
-- RLS (Row Level Security) - опционально
-- =========================================================================

-- Включаем RLS для безопасности (если нужно)
-- ALTER TABLE virtual_positions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE position_entries ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE position_exits ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE position_candles ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE position_events ENABLE ROW LEVEL SECURITY;

-- =========================================================================
-- КОММЕНТАРИИ К ТАБЛИЦАМ
-- =========================================================================

COMMENT ON TABLE virtual_positions IS 'Виртуальные торговые позиции с real-time мониторингом';
COMMENT ON TABLE position_entries IS 'История входов в позиции (может быть несколько частичных)';
COMMENT ON TABLE position_exits IS 'История выходов из позиций с расчетом PnL';
COMMENT ON TABLE position_candles IS 'Исторические данные свечей для анализа';
COMMENT ON TABLE position_events IS 'Лог всех событий позиций для аудита';

-- =========================================================================
-- ЗАВЕРШЕНИЕ МИГРАЦИИ
-- =========================================================================

-- Вставляем запись о выполненной миграции (если есть система миграций)
-- INSERT INTO schema_migrations (version, applied_at) 
-- VALUES ('001_virtual_trading_tables', NOW())
-- ON CONFLICT (version) DO NOTHING;
