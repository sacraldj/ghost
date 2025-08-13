# 🔥 GHOST Telegram Setup - Подключение к реальным каналам

## 📋 **Что сделано:**

### ✅ **1. Архитектура системы Дарена интегрирована:**
- **Signal Router** - умный маршрутизатор сигналов
- **Crypto Hub Parser** - для формата `Longing #SUI Here`
- **2Trade Parser** - для формата `PAIR: BTC DIRECTION: LONG`
- **Adaptive Parser** - fallback для любых форматов
- **Telegram Listener** - для сбора из каналов

### ✅ **2. Real Data Integration:**
- **API `/api/signals/collect`** - для сохранения сигналов
- **API `/api/trader-observation`** - с реальной статистикой
- **Supabase интеграция** - все таблицы подключены
- **Real-time updates** - live данные вместо mock

---

## 🚀 **Настройка Telegram API:**

### **Шаг 1: Получить API ключи**
1. Зайди на https://my.telegram.org/apps
2. Войди со своим номером телефона
3. Создай новое приложение:
   - **App title**: `GHOST System`
   - **Short name**: `ghost`
   - **Platform**: `Desktop`
4. Получи:
   - **API ID** (число)
   - **API Hash** (строка)

### **Шаг 2: Добавить в .env.local**
```bash
# Telegram API
TELEGRAM_API_ID="твой_api_id"
TELEGRAM_API_HASH="твой_api_hash"
TELEGRAM_PHONE="+твой_номер_телефона"
```

### **Шаг 3: Настроить каналы**
Отредактируй файл `config/telegram_channels.json`:

```json
{
  "channels": [
    {
      "channel_id": "ID_канала_из_примера",
      "channel_name": "Crypto Hub VIP",
      "trader_id": "crypto_hub_vip",
      "is_active": true,
      "keywords_filter": ["longing", "entry:", "targets:"],
      "exclude_keywords": ["test", "admin"]
    }
  ]
}
```

### **Шаг 4: Получить ID каналов**
Запусти скрипт для получения ID:
```bash
cd /Users/alexandr/Desktop/CODeAPPs/Ghost
python3 scripts/get_channel_ids.py
```

---

## 📊 **Архитектура данных:**

### **signals_raw** (сырые сигналы):
```sql
- raw_id (PK)
- trader_id 
- source_msg_id
- posted_at
- text
- meta (JSON)
- processed (boolean)
```

### **signals_parsed** (обработанные):
```sql
- signal_id (PK)
- trader_id
- symbol (BTC, ETH, etc.)
- side (LONG, SHORT)
- entry, tp1, tp2, tp3, sl
- confidence, is_valid
- checksum (анти-дубликаты)
```

### **signal_outcomes** (результаты):
```sql
- signal_id (PK)
- final_result (TP1_ONLY, TP2_FULL, SL, etc.)
- pnl_sim, roi_sim
- tp1_hit_at, tp2_hit_at, sl_hit_at
```

---

## 🔄 **Поток данных:**

```
Telegram Канал
    ↓
Telegram Listener (фильтры)
    ↓
Signal Router (определяет парсер)
    ↓
Специфичный Parser (Crypto Hub / 2Trade)
    ↓
API /signals/collect (сохранение)
    ↓
Supabase (signals_raw, signals_parsed)
    ↓
Dashboard (статистика реального времени)
```

---

## 🧪 **Тестирование:**

### **1. Тест парсеров:**
```bash
cd /Users/alexandr/Desktop/CODeAPPs/Ghost
python3 signals/crypto_hub_parser.py
python3 signals/parser_2trade.py
```

### **2. Тест роутера:**
```bash
python3 core/signal_router.py
```

### **3. Тест нормализатора:**
```bash
python3 parser/signal_normalizer.py
```

---

## 📱 **Примеры форматов сигналов:**

### **Crypto Hub VIP:**
```
Longing #SUI Here
Long (5x - 10x)
Entry: $3.89 - $3.70
Reason: Chart looks bullish
Targets: $4.0500, $4.2000, $4.3000
Stoploss: $3.4997
```

### **2Trade:**
```
PAIR: BTC
DIRECTION: LONG
ENTRY: $43000 - $43500
TP1: $45000
TP2: $46500
SL: $41500
LEVERAGE: 10X
```

---

## ⚡ **Запуск системы:**

### **1. Запуск Telegram Listener:**
```bash
cd /Users/alexandr/Desktop/CODeAPPs/Ghost
python3 scripts/start_telegram_listener.py
```

### **2. Мониторинг через Dashboard:**
- Открой http://localhost:3000/dashboard
- Вкладка **"Trader Signals"**
- Смотри реальную статистику

### **3. API для проверки:**
```bash
# Статистика сигналов
curl http://localhost:3000/api/signals/collect

# Список трейдеров
curl http://localhost:3000/api/trader-observation
```

---

## 🎯 **Следующие шаги:**

1. **Получи Telegram API** ключи
2. **Найди ID каналов** для мониторинга  
3. **Настрой config/telegram_channels.json**
4. **Запусти Telegram Listener**
5. **Проверь Dashboard** - должны появляться реальные сигналы!

**Система готова собирать РЕАЛЬНЫЕ данные! 🚀**

---

## 🔧 **Troubleshooting:**

### **Ошибка авторизации Telegram:**
- Проверь API_ID и API_HASH
- Убедись что номер телефона правильный
- Удали файл `ghost_session.session` и перезапусти

### **Сигналы не парсятся:**
- Проверь логи в `logs/telegram_listener.log`
- Убедись что `keywords_filter` настроены правильно
- Проверь что канал активен в конфиге

### **Dashboard показывает mock данные:**
- Убедись что в Supabase есть таблицы
- Проверь API `/api/trader-observation` напрямую
- Посмотри `data_source: 'real'` в ответе API

**Все готово для РЕАЛЬНОГО сбора данных трейдеров! 🎯**
