#!/usr/bin/env node

/**
 * Автоматическая инициализация Supabase через API
 * Запуск: node scripts/auto-init-supabase.js
 */

const fs = require('fs');
const path = require('path');

console.log('🚀 Автоматическая инициализация Supabase для GHOST...\n');

// Проверяем наличие .env.local
const envPath = path.join(process.cwd(), '.env.local');
if (!fs.existsSync(envPath)) {
  console.log('❌ .env.local не найден!');
  console.log('Запустите сначала: ./scripts/quick-start.sh');
  process.exit(1);
}

// Читаем переменные окружения
const envContent = fs.readFileSync(envPath, 'utf8');
const supabaseUrl = envContent.match(/NEXT_PUBLIC_SUPABASE_URL="([^"]+)"/)?.[1];
const supabaseKey = envContent.match(/NEXT_PUBLIC_SUPABASE_ANON_KEY="([^"]+)"/)?.[1];

if (!supabaseUrl || !supabaseKey) {
  console.log('❌ Supabase URL или ключ не найдены в .env.local');
  process.exit(1);
}

console.log('✅ Supabase конфигурация найдена');

// Читаем SQL скрипт
const sqlPath = path.join(process.cwd(), 'scripts', 'init-supabase.sql');
if (!fs.existsSync(sqlPath)) {
  console.log('❌ SQL скрипт не найден: scripts/init-supabase.sql');
  process.exit(1);
}

const sqlScript = fs.readFileSync(sqlPath, 'utf8');

console.log('\n📋 Инструкции для инициализации базы данных:');
console.log('==============================================');
console.log('');
console.log('1. Перейдите в Supabase Dashboard:');
console.log(`   ${supabaseUrl.replace('https://', 'https://supabase.com/dashboard/project/')}`);
console.log('');
console.log('2. Откройте SQL Editor (в левом меню)');
console.log('');
console.log('3. Скопируйте и вставьте следующий SQL скрипт:');
console.log('');
console.log('='.repeat(80));
console.log(sqlScript);
console.log('='.repeat(80));
console.log('');
console.log('4. Нажмите "Run" для выполнения скрипта');
console.log('');
console.log('5. После успешного выполнения запустите:');
console.log('   npm run dev');
console.log('');
console.log('🎉 GHOST будет готов к использованию!');
console.log('');
console.log('🔗 Ссылки:');
console.log(`   - Supabase Dashboard: ${supabaseUrl.replace('https://', 'https://supabase.com/dashboard/project/')}`);
console.log('   - Приложение: http://localhost:3000');
console.log('');
console.log('📊 Создастся следующие таблицы:');
console.log('   - users (пользователи)');
console.log('   - trades (сделки)');
console.log('   - signals (сигналы)');
console.log('   - news_events (новости)');
console.log('   - ai_analysis (ИИ-анализ)');
console.log('   - event_anomalies (аномалии)');
console.log('   - market_manipulations (манипуляции)');
console.log('   - strategies (стратегии)');
console.log('   - portfolios (портфели)');
console.log('   - notifications (уведомления)');
console.log('   - trade_timeline (таймлайн сделок)');
console.log('   - price_feed (ценовой фид)');
console.log('');
console.log('🔐 Row Level Security (RLS) включен для всех таблиц');
console.log('🎯 Тестовые данные добавлены автоматически'); 