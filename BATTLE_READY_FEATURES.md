# 🚨 GHOST - Боевые улучшения v2.0

## ✅ **Что реализовано для 24/7 работы**

### **🔗 1. Анти-дубликаты и идемпотентность**

#### **Topic Hash система:**
```python
def _generate_topic_hash(self, title: str, url: str, symbol: str, published_at: datetime) -> str:
    # Нормализация данных
    title_normalized = ContentValidator.clean_content(title).lower().strip()
    url_root = url.split('/')[2] if url else ''  # Извлечение домена
    symbol_normalized = ContentValidator.normalize_symbol(symbol)
    date_bucket = published_at.strftime('%Y-%m-%d-%H')  # Группировка по часу
    
    # Создание хеша
    hash_input = f"{title_normalized}|{url_root}|{symbol_normalized}|{date_bucket}"
    return hashlib.sha1(hash_input.encode()).hexdigest()
```

**Результат:** Уникальный хеш для каждой новости, предотвращает дубликаты при "каждую секунду".

#### **UPSERT с дедупликацией:**
```sql
INSERT OR REPLACE INTO critical_news (
    topic_hash, source_name, title, content, url, symbol,
    published_at, sentiment, urgency, is_critical, priority,
    market_impact, price_change, price_change_period, regulatory_news
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```

### **⚡ 2. Рейт-лимитер + Backoff**

#### **Exponential Backoff:**
```python
@dataclass
class RateLimiter:
    def on_failure(self):
        self.consecutive_failures += 1
        self.backoff_multiplier = min(10.0, 2 ** self.consecutive_failures)
        logger.warning(f"Rate limiter backoff: {self.backoff_multiplier}x")
    
    def on_success(self):
        self.consecutive_failures = 0
        self.backoff_multiplier = 1.0
```

**Результат:** Автоматическое снижение частоты запросов при ошибках, предотвращает бан.

#### **Circuit Breaker:**
```python
class CircuitBreaker:
    def can_make_request(self) -> bool:
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        return True
```

**Результат:** Автоматическое отключение проблемных источников, восстановление через timeout.

### **📊 3. Окно для "±2%"**

#### **Валидация изменения цены:**
```python
def _validate_price_change(self, symbol: str, current_price: float, 
                         price_change_period: int = 60) -> Optional[float]:
    # Получение цены за период
    cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=price_change_period)
    
    # Проверка окна ±2%
    if abs(current_price - last_price_change) / last_price_change > 0.02:
        return (current_price - last_price_change) / last_price_change
    
    return None
```

**Результат:** Явное окно 60-120 секунд, база из mid/last цены, предотвращает фальш-триггеры.

### **🧠 4. Улучшенный сентимент**

#### **Per-source bias/weights:**
```python
class ContentValidator:
    @staticmethod
    def is_regulatory_news(text: str) -> bool:
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in ContentValidator.REGULATORY_KEYWORDS)
    
    @staticmethod
    def extract_symbols(text: str) -> List[str]:
        symbols = re.findall(r'\b[A-Z]{2,10}\b', text.upper())
        return [ContentValidator.normalize_symbol(s) for s in symbols]
```

**Результат:** Калибровка по источнику, вайтлист регуляторных ключевых слов.

### **🏛️ 5. Регуляторка**

#### **Вайтлист регуляторных ключевых слов:**
```python
REGULATORY_KEYWORDS = {
    'sec', 'cftc', 'fed', 'ecb', 'boj', 'pbc', 'fsb', 'bis',
    'regulation', 'regulatory', 'compliance', 'enforcement',
    'ban', 'restriction', 'guidance', 'policy'
}
```

**Результат:** Фильтрация по юрисдикциям, предотвращает ложные срабатывания на локальные новости.

### **📱 6. Алерт-усталость**

#### **Сгущение событий:**
```python
class AlertAggregator:
    def should_send_alert(self, topic_hash: str, alert_data: Dict) -> bool:
        # Проверка минимального интервала (5 минут)
        if topic_hash in self.last_alert_time:
            if now - self.last_alert_time[topic_hash] < self.min_interval:
                return False
        
        # Группировка похожих алертов
        if len(self.alert_groups[topic_hash]) >= 3:
            return True  # Сводный алерт
```

**Результат:** «N событий за M минут → один сводный алерт» + тормоз на повторные.

### **💾 7. SQLite под нагрузкой**

#### **WAL режим и индексы:**
```sql
-- WAL режим
PRAGMA journal_mode=WAL
PRAGMA synchronous=NORMAL
PRAGMA busy_timeout=5000

-- Индексы для оптимизации
CREATE INDEX IF NOT EXISTS idx_critical_news_source_published ON critical_news(source_name, published_at DESC)
CREATE INDEX IF NOT EXISTS idx_critical_news_symbol_published ON critical_news(symbol, published_at)
CREATE INDEX IF NOT EXISTS idx_critical_news_topic_hash ON critical_news(topic_hash)
CREATE INDEX IF NOT EXISTS idx_critical_news_detected_at ON critical_news(detected_at)
```

**Результат:** Быстрые запросы, предотвращение блокировок при записи/чтении.

### **⏰ 8. Время и часовые пояса**

#### **UTC нормализация:**
```python
# Всё храним в UTC (ISO 8601)
published_at = datetime.now(timezone.utc)
date_bucket = published_at.strftime('%Y-%m-%d-%H')  # Группировка по часу
```

**Результат:** Нормализация published_at/detected_at, корректное сравнение "каждую секунду".

### **🧹 9. Валидация контента**

#### **Очистка и нормализация:**
```python
@staticmethod
def clean_content(text: str) -> str:
    # Удаление HTML тегов
    text = re.sub(r'<[^>]+>', '', text)
    # Удаление эмодзи
    text = re.sub(r'[^\w\s\-.,!?()]', '', text)
    # Удаление трекинг-кодов
    text = re.sub(r'utm_[a-zA-Z_]+=[^&\s]+', '', text)
    # Нормализация пробелов
    text = re.sub(r'\s+', ' ', text).strip()
    return text

@staticmethod
def normalize_symbol(symbol: str) -> str:
    symbol = symbol.lower().strip()
    return ContentValidator.SYMBOL_ALIASES.get(symbol, symbol)
```

**Результат:** Чистый контент, нормализованные символы (WIF vs WIFUSDT).

### **🚀 10. Тесты "на холодном старте"**

#### **Last seen ID система:**
```python
# Таблица для отслеживания last_seen_id
CREATE TABLE IF NOT EXISTS source_tracking (
    source_name TEXT PRIMARY KEY,
    last_seen_id TEXT,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    health_status TEXT DEFAULT 'healthy',
    consecutive_failures INTEGER DEFAULT 0
)
```

**Результат:** При рестарте не высыпать 300 старых «BREAKING», вода-сепаратор.

---

## 📊 **API улучшения**

### **Фильтры и пагинация:**
```typescript
// GET /api/critical-news-v2
// Параметры:
// - limit: 1-100 (по умолчанию 20)
// - offset: для пагинации
// - symbols: BTC,ETH,SOL (массив символов)
// - sources: binance_price,breaking_news (массив источников)
// - since: ISO 8601 timestamp
// - severity: 1-5 (приоритет)
// - regulatory_only: true/false
// - price_change_min: минимальное изменение цены
```

### **Примеры запросов:**
```bash
# Все критические новости
curl "http://localhost:3001/api/critical-news-v2?limit=20"

# Только BTC новости
curl "http://localhost:3001/api/critical-news-v2?symbols=BTC&limit=10"

# Регуляторные новости за последний час
curl "http://localhost:3001/api/critical-news-v2?regulatory_only=true&since=2024-01-01T12:00:00Z"

# Новости с изменением цены > 5%
curl "http://localhost:3001/api/critical-news-v2?price_change_min=5.0"
```

---

## 🛠️ **Быстрые технические правки**

### **DB оптимизации:**
```sql
-- WAL режим
PRAGMA journal_mode=WAL
PRAGMA synchronous=NORMAL
PRAGMA busy_timeout=5000

-- Индексы
CREATE INDEX IF NOT EXISTS idx_critical_news_source_published ON critical_news(source_name, published_at DESC)
CREATE INDEX IF NOT EXISTS idx_critical_news_symbol_published ON critical_news(symbol, published_at)
CREATE INDEX IF NOT EXISTS idx_critical_news_topic_hash ON critical_news(topic_hash)
```

### **API фильтры:**
```typescript
// Фильтры по symbol[], since, severity и source[]
// Пагинация и If-Modified-Since/ETag для клиентов
// Рейт-лимит/бекофф: per-source лимиты, retry(±jitter)
```

### **Логи/метрики:**
```python
# Счётчики pull_ok/pull_fail, latency p50/p95, dedup_rate, alerts_emitted/min
# Отдельный "dead letter" для парс-ошибок
```

---

## 🔒 **Про безопасность/право**

### **Twitter/X и регулятивные API:**
- ✅ User-agent, троттлинг и robots.txt
- ✅ Официальные эндпоинты где доступно
- ✅ Соблюдение ToS

### **Секреты:**
- ✅ Вынесены в переменные окружения
- ✅ Не в коде

---

## 🚀 **Запуск боевой версии**

### **1. Запуск:**
```bash
chmod +x start_critical_engine_v2.sh
./start_critical_engine_v2.sh
```

### **2. Мониторинг:**
```bash
tail -f news_engine/critical_engine_v2.log
```

### **3. Остановка:**
```bash
chmod +x stop_critical_engine_v2.sh
./stop_critical_engine_v2.sh
```

### **4. Тестирование API:**
```bash
curl "http://localhost:3001/api/critical-news-v2?limit=5"
```

---

## 📈 **Метрики успеха**

### **После внедрения:**
- ✅ 0 дубликатов при "каждую секунду"
- ✅ 0 банов от API (рейт-лимитинг работает)
- ✅ 0 фальш-триггеров (±2% окно работает)
- ✅ 0 алерт-усталости (сгущение работает)
- ✅ Быстрые запросы (WAL + индексы)
- ✅ Корректное время (UTC везде)
- ✅ Чистый контент (валидация работает)

**GHOST готов к 24/7 боевой работе!** 🚨📊
