#!/usr/bin/env node

const { createClient } = require('@supabase/supabase-js')
const fs = require('fs')
const path = require('path')

// Загружаем переменные окружения
require('dotenv').config()

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY

if (!supabaseUrl || !supabaseServiceKey) {
  console.error('❌ Ошибка: Не найдены переменные окружения SUPABASE_URL или SUPABASE_SERVICE_ROLE_KEY')
  process.exit(1)
}

const supabase = createClient(supabaseUrl, supabaseServiceKey)

async function applyMigration(migrationFile) {
  try {
    console.log(`📄 Применяем миграцию: ${migrationFile}`)
    
    const migrationPath = path.join(__dirname, '..', 'supabase', 'migrations', migrationFile)
    const sql = fs.readFileSync(migrationPath, 'utf8')
    
    const { error } = await supabase.rpc('exec_sql', { sql })
    
    if (error) {
      console.error(`❌ Ошибка при применении миграции ${migrationFile}:`, error)
      return false
    }
    
    console.log(`✅ Миграция ${migrationFile} успешно применена`)
    return true
  } catch (error) {
    console.error(`❌ Ошибка при чтении/применении миграции ${migrationFile}:`, error)
    return false
  }
}

async function applyAllMigrations() {
  console.log('🚀 Начинаем применение миграций Supabase...')
  
  const migrationsDir = path.join(__dirname, '..', 'supabase', 'migrations')
  
  if (!fs.existsSync(migrationsDir)) {
    console.error('❌ Директория миграций не найдена')
    process.exit(1)
  }
  
  const migrationFiles = fs.readdirSync(migrationsDir)
    .filter(file => file.endsWith('.sql'))
    .sort() // Сортируем по имени файла для правильного порядка
  
  console.log(`📁 Найдено ${migrationFiles.length} миграций`)
  
  let successCount = 0
  let errorCount = 0
  
  for (const migrationFile of migrationFiles) {
    const success = await applyMigration(migrationFile)
    if (success) {
      successCount++
    } else {
      errorCount++
    }
    
    // Небольшая пауза между миграциями
    await new Promise(resolve => setTimeout(resolve, 1000))
  }
  
  console.log('\n📊 Результат применения миграций:')
  console.log(`✅ Успешно: ${successCount}`)
  console.log(`❌ Ошибок: ${errorCount}`)
  
  if (errorCount > 0) {
    console.log('\n⚠️  Некоторые миграции не были применены. Проверьте логи выше.')
    process.exit(1)
  } else {
    console.log('\n🎉 Все миграции успешно применены!')
  }
}

// Проверяем подключение к Supabase
async function testConnection() {
  try {
    const { data, error } = await supabase.from('profiles').select('count').limit(1)
    
    if (error) {
      console.error('❌ Ошибка подключения к Supabase:', error)
      return false
    }
    
    console.log('✅ Подключение к Supabase успешно')
    return true
  } catch (error) {
    console.error('❌ Ошибка подключения к Supabase:', error)
    return false
  }
}

async function main() {
  console.log('🔧 GHOST Database Migration Tool')
  console.log('================================')
  
  // Проверяем подключение
  const connected = await testConnection()
  if (!connected) {
    console.error('❌ Не удалось подключиться к Supabase. Проверьте переменные окружения.')
    process.exit(1)
  }
  
  // Применяем миграции
  await applyAllMigrations()
}

if (require.main === module) {
  main().catch(console.error)
}

module.exports = { applyMigration, applyAllMigrations }
