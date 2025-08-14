-- Исправление: создание таблицы signal_analysis для системы анализа сигналов
-- Выполнить в Supabase SQL Editor

-- Создаем таблицу для анализа сигналов как у Дарена
CREATE TABLE IF NOT EXISTS signal_analysis (
    analysis_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id TEXT NOT NULL,
    trader_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    
    -- Предсказания вероятностей (как у Дарена)
    tp1_probability DECIMAL(5,2) NOT NULL,
    tp2_probability DECIMAL(5,2) NOT NULL,
    sl_probability DECIMAL(5,2) NOT NULL,
    confidence_score DECIMAL(5,2) NOT NULL,
    
    -- Структурные показатели
    rr_ratio_tp1 DECIMAL(8,2),
    rr_ratio_tp2 DECIMAL(8,2),
    risk_distance DECIMAL(8,2),
    
    -- Рыночные условия
    market_conditions JSONB,
    
    -- Факторы уверенности и риска
    confidence_factors TEXT[],
    risk_factors TEXT[],
    
    -- Исторический контекст
    similar_signals_count INTEGER,
    similar_signals_success_rate DECIMAL(5,2),
    
    -- Метаданные
    analysis_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Создаем индексы для signal_analysis
CREATE INDEX IF NOT EXISTS idx_signal_analysis_signal_id ON signal_analysis (signal_id);
CREATE INDEX IF NOT EXISTS idx_signal_analysis_trader_id ON signal_analysis (trader_id);
CREATE INDEX IF NOT EXISTS idx_signal_analysis_symbol ON signal_analysis (symbol);
CREATE INDEX IF NOT EXISTS idx_signal_analysis_tp1_prob ON signal_analysis (tp1_probability DESC);
CREATE INDEX IF NOT EXISTS idx_signal_analysis_confidence ON signal_analysis (confidence_score DESC);

-- Комментарий
COMMENT ON TABLE signal_analysis IS 'Анализ сигналов с предсказанием вероятностей как у Дарена';

-- Тестовая запись для проверки
INSERT INTO signal_analysis (
    signal_id, 
    trader_id, 
    symbol, 
    tp1_probability, 
    tp2_probability, 
    sl_probability, 
    confidence_score,
    rr_ratio_tp1,
    risk_distance,
    market_conditions,
    confidence_factors,
    risk_factors,
    similar_signals_count,
    similar_signals_success_rate
) VALUES (
    'test_001',
    'slivaeminfo', 
    'BTCUSDT',
    89.5,
    65.2,
    10.5,
    87.3,
    2.1,
    3.5,
    '{"trend": "UP", "volatility": 2.3, "volume_spike": true}',
    ARRAY['Отличное R/R: 2.1', 'Всплеск объема', 'Трейдер в форме: 78.5%'],
    ARRAY['Высокая волатильность: 3.2%'],
    15,
    78.5
) ON CONFLICT (analysis_id) DO NOTHING;

-- Проверяем что таблица создана
SELECT 
    'signal_analysis' as table_name,
    COUNT(*) as records_count,
    'Таблица создана успешно!' as status
FROM signal_analysis;
