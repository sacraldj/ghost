#!/bin/bash

echo "🚀 GHOST Quick Setup"
echo "===================="

# Проверяем наличие Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js не установлен. Установите Node.js 18+ и попробуйте снова."
    exit 1
fi

# Проверяем версию Node.js
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Требуется Node.js 18+. Текущая версия: $(node -v)"
    exit 1
fi

echo "✅ Node.js версия: $(node -v)"

# Устанавливаем зависимости
echo "📦 Устанавливаем зависимости..."
npm install

# Проверяем наличие .env.local
if [ ! -f ".env.local" ]; then
    echo "⚠️  Файл .env.local не найден"
    echo "📝 Создайте файл .env.local с необходимыми переменными окружения:"
    echo ""
    echo "NEXT_PUBLIC_SUPABASE_URL=your_supabase_url"
    echo "NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key"
    echo "SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key"
    echo "DATABASE_URL=your_database_url"
    echo "OPENAI_API_KEY=your_openai_api_key"
    echo ""
    echo "После создания файла запустите скрипт снова."
    exit 1
fi

echo "✅ .env.local найден"

# Генерируем Prisma клиент
echo "🔧 Генерируем Prisma клиент..."
npm run db:generate

# Настраиваем Supabase
echo "🔧 Настраиваем Supabase..."
npm run setup:supabase:complete

# Применяем миграции
echo "📊 Применяем миграции базы данных..."
npm run db:migrate:supabase

# Проверяем подключение
echo "🔍 Проверяем подключение к базе данных..."
npm run db:push

echo ""
echo "🎉 Настройка завершена!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Запустите приложение: npm run dev"
echo "2. Откройте http://localhost:3000"
echo "3. Зарегистрируйтесь в системе"
echo "4. Проверьте работу dashboard"
echo ""
echo "📚 Документация:"
echo "- DATABASE_SETUP.md - настройка базы данных"
echo "- README.md - общая документация"
echo ""
echo "🔧 Полезные команды:"
echo "- npm run dev - запуск в режиме разработки"
echo "- npm run build - сборка для продакшена"
echo "- npm run db:studio - просмотр базы данных"
echo "- npm run db:migrate:supabase - применение миграций"
echo ""
echo "🚀 Удачной разработки!"
