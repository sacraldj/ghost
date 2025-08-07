# Настройка базы данных GHOST

## 1. Подготовка Supabase

### 1.1 Создание проекта Supabase

1. Перейдите на [supabase.com](https://supabase.com)
2. Создайте новый проект
3. Запишите URL и API ключи

### 1.2 Настройка переменных окружения

Создайте файл `.env.local` в корне проекта:

```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# Database
DATABASE_URL=your_database_url

# OpenAI (для AI функций)
OPENAI_API_KEY=your_openai_api_key
```

## 2. Применение миграций

### 2.1 Автоматическое применение

```bash
# Применение всех миграций
npm run db:migrate:supabase

# Полная настройка Supabase (включая миграции)
npm run db:setup:supabase
```

### 2.2 Ручное применение

Если автоматическое применение не работает, выполните миграции вручную:

1. Откройте SQL Editor в Supabase Dashboard
2. Примените миграцию `001_initial_schema.sql`
3. Примените миграцию `002_enhanced_schema.sql`

## 3. Структура базы данных

### 3.1 Основные таблицы

- **profiles** - Профили пользователей
- **trades** - Торговые сделки
- **signals** - Торговые сигналы
- **news_events** - Новостные события
- **ai_analysis** - Анализ ИИ
- **portfolios** - Портфолио пользователей
- **strategies** - Торговые стратегии

### 3.2 Новые таблицы (миграция 002)

- **influential_tweets** - Влиятельные твиты
- **market_data** - Рыночные данные
- **analysis_history** - История анализа
- **news_bookmarks** - Закладки новостей
- **user_settings** - Настройки пользователей
- **trading_sessions** - Торговые сессии
- **trading_patterns** - Торговые паттерны
- **trading_goals** - Торговые цели

## 4. Настройка аутентификации

### 4.1 Включение провайдеров

В Supabase Dashboard:

1. Перейдите в Authentication > Providers
2. Включите Email provider
3. Включите Google provider (настройте OAuth)

### 4.2 Настройка URL

В Authentication > URL Configuration:

```
Site URL: http://localhost:3000 (для разработки)
Redirect URLs: 
- http://localhost:3000/dashboard
- http://localhost:3000/auth/callback
```

## 5. Проверка настройки

### 5.1 Тест подключения

```bash
# Проверка подключения к базе данных
npm run db:generate

# Запуск приложения
npm run dev
```

### 5.2 Тест аутентификации

1. Откройте http://localhost:3000
2. Попробуйте зарегистрироваться
3. Проверьте вход в систему

## 6. Устранение проблем

### 6.1 Ошибки миграций

Если миграции не применяются:

1. Проверьте права доступа к базе данных
2. Убедитесь, что service role key правильный
3. Проверьте синтаксис SQL в миграциях

### 6.2 Ошибки аутентификации

Если аутентификация не работает:

1. Проверьте настройки провайдеров в Supabase
2. Убедитесь, что URL настроены правильно
3. Проверьте переменные окружения

### 6.3 Ошибки RLS (Row Level Security)

Если данные не загружаются:

1. Проверьте политики безопасности в Supabase
2. Убедитесь, что пользователь аутентифицирован
3. Проверьте права доступа к таблицам

## 7. Дополнительные настройки

### 7.1 Настройка уведомлений

Для работы с уведомлениями настройте:

- Email провайдер (SMTP)
- Telegram Bot (опционально)

### 7.2 Настройка AI функций

Для работы AI анализа:

1. Получите API ключ OpenAI
2. Добавьте в переменные окружения
3. Настройте лимиты и квоты

### 7.3 Настройка торговых API

Для интеграции с биржами:

1. Создайте API ключи на биржах
2. Настройте безопасное хранение ключей
3. Добавьте в переменные окружения

## 8. Мониторинг и логи

### 8.1 Просмотр логов

В Supabase Dashboard:

- Logs > Database Logs
- Logs > Auth Logs
- Logs > Edge Function Logs

### 8.2 Мониторинг производительности

- Database > Performance
- Database > Connections
- Database > Storage

## 9. Резервное копирование

### 9.1 Автоматические бэкапы

Supabase автоматически создает бэкапы:

- Ежедневные бэкапы (7 дней)
- Еженедельные бэкапы (4 недели)

### 9.2 Ручные бэкапы

```bash
# Экспорт данных
pg_dump your_database_url > backup.sql

# Импорт данных
psql your_database_url < backup.sql
```

## 10. Обновления и миграции

### 10.1 Создание новых миграций

```bash
# Создайте новый файл в supabase/migrations/
# Формат: 003_description.sql
```

### 10.2 Применение обновлений

```bash
# Применение новых миграций
npm run db:migrate:supabase
```

## 11. Безопасность

### 11.1 Рекомендации

- Используйте сильные пароли
- Включите двухфакторную аутентификацию
- Регулярно обновляйте API ключи
- Мониторьте подозрительную активность

### 11.2 Аудит

В Supabase Dashboard:

- Audit Logs > Database
- Audit Logs > Auth
- Audit Logs > API

## 12. Производительность

### 12.1 Оптимизация запросов

- Используйте индексы
- Оптимизируйте сложные запросы
- Используйте кэширование

### 12.2 Мониторинг

- Database > Performance
- Database > Connections
- Database > Storage

## Поддержка

Если у вас возникли проблемы:

1. Проверьте документацию Supabase
2. Посмотрите логи в Dashboard
3. Создайте issue в репозитории проекта
