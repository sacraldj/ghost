# 🧹 GHOST System Cleanup Script
# Удаление дублирующих и лишних файлов

## ❌ ФАЙЛЫ ДЛЯ УДАЛЕНИЯ:

### 1. Дублирующие оркестраторы:
```bash
rm core/orchestrator.py                    # Дублирует ghost_orchestrator.py
```

### 2. Старые news engines:
```bash
rm news_engine/news_engine.py             # Старая версия
rm news_engine/simple_news_engine.py      # Упрощенная версия
rm news_engine/critical_news_engine.py    # Старая версия (есть v2)
```

### 3. Дублирующие telegram listeners:
```bash
rm news_engine/telegram_listener.py       # Старый (есть в core/)
```

### 4. Лишние скрипты запуска:
```bash
rm start_critical_engine.sh               # Дублирует функции оркестратора
rm start_critical_engine_v2.sh            # Дублирует функции оркестратора
rm start_news_engine.sh                   # Заменен оркестратором
rm start_price_feed.sh                    # Заменен оркестратором
rm stop_critical_engine.sh                # Не нужен
rm stop_critical_engine_v2.sh             # Не нужен
rm stop_news_engine.sh                    # Не нужен
rm stop_price_feed.sh                     # Не нужен
```

### 5. Старые конфигурации:
```bash
rm news_engine_config_processed.yaml      # Дублирует news_engine_config.yaml
```

### 6. Лишние test файлы (оставляем только нужные):
```bash
rm test_fills_calculation.py              # Специфичный тест
rm test_roi_calculation.py                # Специфичный тест
rm test_position_exit_tracker.py          # Специфичный тест
```

## ✅ КОМАНДЫ ДЛЯ ВЫПОЛНЕНИЯ:
