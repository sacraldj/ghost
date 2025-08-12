# 🚀 GHOST - Полное руководство по настройке

## ✅ Что готово

### 1. 📊 Синхронизация трейдов
- ✅ `trades_supabase_sync.py` - готов к запуску
- ✅ Минимальная схема таблицы `trades_min` 
- ✅ API endpoint `/api/supabase-trades`

### 2. 📱 Telegram Listener
- ✅ `telegram_listener.py` - полнофункциональный listener
- ✅ Конфигурация каналов `config/telegram_channels.yaml`
- ✅ API endpoint `/api/telegram-signals`
- ✅ React компонент `TelegramSignals.tsx`

### 3. 🌐 Веб-приложение
- ✅ Next.js 15 с полной настройкой
- ✅ Supabase интеграция
- ✅ API endpoints для всех функций
- ✅ Дашборд с графиками

## 🎯 Следующие шаги

### Шаг 1: Создайте таблицы в Supabase

Перейдите в Supabase SQL Editor и выполните:

```sql
-- Минимальная таблица для трейдов
CREATE TABLE IF NOT EXISTS trades_min (
  trade_id text primary key,
  id text,
  symbol text,
  side text,
  entry_price numeric,
  exit_price numeric,
  pnl numeric,
  roi numeric,
  opened_at timestamptz,
  closed_at timestamptz,
  tp1_hit boolean,
  tp2_hit boolean,
  sl_hit boolean,
  synced_at timestamptz default now()
);

-- Security
ALTER TABLE trades_min ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public read trades_min" ON trades_min FOR SELECT USING (true);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_trades_min_symbol ON trades_min(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_min_opened_at ON trades_min(opened_at);
```

### Шаг 2: Настройте переменные окружения

Создайте `.env.local` с настройками:

```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Telegram (необязательно)
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
```

### Шаг 3: Запустите приложение локально

```bash
npm install
npm run dev
```

Откройте http://localhost:3000

### Шаг 4: Настройка синхронизации на сервере Дарэна

**Ручная установка (поскольку SSH недоступен):**

1. Скопируйте файлы на сервер:
   - `news_engine/trades_supabase_sync.py`
   - `news_engine/requirements.txt`

2. На сервере выполните:

```bash
cd /root/ghost_system_final/ghost_system_final_146

# Создайте venv если нет
python3.10 -m venv venv310

# Активируйте
source venv310/bin/activate

# Установите зависимости
pip install supabase python-dotenv

# Создайте .env файл
cat > .env << 'EOF'
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_key
GHOST_DB_PATH=./ghost.db
SYNC_INTERVAL_SEC=60
SYNC_LOOP=1
EOF

# Запустите синхронизацию
python tools/trades_supabase_sync.py
```

3. Для автоматического запуска добавьте в tmux:

```bash
tmux new-window -t ghost -n sync 'cd /root/ghost_system_final/ghost_system_final_146 && source venv310/bin/activate && python tools/trades_supabase_sync.py'
```

### Шаг 5: Настройка Telegram Listener

1. Получите API ключи на https://my.telegram.org

2. Запустите настройку:

```bash
python scripts/setup_telegram.py
```

3. Настройте каналы в `news_engine/config/telegram_channels.yaml`

4. Запустите listener:

```bash
python news_engine/telegram_listener.py
```

### Шаг 6: Деплой на Vercel

```bash
# Установите Vercel CLI
npm i -g vercel

# Логин
vercel login

# Деплой
vercel --prod

# Добавьте переменные окружения в Vercel Dashboard
```

## 📋 Структура проекта

```
Ghost/
├── app/                          # Next.js приложение
│   ├── api/                      # API endpoints
│   │   ├── supabase-trades/      # Трейды из Supabase
│   │   └── telegram-signals/     # Telegram сигналы
│   ├── components/               # React компоненты
│   │   └── TelegramSignals.tsx   # Компонент Telegram
│   └── dashboard/                # Дашборд
├── news_engine/                  # Python модули
│   ├── trades_supabase_sync.py   # Синхронизация трейдов
│   ├── telegram_listener.py      # Telegram listener
│   ├── config/                   # Конфигурации
│   │   ├── telegram_channels.yaml
│   │   └── telethon.yaml
│   └── output/                   # Логи и данные
│       ├── signals.json
│       └── raw_logbook.json
├── scripts/                      # Вспомогательные скрипты
│   ├── setup_telegram.py
│   └── deploy_sync_to_server.sh
└── env.example                   # Шаблон переменных
```

## 🔧 Тестирование

### Проверка API endpoints:

```bash
# Трейды
curl http://localhost:3000/api/supabase-trades

# Telegram сигналы
curl http://localhost:3000/api/telegram-signals

# Добавить тестовый сигнал
curl -X POST http://localhost:3000/api/telegram-signals \
  -H "Content-Type: application/json" \
  -d '{"text": "BTCUSDT LONG 🚀", "source": "Test Channel"}'
```

### Проверка синхронизации:

```bash
# Локально (с тестовой БД)
GHOST_DB_PATH=./test.db python news_engine/trades_supabase_sync.py

# На сервере
python tools/trades_supabase_sync.py
```

## 🎉 Готово к использованию!

Ваш GHOST система готова:
- 📊 Трейды синхронизируются из базы Дарэна в Supabase
- 📱 Telegram listener отслеживает сигналы из каналов
- 🌐 Веб-дашборд показывает все данные в реальном времени
- 🚀 Готово к деплою на Vercel

## 🆘 Поддержка

При возникновении проблем:
1. Проверьте логи синхронизации
2. Убедитесь, что переменные окружения настроены
3. Проверьте подключение к Supabase
4. Для Telegram - проверьте API ключи и права доступа к каналам
