#!/usr/bin/env node

/**
 * Скрипт для инициализации базы данных в Supabase
 * Запуск: node scripts/init-database.js
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🗄️ Инициализация базы данных GHOST в Supabase...\n');

// Проверяем наличие .env.local
const envPath = path.join(process.cwd(), '.env.local');
if (!fs.existsSync(envPath)) {
  console.log('❌ .env.local не найден!');
  console.log('Запустите сначала: ./scripts/quick-start.sh');
  process.exit(1);
}

// Проверяем DATABASE_URL
const envContent = fs.readFileSync(envPath, 'utf8');
if (envContent.includes('[YOUR-PASSWORD]') || envContent.includes('localhost')) {
  console.log('❌ DATABASE_URL не настроен для Supabase!');
  console.log('Обновите .env.local с правильным паролем от Supabase');
  console.log('DATABASE_URL="postgresql://postgres:[PASSWORD]@db.qjdpckwqozsbpskwplfl.supabase.co:5432/postgres"');
  process.exit(1);
}

console.log('✅ DATABASE_URL настроен');

try {
  console.log('🔧 Генерируем Prisma клиент...');
  execSync('npm run db:generate', { stdio: 'inherit' });
  
  console.log('📊 Применяем схему к базе данных...');
  execSync('npm run db:push', { stdio: 'inherit' });
  
  console.log('✅ База данных успешно инициализирована!');
  console.log('\n🎉 GHOST готов к использованию!');
  console.log('Запустите: npm run dev');
  
} catch (error) {
  console.error('❌ Ошибка инициализации базы данных:', error.message);
  console.log('\n🔧 Возможные решения:');
  console.log('1. Проверьте правильность пароля в DATABASE_URL');
  console.log('2. Убедитесь, что Supabase проект активен');
  console.log('3. Проверьте подключение к интернету');
} 