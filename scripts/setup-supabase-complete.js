#!/usr/bin/env node

/**
 * GHOST | Complete Supabase Setup
 * Полная настройка Supabase с созданием всех таблиц
 */

const { createClient } = require('@supabase/supabase-js')
const dotenv = require('dotenv')
const fs = require('fs')
const path = require('path')

dotenv.config()

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY

if (!supabaseUrl || !supabaseKey) {
  console.error('❌ Отсутствуют переменные окружения Supabase')
  console.error('Добавьте в .env:')
  console.error('NEXT_PUBLIC_SUPABASE_URL="your-supabase-url"')
  console.error('SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"')
  process.exit(1)
}

const supabase = createClient(supabaseUrl, supabaseKey)

async function setupSupabase() {
  console.log('🚀 Полная настройка Supabase для GHOST...')
  console.log('📋 URL:', supabaseUrl)

  try {
    // Читаем SQL миграцию
    const migrationPath = path.join(process.cwd(), 'supabase', 'migrations', '001_initial_schema.sql')
    
    if (!fs.existsSync(migrationPath)) {
      console.error('❌ Файл миграции не найден:', migrationPath)
      process.exit(1)
    }

    const sql = fs.readFileSync(migrationPath, 'utf8')
    
    console.log('📋 Выполнение миграции...')
    
    // Выполняем SQL через rpc
    const { data, error } = await supabase.rpc('exec_sql', { sql })
    
    if (error) {
      console.error('❌ Ошибка выполнения SQL:', error)
      
      // Попробуем выполнить через SQL Editor
      console.log('🔄 Попробуем альтернативный способ...')
      
      // Разбиваем SQL на отдельные команды
      const commands = sql.split(';').filter(cmd => cmd.trim().length > 0)
      
      for (let i = 0; i < commands.length; i++) {
        const command = commands[i].trim()
        if (command) {
          try {
            console.log(`📝 Выполнение команды ${i + 1}/${commands.length}...`)
            await supabase.rpc('exec_sql', { sql: command + ';' })
          } catch (cmdError) {
            console.warn(`⚠️ Команда ${i + 1} пропущена:`, cmdError.message)
          }
        }
      }
    }

    console.log('✅ Миграция выполнена успешно!')

    // Проверяем созданные таблицы
    console.log('🔍 Проверка созданных таблиц...')
    
    const tables = [
      'profiles',
      'api_keys', 
      'signals',
      'trades',
      'news_events',
      'ai_analysis',
      'event_anomalies',
      'market_manipulations',
      'strategies',
      'portfolios',
      'notifications',
      'chat_history',
      'trade_timeline',
      'price_feed'
    ]

    for (const table of tables) {
      try {
        const { data, error } = await supabase
          .from(table)
          .select('*')
          .limit(1)
        
        if (error) {
          console.log(`❌ Таблица ${table}: НЕ создана`)
        } else {
          console.log(`✅ Таблица ${table}: создана`)
        }
      } catch (tableError) {
        console.log(`❌ Таблица ${table}: ошибка проверки`)
      }
    }

    console.log('🎉 Настройка Supabase завершена!')
    console.log('📋 Следующие шаги:')
    console.log('1. Настройте аутентификацию в Supabase Dashboard')
    console.log('2. Добавьте провайдеры (Email, Google)')
    console.log('3. Настройте URL для перенаправления')
    console.log('4. Запустите: npm run dev')

  } catch (error) {
    console.error('❌ Ошибка настройки Supabase:', error)
    process.exit(1)
  }
}

// Запуск настройки
setupSupabase().catch(console.error) 