# 🚀 Настройка переменных окружения для GHOST News Engine

## 📋 Обзор

Теперь все API ключи и настройки хранятся в файле `.env`, что обеспечивает безопасность и удобство управления конфигурацией.

## 🔧 Шаги настройки

### 1. Создание файла .env

Скопируйте файл `env.example` в корень проекта:

```bash
# Из корня проекта Ghost/
cp news_engine/env.example .env
```

### 2. Заполнение API ключей

Отредактируйте файл `.env` и замените `your_*_here` на реальные ключи:

```bash
# Основные источники новостей
NEWS_API_KEY=abc123def456ghi789
TWITTER_BEARER_TOKEN=your_actual_twitter_token
CRYPTOCOMPARE_API_KEY=your_actual_cryptocompare_key

# Финансовые источники
ALPHA_VANTAGE_API_KEY=your_actual_alphavantage_key
REUTERS_API_KEY=your_actual_reuters_key
BLOOMBERG_API_KEY=your_actual_bloomberg_key
CNBC_API_KEY=your_actual_cnbc_key

# Крипто источники
COINGECKO_API_KEY=your_actual_coingecko_key
BINANCE_API_KEY=your_actual_binance_key
BINANCE_SECRET_KEY=your_actual_binance_secret
COINBASE_API_KEY=your_actual_coinbase_key
COINBASE_SECRET_KEY=your_actual_coinbase_secret
```

### 3. Получение API ключей

#### 🆓 Бесплатные API (рекомендуется начать с них):

**NewsAPI.org**
1. Зарегистрируйтесь на https://newsapi.org/
2. Получите бесплатный ключ (1000 запросов/день)
3. Добавьте в `.env`: `NEWS_API_KEY=your_key`

**CryptoCompare**
1. Зарегистрируйтесь на https://www.cryptocompare.com/
2. Получите бесплатный ключ
3. Добавьте в `.env`: `CRYPTOCOMPARE_API_KEY=your_key`

**Alpha Vantage**
1. Зарегистрируйтесь на https://www.alphavantage.co/
2. Получите бесплатный ключ (500 запросов/день)
3. Добавьте в `.env`: `ALPHA_VANTAGE_API_KEY=your_key`

#### 💰 Платные API (для продакшена):

**Twitter API v2**
1. Создайте приложение на https://developer.twitter.com/
2. Получите Bearer Token
3. Добавьте в `.env`: `TWITTER_BEARER_TOKEN=your_token`

**Reuters, Bloomberg, CNBC**
- Требуют корпоративные аккаунты
- Свяжитесь с их отделами продаж

### 4. Проверка конфигурации

Запустите скрипт проверки:

```bash
cd news_engine/
python config_loader.py
```

Вы должны увидеть:
```
✅ Конфигурация загружена успешно
📋 Сводка конфигурации GHOST News Engine:
==================================================
📰 Источники новостей: 15
✅ Включенные источники: newsapi, cryptocompare, alphavantage
🔔 Каналы уведомлений: telegram, email, webhook
📊 Уровень логирования: INFO
==================================================
```

## 🔒 Безопасность

### ✅ Что делать:
- Храните `.env` файл локально
- Добавьте `.env` в `.gitignore`
- Используйте разные ключи для разработки и продакшена

### ❌ Что НЕ делать:
- Не коммитьте `.env` файл в Git
- Не делитесь API ключами публично
- Не используйте один ключ для всех проектов

## 🚀 Запуск с новой конфигурацией

### 1. Базовый запуск
```bash
python news_engine.py
```

### 2. С указанием конфигурации
```bash
python news_engine.py --config custom_config.yaml
```

### 3. Тестирование источников
```bash
python test_news_engine.py
```

## 📊 Мониторинг источников

После запуска проверьте логи:

```bash
tail -f ghost_news_engine.log
```

Ищите сообщения типа:
- `✅ Источник newsapi работает нормально`
- `⚠️ Источник twitter отключен (нет токена)`
- `❌ Ошибка подключения к bloomberg`

## 🔧 Устранение проблем

### Проблема: "API key not found"
**Решение**: Проверьте, что ключ добавлен в `.env` и файл находится в правильной папке

### Проблема: "Rate limit exceeded"
**Решение**: Увеличьте интервалы обновления в `news_engine_config.yaml`

### Проблема: "Connection timeout"
**Решение**: Проверьте интернет-соединение и настройки прокси

## 📈 Оптимизация

### Для разработки:
- Используйте только бесплатные API
- Увеличьте интервалы обновления
- Отключите неиспользуемые источники

### Для продакшена:
- Используйте платные API с высокими лимитами
- Настройте мониторинг и алерты
- Оптимизируйте интервалы обновления

## 📞 Поддержка

Если у вас возникли проблемы:
1. Проверьте логи: `tail -f ghost_news_engine.log`
2. Запустите валидацию: `python config_loader.py`
3. Проверьте подключение к интернету
4. Убедитесь, что API ключи активны

---

**Удачи с настройкой GHOST News Engine! 🚀**
