# 🏗️ Гибридная архитектура GHOST

## 📊 Проблема ресурсов:

### **Supabase лимиты:**
- ❌ 50,000 API запросов/месяц (нужно 109,500)
- ❌ 500MB база данных (может быть недостаточно)
- ❌ Нет реального времени для важных новостей

## 🎯 Решение: Гибридная архитектура

### **1. Локальный News Engine (Python)**
```python
# Локальный сервер для сбора новостей
- SQLite база данных (быстрая, без лимитов)
- Асинхронный сбор из всех источников
- Анализ настроений с VADER
- Фильтрация дубликатов
- Определение важности
```

### **2. Supabase для пользовательских данных**
```sql
-- Только пользовательские данные
- profiles (пользователи)
- trades (сделки)
- portfolios (портфолио)
- user_preferences (настройки)
```

### **3. API Gateway (Next.js)**
```typescript
// Объединение локальных и облачных данных
- /api/news (из локальной SQLite)
- /api/user (из Supabase)
- /api/trades (из Supabase)
- /api/portfolio (из Supabase)
```

## 📈 Оптимизированная стратегия:

### **Этап 1: Локальный сбор (Python)**
```bash
# Запуск локального News Engine
python3 news_engine/optimized_news_strategy.py

# Результат: SQLite база с новостями
- 10,000+ новостей/день
- Анализ настроений
- Фильтрация дубликатов
- Определение важности
```

### **Этап 2: API Gateway (Next.js)**
```typescript
// Объединение данных
const news = await getLocalNews()      // SQLite
const user = await getSupabaseUser()   // Supabase
const trades = await getSupabaseTrades() // Supabase

return { news, user, trades }
```

### **Этап 3: Real-time уведомления**
```typescript
// WebSocket для важных новостей
const importantNews = await getImportantNews()
if (importantNews.length > 0) {
  notifyUsers(importantNews)
}
```

## 💰 Стоимость ресурсов:

### **Локальные ресурсы:**
- **CPU**: 1-2 ядра (непрерывная работа)
- **RAM**: 512MB-1GB
- **Диск**: 1-5GB (SQLite + логи)
- **Сеть**: 10-50MB/час

### **Supabase (только пользователи):**
- **API запросы**: ~1,000/месяц (вместо 109,500)
- **База данных**: ~50MB (вместо 500MB)
- **Realtime**: 2 канала (достаточно)

## 🚀 Реализация:

### **1. Локальный News Engine:**
```bash
# Автозапуск при старте системы
./start_news_engine.sh

# Мониторинг
tail -f news_engine/news_engine.log

# Остановка
./stop_news_engine.sh
```

### **2. API Endpoints:**
```typescript
// app/api/news/route.ts
import { getLocalNews } from '@/lib/news-engine'
import { getSupabaseUser } from '@/lib/supabase'

export async function GET() {
  const news = await getLocalNews()
  const user = await getSupabaseUser()
  
  return NextResponse.json({ news, user })
}
```

### **3. Real-time уведомления:**
```typescript
// WebSocket для важных новостей
const ws = new WebSocket('ws://localhost:3001/ws')
ws.onmessage = (event) => {
  const importantNews = JSON.parse(event.data)
  showNotification(importantNews)
}
```

## 📊 Мониторинг производительности:

### **Метрики локального News Engine:**
```sql
-- Проверка производительности
SELECT 
  source_name,
  COUNT(*) as news_count,
  AVG(sentiment) as avg_sentiment,
  COUNT(CASE WHEN is_important = 1 THEN 1 END) as important_count
FROM news_items 
WHERE created_at > datetime('now', '-24 hours')
GROUP BY source_name
ORDER BY news_count DESC;
```

### **Метрики Supabase:**
```sql
-- Использование ресурсов
SELECT 
  table_name,
  pg_size_pretty(pg_total_relation_size(table_name)) as size
FROM information_schema.tables 
WHERE table_schema = 'public';
```

## 🎯 Преимущества гибридной архитектуры:

### **✅ Экономия ресурсов:**
- Supabase: 1,000 запросов/месяц (вместо 109,500)
- База данных: 50MB (вместо 500MB+)
- Стоимость: $0/месяц (вместо $25+/месяц)

### **✅ Производительность:**
- Локальный сбор: мгновенный доступ
- SQLite: быстрые запросы
- Асинхронность: параллельная обработка

### **✅ Масштабируемость:**
- Легко добавить новые источники
- Настройка интервалов по приоритету
- Адаптивная нагрузка

### **✅ Надежность:**
- Локальный контроль над данными
- Резервное копирование SQLite
- Независимость от облачных лимитов

## 🚀 План внедрения:

### **Неделя 1: Локальный News Engine**
- [x] Оптимизированная стратегия сбора
- [x] Разные интервалы по источникам
- [x] Анализ настроений с VADER
- [x] Автозапуск и мониторинг

### **Неделя 2: API Gateway**
- [x] Объединение локальных и облачных данных
- [x] Оптимизация запросов
- [x] Кэширование результатов

### **Неделя 3: Real-time уведомления**
- [ ] WebSocket для важных новостей
- [ ] Push уведомления
- [ ] Telegram бот

### **Неделя 4: Мониторинг и оптимизация**
- [ ] Метрики производительности
- [ ] Автоматическое масштабирование
- [ ] Резервное копирование

**Гибридная архитектура решает все проблемы с ресурсами!** 🎯
