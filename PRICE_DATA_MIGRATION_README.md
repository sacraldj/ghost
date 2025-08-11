# GHOST Price Data Migration Guide

## Обзор

Этот документ описывает процесс расширения базы данных GHOST для поддержки ценовых данных и их связи с новостями.

## Что добавляется

### Новые таблицы

1. **`price_data`** - Сырые ценовые данные (каждую секунду)
   - Цены BTC, ETH и других криптовалют
   - Источники: Binance, Coinbase
   - Временные метки с точностью до секунды

2. **`candles`** - Свечи по разным интервалам
   - 1 минута, 5 минут, 15 минут, 1 час, 4 часа, 1 день
   - OHLCV данные (Open, High, Low, Close, Volume)
   - Автоматическое формирование из сырых цен

3. **`news_price_impact`** - Связь новостей с ценовыми данными
   - Анализ влияния новостей на цены
   - Расчет изменений цены и объема
   - Автоматическое определение market-moving новостей

### Расширение существующих таблиц

- **`critical_news`** - Добавлены поля для связи с ценами
- **`news_events`** - Добавлены связи с ценовыми данными

## Применение миграции

### Шаг 1: Подготовка

1. Убедитесь, что у вас есть доступ к Supabase Dashboard
2. Сделайте резервную копию базы данных (рекомендуется)
3. Откройте SQL Editor в Supabase Dashboard

### Шаг 2: Выполнение миграции

1. Скопируйте содержимое файла `supabase_price_data_migration.sql`
2. Вставьте в SQL Editor
3. Нажмите "Run" для выполнения

### Шаг 3: Проверка

После выполнения миграции проверьте:

```sql
-- Проверка созданных таблиц
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('price_data', 'candles', 'news_price_impact');

-- Проверка новых полей в critical_news
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'critical_news' 
AND column_name IN ('symbol', 'price_at_news', 'is_market_moving');
```

## Структура новых таблиц

### price_data
```sql
CREATE TABLE price_data (
    id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,           -- BTC, ETH, etc.
    price DECIMAL(20, 8) NOT NULL, -- Цена
    volume DECIMAL(20, 8),         -- Объем
    timestamp TIMESTAMP WITH TIME ZONE, -- Время получения
    source TEXT NOT NULL,           -- binance, coinbase
    exchange TEXT NOT NULL,         -- Название биржи
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### candles
```sql
CREATE TABLE candles (
    id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,           -- BTC, ETH, etc.
    interval TEXT NOT NULL,         -- 1m, 5m, 15m, 1h, 4h, 1d
    open DECIMAL(20, 8) NOT NULL,  -- Цена открытия
    high DECIMAL(20, 8) NOT NULL,  -- Максимальная цена
    low DECIMAL(20, 8) NOT NULL,   -- Минимальная цена
    close DECIMAL(20, 8) NOT NULL, -- Цена закрытия
    volume DECIMAL(20, 8),         -- Объем
    open_time TIMESTAMP WITH TIME ZONE,  -- Время открытия
    close_time TIMESTAMP WITH TIME ZONE, -- Время закрытия
    source TEXT NOT NULL,           -- Источник данных
    exchange TEXT NOT NULL,         -- Биржа
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### news_price_impact
```sql
CREATE TABLE news_price_impact (
    id TEXT PRIMARY KEY,
    news_event_id TEXT NOT NULL,    -- ID новости
    price_data_id TEXT,             -- Связь с ценой
    candle_id TEXT,                 -- Связь со свечой
    symbol TEXT NOT NULL,           -- Символ криптовалюты
    price_before DECIMAL(20, 8),   -- Цена до новости
    price_after DECIMAL(20, 8),    -- Цена после новости
    price_change DECIMAL(10, 4),   -- Изменение цены в %
    volume_change DECIMAL(10, 4),  -- Изменение объема в %
    impact_period INTEGER DEFAULT 3600, -- Период влияния (секунды)
    is_market_moving BOOLEAN DEFAULT FALSE, -- Влияет ли на рынок
    impact_score DECIMAL(5, 2),    -- Оценка влияния (0-100)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Созданные индексы

### price_data
- `idx_price_data_symbol_timestamp` - По символу и времени
- `idx_price_data_timestamp` - По времени
- `idx_price_data_symbol` - По символу
- `idx_price_data_source` - По источнику

### candles
- `idx_candles_symbol_interval_opentime` - По символу, интервалу и времени открытия
- `idx_candles_symbol_interval_closetime` - По символу, интервалу и времени закрытия
- `idx_candles_interval_opentime` - По интервалу и времени открытия
- `idx_candles_symbol` - По символу

### news_price_impact
- `idx_news_price_impact_news_event_id` - По ID новости
- `idx_news_price_impact_symbol_created_at` - По символу и времени создания
- `idx_news_price_impact_is_market_moving` - По статусу влияния на рынок
- `idx_news_price_impact_impact_score` - По оценке влияния

## Созданные View

### news_impact_analysis
Анализ влияния новостей на цены с детальной информацией о новостях.

### candle_news_analysis
Анализ свечей с количеством новостей и их влиянием.

## Созданные функции

### get_latest_price(symbol_param TEXT)
Получение последней цены по символу.

### get_candles(symbol_param TEXT, interval_param TEXT, limit_param INTEGER)
Получение свечей по символу и интервалу.

## Триггеры

### update_market_moving_status()
Автоматически обновляет поле `is_market_moving` и рассчитывает `impact_score` на основе изменения цены.

## Связи между таблицами

- `news_price_impact.news_event_id` → `news_events.id` (CASCADE)
- `news_price_impact.price_data_id` → `price_data.id` (SET NULL)
- `news_price_impact.candle_id` → `candles.id` (SET NULL)

## Следующие шаги

После успешного применения миграции:

1. **Создание API endpoints** для работы с ценовыми данными
2. **Интеграция с модулем сбора цен** (price_feed_engine.py)
3. **Модификация critical_news_engine_v2.py** для связи с ценами
4. **Создание дашборда** с графиками цен и новостей

## Возможные проблемы и решения

### Ошибка: "relation already exists"
- Используйте `CREATE TABLE IF NOT EXISTS` - миграция уже учитывает это

### Ошибка: "column already exists"
- Используйте `ADD COLUMN IF NOT EXISTS` - миграция уже учитывает это

### Ошибка: "index already exists"
- Используйте `CREATE INDEX IF NOT EXISTS` - миграция уже учитывает это

## Откат изменений

Для отката миграции выполните:

```sql
-- Удаление таблиц (осторожно!)
DROP TABLE IF EXISTS news_price_impact CASCADE;
DROP TABLE IF EXISTS candles CASCADE;
DROP TABLE IF EXISTS price_data CASCADE;

-- Удаление новых полей из critical_news
ALTER TABLE critical_news 
DROP COLUMN IF EXISTS symbol,
DROP COLUMN IF EXISTS price_at_news,
DROP COLUMN IF EXISTS price_change_1h,
DROP COLUMN IF EXISTS price_change_4h,
DROP COLUMN IF EXISTS volume_change_1h,
DROP COLUMN IF EXISTS is_market_moving;
```

## Поддержка

При возникновении проблем:
1. Проверьте логи выполнения SQL
2. Убедитесь в корректности синтаксиса
3. Проверьте права доступа к базе данных
4. Обратитесь к документации Supabase





