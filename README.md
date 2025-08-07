# GHOST - Professional Trading Platform

🚀 **GHOST** - это профессиональная торговая платформа с AI-анализом, новостным движком и продвинутым дашбордом.

## ✨ Особенности

- 📊 **Интерактивный дашборд** с портфолио и активными позициями
- 🤖 **AI-чат** для анализа и консультаций
- 📰 **News Engine** с анализом настроений и влияния
- 🔐 **Безопасная аутентификация** через Supabase
- 📱 **Адаптивный дизайн** для всех устройств
- ⚡ **Быстрый простой вход** для тестирования

## 🛠 Технологии

- **Frontend:** Next.js 15, React 18, TypeScript
- **Styling:** Tailwind CSS, Framer Motion
- **Backend:** Supabase (PostgreSQL, Auth, Edge Functions)
- **AI:** OpenAI API для чата
- **News Engine:** Python, aiohttp, NLTK
- **Deployment:** Vercel

## 🚀 Быстрый старт

### 1. Клонирование репозитория
```bash
git clone https://github.com/sacraltrack18-sys/ghost.git
cd ghost
```

### 2. Установка зависимостей
```bash
npm install
```

### 3. Настройка переменных окружения
Создайте файл `.env.local`:
```bash
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

### 4. Запуск в режиме разработки
```bash
npm run dev
```

Откройте [http://localhost:3000](http://localhost:3000) в браузере.

## 📱 Использование

### Простой вход (для тестирования)
- Перейдите на `/simple-login`
- Нажмите "🚀 Войти в дашборд"
- Получите мгновенный доступ к системе

### Полная аутентификация
- Перейдите на `/auth`
- Зарегистрируйтесь или войдите
- Подтвердите email (если требуется)

## 🏗 Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Supabase      │    │   News Engine   │
│   (Next.js)     │◄──►│   (PostgreSQL)  │◄──►│   (Python)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Dashboard     │    │   Auth API      │    │   News API      │
│   Components    │    │   (Supabase)    │    │   (REST)        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📊 Компоненты

### Dashboard
- **Portfolio Overview** - Обзор портфолио
- **Active Positions** - Активные позиции
- **Market Overview** - Обзор рынка
- **News Feed** - Лента новостей
- **Trading Signals** - Торговые сигналы
- **Chat Interface** - AI-чат

### News Engine
- **Асинхронный сбор** новостей из множества источников
- **Анализ настроений** с помощью VADER
- **Расчет метрик** влияния, срочности, доверия
- **Фильтрация дубликатов** и спама
- **Конфигурируемость** через YAML

### API Endpoints
- `/api/auth/*` - Аутентификация
- `/api/news` - Новостной API
- `/api/user` - Пользовательские данные

## 🚀 Деплой на Vercel

### 1. Подключение к GitHub
1. Перейдите на [Vercel](https://vercel.com)
2. Подключите ваш GitHub аккаунт
3. Импортируйте репозиторий `ghost`

### 2. Настройка переменных окружения
В Vercel Dashboard добавьте:
```
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
NEXT_PUBLIC_SITE_URL=https://your-domain.vercel.app
```

### 3. Деплой
Vercel автоматически определит Next.js и выполнит деплой.

## 🔧 Настройка Supabase

### 1. Создание проекта
1. Перейдите на [Supabase](https://supabase.com)
2. Создайте новый проект
3. Получите URL и ключи

### 2. Настройка аутентификации
1. В Supabase Dashboard → Authentication → Settings
2. Включите Email аутентификацию
3. Настройте URL перенаправлений

### 3. Применение миграций
```bash
# Ручное применение в Supabase SQL Editor
# Используйте файл: scripts/manual-migrations-updated.sql
```

## 📁 Структура проекта

```
ghost/
├── app/                    # Next.js App Router
│   ├── api/               # API endpoints
│   ├── auth/              # Страница аутентификации
│   ├── dashboard/         # Главный дашборд
│   └── simple-login/      # Простой вход
├── components/            # React компоненты
├── news_engine/          # Python News Engine
├── scripts/              # Скрипты и миграции
├── supabase/             # Supabase конфигурация
└── docs/                 # Документация
```

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Создайте Pull Request

## 📄 Лицензия

MIT License - см. файл [LICENSE](LICENSE)

## 🆘 Поддержка

- 📧 Email: support@ghost-trading.com
- 💬 Issues: [GitHub Issues](https://github.com/sacraltrack18-sys/ghost/issues)
- 📖 Документация: [Wiki](https://github.com/sacraltrack18-sys/ghost/wiki)

## 🚀 Статус

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

**GHOST** - Профессиональная торговая платформа будущего 🚀 