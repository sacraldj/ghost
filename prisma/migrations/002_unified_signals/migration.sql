-- CreateTable
CREATE TABLE "signal_sources" (
    "source_id" VARCHAR(100) NOT NULL,
    "source_type" VARCHAR(50) NOT NULL,
    "name" VARCHAR(200) NOT NULL,
    "connection_params" JSONB DEFAULT '{}',
    "parser_type" VARCHAR(50) DEFAULT 'default',
    "is_active" BOOLEAN DEFAULT true,
    "priority" INTEGER DEFAULT 5,
    "min_confidence" DECIMAL(3,2) DEFAULT 0.7,
    "keywords_filter" TEXT[],
    "exclude_keywords" TEXT[],
    "notes" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "signal_sources_pkey" PRIMARY KEY ("source_id")
);

-- CreateTable
CREATE TABLE "unified_signals" (
    "signal_id" VARCHAR(100) NOT NULL,
    "raw_id" VARCHAR(100),
    "trader_id" VARCHAR(100) NOT NULL,
    "source_type" VARCHAR(50) NOT NULL,
    "raw_text" TEXT NOT NULL,
    "original_message_id" VARCHAR(100),
    "received_at" TIMESTAMP(3) NOT NULL,
    "parsed_at" TIMESTAMP(3),
    "symbol" VARCHAR(20) NOT NULL,
    "raw_symbol" VARCHAR(20),
    "side" VARCHAR(10) NOT NULL,
    "entry_type" VARCHAR(20) DEFAULT 'range',
    "entry_single" DECIMAL(20,8),
    "entry_min" DECIMAL(20,8),
    "entry_max" DECIMAL(20,8),
    "entry_zone" DECIMAL(20,8)[],
    "avg_entry_price" DECIMAL(20,8),
    "targets" DECIMAL(20,8)[],
    "tp1" DECIMAL(20,8),
    "tp2" DECIMAL(20,8),
    "tp3" DECIMAL(20,8),
    "tp4" DECIMAL(20,8),
    "tp5" DECIMAL(20,8),
    "tp6" DECIMAL(20,8),
    "tp7" DECIMAL(20,8),
    "sl" DECIMAL(20,8),
    "sl_type" VARCHAR(20) DEFAULT 'fixed',
    "leverage" VARCHAR(20),
    "source_leverage" VARCHAR(20),
    "volume_split" VARCHAR(50),
    "parser_type" VARCHAR(50) DEFAULT 'unknown',
    "parsing_method" VARCHAR(30) DEFAULT 'rule_based',
    "confidence" DECIMAL(5,2) DEFAULT 0.0,
    "ai_used" BOOLEAN DEFAULT false,
    "ai_model" VARCHAR(50),
    "ai_confidence" DECIMAL(5,2),
    "ai_explanation" TEXT,
    "detected_trader_style" VARCHAR(100),
    "detection_confidence" DECIMAL(5,2),
    "status" VARCHAR(20) DEFAULT 'raw',
    "is_valid" BOOLEAN DEFAULT false,
    "validation_errors" TEXT[],
    "reason" TEXT,
    "note" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "unified_signals_pkey" PRIMARY KEY ("signal_id")
);

-- CreateTable
CREATE TABLE "parser_stats" (
    "id" SERIAL NOT NULL,
    "parser_type" VARCHAR(50) NOT NULL,
    "date" DATE NOT NULL,
    "total_attempts" INTEGER DEFAULT 0,
    "successful_parses" INTEGER DEFAULT 0,
    "failed_parses" INTEGER DEFAULT 0,
    "ai_fallback_used" INTEGER DEFAULT 0,
    "avg_confidence" DECIMAL(5,2),
    "avg_processing_time_ms" INTEGER,
    "sources_processed" TEXT[],
    "traders_detected" TEXT[],
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "parser_stats_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ai_parser_config" (
    "id" SERIAL NOT NULL,
    "ai_provider" VARCHAR(20) NOT NULL,
    "model_name" VARCHAR(50) NOT NULL,
    "is_active" BOOLEAN DEFAULT true,
    "temperature" DECIMAL(3,2) DEFAULT 0.1,
    "max_tokens" INTEGER DEFAULT 500,
    "system_prompt" TEXT,
    "requests_today" INTEGER DEFAULT 0,
    "successful_parses_today" INTEGER DEFAULT 0,
    "cost_today_usd" DECIMAL(10,4) DEFAULT 0.0,
    "daily_request_limit" INTEGER DEFAULT 1000,
    "cost_limit_usd" DECIMAL(10,2) DEFAULT 50.0,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ai_parser_config_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "system_stats" (
    "id" SERIAL NOT NULL,
    "timestamp" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "component" VARCHAR(50) NOT NULL,
    "stats" JSONB NOT NULL,
    "active_sources" INTEGER DEFAULT 0,
    "recent_traders" INTEGER DEFAULT 0,
    "memory_usage_mb" INTEGER,
    "cpu_usage_percent" DECIMAL(5,2),
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "system_stats_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "idx_unified_signals_trader_time" ON "unified_signals"("trader_id", "received_at");

-- CreateIndex
CREATE INDEX "idx_unified_signals_symbol_time" ON "unified_signals"("symbol", "received_at");

-- CreateIndex
CREATE INDEX "idx_unified_signals_status" ON "unified_signals"("status");

-- CreateIndex
CREATE INDEX "idx_unified_signals_is_valid" ON "unified_signals"("is_valid");

-- CreateIndex
CREATE INDEX "idx_unified_signals_parsing_method" ON "unified_signals"("parsing_method");

-- CreateIndex
CREATE INDEX "idx_signal_sources_type_active" ON "signal_sources"("source_type", "is_active");

-- CreateIndex
CREATE INDEX "idx_signal_sources_active" ON "signal_sources"("is_active");

-- CreateIndex
CREATE INDEX "idx_parser_stats_date" ON "parser_stats"("date");

-- CreateIndex
CREATE INDEX "idx_parser_stats_type_date" ON "parser_stats"("parser_type", "date");

-- CreateIndex
CREATE UNIQUE INDEX "parser_stats_parser_type_date_key" ON "parser_stats"("parser_type", "date");

-- CreateIndex
CREATE INDEX "idx_system_stats_timestamp" ON "system_stats"("timestamp");

-- CreateIndex
CREATE INDEX "idx_system_stats_component_time" ON "system_stats"("component", "timestamp");

-- Insert default AI configs
INSERT INTO "ai_parser_config" ("ai_provider", "model_name", "system_prompt") VALUES 
('openai', 'gpt-4o', 'You are a professional crypto trading signal parser. Extract structured data from trading signals. Return JSON only.'),
('gemini', 'gemini-1.5-pro', 'Parse crypto trading signals and return structured JSON data only.')
ON CONFLICT DO NOTHING;

-- Insert test signal sources  
INSERT INTO "signal_sources" ("source_id", "source_type", "name", "connection_params", "parser_type", "keywords_filter") VALUES
('whales_guide_test', 'telegram_channel', 'Whales Guide Test', '{"channel_id": "-1001234567890"}', 'whales_crypto_parser', ARRAY['longing', 'entry', 'targets']),
('test_channel_2trade', 'telegram_channel', '2Trade Test', '{"channel_id": "-1001234567891"}', '2trade_parser', ARRAY['long', 'short', 'вход', 'стоп']),
('test_channel_crypto_hub', 'telegram_channel', 'Crypto Hub Test', '{"channel_id": "-1001234567892"}', 'crypto_hub_parser', ARRAY['entry', 'tp1', 'tp2', 'sl'])
ON CONFLICT ("source_id") DO NOTHING;
