# 🚀 GHOST System - Руководство по установке
**Полная инструкция для установки объединённой торговой системы**

---

## 📋 Системные требования

### **Минимальные требования:**
- **OS:** macOS 10.15+, Ubuntu 18.04+, Windows 10+ (WSL2)
- **RAM:** 4GB (рекомендуется 8GB+)
- **CPU:** 2 cores (рекомендуется 4+ cores)
- **Диск:** 5GB свободного места
- **Интернет:** Стабильное подключение для API

### **Необходимое ПО:**
- **Python 3.8+** 
- **Node.js 18+** 
- **npm или yarn**
- **Redis** (будет установлен автоматически)
- **Git**

---

## 📦 Шаг 1: Распаковка и подготовка

### **1.1 Распаковка архива:**
```bash
# Распакуйте архив в удобную папку
unzip ghost-system.zip
cd ghost-system

# Или если архив .tar.gz
tar -xzf ghost-system.tar.gz
cd ghost-system
```

### **1.2 Проверка структуры:**
```bash
ls -la
# Должны быть папки:
# ├── app/           # Next.js приложение
# ├── components/    # React компоненты  
# ├── config/        # Конфигурационные файлы
# ├── core/          # Python модули торговой системы
# ├── news_engine/   # Модули сбора новостей
# ├── utils/         # Утилиты
# ├── package.json   # Node.js зависимости
# ├── requirements.txt # Python зависимости
# └── README.md
```

---

## 🔧 Шаг 2: Установка зависимостей

### **2.1 Проверка Python:**
```bash
# Проверка версии Python
python3 --version
# Должно быть Python 3.8 или выше

# Если Python не установлен:
# macOS: brew install python3
# Ubuntu: sudo apt update && sudo apt install python3 python3-pip
# Windows: Скачайте с python.org
```

### **2.2 Создание виртуального окружения:**
```bash
# Создание виртуального окружения
python3 -m venv ghost_venv

# Активация окружения
# macOS/Linux:
source ghost_venv/bin/activate

# Windows:
# ghost_venv\Scripts\activate

# Проверка активации (должно показать путь к venv)
which python
```

### **2.3 Установка Python зависимостей:**
```bash
# Убедитесь что venv активирован
source ghost_venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Проверка установки ключевых пакетов
python -c "import asyncio, yaml, psutil, aioredis, telethon; print('✅ Python dependencies OK')"
```

### **2.4 Проверка Node.js:**
```bash
# Проверка версии
node --version
npm --version
# Должно быть Node.js 18+ и npm 8+

# Если Node.js не установлен:
# macOS: brew install node
# Ubuntu: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs
# Windows: Скачайте с nodejs.org
```

### **2.5 Установка Node.js зависимостей:**
```bash
# Установка зависимостей
npm install

# Проверка установки
npm list next react typescript
```

---

## 🔧 Шаг 3: Установка Redis

### **3.1 Установка Redis:**

#### **macOS:**
```bash
# Установка через Homebrew
brew install redis

# Запуск Redis
brew services start redis

# Проверка
redis-cli ping
# Должно ответить: PONG
```

#### **Ubuntu/Debian:**
```bash
# Установка Redis
sudo apt update
sudo apt install redis-server

# Запуск Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Проверка
redis-cli ping
```

#### **Windows (WSL2):**
```bash
# В WSL2 терминале
sudo apt update
sudo apt install redis-server

# Запуск
sudo service redis-server start

# Проверка
redis-cli ping
```

---

## 🔑 Шаг 4: Настройка переменных окружения

### **4.1 Создание файла .env:**
```bash
# Создайте файл .env в корне проекта
cp env.example .env

# Или создайте вручную:
touch .env
```

### **4.2 Заполнение .env файла:**
```env
# ===========================================
# ОСНОВНЫЕ НАСТРОЙКИ СИСТЕМЫ
# ===========================================

# Supabase Configuration (обязательно)
NEXT_PUBLIC_SUPABASE_URL=https://qjdpckwqozsbpskwplfl.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFqZHBja3dxb3pzYnBza3dwbGZsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ1MDUyNTUsImV4cCI6MjA3MDA4MTI1NX0.kY8A88CoBNN2m7EAbJpy1TNfqu9zOY4pFKmvLZ42Lf8
SUPABASE_SECRET_KEY=YOUR_SUPABASE_SECRET_KEY

# Redis Configuration  
REDIS_URL=redis://localhost:6379/1

# ===========================================
# TELEGRAM API (для торговых сигналов)
# ===========================================
# Получить на: https://my.telegram.org/auth
TELEGRAM_API_ID=YOUR_API_ID
TELEGRAM_API_HASH=YOUR_API_HASH
TELEGRAM_PHONE=+1234567890

# Telegram Bot (для уведомлений)
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
TELEGRAM_ADMIN_CHAT_ID=YOUR_CHAT_ID

# ===========================================
# ТОРГОВЫЕ API (опционально)
# ===========================================
# Bybit API
BYBIT_API_KEY=YOUR_BYBIT_API_KEY
BYBIT_API_SECRET=YOUR_BYBIT_API_SECRET

# Binance API (для ценовых данных)
BINANCE_API_KEY=YOUR_BINANCE_API_KEY
BINANCE_API_SECRET=YOUR_BINANCE_API_SECRET

# ===========================================
# NEWS API (для сбора новостей)
# ===========================================
NEWSAPI_KEY=YOUR_NEWSAPI_KEY
CRYPTOCOMPARE_API_KEY=YOUR_CRYPTOCOMPARE_KEY

# ===========================================
# УВЕДОМЛЕНИЯ (опционально)
# ===========================================
SIGNAL_WEBHOOK_URL=YOUR_WEBHOOK_URL
WEBHOOK_SECRET=YOUR_WEBHOOK_SECRET

# ===========================================
# РЕЖИМ РАБОТЫ
# ===========================================
NODE_ENV=development
NEXT_PUBLIC_APP_ENV=development
```

### **4.3 Получение API ключей:**

#### **Telegram API (обязательно для торговых сигналов):**
1. Перейдите на https://my.telegram.org/auth
2. Войдите с вашим номером телефона
3. Перейдите в "API development tools"
4. Создайте приложение и получите `api_id` и `api_hash`

#### **Supabase (уже настроено):**
- URL и ключи уже предоставлены в примере
- Если нужен доступ к админ панели - запросите приглашение

#### **Bybit API (для автоторговли):**
1. Зарегистрируйтесь на Bybit.com
2. Перейдите в Account & Security → API Management  
3. Создайте API ключ с правами на торговлю
4. Добавьте ключи в .env

---

## 🧪 Шаг 5: Тестирование установки

### **5.1 Проверка Python системы:**
```bash
# Активируйте окружение
source ghost_venv/bin/activate

# Запустите тесты
python3 test_orchestrator.py

# Должно показать:
# ✅ All tests passed! System is ready.
```

### **5.2 Проверка Next.js:**
```bash
# Запуск дашборда
npm run dev

# Откройте браузер: http://localhost:3000
# Должен загрузиться дашборд GHOST
```

### **5.3 Проверка Redis:**
```bash
# Проверка подключения
redis-cli ping
# Ответ: PONG

# Проверка через дашборд:
# Откройте http://localhost:3000
# В System Monitor должен быть статус Redis: connected
```

---

## 🚀 Шаг 6: Первый запуск

### **6.1 Запуск в режиме разработки:**

#### **Терминал 1 - Python Orchestrator:**
```bash
# Активация окружения
source ghost_venv/bin/activate

# Установка зависимостей (если не сделано)
./start_orchestrator.sh install

# Запуск оркестратора
./start_orchestrator.sh start

# Проверка статуса
./start_orchestrator.sh status
```

#### **Терминал 2 - Next.js Dashboard:**
```bash
# Запуск дашборда
npm run dev

# Дашборд будет доступен на:
# http://localhost:3000
```

### **6.2 Проверка работоспособности:**

1. **Откройте дашборд:** http://localhost:3000

2. **Проверьте System Monitor:**
   - Должны быть зелёные статусы модулей
   - CPU и память в норме
   - Redis подключён

3. **Проверьте Signals Monitor:**
   - Интерфейс загружается
   - API отвечает (даже если сигналов пока нет)

4. **Проверьте News Feed:**
   - Новости загружаются из базы
   - Критические новости отображаются

---

## ⚙️ Шаг 7: Настройка торговых каналов

### **7.1 Настройка Telegram каналов:**
```bash
# Отредактируйте конфигурацию
nano config/telegram_config.yaml

# Добавьте ваши каналы:
channels:
  - id: "@your_signals_channel"
    name: "Your Trading Channel"
    trader_name: "YourTrader"
    enabled: true
    parser_type: "default"
    priority: 5
```

### **7.2 Первая авторизация Telegram:**
```bash
# Запустите Telegram Listener отдельно для авторизации
source ghost_venv/bin/activate
cd core
python3 telegram_listener.py

# Введите код подтверждения когда запросит
# После успешной авторизации остановите (Ctrl+C)
```

### **7.3 Проверка торговых сигналов:**
1. Запустите полную систему
2. Напишите тестовый сигнал в настроенный канал:
   ```
   🔥 BTCUSDT LONG
   Entry: 42000-42500
   TP1: 44000
   TP2: 45500
   SL: 40500
   Leverage: 20x
   ```
3. Проверьте в дашборде раздел "Trading Signals"

---

## 🔧 Шаг 8: Производственная настройка

### **8.1 Настройка автозапуска (systemd):**
```bash
# Создайте systemd сервис
sudo nano /etc/systemd/system/ghost-orchestrator.service

# Содержимое файла:
[Unit]
Description=GHOST Trading System Orchestrator
After=network.target redis.service

[Service]
Type=forking
User=your_username
WorkingDirectory=/path/to/ghost-system
Environment=PATH=/path/to/ghost-system/ghost_venv/bin
ExecStart=/path/to/ghost-system/start_orchestrator.sh start
ExecStop=/path/to/ghost-system/start_orchestrator.sh stop
Restart=always

[Install]
WantedBy=multi-user.target

# Активация сервиса
sudo systemctl daemon-reload
sudo systemctl enable ghost-orchestrator
sudo systemctl start ghost-orchestrator
```

### **8.2 Настройка процесс-менеджера (PM2):**
```bash
# Установка PM2
npm install -g pm2

# Создание ecosystem файла
nano ecosystem.config.js

# Содержимое:
module.exports = {
  apps: [
    {
      name: 'ghost-dashboard',
      script: 'npm',
      args: 'start',
      cwd: '/path/to/ghost-system',
      env: {
        NODE_ENV: 'production'
      }
    }
  ]
}

# Запуск через PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

---

## 📊 Шаг 9: Мониторинг и логи

### **9.1 Проверка логов:**
```bash
# Логи оркестратора
tail -f logs/orchestrator.log

# Логи Telegram Listener
tail -f logs/telegram_listener.log

# Логи Signal Processor  
tail -f logs/signal_processor.log

# Логи системы
tail -f logs/ghost_system.log
```

### **9.2 Мониторинг через дашборд:**
- **System Monitor:** Статус всех модулей
- **Performance:** CPU, память, диск
- **Trading Signals:** Live мониторинг сигналов
- **News Feed:** Актуальные новости
- **API Status:** Состояние всех подключений

---

## 🚨 Устранение неполадок

### **Частые проблемы:**

#### **1. Python модули не запускаются:**
```bash
# Проверка виртуального окружения
source ghost_venv/bin/activate
which python
pip list

# Переустановка зависимостей
pip install -r requirements.txt --force-reinstall
```

#### **2. Redis не подключается:**
```bash
# Проверка статуса Redis
redis-cli ping

# Перезапуск Redis
# macOS: brew services restart redis
# Linux: sudo systemctl restart redis-server
```

#### **3. Next.js ошибки:**
```bash
# Очистка кэша
rm -rf .next
npm run build

# Переустановка зависимостей
rm -rf node_modules
npm install
```

#### **4. Telegram API ошибки:**
- Проверьте правильность `api_id` и `api_hash`
- Убедитесь что номер телефона указан в международном формате
- Проверьте файл сессии: `core/ghost_listener.session`

#### **5. Supabase подключение:**
- Проверьте URL и ключи в .env
- Проверьте интернет соединение
- Проверьте статус в дашборде Supabase

### **Логи для диагностики:**
```bash
# Полные логи системы
tail -f logs/*.log

# Статус всех процессов
./start_orchestrator.sh status

# Проверка портов
netstat -tulpn | grep -E ":3000|:6379"
```

---

## 🎯 Финальная проверка

### **Чеклист готовности:**

- [ ] **Python 3.8+** установлен и работает
- [ ] **Node.js 18+** установлен
- [ ] **Redis** запущен и отвечает на ping
- [ ] **Виртуальное окружение** создано и активировано
- [ ] **Python зависимости** установлены
- [ ] **Node.js зависимости** установлены
- [ ] **Файл .env** создан и заполнен
- [ ] **Telegram API** настроен (api_id, api_hash)
- [ ] **Тесты системы** прошли успешно
- [ ] **Дашборд** запускается на localhost:3000
- [ ] **System Monitor** показывает зелёные статусы
- [ ] **API endpoints** отвечают
- [ ] **Торговые каналы** настроены
- [ ] **Логи** ведутся корректно

### **Успешный запуск выглядит так:**
```bash
# В терминале:
✅ All tests passed! System is ready.
✅ GHOST Orchestrator started successfully  
✅ Redis connected
✅ Next.js ready on http://localhost:3000

# В браузере (localhost:3000):
✅ Дашборд загружается
✅ System Monitor показывает зелёные статусы
✅ Trading Signals отображается
✅ News Feed работает
```

---

## 📞 Поддержка

### **Если что-то не работает:**

1. **Проверьте логи:** `tail -f logs/*.log`
2. **Запустите тесты:** `python3 test_orchestrator.py`
3. **Проверьте статус:** `./start_orchestrator.sh status`
4. **Перезапустите систему:**
   ```bash
   ./start_orchestrator.sh restart
   npm run dev
   ```

### **Полезные команды:**
```bash
# Остановка всей системы
./start_orchestrator.sh stop
pkill -f "npm run dev"

# Полный перезапуск
./start_orchestrator.sh restart
npm run dev

# Проверка состояния
ps aux | grep -E "python|npm|redis"
```

---

**🎉 Поздравляем! Система GHOST успешно установлена и готова к работе!**

После успешной установки вы сможете:
- Мониторить торговые сигналы в реальном времени
- Отслеживать новости и их влияние на рынок  
- Управлять всей системой через веб-интерфейс
- Автоматизировать торговые решения

*Удачной торговли! 🚀*
