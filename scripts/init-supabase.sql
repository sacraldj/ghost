-- GHOST Trading Platform - Инициализация базы данных
-- Выполните этот скрипт в SQL Editor Supabase Dashboard

-- Включаем расширения
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Создаем ENUM типы
CREATE TYPE "UserRole" AS ENUM ('USER', 'PREMIUM', 'ADMIN');
CREATE TYPE "TradeSide" AS ENUM ('LONG', 'SHORT');
CREATE TYPE "SignalStatus" AS ENUM ('PENDING', 'EXECUTED', 'EXPIRED', 'CANCELLED');
CREATE TYPE "TradeStatus" AS ENUM ('OPEN', 'CLOSED', 'CANCELLED', 'ERROR');
CREATE TYPE "TradeVerdict" AS ENUM ('SUCCESS', 'FAILURE', 'BREAKEVEN', 'PARTIAL_SUCCESS');
CREATE TYPE "ReactionType" AS ENUM ('PUMP', 'DUMP', 'NEUTRAL', 'SHORT_PUMP_THEN_FADE', 'MODERATE_MOVE');
CREATE TYPE "AnomalyType" AS ENUM ('NEWS_WITHOUT_REACTION', 'REACTION_WITHOUT_NEWS', 'UNEXPECTED_MOVEMENT', 'MANIPULATION');
CREATE TYPE "ManipulationType" AS ENUM ('PUMP', 'DUMP', 'SQUEEZE', 'LIQUIDATION');
CREATE TYPE "NotificationType" AS ENUM ('TRADE_OPENED', 'TRADE_CLOSED', 'SIGNAL_RECEIVED', 'NEWS_EVENT', 'SYSTEM_ALERT');

-- Таблица пользователей
CREATE TABLE IF NOT EXISTS "users" (
    "id" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "name" TEXT,
    "avatar" TEXT,
    "role" "UserRole" NOT NULL DEFAULT 'USER',
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "users_pkey" PRIMARY KEY ("id")
);

-- Таблица API ключей
CREATE TABLE IF NOT EXISTS "api_keys" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "key" TEXT NOT NULL,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "userId" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "lastUsed" TIMESTAMP(3),

    CONSTRAINT "api_keys_pkey" PRIMARY KEY ("id")
);

-- Таблица торговых сигналов
CREATE TABLE IF NOT EXISTS "signals" (
    "id" TEXT NOT NULL,
    "source" TEXT NOT NULL,
    "symbol" TEXT NOT NULL,
    "side" "TradeSide" NOT NULL,
    "entryPrice" DOUBLE PRECISION NOT NULL,
    "tp1Price" DOUBLE PRECISION,
    "tp2Price" DOUBLE PRECISION,
    "slPrice" DOUBLE PRECISION,
    "leverage" INTEGER NOT NULL DEFAULT 20,
    "risk" DOUBLE PRECISION NOT NULL DEFAULT 0.02,
    "confidence" DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    "status" "SignalStatus" NOT NULL DEFAULT 'PENDING',
    "rawMessage" TEXT NOT NULL,
    "parsedData" JSONB NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "expiresAt" TIMESTAMP(3),

    CONSTRAINT "signals_pkey" PRIMARY KEY ("id")
);

-- Таблица торговых сделок
CREATE TABLE IF NOT EXISTS "trades" (
    "id" TEXT NOT NULL,
    "signalId" TEXT,
    "userId" TEXT NOT NULL,
    "symbol" TEXT NOT NULL,
    "side" "TradeSide" NOT NULL,
    "status" "TradeStatus" NOT NULL DEFAULT 'OPEN',
    "entryPrice" DOUBLE PRECISION NOT NULL,
    "exitPrice" DOUBLE PRECISION,
    "tp1Price" DOUBLE PRECISION,
    "tp2Price" DOUBLE PRECISION,
    "slPrice" DOUBLE PRECISION,
    "quantity" DOUBLE PRECISION NOT NULL,
    "leverage" INTEGER NOT NULL,
    "marginUsed" DOUBLE PRECISION NOT NULL,
    "pnlGross" DOUBLE PRECISION,
    "pnlNet" DOUBLE PRECISION,
    "roiPercent" DOUBLE PRECISION,
    "fees" DOUBLE PRECISION,
    "openedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "closedAt" TIMESTAMP(3),
    "duration" INTEGER,
    "entryOrderId" TEXT,
    "exitOrderId" TEXT,
    "slippage" DOUBLE PRECISION,
    "latency" INTEGER,
    "beforeCandles" JSONB,
    "afterCandles" JSONB,
    "marketContext" JSONB,
    "verdict" "TradeVerdict",
    "verdictReason" TEXT,

    CONSTRAINT "trades_pkey" PRIMARY KEY ("id")
);

-- Таблица новостных событий
CREATE TABLE IF NOT EXISTS "news_events" (
    "id" TEXT NOT NULL,
    "tradeId" TEXT,
    "cluster" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "content" TEXT,
    "source" TEXT NOT NULL,
    "publishedAt" TIMESTAMP(3) NOT NULL,
    "significance" DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    "priceAtEvent" DOUBLE PRECISION,
    "price1h" DOUBLE PRECISION,
    "price4h" DOUBLE PRECISION,
    "price24h" DOUBLE PRECISION,
    "priceChange1h" DOUBLE PRECISION,
    "priceChange4h" DOUBLE PRECISION,
    "priceChange24h" DOUBLE PRECISION,
    "reactionType" "ReactionType",
    "volumeChange" DOUBLE PRECISION,
    "marketContext" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "news_events_pkey" PRIMARY KEY ("id")
);

-- Таблица ИИ-анализа
CREATE TABLE IF NOT EXISTS "ai_analysis" (
    "id" TEXT NOT NULL,
    "tradeId" TEXT,
    "newsEventId" TEXT,
    "gptAnalysis" JSONB,
    "gptConfidence" DOUBLE PRECISION,
    "gptReasoning" TEXT,
    "geminiAnalysis" JSONB,
    "geminiConfidence" DOUBLE PRECISION,
    "geminiReasoning" TEXT,
    "finalVerdict" TEXT,
    "confidence" DOUBLE PRECISION,
    "reasoning" TEXT,
    "patterns" TEXT[],
    "similarCases" INTEGER NOT NULL DEFAULT 0,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ai_analysis_pkey" PRIMARY KEY ("id")
);

-- Таблица аномалий событий
CREATE TABLE IF NOT EXISTS "event_anomalies" (
    "id" TEXT NOT NULL,
    "eventType" "AnomalyType" NOT NULL,
    "newsEventId" TEXT,
    "timestamp" TIMESTAMP(3) NOT NULL,
    "priceBefore" DOUBLE PRECISION,
    "priceAfter" DOUBLE PRECISION,
    "priceChange" DOUBLE PRECISION,
    "volumeChange" DOUBLE PRECISION,
    "newsCluster" TEXT,
    "marketContext" JSONB,
    "anomalyScore" DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    "possibleCauses" TEXT[],
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "event_anomalies_pkey" PRIMARY KEY ("id")
);

-- Таблица манипуляций рынка
CREATE TABLE IF NOT EXISTS "market_manipulations" (
    "id" TEXT NOT NULL,
    "timestamp" TIMESTAMP(3) NOT NULL,
    "symbol" TEXT NOT NULL,
    "manipulationType" "ManipulationType" NOT NULL,
    "priceBefore" DOUBLE PRECISION NOT NULL,
    "priceAfter" DOUBLE PRECISION NOT NULL,
    "volumeSpike" DOUBLE PRECISION NOT NULL,
    "fundingRateChange" DOUBLE PRECISION,
    "openInterestChange" DOUBLE PRECISION,
    "confidenceScore" DOUBLE PRECISION NOT NULL,
    "evidence" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "market_manipulations_pkey" PRIMARY KEY ("id")
);

-- Таблица стратегий
CREATE TABLE IF NOT EXISTS "strategies" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "settings" JSONB NOT NULL,
    "performance" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "strategies_pkey" PRIMARY KEY ("id")
);

-- Таблица портфелей
CREATE TABLE IF NOT EXISTS "portfolios" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "balance" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "totalPnL" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "winRate" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "portfolios_pkey" PRIMARY KEY ("id")
);

-- Таблица уведомлений
CREATE TABLE IF NOT EXISTS "notifications" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "type" "NotificationType" NOT NULL,
    "title" TEXT NOT NULL,
    "message" TEXT NOT NULL,
    "isRead" BOOLEAN NOT NULL DEFAULT false,
    "data" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "notifications_pkey" PRIMARY KEY ("id")
);

-- Таблица таймлайна сделок
CREATE TABLE IF NOT EXISTS "trade_timeline" (
    "id" TEXT NOT NULL,
    "tradeId" TEXT NOT NULL,
    "event" TEXT NOT NULL,
    "timestamp" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "data" JSONB,
    "price" DOUBLE PRECISION,
    "volume" DOUBLE PRECISION,

    CONSTRAINT "trade_timeline_pkey" PRIMARY KEY ("id")
);

-- Таблица ценового фида
CREATE TABLE IF NOT EXISTS "price_feed" (
    "id" TEXT NOT NULL,
    "symbol" TEXT NOT NULL,
    "interval" TEXT NOT NULL,
    "timestamp" TIMESTAMP(3) NOT NULL,
    "open" DOUBLE PRECISION NOT NULL,
    "high" DOUBLE PRECISION NOT NULL,
    "low" DOUBLE PRECISION NOT NULL,
    "close" DOUBLE PRECISION NOT NULL,
    "volume" DOUBLE PRECISION NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "price_feed_pkey" PRIMARY KEY ("id")
);

-- Создаем индексы для производительности
CREATE INDEX IF NOT EXISTS "users_email_idx" ON "users"("email");
CREATE INDEX IF NOT EXISTS "trades_userId_idx" ON "trades"("userId");
CREATE INDEX IF NOT EXISTS "trades_symbol_idx" ON "trades"("symbol");
CREATE INDEX IF NOT EXISTS "trades_openedAt_idx" ON "trades"("openedAt");
CREATE INDEX IF NOT EXISTS "news_events_cluster_idx" ON "news_events"("cluster");
CREATE INDEX IF NOT EXISTS "news_events_publishedAt_idx" ON "news_events"("publishedAt");
CREATE INDEX IF NOT EXISTS "price_feed_symbol_timestamp_idx" ON "price_feed"("symbol", "timestamp");
CREATE UNIQUE INDEX IF NOT EXISTS "price_feed_symbol_interval_timestamp_idx" ON "price_feed"("symbol", "interval", "timestamp");

-- Создаем внешние ключи
ALTER TABLE "api_keys" ADD CONSTRAINT "api_keys_userId_fkey" FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "trades" ADD CONSTRAINT "trades_signalId_fkey" FOREIGN KEY ("signalId") REFERENCES "signals"("id") ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE "trades" ADD CONSTRAINT "trades_userId_fkey" FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "news_events" ADD CONSTRAINT "news_events_tradeId_fkey" FOREIGN KEY ("tradeId") REFERENCES "trades"("id") ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE "ai_analysis" ADD CONSTRAINT "ai_analysis_tradeId_fkey" FOREIGN KEY ("tradeId") REFERENCES "trades"("id") ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE "ai_analysis" ADD CONSTRAINT "ai_analysis_newsEventId_fkey" FOREIGN KEY ("newsEventId") REFERENCES "news_events"("id") ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE "event_anomalies" ADD CONSTRAINT "event_anomalies_newsEventId_fkey" FOREIGN KEY ("newsEventId") REFERENCES "news_events"("id") ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE "strategies" ADD CONSTRAINT "strategies_userId_fkey" FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "portfolios" ADD CONSTRAINT "portfolios_userId_fkey" FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "notifications" ADD CONSTRAINT "notifications_userId_fkey" FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "trade_timeline" ADD CONSTRAINT "trade_timeline_tradeId_fkey" FOREIGN KEY ("tradeId") REFERENCES "trades"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- Включаем Row Level Security (RLS)
ALTER TABLE "users" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "api_keys" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "signals" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "trades" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "news_events" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "ai_analysis" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "event_anomalies" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "market_manipulations" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "strategies" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "portfolios" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "notifications" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "trade_timeline" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "price_feed" ENABLE ROW LEVEL SECURITY;

-- Создаем политики RLS для пользователей
CREATE POLICY "Users can view own profile" ON "users" FOR SELECT USING (auth.uid()::text = id);
CREATE POLICY "Users can update own profile" ON "users" FOR UPDATE USING (auth.uid()::text = id);

-- Создаем политики RLS для сделок
CREATE POLICY "Users can view own trades" ON "trades" FOR SELECT USING (auth.uid()::text = "userId");
CREATE POLICY "Users can insert own trades" ON "trades" FOR INSERT WITH CHECK (auth.uid()::text = "userId");
CREATE POLICY "Users can update own trades" ON "trades" FOR UPDATE USING (auth.uid()::text = "userId");

-- Создаем политики RLS для новостей (публичные)
CREATE POLICY "Anyone can view news events" ON "news_events" FOR SELECT USING (true);
CREATE POLICY "Authenticated users can insert news events" ON "news_events" FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- Создаем политики RLS для ИИ-анализа
CREATE POLICY "Users can view own ai analysis" ON "ai_analysis" FOR SELECT USING (auth.uid()::text = "userId");
CREATE POLICY "Users can insert own ai analysis" ON "ai_analysis" FOR INSERT WITH CHECK (auth.uid()::text = "userId");

-- Создаем политики RLS для стратегий
CREATE POLICY "Users can view own strategies" ON "strategies" FOR SELECT USING (auth.uid()::text = "userId");
CREATE POLICY "Users can insert own strategies" ON "strategies" FOR INSERT WITH CHECK (auth.uid()::text = "userId");
CREATE POLICY "Users can update own strategies" ON "strategies" FOR UPDATE USING (auth.uid()::text = "userId");

-- Создаем политики RLS для портфелей
CREATE POLICY "Users can view own portfolios" ON "portfolios" FOR SELECT USING (auth.uid()::text = "userId");
CREATE POLICY "Users can insert own portfolios" ON "portfolios" FOR INSERT WITH CHECK (auth.uid()::text = "userId");
CREATE POLICY "Users can update own portfolios" ON "portfolios" FOR UPDATE USING (auth.uid()::text = "userId");

-- Создаем политики RLS для уведомлений
CREATE POLICY "Users can view own notifications" ON "notifications" FOR SELECT USING (auth.uid()::text = "userId");
CREATE POLICY "Users can insert own notifications" ON "notifications" FOR INSERT WITH CHECK (auth.uid()::text = "userId");
CREATE POLICY "Users can update own notifications" ON "notifications" FOR UPDATE USING (auth.uid()::text = "userId");

-- Создаем политики RLS для таймлайна сделок
CREATE POLICY "Users can view own trade timeline" ON "trade_timeline" FOR SELECT USING (auth.uid()::text = "userId");
CREATE POLICY "Users can insert own trade timeline" ON "trade_timeline" FOR INSERT WITH CHECK (auth.uid()::text = "userId");

-- Создаем политики RLS для ценового фида (публичные)
CREATE POLICY "Anyone can view price feed" ON "price_feed" FOR SELECT USING (true);
CREATE POLICY "Authenticated users can insert price feed" ON "price_feed" FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- Вставляем тестовые данные
INSERT INTO "users" ("id", "email", "name", "role") VALUES 
('test-user-1', 'test@ghost.com', 'Test User', 'USER')
ON CONFLICT ("id") DO NOTHING;

INSERT INTO "portfolios" ("id", "userId", "name", "description", "balance", "totalPnL", "winRate") VALUES 
('test-portfolio-1', 'test-user-1', 'Main Portfolio', 'Основной портфель', 10000, 250, 75.5)
ON CONFLICT ("id") DO NOTHING;

-- Сообщение об успешном создании
SELECT 'GHOST Trading Platform - База данных успешно инициализирована!' as message; 