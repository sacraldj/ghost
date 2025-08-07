#!/bin/bash

echo "🚀 GHOST Trading Platform - Быстрый старт"
echo "=========================================="

# Проверяем наличие Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js не установлен. Установите Node.js 18+"
    exit 1
fi

# Проверяем наличие npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm не установлен"
    exit 1
fi

echo "✅ Node.js и npm найдены"

# Устанавливаем зависимости
echo "📦 Устанавливаем зависимости..."
npm install

# Создаем .env.local если не существует
if [ ! -f .env.local ]; then
    echo "📝 Создаем .env.local..."
    cp env.example .env.local
    echo "✅ .env.local создан"
else
    echo "✅ .env.local уже существует"
fi

# Генерируем Prisma клиент
echo "🔧 Генерируем Prisma клиент..."
npm run db:generate

echo ""
echo "🎯 Следующие шаги:"
echo "1. Получите пароль от базы данных в Supabase Dashboard"
echo "2. Обновите DATABASE_URL в .env.local"
echo "3. Запустите: npm run db:push"
echo "4. Запустите: npm run dev"
echo ""
echo "🔗 Supabase Dashboard: https://supabase.com/dashboard/project/qjdpckwqozsbpskwplfl"
echo "🔗 Database URL: postgresql://postgres:[PASSWORD]@db.qjdpckwqozsbpskwplfl.supabase.co:5432/postgres"
echo ""
echo "🚀 Готово! GHOST настроен для работы с Supabase!" 