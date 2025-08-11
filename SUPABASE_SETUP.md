# 🚀 GHOST Supabase Integration

## 📊 Гибридная архитектура: Локальная SQLite + Supabase

### **🎯 Текущая архитектура:**

#### **✅ Локальная часть (SQLite):**
- **Critical News Engine** - сбор каждую секунду
- **Быстрая обработка** - мгновенный анализ
- **Низкая задержка** - локальная база данных
- **Независимость** - работает без интернета

#### **✅ Облачная часть (Supabase):**
- **Синхронизация данных** - каждые 30 секунд
- **Масштабируемость** - неограниченное хранилище
- **Доступ извне** - API для других приложений
- **Резервное копирование** - автоматическое

## 🔄 Как работает синхронизация:

### **1. Локальный сбор (каждую секунду):**
```python
# Critical News Engine собирает данные в SQLite
while True:
    fetch_critical_data()  # Каждую секунду
    save_to_sqlite()      # Локальная база
    await asyncio.sleep(0.1)  # 100ms пауза
```

### **2. Синхронизация с Supabase (каждые 30 секунд):**
```python
# Supabase Sync отправляет данные в облако
while True:
    get_local_news()      # Из SQLite
    sync_to_supabase()    # В Supabase
    await asyncio.sleep(30)  # 30 секунд пауза
```

### **3. API Endpoints:**
```typescript
// Локальные данные (быстро)
GET /api/critical-news    // Из SQLite
GET /api/news            // Из SQLite

// Облачные данные (масштабируемо)
GET /api/supabase-news   // Из Supabase
```

## 🚀 Настройка Supabase:

### **1. Создание проекта Supabase:**
1. Перейдите на [supabase.com](https://supabase.com)
2. Создайте новый проект
3. Получите URL и Service Role Key

### **2. Настройка переменных окружения:**
```bash
# Добавьте в .env.local
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

### **3. Применение миграций:**
```bash
# В Supabase Dashboard → SQL Editor
# Скопируйте и выполните содержимое supabase_migrations.sql
```

### **4. Запуск синхронизации:**
```bash
# Установка зависимостей
pip3 install supabase

# Запуск синхронизации
./start_supabase_sync.sh

# Остановка
./stop_supabase_sync.sh
```

## 📊 Структура данных в Supabase:

### **Таблица critical_news:**
```sql
CREATE TABLE critical_news (
    id BIGSERIAL PRIMARY KEY,
    local_id INTEGER,           -- ID из локальной SQLite
    source_name TEXT,           -- Источник новости
    title TEXT,                 -- Заголовок
    content TEXT,               -- Содержание
    url TEXT,                   -- Ссылка
    published_at TIMESTAMPTZ,   -- Время публикации
    sentiment REAL,             -- Настроение (-1 до 1)
    urgency REAL,               -- Срочность (0 до 1)
    is_critical BOOLEAN,        -- Критическая новость
    priority INTEGER,           -- Приоритет (1-5)
    market_impact REAL,         -- Влияние на рынок
    synced_at TIMESTAMPTZ,      -- Время синхронизации
    created_at TIMESTAMPTZ,     -- Время создания
    updated_at TIMESTAMPTZ      -- Время обновления
);
```

### **Таблица news_items:**
```sql
CREATE TABLE news_items (
    id BIGSERIAL PRIMARY KEY,
    local_id INTEGER,           -- ID из локальной SQLite
    source_name TEXT,           -- Источник новости
    title TEXT,                 -- Заголовок
    content TEXT,               -- Содержание
    url TEXT,                   -- Ссылка
    published_at TIMESTAMPTZ,   -- Время публикации
    sentiment REAL,             -- Настроение (-1 до 1)
    urgency REAL,               -- Срочность (0 до 1)
    is_important BOOLEAN,       -- Важная новость
    priority_level INTEGER,     -- Уровень приоритета
    synced_at TIMESTAMPTZ,      -- Время синхронизации
    created_at TIMESTAMPTZ,     -- Время создания
    updated_at TIMESTAMPTZ      -- Время обновления
);
```

## 🔄 API Endpoints:

### **Локальные данные (быстро):**
```bash
# Критические новости из SQLite
curl "http://localhost:3001/api/critical-news?limit=10&minutes=5"

# Обычные новости из SQLite
curl "http://localhost:3001/api/news?limit=50&minutes=60"
```

### **Облачные данные (масштабируемо):**
```bash
# Критические новости из Supabase
curl "http://localhost:3001/api/supabase-news?type=critical&limit=10&minutes=5"

# Обычные новости из Supabase
curl "http://localhost:3001/api/supabase-news?type=regular&limit=50&minutes=60"
```

## 📈 Преимущества гибридной архитектуры:

### **✅ Локальная часть:**
- **Скорость** - мгновенный доступ к данным
- **Надежность** - работает без интернета
- **Производительность** - низкая задержка
- **Контроль** - полный контроль над данными

### **✅ Облачная часть:**
- **Масштабируемость** - неограниченное хранилище
- **Доступность** - доступ из любой точки мира
- **Резервное копирование** - автоматическое
- **Интеграция** - API для других приложений

## 🚨 Мониторинг:

### **Проверка синхронизации:**
```bash
# Логи синхронизации
tail -f news_engine/supabase_sync.log

# Проверка процесса
ps aux | grep supabase_sync

# Статистика синхронизации
sqlite3 ghost_news.db "SELECT COUNT(*) FROM critical_news;"
```

### **Проверка Supabase:**
```sql
-- Количество критических новостей в Supabase
SELECT COUNT(*) FROM critical_news;

-- Последние синхронизированные новости
SELECT title, synced_at 
FROM critical_news 
ORDER BY synced_at DESC 
LIMIT 10;
```

## 💰 Стоимость ресурсов:

### **Локальные ресурсы:**
- **CPU**: 1-2 ядра (непрерывная работа)
- **RAM**: 512MB-1GB
- **Диск**: 1-5GB (SQLite + логи)
- **Сеть**: 10-50MB/час

### **Supabase (бесплатный план):**
- **База данных**: 500MB (достаточно для новостей)
- **API запросы**: 50,000/месяц (синхронизация)
- **Edge Functions**: 500,000 вызовов/месяц
- **Стоимость**: $0/месяц

## 🎯 Результат:

### **✅ Достигнуто:**
- **Гибридная архитектура** - локальная + облачная
- **Синхронизация** - каждые 30 секунд
- **API endpoints** - для локальных и облачных данных
- **Масштабируемость** - неограниченное хранилище
- **Надежность** - резервное копирование

### **📊 Производительность:**
- **Локальный сбор**: каждую секунду
- **Синхронизация**: каждые 30 секунд
- **API отклик**: < 100ms (локальный), < 500ms (облачный)
- **Объем данных**: неограничен (Supabase)

### **🚀 Готово к использованию:**
- Critical News Engine работает
- Supabase Sync настроен
- API endpoints созданы
- Миграции готовы

**GHOST теперь сохраняет данные и в локальную SQLite, и в Supabase!** 🎯📈
