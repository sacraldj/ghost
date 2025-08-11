# GHOST UNIFIED SYSTEM - Детальный план архитектуры

## Обзор интеграции

Объединяем две системы:
1. **GHOST News Engine** (ваша система) - сбор и анализ новостей, ценовые данные
2. **GHOST SYSTEM MASTER BUILD** (система партнёра) - торговые сигналы, исполнение сделок, управление позициями

## Цель интеграции

Создать единую самообучающуюся систему с центральным оркестратором, которая:
- Собирает данные из всех источников (новости, цены, сигналы)
- Фильтрует торговые сигналы с помощью ML
- Исполняет сделки автоматически
- Управляет рисками и позициями
- Анализирует результаты и самообучается
- Предоставляет красивый дашборд

## Архитектура объединённой системы

### 1. Central Orchestrator (Центральный оркестратор)
**Файл:** `core/ghost_orchestrator.py`
- Главный процесс управления всей системой
- Координирует работу всех модулей
- Управляет lifecycle процессов
- Обеспечивает мониторинг и восстановление
- Логирование и трассировка

### 2. Data Collection Layer (Слой сбора данных)

#### News Engine (`news_engine/enhanced_news_engine.py`)
- Асинхронный сбор новостей из RSS, API
- Анализ sentiment, urgency, influence
- Определение критических событий
- Связь новостей с движениями цен

#### Price Feed Engine (`news_engine/price_feed_engine.py`)
- Реальное время: BTC/ETH каждую секунду
- Формирование свечей (1m, 5m, 15m, 1h, 4h, 1d)
- Множественные источники (Binance, Coinbase)
- Связь с торговыми событиями

#### Telegram Listener (`core/telegram_listener.py`)
- Прослушивание 80-100 торговых каналов
- Парсинг сигналов в реальном времени
- Классификация и валидация сигналов
- Метаданные трейдеров

#### Bybit Integration (`core/bybit_integration.py`)
- Получение позиций и ордеров
- Мониторинг исполнения
- Получение PnL данных
- Rate limiting и error handling

### 3. Processing Layer (Слой обработки)

#### Signal Processor (`core/signal_processor.py`)
- Парсинг входящих сигналов
- Нормализация символов
- Извлечение TP/SL уровней
- Определение направления сделки

#### ML Filtering System (`core/ml_filtering_system.py`)
- **Feature Engineering:**
  - Метрики трейдера (Win Rate, ROI, Drawdown)
  - Рыночная фаза (тренд/флэт/волатильность)
  - Новостной фон (sentiment, urgency)
  - Временные паттерны (время суток, день недели)
  - Технические индикаторы

- **ML Models:**
  - Logistic Regression (базовая модель)
  - XGBoost (основная модель)
  - Neural Network (для комплексных паттернов)
  - Ensemble методы

- **Self-Learning:**
  - Автоматическое обновление моделей
  - A/B тестирование стратегий
  - Адаптация к изменениям рынка

#### Risk Analyzer (`core/risk_analyzer.py`)
- Анализ размера позиции
- Корреляция с открытыми сделками
- Проверка лимитов риска
- Динамическое управление плечом

### 4. Management Layer (Слой управления)

#### Trade Executor (`core/trade_executor.py`)
- Размещение ордеров на Bybit
- Управление исполнением
- Обработка частичных заполнений
- Создание записи сделки

#### Position Manager (`core/position_manager.py`)
- Отслеживание открытых позиций
- Управление lifecycle сделок
- Синхронизация с биржей
- Обновление статусов

#### TP/SL Handler (`core/tp_sl_handler.py`)
- Управление тейк-профитами
- Перенос стоп-лосса в безубыток
- Частичное закрытие позиций
- Трейлинг стопы

#### Position Exit Tracker (`core/position_exit_tracker.py`)
- Отслеживание закрытия позиций
- Расчёт финального PnL/ROI
- Обновление записей в БД
- Финализация сделок

#### PnL Checker (`core/pnl_checker.py`)
- Верификация PnL через Bybit API
- Сверка комиссий
- Обнаружение расхождений
- Коррекция данных

### 5. Storage Layer (Слой хранения)

#### Unified Database (Supabase PostgreSQL)
```sql
-- Основные таблицы:
- trades              -- Полная схема сделок от партнёра
- news_events         -- Новостные события
- price_data          -- Сырые ценовые данные (секундные)
- candles             -- Агрегированные свечи
- signal_sources      -- Источники сигналов и их метрики
- ml_predictions      -- Предсказания ML моделей
- system_metrics      -- Метрики производительности системы
```

#### Redis Cache
- Реальные цены и свечи
- Открытые позиции
- Активные сигналы
- ML features cache

### 6. Interface Layer (Слой интерфейса)

#### REST API (Next.js Routes)
```typescript
/api/trades          -- Торговые данные
/api/news           -- Новостная лента
/api/signals        -- Торговые сигналы
/api/ml/predictions -- ML предсказания
/api/analytics      -- Аналитика и метрики
/api/system/status  -- Статус системы
```

#### Dashboard UI (React Components)
- **Portfolio Overview** - обзор портфолио
- **Live Trading** - торговля в реальном времени
- **News Analytics** - анализ новостей
- **ML Performance** - производительность ML
- **Risk Management** - управление рисками
- **System Monitoring** - мониторинг системы

### 7. External Services (Внешние сервисы)

#### Bybit Exchange
- REST API для торговли
- WebSocket для реального времени
- Получение исторических данных

#### News Sources
- NewsAPI, CryptoPanic, CoinTelegraph
- RSS feeds криптовалютных медиа
- Twitter/X API для трендов

#### Telegram
- Bot API для уведомлений
- Channels API для сигналов
- Webhook integration

## Поток данных в системе

### 1. Сбор данных
```
News Sources → News Engine → Database
Price APIs → Price Feed → Database + Cache
Telegram → Signal Parser → ML Filter → Database
```

### 2. Принятие решений
```
Signal + News + Price → ML Filter → Risk Analyzer → Trade Decision
```

### 3. Исполнение сделки
```
Trade Decision → Trade Executor → Bybit → Position Manager → Database
```

### 4. Управление позицией
```
Open Position → TP/SL Handler → Position Exit Tracker → PnL Checker → Database
```

### 5. Обучение системы
```
Closed Trades → ML Training → Model Update → Better Predictions
```

## Конфигурация и управление

### Environment Variables
```env
# Supabase
SUPABASE_URL=
SUPABASE_SECRET_KEY=

# Bybit
BYBIT_API_KEY=
BYBIT_SECRET_KEY=

# News APIs
NEWSAPI_KEY=
TWITTER_BEARER_TOKEN=

# Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Redis
REDIS_URL=

# ML Configuration
ML_MODEL_UPDATE_INTERVAL=3600
ML_FEATURE_CACHE_TTL=300
```

### System Configuration (`config/system_config.yaml`)
```yaml
orchestrator:
  check_interval: 10  # seconds
  max_restarts: 3
  health_check_timeout: 30

trading:
  max_concurrent_trades: 5
  max_risk_per_trade: 0.02  # 2%
  max_daily_risk: 0.10      # 10%

ml_filtering:
  min_confidence: 0.7
  retrain_interval: 3600    # 1 hour
  feature_lookback: 168     # 7 days

data_collection:
  news_check_interval: 30   # seconds
  price_feed_interval: 1    # seconds
  telegram_poll_interval: 1 # seconds
```

## Преимущества объединённой системы

### 1. Централизованное управление
- Единый оркестратор для всех процессов
- Унифицированное логирование и мониторинг
- Автоматическое восстановление при сбоях

### 2. Интеллектуальная фильтрация
- ML-модели учитывают новостной фон
- Адаптация к изменениям рынка
- Самообучение на результатах

### 3. Комплексный анализ
- Корреляция новостей и движений цен
- Анализ эффективности трейдеров
- Выявление рыночных паттернов

### 4. Масштабируемость
- Микросервисная архитектура
- Горизонтальное масштабирование
- Облачная готовность

### 5. Прозрачность
- Полная трассируемость решений
- Детальная аналитика
- Визуализация в реальном времени

## План реализации

### Фаза 1: Инфраструктура (1-2 недели)
1. Центральный оркестратор
2. Унифицированная схема БД
3. Базовые API endpoints
4. Система конфигурации

### Фаза 2: Интеграция данных (1-2 недели)
1. Объединение News Engine
2. Интеграция Price Feed
3. Подключение Telegram Listener
4. Синхронизация с Bybit

### Фаза 3: ML и торговля (2-3 недели)
1. ML Filtering System
2. Trade Executor
3. Position Management
4. Risk Management

### Фаза 4: UI и аналитика (1-2 недели)
1. Dashboard UI
2. Real-time визуализация
3. Аналитические отчёты
4. System monitoring

### Фаза 5: Тестирование и оптимизация (1-2 недели)
1. Интеграционные тесты
2. Performance тестирование
3. Бэктестинг стратегий
4. Production deployment

## Метрики успеха

### Технические метрики
- Uptime > 99.9%
- Latency < 100ms для критических операций
- Data accuracy > 99.95%

### Торговые метрики
- Sharpe Ratio > 1.5
- Maximum Drawdown < 10%
- Win Rate > 60%
- Profit Factor > 1.3

### ML метрики
- Precision > 0.75
- Recall > 0.70
- F1-Score > 0.72
- Model drift detection

Эта архитектура обеспечит создание профессиональной, масштабируемой и самообучающейся торговой системы, которая объединит лучшие элементы обеих систем в единое целое.
