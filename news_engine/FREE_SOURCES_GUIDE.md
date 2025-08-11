# 🆓 **Руководство по бесплатным источникам GHOST News Engine**

## 🚀 **Быстрый старт (5 минут)**

### **1. Установка зависимостей**
```bash
cd news_engine
pip3 install -r requirements_free.txt
```

### **2. Тест RSS парсера**
```bash
python3 rss_parser.py
```
**Результат**: Получите новости из CoinDesk и CoinTelegraph

### **3. Тест Public API клиента**
```bash
python3 public_api_client.py
```
**Результат**: Получите цены криптовалют и рыночные данные

### **4. Полная демонстрация**
```bash
python3 demo_free_sources.py
```
**Результат**: Увидите все возможности бесплатных источников

## 📰 **Что работает БЕСПЛАТНО**

### **RSS источники (новости каждые 5 минут):**
- ✅ **CoinDesk** - https://www.coindesk.com/arc/outboundfeeds/rss/
- ✅ **CoinTelegraph** - https://cointelegraph.com/rss
- ✅ **Bitcoin News** - https://news.bitcoin.com/feed/
- ⚠️ **CryptoNews** - https://cryptonews.com/news/feed (может блокировать)

### **Public APIs (данные каждые 1-3 минуты):**
- ✅ **CoinGecko** - 50 запросов/минуту
- ✅ **Binance Public** - 1200 запросов/минуту  
- ✅ **CoinCap** - 100 запросов/минуту

## 💡 **Примеры использования**

### **Получение новостей:**
```python
from rss_parser import RSSParser

parser = RSSParser()
feeds = [
    {
        'url': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
        'max_articles': 10,
        'keywords': ['bitcoin', 'crypto']
    }
]

articles = parser.get_multiple_feeds(feeds)
for article in articles:
    print(f"📰 {article['title']}")
    print(f"   📅 {article['published_date']}")
    print(f"   📰 {article['source_name']}")
```

### **Получение цен криптовалют:**
```python
from public_api_client import PublicAPIClient

client = PublicAPIClient()

# Топ-10 криптовалют
top_coins = client.get_top_cryptocurrencies(10)
for coin in top_coins:
    print(f"{coin['symbol']}: ${coin['current_price']:,.2f}")

# Цены конкретных монет
prices = client.get_crypto_price(['bitcoin', 'ethereum'])
print(f"BTC: ${prices['bitcoin']['usd']}")
print(f"ETH: ${prices['ethereum']['usd']}")
```

### **Рыночные данные:**
```python
# Данные BTC/USDT
btc_data = client.get_market_data("BTCUSDT")
print(f"BTC: ${btc_data['price']:,.2f}")
print(f"24h Change: {btc_data['price_change_percent']:.2f}%")
print(f"Volume: ${btc_data['volume_24h']:,.0f}")
```

## ⚙️ **Настройка**

### **Конфигурация в `news_engine_config.yaml`:**
```yaml
sources:
  # RSS источники
  coindesk_rss:
    enabled: true
    type: "rss"
    url: "https://www.coindesk.com/arc/outboundfeeds/rss/"
    keywords: ["crypto", "bitcoin", "ethereum"]
    interval: 300  # 5 минут
    
  # Public APIs
  coingecko_public:
    enabled: true
    type: "public_api"
    base_url: "https://api.coingecko.com/api/v3"
    interval: 120  # 2 минуты
```

### **Фильтрация по ключевым словам:**
```yaml
keywords:
  - "bitcoin"
  - "ethereum" 
  - "defi"
  - "nft"
  - "binance"
  - "coinbase"
  - "regulation"
  - "blockchain"
```

## 📊 **Лимиты и ограничения**

### **RSS источники:**
- **Частота**: каждые 5 минут
- **Статей за раз**: до 20
- **Ограничения**: нет (только вежливость)

### **Public APIs:**
- **CoinGecko**: 50 запросов/минуту
- **Binance**: 1200 запросов/минуту
- **CoinCap**: 100 запросов/минуту

### **Общие рекомендации:**
- Не делайте запросы чаще чем раз в минуту
- Используйте фильтрацию по ключевым словам
- Обрабатывайте ошибки gracefully

## 🔧 **Решение проблем**

### **RSS feed недоступен:**
```bash
# Проверьте доступность
curl -I "https://www.coindesk.com/arc/outboundfeeds/rss/"

# Попробуйте альтернативный источник
# Обновите User-Agent в rss_parser.py
```

### **Public API ошибки:**
```bash
# Проверьте rate limits
python3 public_api_client.py

# Увеличьте интервалы в конфигурации
# Добавьте retry логику
```

### **Проблемы с зависимостями:**
```bash
# Обновите pip
pip3 install --upgrade pip

# Переустановите зависимости
pip3 uninstall feedparser requests
pip3 install -r requirements_free.txt
```

## 🚀 **Следующие шаги**

### **1. Интеграция с основным движком:**
```python
# В news_engine.py добавьте:
from rss_parser import RSSParser
from public_api_client import PublicAPIClient

# Инициализируйте бесплатные источники
self.rss_parser = RSSParser()
self.public_api_client = PublicAPIClient()
```

### **2. Добавление новых RSS источников:**
```yaml
# В news_engine_config.yaml:
new_source_rss:
  enabled: true
  type: "rss"
  url: "https://example.com/rss"
  keywords: ["crypto", "blockchain"]
  interval: 300
```

### **3. Добавление новых Public APIs:**
```python
# В public_api_client.py добавьте метод:
def _get_new_api_data(self, endpoint, params):
    # Ваша логика здесь
    pass
```

## 📈 **Мониторинг и логи**

### **Включение подробного логирования:**
```python
import logging
logging.basicConfig(level=logging.INFO)
```

### **Проверка статуса источников:**
```bash
# Тест конфигурации
python3 test_config.py

# Тест RSS парсера
python3 rss_parser.py

# Тест Public API
python3 public_api_client.py
```

## 🎯 **Лучшие практики**

### **Для RSS источников:**
1. **Используйте ключевые слова** для фильтрации
2. **Устанавливайте разумные интервалы** (5+ минут)
3. **Обрабатывайте ошибки** gracefully
4. **Кэшируйте результаты** для избежания дублирования

### **Для Public APIs:**
1. **Соблюдайте rate limits**
2. **Используйте fallback источники**
3. **Кэшируйте данные** на короткое время
4. **Мониторьте использование** API

### **Общие рекомендации:**
1. **Начните с демонстрации** (`demo_free_sources.py`)
2. **Тестируйте каждый источник** отдельно
3. **Мониторьте логи** для выявления проблем
4. **Добавляйте источники постепенно**

## 🎉 **Готово!**

Теперь у вас есть **полностью рабочий новостный движок** без необходимости в API ключах!

**🚀 Запустите `python3 demo_free_sources.py` и увидите все в действии!**

---

**💡 Вопросы? Проблемы? Создайте issue в репозитории!**
