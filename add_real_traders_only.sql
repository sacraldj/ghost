-- Добавляем только реальных трейдеров без тестовых сигналов
-- Система будет получать реальные сигналы из Telegram каналов

-- Очищаем существующие записи
DELETE FROM trader_registry WHERE trader_id IN (
    'whales_crypto_guide', 
    'cryptoattack24', 
    '2trade_premium', 
    'crypto_hub_vip'
);

-- Добавляем только трейдеров (без тестовых сигналов)
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
    'English premium crypto signals - REAL CHANNEL',
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
    'Russian crypto news and pump signals - REAL CHANNEL',
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
    'Russian structured trading signals - REAL CHANNEL',
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
    'VIP crypto signals with emoji formatting - REAL CHANNEL',
    NOW(),
    NOW()
);

-- Проверяем результат
SELECT 
    trader_id,
    name,
    source_handle,
    is_active,
    notes,
    created_at
FROM trader_registry 
ORDER BY name;

-- Показываем что трейдеры готовы к получению реальных сигналов
SELECT 
    COUNT(*) as total_traders,
    COUNT(CASE WHEN is_active = true THEN 1 END) as active_traders
FROM trader_registry;
