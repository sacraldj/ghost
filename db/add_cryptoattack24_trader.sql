-- Добавление нового трейдера CryptoAttack24 в базу данных
-- Безопасная вставка с ON CONFLICT DO NOTHING

-- Добавляем трейдера в таблицу traders (если таблица существует)
INSERT INTO traders (trader_id, name, source_type, is_traded, trust_score, status, created_at, updated_at) VALUES
('cryptoattack24', 'КриптоАтака 24', 'telegram', 1, 0.75, '🟡', extract(epoch from now()) * 1000, extract(epoch from now()) * 1000)
ON CONFLICT (trader_id) DO UPDATE SET
    name = EXCLUDED.name,
    trust_score = EXCLUDED.trust_score,
    status = EXCLUDED.status,
    updated_at = extract(epoch from now()) * 1000;

-- Добавляем в trader_registry (если таблица существует)
INSERT INTO trader_registry (trader_id, name, source, is_active, trust_score, created_at, updated_at) VALUES
('cryptoattack24', 'КриптоАтака 24', 'telegram:cryptoattack24', true, 75, now(), now())
ON CONFLICT (trader_id) DO UPDATE SET
    name = EXCLUDED.name,
    trust_score = EXCLUDED.trust_score,
    updated_at = now();

-- Добавляем начальную статистику в trader_stats
INSERT INTO trader_stats (trader_id, period_key, strategy_id, trades_cnt, winrate_pct, roi_avg_pct, pnl_usdt, max_dd_pct, tp1_pct, tp2_pct, tp3_pct, avg_t_to_tp1, avg_t_to_tp2, avg_mae_pct, avg_mfe_pct, roi_trend_sign, updated_at) VALUES
('cryptoattack24', '7d', 'tp2_sl_be', 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, extract(epoch from now()) * 1000),
('cryptoattack24', '30d', 'tp2_sl_be', 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, extract(epoch from now()) * 1000),
('cryptoattack24', 'ytd', 'tp2_sl_be', 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, extract(epoch from now()) * 1000),
('cryptoattack24', 'all', 'tp2_sl_be', 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, extract(epoch from now()) * 1000),
('cryptoattack24', '7d', 'scalping', 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, extract(epoch from now()) * 1000),
('cryptoattack24', '30d', 'scalping', 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, extract(epoch from now()) * 1000),
('cryptoattack24', '7d', 'swing', 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, extract(epoch from now()) * 1000),
('cryptoattack24', '30d', 'swing', 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, extract(epoch from now()) * 1000)
ON CONFLICT (trader_id, period_key, strategy_id) DO NOTHING;

-- Успешное сообщение
SELECT 'CryptoAttack24 trader successfully added to database!' as result;
