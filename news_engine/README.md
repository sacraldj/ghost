# GHOST News Engine 🚀

**Мощный движок для агрегации и анализа новостей о криптовалютах и блокчейне**

## 🌟 **НОВОЕ: Бесплатные источники без API ключей!**

Теперь GHOST News Engine работает **полностью бесплатно** с RSS feeds и Public APIs:

### 📰 **Бесплатные RSS источники:**
- **CoinDesk** - https://www.coindesk.com/arc/outboundfeeds/rss/
- **CoinTelegraph** - https://cointelegraph.com/rss  
- **CryptoNews** - https://cryptonews.com/news/feed
- **Bitcoin News** - https://news.bitcoin.com/feed/

### 🌐 **Бесплатные Public APIs:**
- **CoinGecko** - 50 запросов/минуту
- **Binance Public** - 1200 запросов/минуту
- **CoinCap** - 100 запросов/минуту

### 🚀 **Быстрый старт (без API ключей):**
```bash
# Установка зависимостей
pip install -r requirements_free.txt

# Демонстрация бесплатных источников
python3 demo_free_sources.py

# Тест RSS парсера
python3 rss_parser.py

# Тест Public API клиента
python3 public_api_client.py
```

## 📋 **Содержание**

- [🚀 Быстрый старт](#-быстрый-старт)
- [⚙️ Настройка](#️-настройка)
- [🔧 Конфигурация](#-конфигурация)
- [📰 Источники новостей](#-источники-новостей)
- [🌐 API клиенты](#-api-клиенты)
- [🔔 Уведомления](#-уведомления)
- [📊 Анализ и обработка](#-анализ-и-обработка)
- [🗄️ База данных](#️-база-данных)
- [📈 Мониторинг](#-мониторинг)
- [🆓 Бесплатные источники](#-бесплатные-источники)
- [🔐 Платные источники](#-платные-источники)
- [📁 Структура проекта](#-структура-проекта)

## 🚀 **Быстрый старт**

### **Вариант 1: Только бесплатные источники (рекомендуется для начала)**
```bash
# 1. Клонируйте репозиторий
git clone <your-repo>
cd Ghost/news_engine

# 2. Установите зависимости для бесплатных источников
pip install -r requirements_free.txt

# 3. Запустите демонстрацию
python3 demo_free_sources.py

# 4. Запустите RSS парсер
python3 rss_parser.py

# 5. Запустите Public API клиент
python3 public_api_client.py
```

### **Вариант 2: Полная версия с API ключами**
```bash
# 1. Создайте .env файл
cp env.example .env

# 2. Заполните API ключи в .env
# 3. Установите все зависимости
pip install -r requirements.txt

# 4. Запустите движок
python3 news_engine.py
```

## 🆓 **Бесплатные источники**

### **RSS Parser (`rss_parser.py`)**
- **4 RSS источника** без API ключей
- **Фильтрация по ключевым словам**
- **Автоматическое определение источников**
- **Обработка ошибок и retry логика**

```python
from rss_parser import RSSParser

parser = RSSParser()
feeds = [
    {
        'url': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
        'max_articles': 10,
        'keywords': ['bitcoin', 'crypto', 'ethereum']
    }
]

articles = parser.get_multiple_feeds(feeds)
```

### **Public API Client (`public_api_client.py`)**
- **3 бесплатных API** для криптовалют
- **Rate limiting** и обработка ошибок
- **Единый интерфейс** для всех источников
- **Автоматический fallback**

```python
from public_api_client import PublicAPIClient

client = PublicAPIClient()

# Топ криптовалют
top_coins = client.get_top_cryptocurrencies(100)

# Цены монет
prices = client.get_crypto_price(['bitcoin', 'ethereum'])

# Рыночные данные
btc_data = client.get_market_data("BTCUSDT")
```

## 🔐 **Платные источники (опционально)**

### **Основные API:**
- **NewsAPI.org** - 1000 запросов/день бесплатно
- **Twitter API v2** - требует регистрации
- **CryptoCompare** - 100,000 запросов/месяц бесплатно
- **Alpha Vantage** - 500 запросов/день бесплатно

### **Премиум источники:**
- **Reuters, Bloomberg, CNBC**
- **SEC, CFTC данные**
- **Binance, Coinbase торговые данные**

## ⚙️ **Настройка**

### **1. Создание .env файла**
```bash
# Скопируйте шаблон
cp env.example .env

# Отредактируйте .env
nano .env
```

### **2. Получение API ключей**
- **NewsAPI.org**: https://newsapi.org/ (бесплатно)
- **CryptoCompare**: https://www.cryptocompare.com/ (бесплатно)
- **Alpha Vantage**: https://www.alphavantage.co/ (бесплатно)

### **3. Проверка конфигурации**
```bash
# Тест конфигурации
python3 test_config.py

# Загрузка конфигурации
python3 config_loader.py
```

## 🔧 **Конфигурация**

### **Основной файл: `news_engine_config.yaml`**
```yaml
sources:
  # === БЕСПЛАТНЫЕ ИСТОЧНИКИ ===
  coindesk_rss:
    enabled: true
    type: "rss"
    url: "https://www.coindesk.com/arc/outboundfeeds/rss/"
    keywords: ["crypto", "bitcoin", "ethereum"]
    interval: 300
    
  coingecko_public:
    enabled: true
    type: "public_api"
    base_url: "https://api.coingecko.com/api/v3"
    interval: 120

  # === ПЛАТНЫЕ ИСТОЧНИКИ ===
  newsapi:
    enabled: false  # Отключен, пока нет ключа
    api_key: "${NEWS_API_KEY}"
    interval: 60
```

### **Переменные окружения (.env)**
```bash
# RSS источники не требуют ключей
# Public APIs не требуют ключей

# Платные источники (опционально)
NEWS_API_KEY=your_key_here
TWITTER_BEARER_TOKEN=your_token_here
CRYPTOCOMPARE_API_KEY=your_key_here
```

## 📰 **Источники новостей**

### **Бесплатные (всегда доступны):**
1. **CoinDesk RSS** - Новости о криптовалютах
2. **CoinTelegraph RSS** - Крипто новости и аналитика
3. **CryptoNews RSS** - Агрегатор новостей
4. **Bitcoin News RSS** - Новости Bitcoin
5. **CoinGecko Public** - Рыночные данные
6. **Binance Public** - Торговые данные
7. **CoinCap Public** - Рыночная статистика

### **Платные (требуют API ключи):**
8. **NewsAPI.org** - Общие новости
9. **Twitter API** - Социальные сети
10. **CryptoCompare** - Крипто данные
11. **Alpha Vantage** - Финансовые данные
12. **Reuters** - Бизнес новости
13. **Bloomberg** - Финансовые новости
14. **CNBC** - Бизнес новости
15. **TechCrunch** - Технологии
16. **The Verge** - Технологии
17. **SEC** - Регулятивные данные
18. **CFTC** - Торговые данные
19. **Reddit** - Социальные обсуждения

## 🌐 **API клиенты**

### **RSS Parser**
- Парсинг XML/RSS feeds
- Фильтрация по ключевым словам
- Автоматическое определение источников
- Обработка ошибок и retry

### **Public API Client**
- CoinGecko API (50 req/min)
- Binance Public API (1200 req/min)
- CoinCap API (100 req/min)
- Rate limiting и fallback

### **Платные API клиенты**
- NewsAPI.org клиент
- Twitter API v2 клиент
- CryptoCompare клиент
- Alpha Vantage клиент

## 🔔 **Уведомления**

### **Поддерживаемые каналы:**
- **Telegram Bot** - Мгновенные уведомления
- **Email** - Ежедневные дайджесты
- **Webhook** - Интеграция с внешними системами
- **Discord** - Серверные уведомления

### **Настройка Telegram:**
```bash
# В .env файле
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

## 📊 **Анализ и обработка**

### **Анализ влияния:**
- **Ключевые слова** в заголовках
- **Источник новости** (вес источника)
- **Время публикации** (свежесть)
- **Длина контента** (детализация)

### **Анализ настроений:**
- **Положительные** ключевые слова
- **Отрицательные** ключевые слова
- **Нейтральные** новости
- **Смешанные** настроения

### **Анализ срочности:**
- **Breaking news** индикаторы
- **Временные метки** (сегодня, вчера)
- **Ключевые слова** срочности
- **Источник** (новостные агентства)

## 🗄️ **База данных**

### **SQLite база (`ghost_news.db`)**
- **Таблица новостей** - все полученные новости
- **Таблица источников** - метаданные источников
- **Таблица анализа** - результаты анализа
- **Таблица уведомлений** - история уведомлений

### **Схема базы:**
```sql
-- Новости
CREATE TABLE news (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    source TEXT,
    published_date DATETIME,
    influence_score REAL,
    sentiment_score REAL,
    urgency_score REAL
);

-- Источники
CREATE TABLE sources (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT,
    url TEXT,
    enabled BOOLEAN
);
```

## 📈 **Мониторинг**

### **Метрики производительности:**
- **Количество новостей** в час/день
- **Время ответа** API
- **Ошибки** и их типы
- **Использование** API лимитов

### **Логирование:**
- **Уровень логирования** настраивается
- **Файл логов** с ротацией
- **Цветные логи** для консоли
- **Структурированные** логи

## 📁 **Структура проекта**

```
news_engine/
├── 📄 news_engine.py          # Основной движок
├── 📄 config_loader.py        # Загрузчик конфигурации
├── 📄 rss_parser.py           # RSS парсер (БЕСПЛАТНО!)
├── 📄 public_api_client.py    # Public API клиент (БЕСПЛАТНО!)
├── 📄 demo_free_sources.py    # Демо бесплатных источников
├── 📄 test_config.py          # Тест конфигурации
├── 📄 requirements_free.txt    # Зависимости для бесплатных источников
├── 📄 requirements.txt         # Все зависимости
├── 📄 env.example             # Шаблон .env
├── 📄 SETUP_ENV.md            # Инструкции по настройке
├── 📄 ENV_MIGRATION_SUMMARY.md # Сводка изменений
├── 📄 README.md               # Этот файл
├── 📁 api_clients/            # Платные API клиенты
│   ├── newsapi_client.py
│   ├── twitter_client.py
│   └── cryptocompare_client.py
├── 📁 processors/             # Обработчики новостей
│   ├── influence_analyzer.py
│   ├── sentiment_analyzer.py
│   └── urgency_analyzer.py
├── 📁 notifications/          # Система уведомлений
│   ├── telegram_sender.py
│   ├── email_sender.py
│   └── webhook_sender.py
└── 📁 database/               # Работа с БД
    ├── db_manager.py
    └── models.py
```

## 🚀 **Использование**

### **Запуск RSS парсера:**
```bash
python3 rss_parser.py
```

### **Запуск Public API клиента:**
```bash
python3 public_api_client.py
```

### **Демонстрация всех возможностей:**
```bash
python3 demo_free_sources.py
```

### **Тест конфигурации:**
```bash
python3 test_config.py
```

### **Загрузка конфигурации:**
```bash
python3 config_loader.py ../news_engine_config.yaml
```

## 🔧 **Разработка**

### **Добавление нового RSS источника:**
1. Добавьте URL в `news_engine_config.yaml`
2. Обновите маппинг в `rss_parser.py`
3. Протестируйте с `rss_parser.py`

### **Добавление нового Public API:**
1. Добавьте endpoint в `news_engine_config.yaml`
2. Создайте метод в `public_api_client.py`
3. Протестируйте с `public_api_client.py`

## 📊 **Статистика**

### **Бесплатные источники:**
- **4 RSS feeds** - новости каждые 5 минут
- **3 Public APIs** - данные каждые 1-3 минуты
- **Общий лимит**: ~2000 запросов/час

### **Платные источники (с ключами):**
- **NewsAPI**: 1000 запросов/день
- **CryptoCompare**: 100,000 запросов/месяц
- **Alpha Vantage**: 500 запросов/день

## 🎯 **Рекомендации**

### **Для начала (рекомендуется):**
1. **Используйте только бесплатные источники**
2. **Запустите `demo_free_sources.py`**
3. **Протестируйте RSS парсер**
4. **Протестируйте Public API клиент**

### **Для продакшена:**
1. **Получите бесплатные API ключи**
2. **Настройте уведомления**
3. **Добавьте мониторинг**
4. **Настройте логирование**

## 🤝 **Поддержка**

### **Проблемы с бесплатными источниками:**
- Проверьте интернет соединение
- Убедитесь, что RSS feeds доступны
- Проверьте rate limits Public APIs

### **Проблемы с платными источниками:**
- Проверьте API ключи в `.env`
- Убедитесь, что ключи активны
- Проверьте лимиты API

## 📝 **Лицензия**

MIT License - используйте свободно для любых целей!

---

**🎉 Теперь у вас есть полностью рабочий новостный движок без необходимости в API ключах!**

**🚀 Начните с `python3 demo_free_sources.py` для демонстрации всех возможностей!**
