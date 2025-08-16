# 🚀 GHOST Render.com Deployment Guide

Полная инструкция по развертыванию системы GHOST на Render.com для цепочки **Telegram → Render → Supabase → Vercel**.

## 📋 Предварительные требования

### 1. Аккаунты
- ✅ [Render.com](https://render.com) (бесплатный план доступен)
- ✅ [GitHub](https://github.com) (для подключения репозитория)
- ✅ [Telegram](https://my.telegram.org/auth) (API ключи)
- ✅ [Supabase](https://supabase.com) (база данных)

### 2. API Ключи
Подготовьте следующие ключи:
```bash
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=+1234567890  # Опционально

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key

OPENAI_API_KEY=sk-...  # Для анализа новостей
GEMINI_API_KEY=your_gemini_key
NEWS_API_KEY=your_news_api_key
```

## 🛠 Шаг 1: Подготовка репозитория

### 1.1 Убедитесь, что файлы готовы:
```bash
# Проверьте наличие файлов
ls -la render.yaml
ls -la requirements.txt
ls -la api/main.py
ls -la core/telegram_render_bridge.py
ls -la telegram_parsers/cryptoattack24_parser.py
```

### 1.2 Коммит и пуш в GitHub:
```bash
git add .
git commit -m "Add Render.com deployment configuration"
git push origin main
```

## 🌐 Шаг 2: Создание сервисов на Render

### 2.1 API Service (Web Service)
1. Зайдите в [Render Dashboard](https://dashboard.render.com)
2. Нажмите **"New +"** → **"Web Service"**
3. Подключите GitHub репозиторий
4. Настройки:
   ```
   Name: ghost-api
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: python -m uvicorn api.main:app --host 0.0.0.0 --port $PORT
   Plan: Starter (Free)
   ```

5. **Environment Variables** (добавьте все):
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your_anon_key
   SUPABASE_SERVICE_KEY=your_service_key
   OPENAI_API_KEY=sk-...
   GEMINI_API_KEY=your_gemini_key
   NEWS_API_KEY=your_news_api_key
   PYTHONPATH=/opt/render/project/src
   LOG_LEVEL=INFO
   ```

6. Нажмите **"Create Web Service"**

### 2.2 Telegram Bridge (Background Worker)
1. Нажмите **"New +"** → **"Background Worker"**
2. Подключите тот же репозиторий
3. Настройки:
   ```
   Name: ghost-telegram-bridge
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: python core/telegram_render_bridge.py
   Plan: Starter (Free)
   ```

4. **Environment Variables**:
   ```
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   TELEGRAM_PHONE=+1234567890
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your_anon_key
   RENDER_WEBHOOK_URL=https://ghost-api.onrender.com/webhooks/telegram
   PYTHONPATH=/opt/render/project/src
   LOG_LEVEL=INFO
   GHOST_NEWS_INTEGRATION_ENABLED=true
   ```

5. Нажмите **"Create Background Worker"**

## 🗄 Шаг 3: Настройка Supabase

### 3.1 Применение схемы базы данных
1. Зайдите в [Supabase Dashboard](https://supabase.com/dashboard)
2. Откройте **SQL Editor**
3. Выполните скрипт `db/safe_add_new_tables.sql`
4. Выполните скрипт `db/add_cryptoattack24_trader.sql`

### 3.2 Настройка RLS (Row Level Security)
```sql
-- Отключаем RLS для API доступа (осторожно в продакшене!)
ALTER TABLE traders DISABLE ROW LEVEL SECURITY;
ALTER TABLE trader_stats DISABLE ROW LEVEL SECURITY;
ALTER TABLE signals DISABLE ROW LEVEL SECURITY;
ALTER TABLE strategies DISABLE ROW LEVEL SECURITY;
```

## 📱 Шаг 4: Настройка Telegram

### 4.1 Получение Channel ID
1. Добавьте бота [@userinfobot](https://t.me/userinfobot) в канал
2. Скопируйте Chat ID (например: `-1001234567890`)
3. Обновите `config/telegram_channels.json`:
   ```json
   {
     "channel_id": "-1001234567890",
     "channel_name": "КриптоАтака 24",
     "trader_id": "cryptoattack24",
     "is_active": true
   }
   ```

### 4.2 Авторизация Telegram
При первом запуске Telegram Bridge:
1. Проверьте логи в Render Dashboard
2. При необходимости введите код авторизации через Render Shell

## 🎯 Шаг 5: Тестирование

### 5.1 Проверка API
```bash
# Health check
curl https://ghost-api.onrender.com/health

# Статистика
curl https://ghost-api.onrender.com/stats

# Тест парсера
curl -X POST https://ghost-api.onrender.com/api/test-parser \
  -H "Content-Type: application/json" \
  -d '{
    "parser_type": "cryptoattack24",
    "message": "🚀🔥 #ALPINE запампили на +57% со вчерашнего вечера"
  }'
```

### 5.2 Проверка логов
1. В Render Dashboard откройте сервис
2. Перейдите в **"Logs"**
3. Проверьте успешный запуск и обработку сообщений

## 🔄 Шаг 6: Интеграция с Vercel

### 6.1 Обновление API endpoints в Next.js
В вашем Vercel проекте обновите API URLs:
```javascript
// В компонентах
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://ghost-api.onrender.com'
  : 'http://localhost:3000';
```

### 6.2 Environment Variables в Vercel
```bash
NEXT_PUBLIC_API_URL=https://ghost-api.onrender.com
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
```

## 📊 Мониторинг и обслуживание

### Полезные endpoints для мониторинга:
- 🟢 **Health**: `https://ghost-api.onrender.com/health`
- 📈 **Stats**: `https://ghost-api.onrender.com/stats`
- 📖 **Docs**: `https://ghost-api.onrender.com/docs`
- 🔧 **Config**: `https://ghost-api.onrender.com/api/config`

### Логи в реальном времени:
```bash
# Через Render CLI (если установлен)
render logs ghost-api
render logs ghost-telegram-bridge
```

## 🚨 Troubleshooting

### Проблема: Telegram Bridge не запускается
**Решение**: Проверьте переменные окружения `TELEGRAM_API_ID` и `TELEGRAM_API_HASH`

### Проблема: Не сохраняются сигналы в Supabase
**Решение**: 
1. Проверьте `SUPABASE_URL` и `SUPABASE_ANON_KEY`
2. Убедитесь, что таблицы созданы
3. Проверьте RLS настройки

### Проблема: Парсер не работает
**Решение**: 
1. Проверьте логи Background Worker
2. Убедитесь, что `channel_id` правильный
3. Протестируйте парсер через API

## ✅ Финальная проверка

После развертывания проверьте:
- [ ] ✅ API отвечает на `/health`
- [ ] ✅ Telegram Bridge подключен к каналам
- [ ] ✅ Сигналы сохраняются в Supabase
- [ ] ✅ Парсер CryptoAttack24 работает
- [ ] ✅ Новостная интеграция активна
- [ ] ✅ Vercel подключен к Render API

## 🎉 Готово!

Теперь у вас работает полная цепочка:
**Telegram** → **Render** → **Supabase** → **Vercel**

Все сигналы из канала `t.me/cryptoattack24` будут автоматически парситься, обрабатываться и отображаться в дашборде!