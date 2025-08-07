# Обновление переменных окружения

## Добавьте в файл .env.local:

```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL="https://qjdpckwqozsbpskwplfl.supabase.co"
NEXT_PUBLIC_SUPABASE_ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFqZHBja3dxb3pzYnBza3dwbGZsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ1MDUyNTUsImV4cCI6MjA3MDA4MTI1NX0.kY8A88CoBNN2m7EAbJpy1TNfqu9zOY4pFKmvLZ42Lf8"
SUPABASE_SERVICE_ROLE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFqZHBja3dxb3pzYnBza3dwbGZsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NDUwNTI1NSwiZXhwIjoyMDcwMDgxMjU1fQ.At9S4Jb1maeGrh3GfFtj1ItcOSDBn0Qj1dJ7aWZD97g"

# Database
DATABASE_URL="postgresql://postgres:[YOUR-PASSWORD]@db.qjdpckwqozsbpskwplfl.supabase.co:5432/postgres"

# OpenAI
OPENAI_API_KEY="your-openai-api-key"

# Google Gemini
GEMINI_API_KEY="your-gemini-api-key"

# Bybit API
BYBIT_API_KEY="your-bybit-api-key"
BYBIT_API_SECRET="your-bybit-api-secret"

# Environment
NODE_ENV="development"
```

## Получение пароля базы данных

1. Перейдите в Supabase Dashboard
2. Settings > Database
3. Найдите "Connection string"
4. Скопируйте пароль из строки подключения
5. Замените `[YOUR-PASSWORD]` на реальный пароль

## После обновления .env.local:

```bash
# Тестирование подключения
node scripts/test-connection.js

# Применение миграций
npm run db:migrate:supabase

# Запуск приложения
npm run dev
```
