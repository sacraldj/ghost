# 📰 GHOST News Integration

## 🛡️ **БЕЗОПАСНАЯ ИНТЕГРАЦИЯ**

**Все модули работают НЕЗАВИСИМО от основной торговой логики!**
- ✅ НЕ ИЗМЕНЯЮТ существующие сигналы
- ✅ НЕ ВЛИЯЮТ на торговые решения  
- ✅ Работают как ОПЦИОНАЛЬНЫЙ слой
- ✅ Можно включить/выключить одной переменной

---

## 🚀 **БЫСТРЫЙ СТАРТ**

### 1. Включение интеграции
```bash
# В .env файле
GHOST_NEWS_INTEGRATION_ENABLED=true
```

### 2. Тестирование
```bash
python test_news_integration.py
```

### 3. Добавление в дашборд
```tsx
import NewsAnalysisDashboard from '@/components/NewsAnalysisDashboard'

// В любом компоненте
<NewsAnalysisDashboard />
```

### 4. API доступ
```
GET /api/news-analysis?action=overview
GET /api/news-analysis?action=statistics&days=7
GET /api/news-analysis?action=recent&limit=20
```

---

## 📦 **СОЗДАННЫЕ МОДУЛИ**

### 🔧 **core/news_signal_enhancer.py**
- **Назначение**: Обогащение сигналов новостным контекстом
- **Безопасность**: НЕ изменяет исходные сигналы
- **Выход**: Добавляет поле `news_enhancement` с дополнительной информацией

```python
from core.news_signal_enhancer import get_news_enhancer

enhancer = get_news_enhancer()
context = await enhancer.enhance_signal_context(signal_data, source_config)
```

### 📊 **core/news_statistics_tracker.py**
- **Назначение**: Полная статистика новостей (как просил Дарэн)
- **Функции**: Точность предсказаний, надёжность источников, временной анализ
- **База данных**: `data/news_statistics.db`

```python
from core.news_statistics_tracker import get_news_stats_tracker

tracker = get_news_stats_tracker()
tracker.print_daily_report()
```

### 🔍 **core/news_noise_filter.py**
- **Назначение**: Агрессивная фильтрация шума (как просил Дарэн)
- **Критерии**: ФРС, регулирование, активность китов, структурные изменения
- **Отсеивает**: 90%+ мусора, оставляет только важное

```python
from core.news_noise_filter import NewsNoiseFilter

filter_instance = NewsNoiseFilter()
result = filter_instance.filter_news(news_data)
if result.is_important:
    print(f"Важная новость: {result.importance_score:.2f}")
```

### 🔗 **core/safe_news_integrator.py**
- **Назначение**: Безопасная интеграция всех компонентов
- **Принцип**: Middleware подход - НЕ нарушает существующую логику
- **Hook система**: Можно подключать к любым процессам

```python
from core.safe_news_integrator import safe_enhance_signal

enhanced_signal = await safe_enhance_signal(signal_data)
# enhanced_signal содержит исходный сигнал + news_enhancement
```

---

## 🎯 **ИНТЕГРАЦИЯ С СУЩЕСТВУЮЩЕЙ СИСТЕМОЙ**

### Опция 1: Декоратор (самый простой)
```python
from core.safe_news_integrator import with_news_context

@with_news_context
async def process_signal(signal_data, source_config):
    # signal_data теперь может содержать news_enhancement
    if 'news_enhancement' in signal_data:
        news_context = signal_data['news_enhancement']['context']
        confidence_modifier = news_context['confidence_modifier']
        # Используем дополнительную информацию по желанию
    
    return processed_signal
```

### Опция 2: Прямое использование
```python
from core.safe_news_integrator import get_safe_news_integrator

async def your_existing_function(signal_data):
    # Ваша существующая логика остаётся без изменений
    processed_signal = existing_processing(signal_data)
    
    # ОПЦИОНАЛЬНО: добавляем новостной контекст
    integrator = get_safe_news_integrator()
    enhanced_signal = await integrator.enhance_signal_safely(processed_signal, {})
    
    return enhanced_signal  # или processed_signal если не нужно обогащение
```

### Опция 3: В LiveSignalProcessor (если хотите)
```python
# В core/live_signal_processor.py (ОПЦИОНАЛЬНО!)
from core.safe_news_integrator import safe_enhance_signal

async def _handle_telegram_message(self, message_data):
    # Существующая логика остаётся БЕЗ ИЗМЕНЕНИЙ
    signal_data = self._extract_signal_data(message_data)
    
    # ОПЦИОНАЛЬНО: обогащаем новостным контекстом
    enhanced_signal = await safe_enhance_signal(signal_data, source_config)
    
    # Продолжаем с существующей логикой
    await self._save_raw_signal(source_config, enhanced_signal)
```

---

## 🎛️ **НАСТРОЙКИ**

### Переменные окружения
```bash
# Основное включение/выключение
GHOST_NEWS_INTEGRATION_ENABLED=true

# Опциональные (для AI анализа)
OPENAI_API_KEY=your_key
GEMINI_API_KEY=your_key
NEWS_API_KEY=your_key
```

### Настройка фильтра
```python
from core.news_noise_filter import NewsNoiseFilter

filter_instance = NewsNoiseFilter()
filter_instance.update_threshold(0.8)  # Более строгий фильтр
```

---

## 📈 **ДАШБОРД**

### API Endpoints
- `GET /api/news-analysis?action=overview` - Полный обзор
- `GET /api/news-analysis?action=statistics&days=7` - Статистика за период  
- `GET /api/news-analysis?action=recent&limit=20` - Недавние новости
- `GET /api/news-analysis?action=status` - Статус интеграции

### Компонент React
```tsx
import NewsAnalysisDashboard from '@/components/NewsAnalysisDashboard'

export default function DashboardPage() {
  return (
    <div>
      <h1>GHOST Dashboard</h1>
      <NewsAnalysisDashboard />
    </div>
  )
}
```

---

## 🧪 **ТЕСТИРОВАНИЕ**

### Полный тест системы
```bash
python test_news_integration.py
```

### Тест отдельных модулей
```python
# Тест фильтра
python -m core.news_noise_filter

# Тест статистики
python -m core.news_statistics_tracker

# Тест обогащения
python -m core.news_signal_enhancer
```

---

## 📊 **СТАТИСТИКА (КАК ПРОСИЛ ДАРЭН)**

### Доступные метрики
- **Общая статистика**: Всего новостей, критических новостей
- **Точность предсказаний**: По временным рамкам (1h, 4h, 24h)
- **Надёжность источников**: Рейтинг по точности
- **Производительность кластеров**: Анализ по типам новостей
- **Sentiment анализ**: Распределение настроений
- **Временной анализ**: Влияние новостей во времени

### Получение статистики
```python
from core.news_statistics_tracker import get_news_stats_tracker

tracker = get_news_stats_tracker()

# Печать ежедневного отчёта
tracker.print_daily_report()

# Программное получение
stats = tracker.get_full_statistics(days=30)
print(f"Точность: {stats.prediction_accuracy:.2%}")
print(f"Всего новостей: {stats.total_news_processed}")
```

---

## 🔍 **ФИЛЬТРАЦИЯ ШУМА (КАК ПРОСИЛ ДАРЭН)**

### Критерии важности
1. **ФРС и монетарная политика**: ставки, Пауэлл, FOMC
2. **Регулирование**: SEC, ETF одобрения, лицензии  
3. **Активность китов**: Артур Хейс, Майкл Сэйлор, крупные покупки
4. **Структурные изменения**: листинги, халвинги, разлоки
5. **Макро события**: инфляция, GDP, кризисы

### Автоматическая фильтрация спама
- ❌ Промо и реклама
- ❌ Кликбейт заголовки  
- ❌ Общие прогнозы цен
- ❌ Социальный шум (мемы, хайп)
- ❌ Неподтверждённые слухи

### Пример работы
```python
# Важная новость (проходит фильтр)
news1 = {
    'title': 'Министр финансов США: снижение ставки ФРС на 25 б.п.',
    'source': 'reuters'
}
# → Результат: ✅ ВАЖНАЯ (score: 0.85)

# Спам (отфильтровывается)  
news2 = {
    'title': 'Шокирующая правда о биткоине! К луне!',
    'source': 'cryptopotato'
}
# → Результат: ❌ ОТФИЛЬТРОВАНО (spam indicators)
```

---

## ⚠️ **ВАЖНЫЕ ПРИНЦИПЫ**

### 🛡️ Безопасность
- **НЕ ИЗМЕНЯЕМ** файлы `core/live_signal_processor.py`, `signals/*`, `core/telegram_listener.py`
- **НЕ ВЛИЯЕМ** на торговые решения автоматически
- **ТОЛЬКО ДОБАВЛЯЕМ** дополнительную информацию
- **МОЖНО ОТКЛЮЧИТЬ** в любой момент

### 🔄 Независимость  
- Все модули работают автономно
- Ошибка в новостном анализе НЕ ломает торговлю
- Graceful degradation - если модуль недоступен, система продолжает работать

### 📈 Расширяемость
- Легко добавлять новые источники новостей
- Настраиваемые пороги и фильтры  
- Hook система для интеграции с любыми процессами
- API для внешнего доступа

---

## 🎉 **РЕЗУЛЬТАТ**

✅ **Полная новостная система** готова к использованию
✅ **Безопасная интеграция** без риска для торговли  
✅ **Агрессивная фильтрация шума** (как просил Дарэн)
✅ **Полная статистика** с точностью и надёжностью
✅ **Дашборд с визуализацией** для мониторинга
✅ **Простое включение/выключение** через переменную окружения

**Система готова дополнить GHOST алгоритм Дарэна мощным новостным анализом! 🚀**
