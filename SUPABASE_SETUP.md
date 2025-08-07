# Настройка Supabase для GHOST

## 1. Получение ключей Supabase

### 1.1 Создание проекта

1. Перейдите на [supabase.com](https://supabase.com)
2. Создайте новый проект
3. Дождитесь завершения инициализации

### 1.2 Получение ключей

В Supabase Dashboard:

1. Перейдите в **Settings** > **API**
2. Скопируйте следующие ключи:

```bash
# Project URL
NEXT_PUBLIC_SUPABASE_URL="https://your-project-id.supabase.co"

# Anon public key
NEXT_PUBLIC_SUPABASE_ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Service role key (ВАЖНО!)
SUPABASE_SERVICE_ROLE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 1.3 Настройка переменных окружения

Создайте или обновите файл `.env.local`:

```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL="https://your-project-id.supabase.co"
NEXT_PUBLIC_SUPABASE_ANON_KEY="your-anon-key"
SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"

# Database (для Prisma)
DATABASE_URL="postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres"

# OpenAI (опционально)
OPENAI_API_KEY="your-openai-key"

# Environment
NODE_ENV="development"
```

## 2. Настройка аутентификации

### 2.1 Включение провайдеров

В Supabase Dashboard:

1. Перейдите в **Authentication** > **Providers**
2. Включите **Email** provider
3. Включите **Google** provider (настройте OAuth)

### 2.2 Настройка URL

В **Authentication** > **URL Configuration**:

```
Site URL: http://localhost:3000 (для разработки)
Redirect URLs: 
- http://localhost:3000/dashboard
- http://localhost:3000/auth/callback
```

## 3. Применение миграций

### 3.1 Автоматическое применение

```bash
# Применение всех миграций
npm run db:migrate:supabase

# Полная настройка
npm run db:setup:supabase
```

### 3.2 Ручное применение

Если автоматическое применение не работает:

1. Откройте **SQL Editor** в Supabase Dashboard
2. Примените миграцию `001_initial_schema.sql`
3. Примените миграцию `002_enhanced_schema.sql`

## 4. Проверка настройки

### 4.1 Тест подключения

```bash
# Проверка Prisma
npm run db:generate

# Проверка подключения
npm run db:push
```

### 4.2 Тест аутентификации

1. Запустите приложение: `npm run dev`
2. Откройте http://localhost:3000
3. Попробуйте зарегистрироваться

## 5. Устранение проблем

### 5.1 Ошибка "Invalid API key"

Проверьте:
- Правильность `SUPABASE_SERVICE_ROLE_KEY`
- Что ключ не содержит лишних символов
- Что проект активен в Supabase

### 5.2 Ошибка подключения к базе данных

Проверьте:
- Правильность `DATABASE_URL`
- Что база данных доступна
- Настройки RLS политик

### 5.3 Ошибки миграций

Если миграции не применяются:

1. Проверьте права доступа
2. Убедитесь, что service role key правильный
3. Проверьте синтаксис SQL

## 6. Получение DATABASE_URL

В Supabase Dashboard:

1. Перейдите в **Settings** > **Database**
2. Найдите **Connection string**
3. Скопируйте строку подключения
4. Замените `[YOUR-PASSWORD]` на пароль базы данных

Пример:
```
DATABASE_URL="postgresql://postgres:your-password@db.qjdpckwqozsbpskwplfl.supabase.co:5432/postgres"
```

## 7. Безопасность

### 7.1 Рекомендации

- Никогда не коммитьте `.env.local` в git
- Используйте разные ключи для разработки и продакшена
- Регулярно ротируйте ключи
- Мониторьте использование API

### 7.2 Переменные для продакшена

Для продакшена используйте:

```bash
NODE_ENV="production"
NEXT_PUBLIC_SUPABASE_URL="https://your-project.supabase.co"
NEXT_PUBLIC_SUPABASE_ANON_KEY="your-anon-key"
SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
```

## 8. Мониторинг

### 8.1 Supabase Dashboard

- **Database** > **Tables** - просмотр таблиц
- **Authentication** > **Users** - управление пользователями
- **Logs** > **Database Logs** - логи базы данных
- **Logs** > **Auth Logs** - логи аутентификации

### 8.2 Метрики

- **Database** > **Performance** - производительность
- **Database** > **Connections** - активные подключения
- **Database** > **Storage** - использование хранилища

## Поддержка

Если у вас возникли проблемы:

1. Проверьте документацию Supabase
2. Посмотрите логи в Dashboard
3. Проверьте переменные окружения
4. Убедитесь, что все ключи правильные
