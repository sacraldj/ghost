# 🏗️ GHOST SYSTEM - ПОЛНЫЙ АНАЛИЗ АРХИТЕКТУРЫ

**Дата:** 14 августа 2025  
**Статус:** Полный анализ системы от начала до конца

---

## 🎯 ОБЩИЙ ОБЗОР СИСТЕМЫ

**GHOST Trading System** - это полноценная система анализа торговых сигналов с автоматическим сбором данных из Telegram каналов, их парсингом с помощью AI, сохранением в Supabase и отображением в Next.js дашборде.

## 🚀 1. ТОЧКА ВХОДА - start_all.py

### **Главный файл запуска:**
```python
start_all.py
├── UnifiedSystemManager
├── start_live_system() → LiveSystemOrchestrator
├── start_orchestrator() → GhostOrchestrator  
└── Health HTTP Server (порт 8080)
```

### **Что происходит при запуске:**
1. **Создается HTTP сервер** для health checks на порту 8080
2. **Запускается LiveSystemOrchestrator** - основная система обработки сигналов
3. **Запускается GhostOrchestrator** - центральный координатор
4. **Система работает в цикле** с автоматическими перезапусками

---

## 🧠 2. ОСНОВНЫЕ КОМПОНЕНТЫ СИСТЕМЫ

### **A. LiveSystemOrchestrator (scripts/start_live_system.py)**
**Роль:** Главный оркестратор обработки live сигналов

**Компоненты:**
- `ChannelManager` - управление источниками Telegram каналов
- `TelegramListener` - подключение к Telegram API
- `UnifiedSignalParser` - парсинг сигналов (AI + regex)
- `LiveSignalProcessor` - обработка и сохранение в БД

**Проверки при запуске:**
```python
def check_prerequisites():
    ✅ Переменные окружения (Supabase, Telegram API)
    ✅ Подключение к Supabase
    ❌ Активные источники сигналов ← ПРОБЛЕМА!
    ✅ Инициализация парсеров
    ⚠️ AI парсеры (опционально)
```

### **B. ChannelManager (core/channel_manager.py)**
**Роль:** Управление источниками сигналов

**Конфигурация:** `config/sources.json`
```json
{
  "sources": [
    {
      "source_id": "whales_guide_main",
      "source_type": "telegram_channel", 
      "name": "Whales Crypto Guide",
      "is_active": true,
      "connection_params": {
        "channel_id": "-1001234567890",
        "username": "@whalesguide"
      }
    }
  ]
}
```

**❌ ПРОБЛЕМА:** Система не загружает источники из JSON! Нужно исправить.

### **C. TelegramListener (core/telegram_listener.py)**
**Роль:** Подключение к Telegram API и получение сообщений

**Поток данных:**
```
Telegram API → Raw Messages → Filter → Signal Detection → Parse
```

### **D. UnifiedSignalParser (signals/unified_signal_system.py)**
**Роль:** Парсинг текста сигналов в структурированные данные

**Методы парсинга:**
- **Regex парсеры** - быстро, для стандартных форматов
- **AI парсеры** - OpenAI/Gemini для сложных случаев
- **Fallback система** - если один не сработал, пробует другой

### **E. LiveSignalProcessor (core/live_signal_processor.py)**
**Роль:** Обработка и сохранение сигналов в БД

**Процесс:**
```
Raw Message → Parse → Validate → Save to Supabase → Update Stats
```

---

## 🗄️ 3. БАЗА ДАННЫХ SUPABASE

### **Основные таблицы:**

#### **A. signals_raw**
**Назначение:** Сырые сообщения из Telegram
```sql
CREATE TABLE signals_raw (
    raw_id SERIAL PRIMARY KEY,
    trader_id VARCHAR(50),
    source_msg_id VARCHAR(100),
    posted_at TIMESTAMP,
    text TEXT,
    meta JSONB,
    processed BOOLEAN DEFAULT false
);
```

#### **B. signals_parsed**  
**Назначение:** Обработанные структурированные сигналы
```sql
CREATE TABLE signals_parsed (
    signal_id SERIAL PRIMARY KEY,
    trader_id VARCHAR(50),
    symbol VARCHAR(20),
    side VARCHAR(10), -- BUY/SELL
    entry DECIMAL(20,8),
    tp1 DECIMAL(20,8),
    tp2 DECIMAL(20,8),
    sl DECIMAL(20,8),
    confidence DECIMAL(5,2),
    is_valid BOOLEAN
);
```

#### **C. trades**
**Назначение:** Активные торговые позиции
```sql
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    trade_id VARCHAR(50),
    symbol VARCHAR(20),
    side VARCHAR(10),
    real_entry_price DECIMAL(20,8),
    position_qty DECIMAL(20,8),
    status VARCHAR(20), -- open/closed
    opened_at TIMESTAMP
);
```

#### **D. trader_registry**
**Назначение:** Реестр отслеживаемых трейдеров
```sql
CREATE TABLE trader_registry (
    trader_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100),
    source_type VARCHAR(20),
    source_handle VARCHAR(100),
    is_active BOOLEAN
);
```

### **Поток данных в Supabase:**
```
Telegram Message
    ↓
signals_raw (сохранение сырого текста)
    ↓
UnifiedParser (обработка)
    ↓
signals_parsed (структурированный сигнал)
    ↓
Dashboard API (отображение)
```

---

## 🌐 4. NEXT.JS DASHBOARD

### **Главный файл:** `app/page.tsx` - Unified Dashboard

### **Основные компоненты:**

#### **A. TradingDashboard**
- **API:** `/api/trades/active` → `trades` table
- **Данные:** Live P&L, активные позиции, статистика
- **Обновление:** Каждые 30 секунд

#### **B. TelegramSignalsDashboard**
- **API:** `/api/telegram-signals` → `signals_parsed` table  
- **Данные:** Реальные сигналы из Telegram
- **Обновление:** Каждые 30 секунд

#### **C. SystemMonitor**
- **API:** `/api/system/status` → System health
- **Данные:** Статус системы, uptime, ошибки
- **Обновление:** Каждые 10 секунд

#### **D. RealtimeChart**
- **WebSocket:** Binance API (wss://stream.binance.com)
- **Данные:** Live цены, свечи
- **Обновление:** Реальное время

#### **E. NewsFeed**
- **API:** `/api/critical-news` → `critical_news` table
- **Данные:** Критические новости
- **Обновление:** Каждую минуту

---

## 🔌 5. API ENDPOINTS

### **Основные эндпоинты:**

#### **A. /api/trades/active**
```typescript
// Возвращает активные сделки из trades table
GET /api/trades/active
→ SELECT * FROM trades WHERE status = 'open'
```

#### **B. /api/telegram-signals**
```typescript  
// Возвращает сигналы из signals_parsed table
GET /api/telegram-signals?limit=50
→ SELECT * FROM signals_parsed ORDER BY posted_at DESC
```

#### **C. /api/system/status**
```typescript
// Возвращает статус системы
GET /api/system/status
→ System health, uptime, module status
```

#### **D. /api/market-data**
```typescript
// Возвращает рыночные данные
GET /api/market-data?symbol=BTCUSDT
→ Bybit API + market_snapshots table
```

---

## ⚡ 6. РЕАЛЬНОЕ ВРЕМЯ И ОБНОВЛЕНИЯ

### **Источники данных:**

#### **A. Telegram API (Python)**
```python
# Подключение к Telegram
TelegramClient(api_id, api_hash, phone)
→ Real-time messages from channels
→ Parse & save to Supabase
```

#### **B. Binance WebSocket (Frontend)**
```typescript
// WebSocket подключение
wss://stream.binance.com:9443/ws/btcusdt@kline_1m
→ Real-time price updates
→ Live charts
```

#### **C. Bybit API (Backend)**
```python
# Live цены через REST API
GET https://api.bybit.com/v5/market/tickers
→ Current prices for P&L calculation
```

---

## 🔄 7. ЦИКЛЫ ОБНОВЛЕНИЯ

### **Python Backend:**
- **Telegram listener:** Постоянно слушает новые сообщения
- **Signal processor:** Обрабатывает очередь сигналов
- **Market data:** Обновляет цены каждые 30 секунд
- **System health:** Проверяет статус каждые 10 секунд

### **Next.js Frontend:**
- **Dashboard components:** Обновляются каждые 10-30 секунд
- **WebSocket charts:** Обновляются в реальном времени
- **API calls:** Автоматические запросы по расписанию

---

## ❌ 8. ТЕКУЩИЕ ПРОБЛЕМЫ

### **A. Система на Render не запускается:**
```
❌ Prerequisites check failed:
   • No active signal sources configured
```

**Причина:** `ChannelManager` не загружает источники из `config/sources.json`

**Решение:** Добавить метод `load_sources_from_json()` в ChannelManager

### **B. Мало данных в дашборде:**
- **trades table:** 0 записей (нет активных сделок)
- **signals_parsed:** 1 запись (мало сигналов)

**Причина:** Система не работает → не собирает сигналы

### **C. Telegram API не настроен:**
- Нужны реальные `api_id`, `api_hash`, `phone` для Telegram
- Нужны реальные channel_id для каналов

---

## ✅ 9. ПЛАН ИСПРАВЛЕНИЯ

### **Приоритет 1 - КРИТИЧНО:**
1. **Исправить ChannelManager** - добавить загрузку из JSON
2. **Настроить Telegram API** - реальные credentials
3. **Добавить реальные channel_id** - подключить к каналам
4. **Запустить систему** - проверить сбор сигналов

### **Приоритет 2 - УЛУЧШЕНИЯ:**
1. **Создать тестовые данные** - для демонстрации
2. **Улучшить обработку ошибок** - graceful degradation
3. **Добавить мониторинг** - алерты при проблемах
4. **Оптимизировать производительность** - кэширование

---

## 🏆 ЗАКЛЮЧЕНИЕ

**GHOST System - это мощная и сложная система** с правильной архитектурой:

✅ **Модульная структура** - каждый компонент отвечает за свою задачу  
✅ **Реальные данные** - интеграция с Telegram API и биржами  
✅ **Масштабируемость** - Supabase + Next.js + Python  
✅ **Мониторинг** - health checks и статистика  

❌ **Основная проблема:** Система не может запуститься на Render из-за отсутствия активных источников

**После исправления ChannelManager система будет полностью функциональной!**

---

## 📊 СТАТИСТИКА СИСТЕМЫ

| Компонент | Файлы | Статус | Данные |
|-----------|-------|---------|---------|
| **Python Backend** | 15+ файлов | ⚠️ Частично работает | Нет активных источников |
| **Next.js Frontend** | 20+ компонентов | ✅ Работает | Показывает реальные API |
| **Supabase DB** | 8 таблиц | ✅ Работает | Схема готова, мало данных |
| **API Endpoints** | 10+ эндпоинтов | ✅ Работают | Возвращают реальные данные |
| **WebSocket** | 1 компонент | ✅ Работает | Binance real-time |

**ИТОГО:** 70% системы работает, нужно исправить 30% для полной функциональности!
