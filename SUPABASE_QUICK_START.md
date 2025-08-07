# 🚀 Быстрая настройка Supabase для GHOST

## 📋 Шаги (5 минут):

### 1. Создайте проект Supabase
1. Перейдите на [supabase.com](https://supabase.com)
2. Нажмите "New Project"
3. Выберите организацию
4. Введите имя проекта: `ghost-trading`
5. Введите пароль для базы данных
6. Выберите регион (ближайший к вам)
7. Нажмите "Create new project"

### 2. Получите ключи
После создания проекта:
1. Перейдите в **Settings** → **API**
2. Скопируйте:
   - **Project URL** (например: `https://abc123.supabase.co`)
   - **anon public** ключ
   - **service_role** ключ

### 3. Настройте переменные окружения
Создайте файл `.env` в корне проекта:

```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL="https://your-project.supabase.co"
NEXT_PUBLIC_SUPABASE_ANON_KEY="your-anon-key"
SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"

# ChatGPT Server
CHATGPT_SERVER_URL="http://localhost:3001"

# Другие API ключи...
OPENAI_API_KEY="your-openai-key"
GEMINI_API_KEY="your-gemini-key"
```

### 4. Запустите автоматическую настройку
```bash
npm run setup:supabase:complete
```

### 5. Проверьте результат
В Supabase Dashboard → **Table Editor** должны появиться:

✅ **profiles** - профили пользователей  
✅ **trades** - торговые сделки  
✅ **signals** - торговые сигналы  
✅ **news_events** - новости  
✅ **ai_analysis** - ИИ-анализ  
✅ **chat_history** - история чатов  
✅ **event_anomalies** - аномалии  
✅ **market_manipulations** - манипуляции  
✅ **strategies** - стратегии  
✅ **portfolios** - портфели  
✅ **notifications** - уведомления  
✅ **trade_timeline** - временная шкала  
✅ **price_feed** - ценовые данные  
✅ **api_keys** - API ключи  

### 6. Запустите приложение
```bash
npm run dev
```

Откройте http://localhost:3000 и проверьте:
- ✅ Регистрация/вход работает
- ✅ Данные сохраняются в Supabase
- ✅ Чат с ChatGPT работает

## 🔧 Если что-то не работает:

### Проблема: "Table doesn't exist"
**Решение:** Выполните SQL вручную в Supabase SQL Editor:

```sql
-- Создание основных таблиц
CREATE TABLE profiles (
  id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  email TEXT UNIQUE,
  name TEXT,
  avatar TEXT,
  role TEXT DEFAULT 'USER',
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE trades (
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

CREATE TABLE chat_history (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  message TEXT NOT NULL,
  response TEXT NOT NULL,
  context JSONB,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Включение RLS
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;

-- Политики безопасности
CREATE POLICY "Users can view own profile" ON profiles
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can view own trades" ON trades
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can view own chat history" ON chat_history
  FOR SELECT USING (auth.uid() = user_id);
```

### Проблема: "Permission denied"
**Решение:** Проверьте правильность SERVICE_ROLE_KEY

### Проблема: "RLS policy violation"
**Решение:** Убедитесь, что пользователь аутентифицирован

## 🎯 Готово!

После настройки у вас будет:
- ✅ Полная база данных Supabase
- ✅ Интеграция с ChatGPT сервером
- ✅ Готовое приложение GHOST
- ✅ Все таблицы и политики безопасности

**Теперь можно запускать приложение и тестировать!** 🚀 