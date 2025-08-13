# 🚀 **GHOST Real Signals Setup Guide**
## Полный гайд по подключению реальных сигналов

---

## 📋 **Что уже готово:**
- ✅ Парсер для канала **@Whalesguide** 
- ✅ Telegram слушатель для реального времени
- ✅ Оркестратор сигналов с автоматическим сохранением
- ✅ Интеграция с Supabase
- ✅ Дашборд на Vercel
- ✅ Конфигурация для Railway

---

## 🔧 **ШАГ 1: Настройка Telegram API**

### 1.1 Получение API ключей Telegram
1. Идите на https://my.telegram.org/
2. Войдите под своим номером телефона
3. Создайте новое приложение:
   - **App title**: `GHOST Signals Parser`
   - **Short name**: `ghost-signals`
   - **Platform**: `Desktop`
4. Сохраните:
   - `api_id` (число)
   - `api_hash` (строка)

### 1.2 Настройка переменных окружения
Создайте файл `.env.local` в корне проекта:

```bash
# Telegram Configuration
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890
TELEGRAM_PHONE=+1234567890

# Supabase (уже есть)
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key

# Optional: Alert webhooks
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

---

## 🗄️ **ШАГ 2: Настройка базы данных**

### 2.1 Supabase Tables (уже настроено)
Убедитесь что в Supabase есть таблица `trades` с полями:
- `telegram_message_id` (bigint)
- `telegram_channel_id` (bigint)  
- `source_url` (text)
- `parser_used` (text)
- `processed_at` (timestamp)

### 2.2 Создание индексов для производительности
```sql
-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_trades_telegram_message ON trades(telegram_message_id);
CREATE INDEX IF NOT EXISTS idx_trades_source ON trades(source);
CREATE INDEX IF NOT EXISTS idx_trades_symbol_timestamp ON trades(symbol, timestamp);
CREATE INDEX IF NOT EXISTS idx_trades_confidence ON trades(confidence);
```

---

## 🤖 **ШАГ 3: Запуск Telegram парсера**

### 3.1 Локальное тестирование
```bash
# Установка зависимостей
cd telegram_parsers
pip install -r requirements.txt

# Запуск парсера (будет запрашивать SMS код при первом запуске)
python whales_guide_listener.py
```

### 3.2 Первая авторизация
При первом запуске Telegram попросит:
1. **SMS код** - введите код из SMS
2. **2FA пароль** (если включен) - введите пароль двухфакторной аутентификации
3. Создастся файл `whales_session.session` - НЕ удаляйте его!

### 3.3 Проверка работы
- Парсер должен найти канал @Whalesguide
- В логах появится: `✅ Found channel: Whales Crypto Guide`
- При новых сообщениях: `📨 New message: ID=...`
- При сигналах: `🎯 Detected potential signal!`

---

## 🔄 **ШАГ 4: Настройка оркестратора сигналов**

### 4.1 Запуск оркестратора
```bash
# В отдельном терминале
python signals/signal_orchestrator.py
```

### 4.2 Тестирование парсинга
```bash
# Тестирование парсера Whales
python signals/whales_crypto_parser.py

# Проверка интеграции
python signals/signal_orchestrator.py
```

---

## 🚀 **ШАГ 5: Развертывание на Railway**

### 5.1 Создание аккаунта Railway
1. Идите на https://railway.app/
2. Зарегистрируйтесь через GitHub
3. Создайте новый проект

### 5.2 Настройка переменных окружения в Railway
В Railway Dashboard > Variables добавьте:
```bash
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890  
TELEGRAM_PHONE=+1234567890
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
PYTHON_VERSION=3.11
```

### 5.3 Развертывание
```bash
# Установка Railway CLI
npm install -g @railway/cli

# Логин в Railway
railway login

# Связывание с проектом
railway link

# Развертывание
railway up
```

### 5.4 Загрузка session файла
После первого запуска локально, загрузите `whales_session.session`:
```bash
# Загрузка session файла в Railway
railway run cp whales_session.session /app/
```

---

## 📊 **ШАГ 6: Проверка работы системы**

### 6.1 Мониторинг логов
```bash
# Логи Telegram парсера
railway logs --service telegram_parser

# Логи оркестратора
railway logs --service signal_processor
```

### 6.2 Проверка в дашборде
1. Откройте ваш дашборд на Vercel
2. Перейдите в раздел "Trading Signals"
3. Должны появляться новые сигналы от `whales_crypto_guide`

### 6.3 Проверка в Supabase
```sql
-- Последние сигналы от Whales
SELECT * FROM trades 
WHERE trader_id = 'whales_crypto_guide' 
ORDER BY timestamp DESC 
LIMIT 10;
```

---

## ⚡ **ШАГ 7: Мониторинг и алерты**

### 7.1 Настройка Discord алертов (опционально)
1. Создайте webhook в Discord сервере
2. Добавьте URL в переменные окружения
3. Система будет отправлять алерты о новых сигналах

### 7.2 Мониторинг производительности
- **Логи**: `whales_guide_listener.log`
- **Метрики**: Каждые 10 сообщений выводится статистика
- **База данных**: Локальные SQLite файлы для кэширования

---

## 🛠️ **Устранение неполадок**

### Проблема: "Channel not found"
**Решение**: 
1. Убедитесь что вы подписаны на @Whalesguide
2. Попробуйте разные варианты: `Whalesguide`, `whalesguide`
3. Проверьте что канал публичный

### Проблема: "Authentication failed"
**Решение**:
1. Удалите `whales_session.session`
2. Перезапустите парсер
3. Введите новый SMS код

### Проблема: "Database connection failed"
**Решение**:
1. Проверьте переменные `SUPABASE_URL` и `SUPABASE_ANON_KEY`
2. Убедитесь что Supabase проект активен
3. Проверьте настройки RLS (Row Level Security)

### Проблема: Парсер не обнаруживает сигналы
**Решение**:
1. Проверьте логи: ищите "can_parse: False"
2. Обновите паттерны в `whales_crypto_parser.py`
3. Добавьте отладочные принты

---

## 📈 **Расширение функциональности**

### Добавление новых каналов
1. Скопируйте `whales_guide_listener.py`
2. Измените `channel_username`
3. Адаптируйте парсер под формат нового канала
4. Добавьте в `railway.toml` новый сервис

### Интеграция с биржами
1. Добавьте API ключи биржи в переменные окружения
2. Создайте модуль автоторговли
3. Подключите к оркестратору сигналов

---

## ✅ **Чек-лист запуска**

- [ ] Получены Telegram API ключи
- [ ] Настроены переменные окружения
- [ ] Локально протестирован парсер
- [ ] Авторизация в Telegram прошла успешно
- [ ] Канал @Whalesguide найден
- [ ] Сигналы парсятся корректно
- [ ] Данные сохраняются в Supabase
- [ ] Railway проект создан
- [ ] Переменные окружения настроены в Railway
- [ ] Session файл загружен в Railway
- [ ] Сервисы запущены на Railway
- [ ] Логи показывают корректную работу
- [ ] Дашборд отображает новые сигналы

---

## 🆘 **Поддержка**

При возникновении проблем:
1. Проверьте логи: `tail -f *.log`
2. Проверьте статус Railway сервисов
3. Убедитесь что все переменные окружения настроены
4. Проверьте подключение к интернету и API лимиты

**Все готово для реальной торговли! 🚀📈**
