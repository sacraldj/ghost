#!/usr/bin/env node

const { createClient } = require('@supabase/supabase-js')
require('dotenv').config()

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY

console.log('🔧 Тестирование подключения к Supabase...')
console.log('================================')

// Проверяем наличие переменных окружения
console.log('📋 Проверка переменных окружения:')
console.log(`URL: ${supabaseUrl ? '✅' : '❌'} ${supabaseUrl || 'НЕ НАЙДЕН'}`)
console.log(`Anon Key: ${supabaseAnonKey ? '✅' : '❌'} ${supabaseAnonKey ? 'НАЙДЕН' : 'НЕ НАЙДЕН'}`)
console.log(`Service Key: ${supabaseServiceKey ? '✅' : '❌'} ${supabaseServiceKey ? 'НАЙДЕН' : 'НЕ НАЙДЕН'}`)

if (!supabaseUrl || !supabaseAnonKey || !supabaseServiceKey) {
  console.log('\n❌ Отсутствуют необходимые переменные окружения!')
  console.log('📝 Добавьте в .env.local:')
  console.log('NEXT_PUBLIC_SUPABASE_URL="your-url"')
  console.log('NEXT_PUBLIC_SUPABASE_ANON_KEY="your-anon-key"')
  console.log('SUPABASE_SERVICE_ROLE_KEY="your-service-key"')
  process.exit(1)
}

// Тестируем подключение с anon key
console.log('\n🔍 Тестирование с anon key...')
const supabaseAnon = createClient(supabaseUrl, supabaseAnonKey)

async function testAnonConnection() {
  try {
    const { data, error } = await supabaseAnon.from('profiles').select('count').limit(1)
    
    if (error) {
      console.log(`❌ Ошибка anon подключения: ${error.message}`)
      return false
    }
    
    console.log('✅ Anon подключение успешно')
    return true
  } catch (error) {
    console.log(`❌ Ошибка anon подключения: ${error.message}`)
    return false
  }
}

// Тестируем подключение с service key
console.log('\n🔍 Тестирование с service key...')
const supabaseService = createClient(supabaseUrl, supabaseServiceKey)

async function testServiceConnection() {
  try {
    const { data, error } = await supabaseService.from('profiles').select('count').limit(1)
    
    if (error) {
      console.log(`❌ Ошибка service подключения: ${error.message}`)
      return false
    }
    
    console.log('✅ Service подключение успешно')
    return true
  } catch (error) {
    console.log(`❌ Ошибка service подключения: ${error.message}`)
    return false
  }
}

// Проверяем таблицы
async function checkTables() {
  console.log('\n📊 Проверка таблиц...')
  
  const tables = [
    'profiles',
    'trades',
    'signals',
    'news_events',
    'ai_analysis',
    'portfolios',
    'strategies',
    'notifications',
    'chat_history'
  ]
  
  let foundTables = 0
  
  for (const table of tables) {
    try {
      const { data, error } = await supabaseService.from(table).select('*').limit(1)
      
      if (error) {
        console.log(`❌ Таблица ${table}: НЕ найдена`)
      } else {
        console.log(`✅ Таблица ${table}: найдена`)
        foundTables++
      }
    } catch (error) {
      console.log(`❌ Таблица ${table}: ошибка проверки`)
    }
  }
  
  console.log(`\n📈 Найдено таблиц: ${foundTables}/${tables.length}`)
  
  if (foundTables === 0) {
    console.log('\n⚠️  Таблицы не найдены. Возможно, миграции не применены.')
    console.log('💡 Запустите: npm run db:migrate:supabase')
  }
  
  return foundTables > 0
}

// Основная функция
async function main() {
  const anonOk = await testAnonConnection()
  const serviceOk = await testServiceConnection()
  const tablesOk = await checkTables()
  
  console.log('\n📊 Результаты тестирования:')
  console.log(`Anon подключение: ${anonOk ? '✅' : '❌'}`)
  console.log(`Service подключение: ${serviceOk ? '✅' : '❌'}`)
  console.log(`Таблицы: ${tablesOk ? '✅' : '❌'}`)
  
  if (anonOk && serviceOk && tablesOk) {
    console.log('\n🎉 Все тесты пройдены! Supabase настроен правильно.')
    console.log('🚀 Можете запускать приложение: npm run dev')
  } else {
    console.log('\n❌ Есть проблемы с настройкой Supabase.')
    console.log('📚 Проверьте документацию: SUPABASE_SETUP.md')
    
    if (!anonOk || !serviceOk) {
      console.log('🔑 Проверьте ключи в .env.local')
    }
    
    if (!tablesOk) {
      console.log('📊 Примените миграции: npm run db:migrate:supabase')
    }
  }
}

main().catch(console.error)
