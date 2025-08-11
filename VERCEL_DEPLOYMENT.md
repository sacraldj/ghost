# Деплой Ghost на Vercel

## Быстрая настройка переменных окружения

### 1. Создайте проект Supabase (если еще не создан)
1. Перейдите на [supabase.com](https://supabase.com)
2. Создайте новый проект
3. Скопируйте URL проекта и API ключи из Settings > API

### 2. Настройте переменные окружения в Vercel

В панели управления Vercel добавьте следующие переменные окружения:

#### Обязательные переменные:
```bash
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
NEXTAUTH_SECRET=your_random_secret_string
NEXTAUTH_URL=https://your-vercel-app.vercel.app
```

#### Дополнительные переменные (опционально):
```bash
# News API ключи
NEWS_API_KEY=your_newsapi_key
CRYPTOCOMPARE_API_KEY=your_cryptocompare_key
ALPHA_VANTAGE_API_KEY=your_alphavantage_key

# Telegram для уведомлений
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Database
DATABASE_URL=your_database_connection_string
```

### 3. Команды для деплоя через CLI

```bash
# Установите Vercel CLI (если еще не установлен)
npm i -g vercel

# Логин в Vercel
vercel login

# Деплой проекта
vercel

# Установка переменных окружения через CLI
vercel env add NEXT_PUBLIC_SUPABASE_URL
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY
vercel env add SUPABASE_SERVICE_ROLE_KEY
vercel env add NEXTAUTH_SECRET
vercel env add NEXTAUTH_URL
```

### 4. Настройка домена (после деплоя)

Обновите `NEXTAUTH_URL` на ваш актуальный домен:
```bash
vercel env rm NEXTAUTH_URL
vercel env add NEXTAUTH_URL production
# Введите: https://your-actual-domain.vercel.app
```

### 5. Генерация NEXTAUTH_SECRET

Используйте следующую команду для генерации безопасного секрета:

```bash
# В терминале
openssl rand -base64 32
```

Или используйте онлайн генератор: https://generate-secret.vercel.app/32

### 6. Проверка переменных

После деплоя проверьте, что все переменные установлены:
```bash
vercel env ls
```

## Структура проекта для Vercel

Убедитесь, что у вас есть:
- ✅ `package.json` с корректными скриптами
- ✅ `next.config.js` 
- ✅ `vercel.json` с правильной конфигурацией
- ✅ Все переменные окружения настроены

## Troubleshooting

### Ошибка "Secret does not exist"
Это означает, что переменная окружения не настроена в Vercel. Добавьте ее через:
1. Vercel Dashboard > Project Settings > Environment Variables
2. Или через CLI: `vercel env add VARIABLE_NAME`

### Ошибки сборки
Проверьте логи сборки в Vercel Dashboard для подробной информации об ошибках.

### База данных не подключается
Убедитесь, что:
1. Supabase проект активен
2. API ключи корректны
3. URL правильно указан (без слэша в конце)
