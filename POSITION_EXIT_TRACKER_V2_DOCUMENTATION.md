# 📚 GHOST Position Exit Tracker v2.0 - Полная документация

## 📋 Обзор системы

**Файл:** `position_exit_tracker.py`  
**Версия:** v2.0 (fills-first + fallback)  
**Статус:** ✅ Боевой готовый  
**Дата:** 2025-01-27

### 🎯 Назначение
Отслеживает закрытие позиций, корректно рассчитывает PnL/ROI на основе реальных fills от биржи с fallback на существующую логику.

## 🏗️ Архитектура

### Основные компоненты:

```
position_exit_tracker.py
├── API Layer (Bybit HTTP)
├── Fills Processing
│   ├── _get_executions()
│   ├── _split_fills_by_legs()
│   └── _calc_from_fills()
├── Fallback Layer
│   └── _fallback_calc()
├── Data Processing
│   ├── _vwap_qty_fee()
│   └── _signed_profit()
└── Output Layer
    ├── _preview_message()
    └── ghost_write_safe()
```

## 🔧 Функции и методы

### 1. Основные расчётные функции

#### `_signed_profit(entry, exit_price, qty, side)`
**Назначение:** Вычисляет PnL с учётом направления позиции

**Параметры:**
- `entry` (float): Цена входа
- `exit_price` (float): Цена выхода  
- `qty` (float): Количество
- `side` (str): Направление ("Buy"/"Sell")

**Возвращает:** float - PnL с правильным знаком

**Пример:**
```python
# LONG позиция
pnl = _signed_profit(1000, 1100, 100, "Buy")  # +10000

# SHORT позиция  
pnl = _signed_profit(1000, 900, 100, "Sell")  # +10000
```

#### `_vwap_qty_fee(fills)`
**Назначение:** Вычисляет VWAP, общее количество и сумму комиссий из fills

**Параметры:**
- `fills` (List[Dict]): Список fills от биржи

**Возвращает:** Tuple[float, float, float] - (vwap, qty, fee_sum)

**Пример:**
```python
fills = [
    {"execPrice": "1000", "execQty": "50", "execFee": "2.75"},
    {"execPrice": "1100", "execQty": "50", "execFee": "3.025"}
]
vwap, qty, fee = _vwap_qty_fee(fills)
# vwap = 1050, qty = 100, fee = 5.775
```

#### `_split_fills_by_legs(fills, qty_total, side)`
**Назначение:** Разделяет fills на TP1 (50%) и остаток (50%)

**Параметры:**
- `fills` (List[Dict]): Список fills
- `qty_total` (float): Общее количество позиции
- `side` (str): Направление позиции

**Возвращает:** Tuple[List[Dict], List[Dict]] - (leg_tp1, leg_rest)

**Особенности:**
- Фильтрует закрывающие fills по направлению
- Сортирует по времени исполнения
- Обрабатывает overfill на границе 50%

**Пример:**
```python
fills = [
    {"side": "Sell", "execPrice": "1020", "execQty": "50", "execTime": "1000"},
    {"side": "Sell", "execPrice": "1000.2", "execQty": "50", "execTime": "2000"}
]
leg_tp1, leg_rest = _split_fills_by_legs(fills, 100, "Buy")
# leg_tp1: 50 @ 1020, leg_rest: 50 @ 1000.2
```

### 2. API функции

#### `_get_executions(symbol, start_time, end_time)`
**Назначение:** Получает executions (fills) от Bybit API

**Параметры:**
- `symbol` (str): Торговая пара
- `start_time` (int): Время начала (timestamp * 1000)
- `end_time` (int): Время окончания (timestamp * 1000)

**Возвращает:** List[Dict] - Список fills

**Особенности:**
- Пагинация до исчерпания данных
- Защита от бесконечного цикла (лимит 10000)
- Обработка ошибок API

**Trace-коды:**
- `FILLS_FETCH_OK`: Успешное получение
- `FILLS_FETCH_FAIL`: Ошибка API
- `FILLS_FETCH_LIMIT`: Превышен лимит

### 3. Основные расчётные функции

#### `_calc_from_fills(trade, fills)`
**Назначение:** Вычисляет PnL/ROI на основе fills

**Параметры:**
- `trade` (Dict): Объект сделки
- `fills` (List[Dict]): Список fills

**Возвращает:** Dict - Результаты расчёта

**Обязательные поля trade:**
```python
{
    "symbol": str,
    "side": str,  # "Buy" или "Sell"
    "real_entry_price": float,
    "position_qty": float,
    "margin_used": float,
    "tp2_price": float,  # опционально
    "entry_fee_total": float  # опционально
}
```

**Возвращаемые поля:**
```python
{
    "pnl_tp1_net": float,
    "pnl_rest_net": float,
    "pnl_final_real": float,
    "roi_tp1_real": float,
    "roi_rest_real": float,
    "roi_final_real": float,
    "exit_reason": str,  # "tp2" | "tp1_be" | "sl" | "manual"
    "exit_detail": str,  # "fills: tp1@50% + be@50%"
    "roi_source": "fills",
    "pnl_source": "fills",
    "roi_calc_note": "ok",
    "bybit_fee_open": float,
    "bybit_fee_close": float,
    "bybit_fee_total": float,
    "tp1_hit": bool,
    "tp2_hit": bool,
    "sl_hit": bool,
    "early_exit": False
}
```

#### `_fallback_calc(trade, exit_price)`
**Назначение:** Fallback расчёт на основе существующей логики

**Параметры:**
- `trade` (Dict): Объект сделки
- `exit_price` (float): Цена выхода

**Возвращает:** Dict - Результаты fallback расчёта

**Особенности:**
- Используется только при отсутствии fills
- Сохраняет обратную совместимость
- Устанавливает `roi_source = "fallback"`

### 4. Вспомогательные функции

#### `_duration_sec(trade, exit_dt)`
**Назначение:** Вычисляет длительность сделки в секундах

#### `_preview_message(trade, exit_price, final_pnl, pnl_source, duration_sec)`
**Назначение:** Формирует сообщение предпросмотра закрытия сделки

## 🔄 Алгоритм работы

### 1. Обнаружение закрытия позиции
```python
pos = get_position(symbol)
size = float(pos.get("size", 0))
if size == 0:
    # Позиция закрыта - начинаем обработку
```

### 2. Получение fills
```python
opened_dt = datetime.strptime(trade["opened_at"], "%Y-%m-%d %H:%M:%S")
start_time = int(opened_dt.timestamp() * 1000) - 300000  # -5 минут
end_time = int(exit_dt.timestamp() * 1000) + 60000      # +1 минута
fills = _get_executions(symbol, start_time, end_time)
```

### 3. Расчёт PnL/ROI
```python
if fills:
    calc_result = _calc_from_fills(trade, fills)
    if calc_result.get("roi_calc_note") == "ok":
        # Успешный расчёт на основе fills
    else:
        # Частичный fallback
else:
    # Полный fallback
    calc_result = _fallback_calc(trade, last_price)
```

### 4. Определение exit_reason
```python
if tp2_price > 0:
    if abs(vwap_rest - tp2_price) <= tp2_price * 0.001:
        exit_reason = "tp2"
    elif abs(vwap_rest - entry_price) <= entry_price * BE_EPS:
        exit_reason = "tp1_be"
    else:
        exit_reason = "manual"
```

## 📊 Выходные данные

### Новые обязательные поля:

| Поле | Тип | Описание |
|------|-----|----------|
| `roi_source` | str | "fills" \| "fallback" |
| `pnl_source` | str | "fills" \| "fallback" |
| `roi_calc_note` | str | "ok" \| "skip_calc: ..." \| "fallback" |
| `exit_detail` | str | "fills: tp1@50% + be@50%" |
| `pnl_tp1_net` | float | PnL первой ноги (TP1) |
| `pnl_rest_net` | float | PnL второй ноги (остаток) |
| `roi_tp1_real` | float | ROI первой ноги (%) |
| `roi_rest_real` | float | ROI второй ноги (%) |
| `bybit_fee_open` | float | Комиссия входа (USDT) |
| `bybit_fee_close` | float | Комиссия выхода (USDT) |
| `bybit_fee_total` | float | Общая комиссия (USDT) |

### Улучшенные существующие поля:

| Поле | Изменение |
|------|-----------|
| `exit_reason` | Определяется на основе фактических fills |
| `tp1_hit`, `tp2_hit`, `sl_hit` | Пересчитываются на основе fills |
| `pnl_final_real`, `roi_final_real` | Корректный расчёт на основе fills |

## 🧪 Тестирование

### Запуск тестов:
```bash
python3 test_position_exit_tracker.py
```

### Тестовые сценарии:

#### 1. Unit тесты:
- `test_signed_profit()`: Проверка расчёта PnL для LONG/SHORT
- `test_vwap_qty_fee()`: Проверка расчёта VWAP и комиссий
- `test_split_fills_by_legs()`: Проверка разделения fills
- `test_calc_from_fills()`: Проверка основного расчёта
- `test_fallback_calc()`: Проверка fallback логики

#### 2. Интеграционные тесты:
- `test_edge_cases()`: Граничные случаи
- `run_integration_test()`: Полный сценарий сделки

### Пример тестового сценария:
```python
# LONG позиция с TP1 и BE
trade = {
    "symbol": "BTCUSDT",
    "side": "Buy",
    "real_entry_price": 1000,
    "position_qty": 100,
    "margin_used": 5000,
    "tp1_price": 1020,
    "tp2_price": 1100
}

fills = [
    {"side": "Sell", "execPrice": "1020", "execQty": "50", "execFee": "2.805"},
    {"side": "Sell", "execPrice": "1000.2", "execQty": "50", "execFee": "2.755"}
]

result = _calc_from_fills(trade, fills)
# Ожидаемый результат:
# exit_reason = "tp1_be"
# pnl_tp1_net > 0 (прибыль по TP1)
# pnl_rest_net ≈ -комиссия (BE)
```

## 🔍 Мониторинг и отладка

### Новые trace-коды:

| Код | Описание |
|-----|----------|
| `FILLS_FETCH_OK` | Успешное получение fills |
| `FILLS_FETCH_EMPTY` | Fills не найдены |
| `FILLS_CALC_OK` | Успешный расчёт на основе fills |
| `FILLS_PARTIAL_FALLBACK` | Частичный fallback |
| `FALLBACK_CALC_USED` | Использован полный fallback |
| `FILLS_VS_API_MISMATCH` | Расхождение с API > 1 цент |

### Логирование:
```python
# Успешный расчёт
trace("FILLS_CALC_OK", {"symbol": symbol}, "position_exit_tracker")

# Fallback
trace("FALLBACK_CALC_USED", {"symbol": symbol}, "position_exit_tracker")

# Расхождение с API
trace("FILLS_VS_API_MISMATCH", {
    "symbol": symbol,
    "our_pnl": trade["pnl_final_real"],
    "api_pnl": trade["bybit_pnl_net_api"],
    "diff": diff
}, "position_exit_tracker")
```

## 🚀 Развёртывание

### Пошаговый план:

1. **Бэкап текущей версии:**
   ```bash
   cp position_exit_tracker.py position_exit_tracker_v1.4_backup.py
   ```

2. **Проверка зависимостей:**
   ```bash
   # Убедиться, что все импорты доступны
   python3 -c "import position_exit_tracker"
   ```

3. **Запуск тестов:**
   ```bash
   python3 test_position_exit_tracker.py
   ```

4. **Мониторинг в продакшене:**
   - Проверить логи на новые trace-коды
   - Сравнить PnL с API
   - Убедиться в корректности exit_detail

### Проверка работоспособности:
```bash
# Запуск в тестовом режиме
python3 position_exit_tracker.py

# Проверка логов
tail -f logs/ghost.log | grep "FILLS_"
```

## ⚠️ Граничные случаи

### 1. Пустые fills
- **Симптом:** `FILLS_FETCH_EMPTY`
- **Действие:** Переход в fallback режим
- **Результат:** `roi_source = "fallback"`

### 2. Неполные fills
- **Симптом:** `FILLS_PARTIAL_FALLBACK`
- **Действие:** Частичный расчёт с пометкой
- **Результат:** `roi_calc_note = "partial"`

### 3. Ошибки API
- **Симптом:** `FILLS_FETCH_FAIL`
- **Действие:** Graceful degradation к fallback
- **Результат:** Сохранение работоспособности

### 4. Расхождение с API
- **Симптом:** `FILLS_VS_API_MISMATCH`
- **Действие:** Логирование расхождения
- **Результат:** Аудит точности расчётов

## 📈 Производительность

### Ограничения:
- **API запросы:** Не более 2/сек к executions
- **Пагинация:** Лимит 10000 fills на сделку
- **Время окна:** opened_at - 5мин до now + 1мин

### Оптимизации:
- Кэширование fills в памяти
- Graceful degradation при ошибках
- Асинхронная обработка API запросов

## 🔒 Безопасность

### Защита от ошибок:
- Try-catch блоки для всех API вызовов
- Валидация входных данных
- Fallback режим для критических функций

### Логирование:
- Все операции логируются
- Чувствительные данные не записываются
- Trace-коды для отладки

## 📝 Заключение

Position Exit Tracker v2.0 представляет собой значительное улучшение точности расчёта PnL/ROI при сохранении полной обратной совместимости. Основной фокус на использовании реальных fills от биржи как первоисточника истины обеспечивает корректность расчётов во всех сценариях торговли.

**Статус:** ✅ Готов к развёртыванию в продакшене

---

*Документация создана: 2025-01-27*  
*Версия: v2.0*  
*Автор: GHOST System*
