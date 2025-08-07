# GHOST Enhanced News Engine

## Обзор улучшений

На основе глубокого анализа архитектуры мы значительно улучшили систему GHOST News Engine, добавив:

### 🚀 Ключевые улучшения

1. **Асинхронная архитектура** - Использование `asyncio` и `aiohttp` для параллельного сбора данных
2. **Умный анализ метрик** - Автоматический расчет влияния, настроения, срочности и доверия
3. **Фильтрация дубликатов** - Хэширование контента и уникальные индексы в БД
4. **Конфигурируемость** - YAML конфигурация для всех параметров
5. **Устойчивость к ошибкам** - Повторные попытки, логирование, обработка исключений
6. **Интеграция с фронтендом** - Новый API и компонент NewsFeed

## Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   NewsAPI       │    │   Twitter       │    │  CryptoCompare  │
│   Client        │    │   Client        │    │   Client        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  News Processor │
                    │  (Sentiment,    │
                    │   Influence,    │
                    │   Urgency)      │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │  News Database  │
                    │  (SQLite/PostgreSQL) │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Frontend API   │
                    │  (/api/news)    │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │  NewsFeed       │
                    │  Component      │
                    └─────────────────┘
```

## Компоненты системы

### 1. Enhanced News Engine (`news_engine/enhanced_news_engine.py`)

**Основные классы:**
- `NewsItem` - Структура новостного элемента
- `NewsEngineConfig` - Управление конфигурацией
- `SentimentAnalyzer` - Анализ настроения с VADER
- `NewsDatabase` - Работа с базой данных
- `NewsProcessor` - Обработка и расчет метрик
- `NewsAPIClient` - Клиент для NewsAPI
- `CryptoCompareClient` - Клиент для CryptoCompare
- `EnhancedNewsEngine` - Основной движок

**Ключевые возможности:**
```python
# Асинхронный сбор данных
async def run(self):
    async with aiohttp.ClientSession() as session:
        tasks = [self._fetch_with_retry(session, client) 
                for client in self.clients.values()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
```

### 2. Конфигурация (`news_engine_config.yaml`)

**Настройки источников:**
```yaml
sources:
  newsapi:
    enabled: true
    api_key: "your_api_key"
    keywords: ["crypto", "bitcoin", "ethereum"]
    interval: 60
```

**Настройки доверия:**
```yaml
trust_scores:
  "Reuters": 0.95
  "Bloomberg": 0.90
  "CoinTelegraph": 0.75
  "*": 0.50  # По умолчанию
```

**Настройки метрик:**
```yaml
sentiment:
  method: "vader"
  thresholds:
    positive: 0.1
    negative: -0.1

urgency:
  decay_hours: 24
  instant_keywords: ["BREAKING", "URGENT", "CRASH"]
```

### 3. API для фронтенда (`app/api/news/route.ts`)

**GET запросы с фильтрами:**
```typescript
// Получение новостей с фильтрами
GET /api/news?important=true&sentiment=0.3&influence=0.8&limit=50
```

**POST запросы для действий:**
```typescript
// Закладка новости
POST /api/news
{
  "action": "bookmark",
  "data": { "user_id": "123", "news_id": "456" }
}
```

### 4. Компонент NewsFeed (`components/NewsFeed.tsx`)

**Возможности:**
- Статистика в реальном времени
- Фильтры по метрикам
- Анимированные переходы
- Цветовая индикация метрик
- Автообновление каждую минуту

## Метрики и алгоритмы

### 1. Влияние (Influence)

**Для новостей:**
```python
def _calculate_influence(self, item: NewsItem) -> float:
    base_influence = self.config["influence"]["news"]["base_influence"]
    return base_influence.get(item.source_name, 0.5)
```

**Для твитов:**
```python
def _calculate_influence_tweet(self, stats: Dict) -> float:
    followers = stats.get('followers', 0)
    retweets = stats.get('retweets', 0)
    likes = stats.get('likes', 0)
    
    influence = (
        self.config["influence"]["tweet"]["weight_followers"] * log(followers) +
        self.config["influence"]["tweet"]["weight_retweets"] * log(retweets + 1) +
        self.config["influence"]["tweet"]["weight_likes"] * log(likes + 1)
    )
    return min(1.0, influence)
```

### 2. Настроение (Sentiment)

**Использование VADER:**
```python
def analyze(self, text: str) -> float:
    scores = self.analyzer.polarity_scores(text)
    return scores["compound"]  # -1 до 1
```

### 3. Срочность (Urgency)

**Расчет по времени и ключевым словам:**
```python
def _calculate_urgency(self, item: NewsItem) -> float:
    age_hours = (now - item.published_at).total_seconds() / 3600
    urgency = max(0.0, 1.0 - age_hours / decay_hours)
    
    # Проверка ключевых слов
    for keyword in instant_keywords:
        if keyword in item.title.upper():
            urgency = max(urgency, 0.9)
    
    return urgency
```

### 4. Доверие (Trust)

**На основе репутации источника:**
```python
def _calculate_source_trust(self, source_name: str) -> float:
    trust_scores = self.config["trust_scores"]
    return trust_scores.get(source_name, trust_scores.get("*", 0.5))
```

## База данных

### Схема таблицы `news_items`:

```sql
CREATE TABLE news_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_type TEXT NOT NULL,           -- "news", "tweet", "regulatory"
    source_name TEXT,                  -- Название источника
    author TEXT,                       -- Автор
    title TEXT,                        -- Заголовок
    content TEXT,                      -- Содержание
    published_at TIMESTAMP,            -- Время публикации
    url TEXT,                          -- Ссылка
    external_id TEXT,                  -- Внешний ID
    influence REAL DEFAULT 0.0,        -- Влияние (0-1)
    sentiment REAL DEFAULT 0.0,        -- Настроение (-1 до 1)
    urgency REAL DEFAULT 0.0,          -- Срочность (0-1)
    source_trust REAL DEFAULT 0.5,     -- Доверие к источнику (0-1)
    source_type TEXT DEFAULT 'unknown', -- Тип источника
    category TEXT,                     -- Категория
    keywords TEXT,                     -- Ключевые слова (JSON)
    entities TEXT,                     -- Сущности (JSON)
    summary TEXT,                      -- Краткое содержание
    is_important BOOLEAN DEFAULT FALSE, -- Важность
    priority_level INTEGER DEFAULT 1,   -- Уровень приоритета (1-5)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    content_hash TEXT,                 -- Хэш для дубликатов
    UNIQUE(item_type, external_id, source_name, title, published_at)
);
```

### Индексы для производительности:

```sql
CREATE INDEX idx_published_at ON news_items(published_at);
CREATE INDEX idx_source_name ON news_items(source_name);
CREATE INDEX idx_sentiment ON news_items(sentiment);
CREATE INDEX idx_influence ON news_items(influence);
CREATE INDEX idx_urgency ON news_items(urgency);
```

## Установка и запуск

### 1. Установка зависимостей:

```bash
cd news_engine
pip install -r requirements.txt
```

### 2. Настройка конфигурации:

```bash
# Скопируйте и отредактируйте конфигурацию
cp news_engine_config.yaml news_engine_config_local.yaml
# Добавьте ваши API ключи
```

### 3. Запуск News Engine:

```bash
# Запуск в фоне
python enhanced_news_engine.py

# Или через systemd
sudo systemctl enable ghost-news-engine
sudo systemctl start ghost-news-engine
```

### 4. Интеграция с фронтендом:

```bash
# Запуск Next.js приложения
npm run dev
```

## Мониторинг и логирование

### Логи:

```python
# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ghost_news_engine.log'),
        logging.StreamHandler()
    ]
)
```

### Метрики для отслеживания:

- Количество новостей в час
- Среднее настроение
- Количество важных новостей
- Распределение доверия к источникам
- Время отклика API
- Процент успешных запросов

### Алерты:

```python
# Важные новости
if important_news:
    logger.warning(f"🚨 Обнаружено {len(important_news)} важных новостей!")

# Ошибки API
if isinstance(result, Exception):
    logger.error(f"Ошибка сбора данных: {result}")
```

## Расширение функциональности

### 1. Добавление новых источников:

```python
class NewSourceClient:
    async def fetch_news(self, session: aiohttp.ClientSession) -> List[NewsItem]:
        # Реализация сбора данных
        pass

# Добавить в конфигурацию
sources:
  newsource:
    enabled: true
    api_key: ""
    base_url: "https://api.newsource.com"
```

### 2. Новые алгоритмы анализа:

```python
class CustomSentimentAnalyzer:
    def analyze(self, text: str) -> float:
        # Ваша логика анализа
        pass
```

### 3. Интеграция с внешними системами:

```python
# Telegram уведомления
async def send_telegram_alert(self, news: NewsItem):
    message = f"🚨 ВАЖНАЯ НОВОСТЬ: {news.title}"
    # Отправка в Telegram
```

## Производительность

### Оптимизации:

1. **Параллельные запросы** - `asyncio.gather()` для одновременного сбора
2. **Кэширование** - Redis для часто запрашиваемых данных
3. **Индексы БД** - Быстрый поиск по метрикам
4. **Пакетная обработка** - Группировка операций вставки
5. **Таймауты** - Предотвращение зависания запросов

### Мониторинг производительности:

```python
# Время выполнения запросов
start_time = time.time()
results = await asyncio.gather(*tasks)
execution_time = time.time() - start_time
logger.info(f"Сбор данных завершен за {execution_time:.2f}с")
```

## Безопасность

### Меры безопасности:

1. **Валидация данных** - Проверка входящих данных
2. **Ограничение запросов** - Rate limiting для API
3. **Безопасное хранение ключей** - Переменные окружения
4. **Логирование действий** - Аудит всех операций
5. **Обработка ошибок** - Предотвращение утечек информации

## Заключение

Улучшенный GHOST News Engine предоставляет:

✅ **Масштабируемость** - Асинхронная архитектура  
✅ **Надежность** - Обработка ошибок и повторные попытки  
✅ **Гибкость** - Конфигурируемость всех параметров  
✅ **Интеграция** - Бесшовная работа с фронтендом  
✅ **Аналитика** - Продвинутые метрики и алгоритмы  
✅ **Мониторинг** - Подробное логирование и метрики  

Система готова к использованию в продакшене и может быть легко расширена для новых источников и алгоритмов анализа.
