#!/usr/bin/env node

/**
 * GHOST | Simple Supabase Setup
 * Упрощенная настройка Supabase
 */

import { createClient } from '@supabase/supabase-js'

// Проверяем переменные окружения
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY

if (!supabaseUrl || !supabaseKey) {
  console.log('❌ Переменные окружения не найдены')
  console.log('')
  console.log('📋 Создайте файл .env в корне проекта:')
  console.log('')
  console.log('NEXT_PUBLIC_SUPABASE_URL="https://your-project.supabase.co"')
  console.log('NEXT_PUBLIC_SUPABASE_ANON_KEY="your-anon-key"')
  console.log('SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"')
  console.log('')
  console.log('🔗 Получите ключи на: https://supabase.com')
  console.log('')
  process.exit(1)
}

const supabase = createClient(supabaseUrl, supabaseKey)

async function setupSupabase() {
  console.log('🚀 Настройка Supabase для GHOST...')
  console.log('📋 URL:', supabaseUrl)

  try {
    // Создаем основные таблицы
    console.log('📋 Создание таблиц...')

    // 1. Таблица профилей
    console.log('✅ Создание таблицы profiles...')
    await supabase.rpc('exec_sql', {
      sql: `
        CREATE TABLE IF NOT EXISTS profiles (
          id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
          email TEXT UNIQUE,
          name TEXT,
          avatar TEXT,
          role TEXT DEFAULT 'USER',
          is_active BOOLEAN DEFAULT true,
          created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
          updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
      `
    })

    // 2. Таблица сделок
    console.log('✅ Создание таблицы trades...')
    await supabase.rpc('exec_sql', {
      sql: `
        CREATE TABLE IF NOT EXISTS trades (
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
        );
      `
    })

    // 3. Таблица чатов
    console.log('✅ Создание таблицы chat_history...')
    await supabase.rpc('exec_sql', {
      sql: `
        CREATE TABLE IF NOT EXISTS chat_history (
          id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
          user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
          message TEXT NOT NULL,
          response TEXT NOT NULL,
          context JSONB,
          timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
      `
    })

    // 4. Таблица новостей
    console.log('✅ Создание таблицы news_events...')
    await supabase.rpc('exec_sql', {
      sql: `
        CREATE TABLE IF NOT EXISTS news_events (
          id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
          cluster TEXT NOT NULL,
          title TEXT NOT NULL,
          content TEXT,
          source TEXT NOT NULL,
          published_at TIMESTAMP WITH TIME ZONE NOT NULL,
          price_change_1h DECIMAL(10,4),
          reaction_type TEXT,
          created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
      `
    })

    // 5. Таблица ИИ-анализа
    console.log('✅ Создание таблицы ai_analysis...')
    await supabase.rpc('exec_sql', {
      sql: `
        CREATE TABLE IF NOT EXISTS ai_analysis (
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
        );
      `
    })

    // Включение RLS
    console.log('🔒 Настройка безопасности...')
    await supabase.rpc('exec_sql', {
      sql: `
        ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
        ALTER TABLE trades ENABLE ROW LEVEL SECURITY;
        ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;
        ALTER TABLE news_events ENABLE ROW LEVEL SECURITY;
        ALTER TABLE ai_analysis ENABLE ROW LEVEL SECURITY;
      `
    })

    // Политики безопасности
    console.log('📋 Создание политик безопасности...')
    await supabase.rpc('exec_sql', {
      sql: `
        CREATE POLICY "Users can view own profile" ON profiles
          FOR SELECT USING (auth.uid() = id);

        CREATE POLICY "Users can view own trades" ON trades
          FOR SELECT USING (auth.uid() = user_id);

        CREATE POLICY "Users can view own chat history" ON chat_history
          FOR SELECT USING (auth.uid() = user_id);

        CREATE POLICY "All users can view news events" ON news_events
          FOR SELECT USING (true);

        CREATE POLICY "All users can view AI analysis" ON ai_analysis
          FOR SELECT USING (true);
      `
    })

    console.log('✅ Supabase успешно настроен!')
    console.log('📋 Создано 5 основных таблиц:')
    console.log('  • profiles - профили пользователей')
    console.log('  • trades - торговые сделки')
    console.log('  • chat_history - история чатов')
    console.log('  • news_events - новости')
    console.log('  • ai_analysis - ИИ-анализ')

    console.log('\n🔗 Ссылки:')
    console.log('  • Supabase Dashboard:', supabaseUrl.replace('/rest/v1', ''))
    console.log('  • Table Editor:', `${supabaseUrl.replace('/rest/v1', '')}/project/default/editor`)

    console.log('\n🚀 Следующие шаги:')
    console.log('  1. Проверьте таблицы в Supabase Dashboard')
    console.log('  2. Запустите приложение: npm run dev')
    console.log('  3. Проверьте регистрацию/вход')

  } catch (error) {
    console.error('❌ Ошибка настройки:', error)
    console.log('\n💡 Попробуйте создать таблицы вручную через SQL Editor в Supabase Dashboard')
    process.exit(1)
  }
}

// Запуск настройки
setupSupabase() 