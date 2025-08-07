# Ручное применение миграций в Supabase

## Пошаговая инструкция

### 1. Откройте Supabase Dashboard

1. Перейдите на [supabase.com](https://supabase.com)
2. Войдите в свой аккаунт
3. Откройте проект GHOST

### 2. Откройте SQL Editor

1. В левом меню найдите **SQL Editor**
2. Нажмите **New Query**

### 3. Примените миграции

1. Скопируйте содержимое файла `scripts/manual-migrations-updated.sql`
2. Вставьте в SQL Editor
3. Нажмите **Run** (или Ctrl+Enter)

**Примечание:** Используйте файл `manual-migrations-updated.sql` вместо `manual-migrations.sql`, так как он игнорирует уже существующие политики.

### 4. Проверьте результат

После выполнения вы должны увидеть:
```
Migration completed successfully!
```

### 5. Проверьте созданные таблицы

В левом меню перейдите в **Table Editor** и убедитесь, что созданы следующие таблицы:

#### Основные таблицы:
- ✅ profiles
- ✅ api_keys
- ✅ signals
- ✅ trades
- ✅ news_events
- ✅ ai_analysis
- ✅ event_anomalies
- ✅ market_manipulations
- ✅ strategies
- ✅ portfolios
- ✅ notifications
- ✅ chat_history
- ✅ trade_timeline
- ✅ price_feed

#### Дополнительные таблицы:
- ✅ influential_tweets
- ✅ market_data
- ✅ analysis_history
- ✅ news_bookmarks
- ✅ user_settings
- ✅ trading_sessions
- ✅ trading_patterns
- ✅ trading_goals

### 6. Проверьте политики безопасности

В **Authentication** > **Policies** должны быть созданы политики для всех таблиц.

### 7. Тестирование

После применения миграций запустите тест:

```bash
npm run test:connection
```

## Устранение проблем

### Ошибка "relation already exists"

Если таблица уже существует, это нормально. Миграция использует `CREATE TABLE IF NOT EXISTS`.

### Ошибка "policy already exists"

Если политика уже существует, это нормально. Можно игнорировать эти ошибки.

### Ошибка "function already exists"

Если функция `update_updated_at_column` уже существует, это нормально.

## Альтернативный способ

Если у вас есть доступ к Supabase CLI, можете использовать:

```bash
# Установка Supabase CLI
npm install -g supabase

# Логин
supabase login

# Привязка проекта
supabase link --project-ref qjdpckwqozsbpskwplfl

# Применение миграций
supabase db push
```

## Проверка после миграции

После успешного применения миграций:

1. Запустите тест подключения:
   ```bash
   npm run test:connection
   ```

2. Запустите приложение:
   ```bash
   npm run dev
   ```

3. Откройте http://localhost:3000

4. Попробуйте зарегистрироваться и войти в систему

## Поддержка

Если возникли проблемы:

1. Проверьте логи в Supabase Dashboard > Logs
2. Убедитесь, что у вас есть права на создание таблиц
3. Проверьте, что проект активен
4. Обратитесь к документации Supabase
