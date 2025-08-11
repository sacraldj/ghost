# 🚀 GHOST News Engine - Настройка

## 📋 Что настроено:

### ✅ **API Endpoints:**
- `GET /api/news` - получение новостей с фильтрацией
- `GET /api/user` - получение пользовательских данных

### ✅ **База данных:**
- SQLite база данных (`ghost_news.db`)
- Автоматическое создание таблиц
- Тестовые данные для демонстрации

### ✅ **News Engine:**
- Упрощенная версия (`simple_news_engine.py`)
- Асинхронный сбор новостей
- Анализ настроений (простой алгоритм)
- Сохранение в базу данных

## 🔧 Что нужно настроить:

### **1. Автоматический запуск News Engine:**

#### **Вариант A: Ручной запуск**
```bash
# Запуск
./start_news_engine.sh

# Остановка
./stop_news_engine.sh
```

#### **Вариант B: Автоматический запуск (macOS)**
```bash
# Копируем plist файл
sudo cp ghost-news-engine.plist ~/Library/LaunchAgents/

# Загружаем сервис
launchctl load ~/Library/LaunchAgents/ghost-news-engine.plist

# Запускаем сервис
launchctl start com.ghost.news-engine
```

#### **Вариант C: Автоматический запуск (Linux)**
```bash
# Создаем systemd сервис
sudo cp ghost-news-engine.service /etc/systemd/system/

# Включаем автозапуск
sudo systemctl enable ghost-news-engine

# Запускаем сервис
sudo systemctl start ghost-news-engine
```

### **2. Настройка API ключей (опционально):**

#### **NewsAPI:**
1. Зарегистрируйтесь на [newsapi.org](https://newsapi.org)
2. Получите API ключ
3. Добавьте в `news_engine_config.yaml`:
```yaml
sources:
  newsapi:
    enabled: true
    api_key: "your-api-key-here"
```

#### **CryptoCompare:**
1. Зарегистрируйтесь на [cryptocompare.com](https://cryptocompare.com)
2. Получите API ключ
3. Добавьте в конфигурацию

### **3. Настройка уведомлений:**

#### **Telegram Bot:**
1. Создайте бота через @BotFather
2. Получите токен и chat_id
3. Добавьте в конфигурацию

#### **Email уведомления:**
1. Настройте SMTP сервер
2. Добавьте учетные данные в конфигурацию

## 🔄 Как работает сбор новостей:

### **Автоматический режим:**
1. **Запуск** - News Engine стартует при загрузке системы
2. **Сбор** - Каждые 5 минут собирает новости из источников
3. **Анализ** - Анализирует настроения с помощью VADER
4. **Сохранение** - Сохраняет в SQLite базу данных
5. **API** - Frontend получает новости через REST API

### **Ручной режим:**
```bash
# Запуск в фоне
nohup python3 news_engine/simple_news_engine.py &

# Просмотр логов
tail -f news_engine/news_engine.log

# Остановка
pkill -f simple_news_engine.py
```

## 📊 Мониторинг:

### **Проверка статуса:**
```bash
# Проверка процесса
ps aux | grep simple_news_engine

# Проверка логов
tail -f news_engine/news_engine.log

# Проверка базы данных
sqlite3 ghost_news.db "SELECT COUNT(*) FROM news_items;"
```

### **API тестирование:**
```bash
# Получить все новости
curl "http://localhost:3001/api/news"

# Получить позитивные новости
curl "http://localhost:3001/api/news?sentiment=positive"

# Получить новости за последний час
curl "http://localhost:3001/api/news?minutes=60"
```

## 🚨 Устранение проблем:

### **News Engine не запускается:**
1. Проверьте Python 3.8+
2. Установите зависимости: `pip3 install aiohttp pyyaml`
3. Проверьте права доступа к файлам

### **API возвращает 404:**
1. Убедитесь, что Next.js сервер запущен
2. Проверьте, что API endpoints созданы
3. Проверьте логи сервера

### **База данных не создается:**
1. Проверьте права на запись в директорию
2. Убедитесь, что sqlite3 установлен
3. Проверьте логи News Engine

## 📈 Расширенная настройка:

### **Добавление новых источников:**
1. Создайте новый клиент в `enhanced_news_engine.py`
2. Добавьте конфигурацию в `news_engine_config.yaml`
3. Перезапустите News Engine

### **Настройка VADER анализа:**
1. Установите NLTK: `pip3 install nltk`
2. Скачайте VADER лексикон: `python3 -c "import nltk; nltk.download('vader_lexicon')"`
3. Используйте полную версию News Engine

### **Интеграция с внешними API:**
1. Добавьте API ключи в `.env.local`
2. Создайте новые API endpoints
3. Обновите frontend компоненты

## ✅ Статус настройки:

- [x] API endpoints созданы
- [x] База данных настроена
- [x] News Engine работает
- [x] Тестовые данные добавлены
- [ ] Автоматический запуск настроен
- [ ] Внешние API ключи добавлены
- [ ] Уведомления настроены

**News Engine готов к работе!** 🚀
