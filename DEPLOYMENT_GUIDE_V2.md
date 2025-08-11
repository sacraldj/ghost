# 🚀 GHOST Position Exit Tracker v2.0 - Инструкция по развёртыванию

## 📋 Быстрый старт

### 1. Подготовка
```bash
# Бэкап текущей версии
cp position_exit_tracker.py position_exit_tracker_v1.4_backup.py

# Проверка зависимостей
python3 -c "import yaml, pybit, json, datetime"
```

### 2. Проверка конфигурации
```bash
# Убедиться, что файл конфигурации существует
ls -la config/api_keys.yaml
```

### 3. Запуск тестов
```bash
# Создать тестовую конфигурацию
mkdir -p config
echo "bybit:\n  api_key: \"test_key\"\n  api_secret: \"test_secret\"" > config/api_keys.yaml

# Запустить тесты
python3 test_position_exit_tracker.py
```

### 4. Развёртывание
```bash
# Новый файл уже готов
# Запустить в тестовом режиме
python3 position_exit_tracker.py
```

## 🔍 Мониторинг

### Проверка логов:
```bash
# Новые trace-коды
tail -f logs/ghost.log | grep "FILLS_"

# Успешные расчёты
grep "FILLS_CALC_OK" logs/ghost.log

# Fallback случаи
grep "FALLBACK_CALC_USED" logs/ghost.log
```

### Проверка данных:
```bash
# Проверить новые поля в БД
sqlite3 ghost_news.db "SELECT roi_source, pnl_source, exit_detail FROM trades ORDER BY id DESC LIMIT 5;"
```

## ⚠️ Критические моменты

### 1. Обратная совместимость
- ✅ Все существующие поля сохранены
- ✅ Формат логов не изменён
- ✅ Fallback режим для надёжности

### 2. Новые поля
- `roi_source`: "fills" | "fallback"
- `pnl_source`: "fills" | "fallback"
- `exit_detail`: "fills: tp1@50% + be@50%"
- `pnl_tp1_net`, `pnl_rest_net`: Детализация по ногам

### 3. Производительность
- API запросы: ≤ 2/сек
- Пагинация: лимит 10000 fills
- Время окна: ±5 минут от сделки

## 🧪 Тестирование

### Unit тесты:
```bash
python3 test_position_exit_tracker.py
```

### Интеграционные тесты:
- Проверка fills-first логики
- Проверка fallback режима
- Проверка граничных случаев

## 📊 Ожидаемые результаты

### Улучшения точности:
- **PnL расчёт**: От приблизительного к фактическому
- **Комиссии**: От фиксированных к реальным
- **TP1/TP2 разделение**: От флагов к фактическим fills
- **Детализация**: От базовой к полной

### Сохранение совместимости:
- ✅ Все существующие поля сохранены
- ✅ Формат логов не изменён
- ✅ Fallback режим для надёжности
- ✅ Обратная совместимость

## 🚨 Откат

В случае проблем:
```bash
# Восстановить предыдущую версию
cp position_exit_tracker_v1.4_backup.py position_exit_tracker.py

# Перезапустить
python3 position_exit_tracker.py
```

## 📞 Поддержка

### Логи для отладки:
- `FILLS_FETCH_OK`: Успешное получение fills
- `FILLS_CALC_OK`: Успешный расчёт
- `FALLBACK_CALC_USED`: Использован fallback
- `FILLS_VS_API_MISMATCH`: Расхождение с API

### Контакты:
- Документация: `POSITION_EXIT_TRACKER_V2_DOCUMENTATION.md`
- Changelog: `POSITION_EXIT_TRACKER_V2_CHANGELOG.md`
- Тесты: `test_position_exit_tracker.py`

---

**Статус:** ✅ Готов к развёртыванию в продакшене  
**Версия:** v2.0  
**Дата:** 2025-01-27
