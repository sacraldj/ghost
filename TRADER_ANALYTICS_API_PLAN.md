# 📊 МАКСИМАЛЬНАЯ АНАЛИТИКА ТРЕЙДЕРОВ - API ПЛАН

## 🎯 НОВЫЕ API ENDPOINTS

### **1. 👤 ДЕТАЛЬНОЕ ДОСЬЕ ТРЕЙДЕРА**
```
GET /api/traders/[traderId]/profile
```
**Возвращает:**
- Полную статистику за все время
- Рейтинги и оценки (Trust Index, Grade A-D)
- Поведенческие паттерны
- Heatmap активности по времени
- Топ сигналы (лучшие/худшие)

### **2. 📈 ДИНАМИЧЕСКАЯ СТАТИСТИКА**
```
GET /api/traders/[traderId]/metrics?period=30d&granularity=daily
```
**Параметры:**
- `period`: 7d, 30d, 90d, 1y, all
- `granularity`: daily, weekly, monthly
- `metrics`: roi,winrate,rrr,streaks

**Возвращает временные ряды для графиков**

### **3. 🔍 ПОВЕДЕНЧЕСКИЙ АНАЛИЗ**
```
GET /api/traders/[traderId]/behavior
```
**Возвращает:**
- Паттерны дублирования сигналов
- Противоречивые сигналы (LONG vs SHORT)
- Частотные аномалии
- Копипаст с других трейдеров

### **4. 🏆 РЕЙТИНГИ И СРАВНЕНИЯ**
```
GET /api/traders/rankings?period=monthly&sortBy=composite_score
```
**Возвращает:**
- Топ-10 трейдеров по категориям
- Сравнительные метрики
- Динамику рейтингов
- Кластерный анализ

### **5. 🎨 HEATMAP ДАННЫЕ**
```
GET /api/traders/[traderId]/time-patterns
```
**Возвращает:**
- 24x7 матрицу активности
- ROI по часам/дням недели  
- Оптимальное время публикации
- Сезонные паттерны

### **6. ❌ АНАЛИЗ ОШИБОК**
```
GET /api/traders/[traderId]/errors?category=logic&period=30d
```
**Возвращает:**
- Классификацию ошибок
- Частоту по типам
- Динамику улучшения/ухудшения
- Рекомендации

### **7. 📊 КРОСС-АНАЛИТИКА**
```
GET /api/analytics/cross-trader?compare=[trader1,trader2,trader3]
```
**Возвращает:**
- Сравнительную таблицу
- Корреляцию результатов  
- Уникальные преимущества каждого
- Портфельную оптимизацию

---

## 🔄 АВТОМАТИЧЕСКИЕ ВЫЧИСЛЕНИЯ

### **DAILY JOBS (cron):**

#### **1. Обновление ежедневной статистики**
```python
# scripts/update_daily_stats.py
def update_trader_daily_stats():
    """Вычисляет метрики за прошедший день для всех трейдеров"""
    - Подсчет сигналов, исходов
    - Расчет ROI, PnL, RRR
    - Определение стриков
    - Обновление trader_stats_daily
```

#### **2. Вычисление поведенческих паттернов**  
```python
# scripts/analyze_behavior.py
def detect_behavioral_patterns():
    """Анализирует поведение трейдеров"""
    - Поиск дубликатов сигналов
    - Обнаружение противоречий
    - Анализ частоты публикации
    - Кластеризация по стилю
```

#### **3. Обновление рейтингов**
```python  
# scripts/calculate_rankings.py  
def update_trader_rankings():
    """Пересчитывает рейтинги еженедельно/ежемесячно"""
    - Trust Index (winrate + consistency + validity)
    - Risk Score (drawdown + volatility + RRR)
    - Grade (A/B/C/D по композитному баллу)
    - Сравнение с предыдущим периодом
```

---

## 📱 FRONTEND КОМПОНЕНТЫ

### **1. TraderProfilePage** - Детальное досье
```tsx
<TraderProfileCard />         // Базовая информация + Grade
<PerformanceMetricsGrid />    // KPI сетка (ROI, Winrate, Sharpe)  
<TimePatternHeatmap />        // 24x7 heatmap активности
<BehavioralInsights />        // Паттерны и аномалии
<SignalsTimeline />          // История лучших/худших сигналов
<RiskProfile />              // Анализ риск-менеджмента
<PeerComparison />           // Сравнение с другими трейдерами
```

### **2. TradersRankingDashboard** - Рейтинговая таблица
```tsx
<RankingFilters />           // Период, категория, сортировка
<TopTradersGrid />           // Карточки топ-10 
<RankingTable />            // Детальная таблица со всеми метриками
<RankingTrends />           // Динамика рейтингов (графики)
```

### **3. TradersAnalyticsDashboard** - Аналитический центр
```tsx
<MarketOverview />          // Общие метрики рынка трейдеров
<PerformanceDistribution /> // Распределение по ROI/Winrate
<BehaviorPatterns />        // Общие поведенческие тренды
<RiskHeatmap />            // Карта рисков по трейдерам
<CorrelationMatrix />       // Корреляции между трейдерами
```

### **4. TraderComparisonTool** - Инструмент сравнения
```tsx
<TraderSelector />          // Выбор 2-5 трейдеров
<MetricsComparison />       // Радар-чарт с метриками
<TimeSeriesComparison />    // Динамика ROI, Sharpe по времени
<StrengthsWeaknesses />     // SWOT анализ каждого
<RecommendationEngine />    // AI рекомендации по выбору
```

---

## 🧮 КЛЮЧЕВЫЕ АЛГОРИТМЫ

### **Trust Index Calculation:**
```python
def calculate_trust_index(trader_metrics):
    """
    Trust Index = weighted average of:
    - Winrate (30%)
    - Consistency (25%) - низкая волатильность ROI
    - Validity Rate (20%) - % валидных сигналов  
    - Risk Management (15%) - адекватные RRR
    - Longevity (10%) - стабильность во времени
    """
    return weighted_score # 0-100
```

### **Grade Assignment:**
```python
def assign_trader_grade(trust_index, risk_score):
    """
    A: Trust > 80, Risk < 30 (Excellent)
    B: Trust > 60, Risk < 50 (Good) 
    C: Trust > 40, Risk < 70 (Average)
    D: Trust < 40 or Risk > 70 (Poor)
    """
    return grade
```

### **Behavioral Pattern Detection:**
```python
def detect_duplicate_signals(trader_signals):
    """
    Использует cosine similarity для обнаружения:
    - Идентичных сигналов (similarity > 0.95)
    - Подозрительно похожих (similarity > 0.80)  
    - Паттернов копирования
    """
    return patterns
```

---

## 🎯 ИТОГОВЫЙ РЕЗУЛЬТАТ

**Каждый трейдер получит полное "досье" как у фонда:**

1. **📊 Основная карточка:** Trust Index, Grade, ROI, Sharpe
2. **📈 Производительность:** Временные ряды всех метрик
3. **🎯 Риск-профиль:** RRR, Drawdown, консистентность
4. **⏰ Временные паттерны:** Heatmap лучших часов/дней
5. **🔍 Поведение:** Дубликаты, противоречия, стиль
6. **🏆 Рейтинги:** Позиция среди всех трейдеров
7. **🚨 Проблемы:** Анализ ошибок и рекомендации
8. **📊 Сравнения:** Как на фоне других трейдеров

**= ПРОФЕССИОНАЛЬНАЯ СИСТЕМА УРОВНЯ HEDGE FUND**
