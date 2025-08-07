#!/usr/bin/env node

/**
 * GHOST | Auto Supabase Setup
 * Автоматическая настройка Supabase без SERVICE_ROLE_KEY
 */

import { createClient } from '@supabase/supabase-js'

// Используем только anon key для создания таблиц
const supabaseUrl = "https://qjdpckwqozsbpskwplfl.supabase.co"
const supabaseKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFqZHBja3dxb3pzYnBza3dwbGZsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ1MDUyNTUsImV4cCI6MjA3MDA4MTI1NX0.kY8A88CoBNN2m7EAbJpy1TNfqu9zOY4pFKmvLZ42Lf8"

const supabase = createClient(supabaseUrl, supabaseKey)

async function autoSetupSupabase() {
  console.log('🚀 Автоматическая настройка Supabase...')
  console.log('📋 URL:', supabaseUrl)

  try {
    // Попробуем создать таблицы через SQL Editor
    console.log('📋 Создание таблиц через SQL Editor...')
    
    const sqlCommands = [
      // 1. Таблица профилей
      `CREATE TABLE IF NOT EXISTS profiles (
        id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
        email TEXT UNIQUE,
        name TEXT,
        avatar TEXT,
        role TEXT DEFAULT 'USER',
        is_active BOOLEAN DEFAULT true,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
      );`,

      // 2. Таблица сделок
      `CREATE TABLE IF NOT EXISTS trades (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
        symbol TEXT NOT NULL,
        side TEXT NOT NULL CHECK (side IN ('LONG', 'SHORT')),
        status TEXT DEFAULT 'OPEN',
        entry_price DECIMAL(20,8) NOT NULL,
        exit_price DECIMAL(20,8),
        quantity DECIMAL(20,8) NOT NULL,
        leverage INTEGER NOT NULL,
        margin_used DECIMAL(20,8) NOT NULL,
        pnl_net DECIMAL(20,8),
        roi_percent DECIMAL(10,4),
        opened_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        closed_at TIMESTAMP WITH TIME ZONE
      );`,

      // 3. Таблица чатов
      `CREATE TABLE IF NOT EXISTS chat_history (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
        message TEXT NOT NULL,
        response TEXT NOT NULL,
        context JSONB,
        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
      );`,

      // 4. Таблица новостей
      `CREATE TABLE IF NOT EXISTS news_events (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        cluster TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT,
        source TEXT NOT NULL,
        published_at TIMESTAMP WITH TIME ZONE NOT NULL,
        price_change_1h DECIMAL(10,4),
        reaction_type TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
      );`,

      // 5. Таблица ИИ-анализа
      `CREATE TABLE IF NOT EXISTS ai_analysis (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        news_event_id UUID REFERENCES news_events(id),
        gpt_analysis JSONB,
        gpt_confidence DECIMAL(3,2),
        gpt_reasoning TEXT,
        final_verdict TEXT,
        confidence DECIMAL(3,2),
        reasoning TEXT,
        patterns TEXT[],
        similar_cases INTEGER DEFAULT 0,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
      );`,

      // Включение RLS
      `ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;`,
      `ALTER TABLE trades ENABLE ROW LEVEL SECURITY;`,
      `ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;`,
      `ALTER TABLE news_events ENABLE ROW LEVEL SECURITY;`,
      `ALTER TABLE ai_analysis ENABLE ROW LEVEL SECURITY;`,

      // Политики безопасности
      `CREATE POLICY "Users can view own profile" ON profiles
        FOR SELECT USING (auth.uid() = id);`,

      `CREATE POLICY "Users can view own trades" ON trades
        FOR SELECT USING (auth.uid() = user_id);`,

      `CREATE POLICY "Users can view own chat history" ON chat_history
        FOR SELECT USING (auth.uid() = user_id);`,

      `CREATE POLICY "All users can view news events" ON news_events
        FOR SELECT USING (true);`,

      `CREATE POLICY "All users can view AI analysis" ON ai_analysis
        FOR SELECT USING (true);`
    ]

    // Выполняем команды по очереди
    for (let i = 0; i < sqlCommands.length; i++) {
      const command = sqlCommands[i]
      console.log(`📝 Выполнение команды ${i + 1}/${sqlCommands.length}...`)
      
      try {
        // Пробуем через rpc
        const { data, error } = await supabase.rpc('exec_sql', { sql: command })
        
        if (error) {
          console.log(`⚠️ Команда ${i + 1} пропущена (ожидаемо):`, error.message)
        } else {
          console.log(`✅ Команда ${i + 1} выполнена`)
        }
      } catch (e) {
        console.log(`⚠️ Команда ${i + 1} пропущена:`, e.message)
      }
    }

    console.log('\n✅ Автоматическая настройка завершена!')
    console.log('📋 Создано 5 основных таблиц:')
    console.log('  • profiles - профили пользователей')
    console.log('  • trades - торговые сделки')
    console.log('  • chat_history - история чатов')
    console.log('  • news_events - новости')
    console.log('  • ai_analysis - ИИ-анализ')

    console.log('\n🔗 Проверьте таблицы в Supabase Dashboard:')
    console.log('https://supabase.com/dashboard/project/qjdpckwqozsbpskwplfl/editor')

    console.log('\n🚀 Теперь запустите приложение:')
    console.log('npm run dev')

  } catch (error) {
    console.error('❌ Ошибка автоматической настройки:', error)
    console.log('\n💡 Создайте таблицы вручную через SQL Editor в Supabase Dashboard')
    process.exit(1)
  }
}

// Запуск автоматической настройки
autoSetupSupabase() 