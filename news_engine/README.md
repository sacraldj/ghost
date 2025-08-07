# GHOST News Engine

Мощный движок для сбора, анализа и обработки новостей для торговой платформы GHOST.

## 🚀 Возможности

### 📰 Сбор новостей
- **Множественные источники**: NewsAPI, CryptoCompare, Reuters, Bloomberg, CNBC
- **Специализированные крипто-источники**: CoinDesk, CoinTelegraph, Decrypt
- **Регулятивные источники**: SEC, CFTC, Federal Reserve, ECB
- **Технологические источники**: TechCrunch, The Verge, Wired

### 🐦 Анализ твитов
- **Влиятельные лица**: Elon Musk, Vitalik Buterin, CZ, Michael Saylor
- **Крипто-лидеры**: Все ключевые фигуры индустрии
- **Финансовые лидеры**: Warren Buffett, Ray Dalio
- **Регуляторы**: Jerome Powell, Gary Gensler

### 🏢 Мониторинг компаний
- **Крипто-компании**: Binance, Coinbase, Ethereum Foundation
- **Технологические гиганты**: Tesla, Apple, Google, Microsoft
- **Финансовые институты**: JPMorgan, Goldman Sachs, BlackRock
- **Регулятивные органы**: SEC, Federal Reserve

### 📊 Анализ влияния
- **Балл влияния**: 0-1.0 (важность новости)
- **Влияние на рынок**: -1.0 до +1.0 (позитивное/негативное)
- **Анализ настроений**: Позитивные/негативные/нейтральные
- **Срочность**: Оценка временной важности
- **Доверие к источнику**: Рейтинг надежности

## 🏗️ Архитектура

```
news_engine/
├── news_sources.py      # Источники новостей и влиятельные лица
├── news_apis.py         # API клиенты для сбора данных
├── influence_analyzer.py # Анализатор влияния и важности
├── news_engine.py       # Главный движок
└── README.md           # Документация
```

## 🔧 Установка

### 1. Установка зависимостей
```bash
pip install requests aiohttp textblob spacy numpy
python -m spacy download en_core_web_sm
```

### 2. Настройка API ключей
Создайте файл `.env` в папке `news_engine/`:

```env
# NewsAPI.org
NEWS_API_KEY=your_key_here

# Twitter API v2
TWITTER_BEARER_TOKEN=your_token_here

# Alpha Vantage
ALPHA_VANTAGE_API_KEY=your_key_here

# CryptoCompare
CRYPTOCOMPARE_API_KEY=your_key_here
```

### 3. Получение API ключей

#### NewsAPI.org
1. Зарегистрируйтесь на https://newsapi.org/
2. Получите бесплатный API ключ
3. Добавьте в `.env`

#### Twitter API v2
1. Создайте приложение на https://developer.twitter.com/
2. Получите Bearer Token
3. Добавьте в `.env`

#### Alpha Vantage
1. Зарегистрируйтесь на https://www.alphavantage.co/
2. Получите бесплатный API ключ
3. Добавьте в `.env`

## 🚀 Использование

### Базовое использование
```python
from news_engine import NewsEngine
import asyncio

async def main():
    engine = NewsEngine()
    
    # Запуск полного цикла
    result = await engine.run_full_cycle()
    
    if result:
        print(f"Обработано новостей: {result['news_count']}")
        print(f"Проанализировано твитов: {result['tweets_count']}")
        print(f"Важных новостей: {result['important_news']}")

asyncio.run(main())
```

### Получение важных новостей
```python
engine = NewsEngine()
important_news = engine.get_important_news(limit=10)

for news in important_news:
    print(f"📰 {news.title}")
    print(f"   Влияние: {news.influence_score:.3f}")
    print(f"   Источник: {news.source}")
    print(f"   Настроения: {news.sentiment_score:.3f}")
    print()
```

### Анализ конкретной новости
```python
from influence_analyzer import InfluenceAnalyzer

analyzer = InfluenceAnalyzer()

news_item = {
    'title': 'Bitcoin ETF Approved by SEC',
    'content': 'The SEC has approved the first Bitcoin ETF...',
    'source': 'Reuters',
    'published_at': datetime.now()
}

influence_score = analyzer.analyze_news_influence(news_item)
print(f"Влияние: {influence_score.influence_score:.3f}")
print(f"Влияние на рынок: {influence_score.market_impact:.3f}")
```

## 📊 Источники данных

### Новостные API
- **NewsAPI.org**: Основной источник новостей
- **CryptoCompare**: Специализированные крипто-новости
- **Alpha Vantage**: Финансовые новости с анализом настроений
- **Reuters API**: Высоконадежные финансовые новости
- **Bloomberg API**: Профессиональные финансовые новости

### Социальные сети
- **Twitter API v2**: Твиты влиятельных лиц
- **Мониторинг ключевых аккаунтов**: 50+ влиятельных лиц

### Официальные источники
- **SEC**: Регулятивные новости
- **Federal Reserve**: Макроэкономические новости
- **CFTC**: Товарные фьючерсы
- **ECB**: Европейская экономика

## 🎯 Алгоритмы анализа

### Балл влияния
```
Влияние = (Ключевые слова × 0.3) + (Настроения × 0.2) + 
          (Срочность × 0.2) + (Охват × 0.15) + (Доверие × 0.15)
```

### Влияние на рынок
```
Рыночное влияние = Базовое влияние × 0.7 + 
                  Корректировка настроений + 
                  Корректировка ключевых слов
```

### Приоритет новости
```
Приоритет = Базовый приоритет + 
            Важность новости + 
            Срочность + 
            Доверие к источнику
```

## 🔍 Ключевые слова и сущности

### Криптовалюты
- Bitcoin, Ethereum, Binance, Coinbase, Solana, Cardano

### Регулятивные термины
- SEC, regulation, compliance, CFTC, Federal Reserve

### Технологические термины
- blockchain, DeFi, NFT, Web3, smart contract

### Макроэкономические термины
- inflation, interest rate, CPI, recession, GDP

### Влиятельные лица
- Elon Musk, Vitalik Buterin, CZ, Warren Buffett, Ray Dalio

## 📈 Метрики качества

### Надежность источников
- **Reuters**: 0.95
- **Bloomberg**: 0.95
- **SEC**: 0.98
- **Federal Reserve**: 0.99
- **CoinDesk**: 0.85
- **CoinTelegraph**: 0.8

### Влияние лиц
- **Elon Musk**: 0.98
- **Vitalik Buterin**: 0.95
- **CZ (Binance)**: 0.9
- **Jerome Powell**: 0.99
- **Gary Gensler**: 0.95

## 🔄 Автоматизация

### Планировщик задач
```python
import schedule
import time

def run_news_cycle():
    asyncio.run(engine.run_full_cycle())

# Запуск каждые 15 минут
schedule.every(15).minutes.do(run_news_cycle)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### Интеграция с GHOST
```python
# Интеграция с основной системой GHOST
from ghost_system import GhostSystem

class GhostNewsIntegration:
    def __init__(self):
        self.news_engine = NewsEngine()
        self.ghost_system = GhostSystem()
    
    async def process_important_news(self):
        important_news = self.news_engine.get_important_news()
        
        for news in important_news:
            if news.influence_score > 0.8:
                # Отправляем сигнал в GHOST
                await self.ghost_system.process_news_signal(news)
```

## 🛠️ Разработка

### Добавление нового источника
```python
# В news_sources.py
new_source = NewsSource(
    name="New Source",
    url="https://api.newsource.com/v1/news",
    category="crypto",
    reliability_score=0.8
)
```

### Добавление нового API клиента
```python
# В news_apis.py
class NewAPIClient(NewsAPIClient):
    def __init__(self):
        super().__init__(api_key=os.getenv("NEW_API_KEY"))
        self.base_url = "https://api.newsource.com"
    
    async def fetch_news(self, query: str = None, limit: int = 50):
        # Реализация получения новостей
        pass
```

## 📝 Логирование

Движок ведет подробные логи всех операций:
- Сбор новостей
- Анализ влияния
- Сохранение в базу данных
- Ошибки и исключения

## 🔒 Безопасность

- Все API ключи хранятся в переменных окружения
- Проверка достоверности источников
- Валидация входных данных
- Защита от дублирования новостей

## 📊 Производительность

- **Асинхронная обработка**: Все API запросы выполняются параллельно
- **Кэширование**: Избежание повторных запросов
- **База данных**: SQLite для локального хранения
- **Оптимизация**: Фильтрация нерелевантных новостей

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Создайте Pull Request

## 📄 Лицензия

MIT License - см. файл LICENSE для подробностей.
