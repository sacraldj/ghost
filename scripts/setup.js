#!/usr/bin/env node

/**
 * GHOST Trading Platform - Быстрый старт
 * Запуск: node scripts/setup.js
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🚀 GHOST Trading Platform - Быстрый старт');
console.log('==========================================');

// Проверяем наличие Node.js
try {
  const nodeVersion = execSync('node --version', { encoding: 'utf8' }).trim();
  console.log(`✅ Node.js найден: ${nodeVersion}`);
} catch (error) {
  console.log('❌ Node.js не установлен. Установите Node.js 18+');
  process.exit(1);
}

// Проверяем наличие npm
try {
  const npmVersion = execSync('npm --version', { encoding: 'utf8' }).trim();
  console.log(`✅ npm найден: ${npmVersion}`);
} catch (error) {
  console.log('❌ npm не установлен');
  process.exit(1);
}

console.log('✅ Node.js и npm найдены');

// Устанавливаем зависимости
console.log('📦 Устанавливаем зависимости...');
try {
  execSync('npm install', { stdio: 'inherit' });
  console.log('✅ Зависимости установлены');
} catch (error) {
  console.log('❌ Ошибка установки зависимостей');
  process.exit(1);
}

// Создаем .env.local если не существует
const envPath = path.join(process.cwd(), '.env.local');
if (!fs.existsSync(envPath)) {
  console.log('📝 Создаем .env.local...');
  try {
    const envExample = fs.readFileSync(path.join(process.cwd(), 'env.example'), 'utf8');
    fs.writeFileSync(envPath, envExample);
    console.log('✅ .env.local создан');
  } catch (error) {
    console.log('❌ Ошибка создания .env.local');
    process.exit(1);
  }
} else {
  console.log('✅ .env.local уже существует');
}

// Генерируем Prisma клиент
console.log('🔧 Генерируем Prisma клиент...');
try {
  execSync('npm run db:generate', { stdio: 'inherit' });
  console.log('✅ Prisma клиент сгенерирован');
} catch (error) {
  console.log('❌ Ошибка генерации Prisma клиента');
  process.exit(1);
}

console.log('');
console.log('🎯 Следующие шаги:');
console.log('1. Получите пароль от базы данных в Supabase Dashboard');
console.log('2. Обновите DATABASE_URL в .env.local');
console.log('3. Запустите: npm run init-supabase');
console.log('4. Запустите: npm run dev');
console.log('');
console.log('🔗 Supabase Dashboard: https://supabase.com/dashboard/project/qjdpckwqozsbpskwplfl');
console.log('🔗 Database URL: postgresql://postgres:[PASSWORD]@db.qjdpckwqozsbpskwplfl.supabase.co:5432/postgres');
console.log('');
console.log('🚀 Готово! GHOST настроен для работы с Supabase!'); 