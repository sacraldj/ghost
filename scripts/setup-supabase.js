#!/usr/bin/env node

/**
 * GHOST | Supabase Setup Script
 * Настройка базы данных и создание таблиц
 */

import { createClient } from '@supabase/supabase-js'
import dotenv from 'dotenv'

dotenv.config()

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY

if (!supabaseUrl || !supabaseKey) {
  console.error('❌ Отсутствуют переменные окружения Supabase')
  process.exit(1)
}

const supabase = createClient(supabaseUrl, supabaseKey)

async function setupSupabase() {
  console.log('🚀 Настройка Supabase для GHOST...')

  try {
    // Создание основных таблиц
    console.log('📋 Создание таблиц...')
    
    // 1. Таблица профилей
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

    // 3. Таблица новостей
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

    // 4. Таблица чатов
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

    console.log('✅ Supabase успешно настроен!')

  } catch (error) {
    console.error('❌ Ошибка настройки Supabase:', error)
    process.exit(1)
  }
}

setupSupabase() 