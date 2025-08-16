-- Добавляем тестовых трейдеров в trader_registry для дашборда
-- Эти трейдеры соответствуют нашим парсерам

-- Сначала очищаем существующие записи (если есть)
DELETE FROM trader_registry WHERE trader_id IN (
    'whales_crypto_guide', 
    'cryptoattack24', 
    '2trade_premium', 
    'crypto_hub_vip'
);

-- Добавляем наших трейдеров
INSERT INTO trader_registry (
    trader_id, 
    name, 
    source_type, 
    source_id, 
    source_handle, 
    mode, 
    risk_profile, 
    parsing_profile, 
    is_active, 
    notes,
    created_at,
    updated_at
) VALUES 
-- 1. Whales Crypto Guide
(
    'whales_crypto_guide',
    'Whales Crypto Guide',
    'telegram',
    '-1001288385100',
    '@whalesguide',
    'observe',
    '{"size_usd": 100, "leverage": 10, "risk_percent": 2}',
    'whales_crypto_parser',
    true,
    'English premium crypto signals with high accuracy',
    NOW(),
    NOW()
),

-- 2. КриптоАтака 24
(
    'cryptoattack24',
    'КриптоАтака 24',
    'telegram',
    '-1001263635145',
    '@cryptoattack24',
    'observe',
    '{"size_usd": 100, "leverage": 5, "risk_percent": 3}',
    'cryptoattack24_parser',
    true,
    'Russian crypto news and pump signals with market analysis',
    NOW(),
    NOW()
),

-- 3. 2Trade Premium
(
    '2trade_premium',
    '2Trade Premium',
    'telegram',
    '-1001234567890',
    '@slivaeminfo',
    'observe',
    '{"size_usd": 100, "leverage": 8, "risk_percent": 2.5}',
    'two_trade_parser',
    true,
    'Russian structured trading signals with clear entry/exit levels',
    NOW(),
    NOW()
),

-- 4. Crypto Hub VIP
(
    'crypto_hub_vip',
    'Crypto Hub VIP',
    'telegram',
    '-1001345678901',
    '@cryptohubvip',
    'observe',
    '{"size_usd": 100, "leverage": 12, "risk_percent": 1.5}',
    'crypto_hub_parser',
    true,
    'VIP crypto signals with emoji formatting and quick calls',
    NOW(),
    NOW()
);

-- Добавляем тестовые сигналы для демонстрации
INSERT INTO signals_raw (
    trader_id, 
    source_msg_id, 
    posted_at, 
    text, 
    processed, 
    created_at
) VALUES 
-- Тестовые сырые сигналы
(
    'whales_crypto_guide',
    '12345',
    NOW() - INTERVAL '1 hour',
    'Longing #BTCUSDT Here
Long (5x - 10x)
Entry: $45000 - $44500
Targets: $46000, $47000, $48000
Stoploss: $43000
Reason: Chart looks bullish with strong support levels',
    true,
    NOW() - INTERVAL '1 hour'
),
(
    'cryptoattack24',
    '12346',
    NOW() - INTERVAL '2 hours',
    '🚀🔥 #ALPINE запампили на +57% со вчерашнего вечера
Сейчас коррекция и можно заходить в лонг
Цели: 2.45, 2.60, 2.85',
    true,
    NOW() - INTERVAL '2 hours'
),
(
    '2trade_premium',
    '12347',
    NOW() - INTERVAL '3 hours',
    'ETHUSDT LONG
ВХОД: 2450-2420
ЦЕЛИ: 2500 2550 2600
СТОП: 2380',
    true,
    NOW() - INTERVAL '3 hours'
);

-- Добавляем обработанные сигналы
INSERT INTO signals_parsed (
    trader_id,
    posted_at,
    symbol,
    side,
    entry_type,
    entry,
    range_low,
    range_high,
    tp1,
    tp2,
    tp3,
    sl,
    leverage_hint,
    confidence,
    parsed_at,
    parse_version,
    checksum,
    is_valid,
    created_at
) VALUES 
-- Обработанный сигнал от Whales Crypto Guide
(
    'whales_crypto_guide',
    NOW() - INTERVAL '1 hour',
    'BTCUSDT',
    'BUY',
    'range',
    44750,
    44500,
    45000,
    46000,
    47000,
    48000,
    43000,
    10,
    0.85,
    NOW() - INTERVAL '1 hour',
    'v1.0',
    'whales_btc_' || EXTRACT(EPOCH FROM NOW())::bigint,
    true,
    NOW() - INTERVAL '1 hour'
),
-- Обработанный сигнал от КриптоАтака 24
(
    'cryptoattack24',
    NOW() - INTERVAL '2 hours',
    'ALPINEUSDT',
    'BUY',
    'market',
    2.25,
    null,
    null,
    2.45,
    2.60,
    2.85,
    2.10,
    5,
    0.75,
    NOW() - INTERVAL '2 hours',
    'v1.0',
    'crypto24_alpine_' || EXTRACT(EPOCH FROM NOW())::bigint,
    true,
    NOW() - INTERVAL '2 hours'
),
-- Обработанный сигнал от 2Trade
(
    '2trade_premium',
    NOW() - INTERVAL '3 hours',
    'ETHUSDT',
    'BUY',
    'range',
    2435,
    2420,
    2450,
    2500,
    2550,
    2600,
    2380,
    8,
    0.90,
    NOW() - INTERVAL '3 hours',
    'v1.0',
    '2trade_eth_' || EXTRACT(EPOCH FROM NOW())::bigint,
    true,
    NOW() - INTERVAL '3 hours'
);

-- Обновляем статистику трейдеров
UPDATE trader_registry SET 
    signal_count_total = (
        SELECT COUNT(*) FROM signals_raw WHERE signals_raw.trader_id = trader_registry.trader_id
    ),
    signal_count_valid = (
        SELECT COUNT(*) FROM signals_parsed WHERE signals_parsed.trader_id = trader_registry.trader_id AND is_valid = true
    ),
    last_signal_at = (
        SELECT MAX(posted_at) FROM signals_parsed WHERE signals_parsed.trader_id = trader_registry.trader_id
    ),
    avg_confidence = (
        SELECT AVG(confidence) FROM signals_parsed WHERE signals_parsed.trader_id = trader_registry.trader_id AND is_valid = true
    );

-- Проверяем результат
SELECT 
    trader_id,
    name,
    source_handle,
    is_active,
    signal_count_total,
    signal_count_valid,
    last_signal_at,
    ROUND(avg_confidence::numeric, 2) as avg_confidence
FROM trader_registry 
ORDER BY signal_count_valid DESC;

-- Показываем статистику сигналов
SELECT 
    'Сырые сигналы' as type,
    COUNT(*) as count,
    COUNT(DISTINCT trader_id) as unique_traders
FROM signals_raw
UNION ALL
SELECT 
    'Обработанные сигналы' as type,
    COUNT(*) as count,
    COUNT(DISTINCT trader_id) as unique_traders
FROM signals_parsed
WHERE is_valid = true;
