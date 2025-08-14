# 🚀 GHOST System - Руководство по деплою на Render

## 📋 Предварительные требования

### 1. Переменные окружения для Render
Обязательные переменные для продакшена:

```bash
# Supabase (ОБЯЗАТЕЛЬНЫЕ)
NEXT_PUBLIC_SUPABASE_URL=https://qjdpckwqozsbpskwplfl.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Telegram (для реальных сигналов)
TELEGRAM_API_ID=20812032
TELEGRAM_API_HASH=0aee8e31e85e29ca115eae60908a91c8
TELEGRAM_PHONE=+375259556962

# AI Providers (опциональные)
OPENAI_API_KEY=sk-proj-M-3VJV2FzYxfSRSwKwkujQT7FWevNwNgXd8KhjENbP4...
GEMINI_API_KEY=AIzaSyDtlg9OCuQ7Tftfwj-XknpOtAH7-X0dtck

# Trading APIs (опциональные)
BYBIT_API_KEY=nNAkOg5FKG8jh8W4p7
BYBIT_API_SECRET=bLUAuBo36T0CFcF4tGXJiNz1G0rgZ7Qj5rCE
```

### 2. Файлы готовы к деплою
- ✅ `render.yaml` - конфигурация Render
- ✅ `requirements.txt` - Python зависимости  
- ✅ `start_all.py` - точка входа для Render
- ✅ Все исправления применены

## 🔧 Шаги деплоя

### Шаг 1: Git Push
```bash
git add .
git commit -m "🚀 Production ready: Fixed modules, Telegram integration, real data flow"
git push origin main
```

### Шаг 2: Render Deploy
1. Зайти в [Render Dashboard](https://dashboard.render.com)
2. Найти сервис `ghost-unified-live-system`
3. Нажать **"Deploy latest commit"**
4. Дождаться завершения деплоя

### Шаг 3: Настройка переменных
В Render Dashboard → Settings → Environment:
- Добавить все переменные из списка выше
- Особенно важно: `SUPABASE_SERVICE_ROLE_KEY` и `TELEGRAM_API_ID`

### Шаг 4: Проверка работы
После деплоя проверить:
- `https://ghost.render.com/api/system/status` - статус системы
- `https://ghost.render.com/api/critical-news` - новости
- `https://ghost.render.com/dashboard` - дашборд

## 📊 Ожидаемые результаты

### Система должна показывать:
- ✅ **Модули:** 3-5/5 здоровых
- ✅ **Новости:** 10+ критических новостей
- ✅ **Telegram:** Подключение к каналам
- ✅ **API:** Все эндпоинты возвращают данные
- ✅ **Дашборд:** Реальные данные вместо пустых экранов

### Возможные проблемы:
- ⚠️ **Telegram сессия:** Может потребоваться повторная авторизация на Render
- ⚠️ **Redis:** Отключен, но это не критично
- ⚠️ **Некоторые модули:** Могут перезапускаться, но система работает

## 🎯 Post-Deploy чеклист

### Сразу после деплоя:
1. ✅ Проверить статус: `/api/system/status`
2. ✅ Проверить новости: `/api/critical-news`  
3. ✅ Проверить дашборд: `/dashboard`
4. ✅ Проверить логи в Render Dashboard

### В течение часа:
1. 📊 Мониторить количество перезапусков модулей
2. 📱 Проверить поступление Telegram сигналов
3. 📰 Убедиться что новости обновляются
4. 💹 Проверить работу Bybit API для цен

## 🚨 Troubleshooting

### Если модули не запускаются:
1. Проверить переменные окружения в Render
2. Проверить логи: Render Dashboard → Logs
3. Убедиться что `requirements.txt` установился

### Если нет Telegram сигналов:
1. Может потребоваться ручная авторизация на сервере
2. Проверить `TELEGRAM_API_ID` и `TELEGRAM_API_HASH`
3. Временно отключить Telegram модули если нужно

### Если нет новостей:
1. Проверить `SUPABASE_SERVICE_ROLE_KEY`
2. Проверить доступ к SQLite базе
3. Перезапустить `news_engine` модуль

---
**Система готова к продакшену! 🎉**
