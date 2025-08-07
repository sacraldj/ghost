# 🚀 Инструкции по деплою GHOST на Vercel

## Проблема с GitHub
Аккаунт GitHub заблокирован. Используйте альтернативные способы деплоя.

## Вариант 1: Ручной пуш на GitHub

### 1. Создайте новый репозиторий
1. Перейдите на [GitHub](https://github.com)
2. Создайте новый репозиторий `ghost`
3. Скопируйте URL репозитория

### 2. Обновите remote URL
```bash
git remote set-url origin https://github.com/YOUR_USERNAME/ghost.git
git push -u origin main
```

## Вариант 2: Деплой через Vercel CLI

### 1. Установите Vercel CLI
```bash
npm i -g vercel
```

### 2. Войдите в Vercel
```bash
vercel login
```

### 3. Деплой проекта
```bash
vercel --prod
```

### 4. Настройте переменные окружения
В Vercel Dashboard добавьте:
```
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
NEXT_PUBLIC_SITE_URL=https://your-domain.vercel.app
```

## Вариант 3: Деплой через GitHub Actions

### 1. Создайте файл `.github/workflows/deploy.yml`
```yaml
name: Deploy to Vercel
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run build
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.ORG_ID }}
          vercel-project-id: ${{ secrets.PROJECT_ID }}
          working-directory: ./
```

### 2. Добавьте секреты в GitHub
- `VERCEL_TOKEN`
- `ORG_ID`
- `PROJECT_ID`

## Вариант 4: Деплой через GitLab

### 1. Создайте репозиторий на GitLab
1. Перейдите на [GitLab](https://gitlab.com)
2. Создайте новый проект `ghost`
3. Скопируйте URL

### 2. Обновите remote
```bash
git remote set-url origin https://gitlab.com/YOUR_USERNAME/ghost.git
git push -u origin main
```

### 3. Настройте CI/CD в GitLab
Создайте `.gitlab-ci.yml`:
```yaml
stages:
  - build
  - deploy

build:
  stage: build
  image: node:18
  script:
    - npm ci
    - npm run build
  artifacts:
    paths:
      - .next/

deploy:
  stage: deploy
  image: alpine:latest
  script:
    - apk add --no-cache curl
    - curl -X POST $VERCEL_DEPLOY_HOOK
  only:
    - main
```

## Настройка Supabase для продакшена

### 1. Создайте проект Supabase
1. Перейдите на [Supabase](https://supabase.com)
2. Создайте новый проект
3. Получите URL и ключи

### 2. Примените миграции
```sql
-- В Supabase SQL Editor выполните:
-- scripts/manual-migrations-updated.sql
```

### 3. Настройте аутентификацию
1. Authentication → Settings
2. Включите Email аутентификацию
3. Добавьте домен в Site URL
4. Настройте Redirect URLs

### 4. Настройте RLS
```sql
-- Включите RLS для всех таблиц
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE news_items ENABLE ROW LEVEL SECURITY;
-- ... и так далее для всех таблиц
```

## Проверка деплоя

### 1. Тестирование функций
- ✅ Простой вход: `/simple-login`
- ✅ Полная аутентификация: `/auth`
- ✅ Дашборд: `/dashboard`
- ✅ API endpoints: `/api/*`

### 2. Проверка переменных окружения
```bash
# В Vercel Dashboard проверьте:
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY
NEXT_PUBLIC_SITE_URL
```

### 3. Логи и мониторинг
- Проверьте логи в Vercel Dashboard
- Мониторьте производительность
- Настройте алерты

## Troubleshooting

### Ошибка 403 при пуше
```bash
# Решение: используйте SSH или токен
git remote set-url origin git@github.com:USERNAME/ghost.git
# Или
git remote set-url origin https://TOKEN@github.com/USERNAME/ghost.git
```

### Ошибки сборки
```bash
# Проверьте зависимости
npm ci
npm run build

# Проверьте TypeScript
npx tsc --noEmit
```

### Проблемы с Supabase
1. Проверьте переменные окружения
2. Убедитесь, что RLS настроен правильно
3. Проверьте права доступа к таблицам

## Полезные команды

```bash
# Локальная разработка
npm run dev

# Продакшн сборка
npm run build

# Линтинг
npm run lint

# Типы TypeScript
npx tsc --noEmit

# Тестирование API
curl http://localhost:3000/api/news
```

## Контакты для поддержки

- 📧 Email: support@ghost-trading.com
- 💬 Issues: GitHub Issues
- 📖 Документация: Wiki

---

**GHOST** готов к деплою! 🚀
