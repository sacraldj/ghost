# Настройка виртуального трейдинга

## Создание таблиц в Supabase

1. **Откройте Supabase Dashboard** для вашего проекта

2. **Перейдите в SQL Editor**

3. **Выполните скрипт создания таблиц**:
   ```sql
   -- Скопируйте и выполните содержимое файла virtual_trading_schema.sql
   ```

4. **Проверьте созданные таблицы**:
   - `virtual_positions` - основная таблица позиций
   - `position_entries` - записи входов в позицию
   - `position_exits` - записи выходов из позиций
   - `position_candles` - исторические данные свечей
   - `position_events` - логи событий позиций

## Схема работы системы

### 1. Получение сигнала
```
Telegram Signal → Ghost Test Parser → Signal Validation
                                   ↓
                            [Валидный сигнал]
                                   ↓
                         Сохранение в v_trades
                                   ↓
                     Создание virtual_position
```

### 2. Вход в позицию
```
Virtual Position → Получение рыночной цены (Bybit/Binance)
                               ↓
                      Проверка зоны входа
                               ↓
                     Выполнение входа по рынку
                               ↓
                 Сохранение в position_entries
```

### 3. Мониторинг позиции
```
Каждые 5 секунд:
- Получение текущих цен
- Расчет PnL
- Проверка TP/SL уровней
- Сохранение position_events
```

### 4. Закрытие по TP/SL
```
Достижение TP1 → Частичное закрытие 50%
                              ↓
                   Сохранение в position_exits
                              ↓
              Обновление статуса позиции
```

## Пример сигнала для тестирования

Отправьте в канал `@ghostsignaltest`:

```
Testing DOGE signal now

Long (3x) 
Entry: $0.15
Targets: $0.18, $0.20
Stop-loss: $0.13
```

### Что произойдет:

1. ✅ **Парсинг сигнала**: DOGEUSDT LONG Entry: $0.15, TP1: $0.18, TP2: $0.20, SL: $0.13
2. ✅ **Валидация**: Проверка логики (TP > Entry > SL для LONG)
3. ✅ **Сохранение v_trades**: Статус `sim_open` если валидный
4. ✅ **Создание позиции**: Новая запись в `virtual_positions`
5. ✅ **Вход по рынку**: Получение цены DOGEUSDT с Bybit → Вход по рыночной цене
6. ✅ **Мониторинг**: Каждые 5 секунд обновление цены и PnL
7. ✅ **Автозакрытие**: При достижении $0.18 → закрытие 50% позиции

## Настройки по умолчанию

- **Размер позиции**: $100 USD
- **Плечо**: 10x
- **Маржа**: $10 USD
- **Стратегия**: S_A_TP1_BE_TP2
- **TP1**: 50% закрытие
- **TP2**: 30% закрытие  
- **TP3**: 20% закрытие
- **Timeout входа**: 48 часов

## Мониторинг результатов

### В базе данных:

1. **Проверьте `virtual_positions`**:
   ```sql
   SELECT symbol, side, status, current_pnl_percent, created_at 
   FROM virtual_positions 
   ORDER BY created_at DESC;
   ```

2. **Посмотрите входы**:
   ```sql
   SELECT p.symbol, e.entry_price, e.entry_percent, e.entry_time
   FROM position_entries e
   JOIN virtual_positions p ON p.id = e.position_id
   ORDER BY e.entry_time DESC;
   ```

3. **История событий**:
   ```sql
   SELECT p.symbol, pe.event_type, pe.event_description, pe.event_time
   FROM position_events pe
   JOIN virtual_positions p ON p.id = pe.position_id
   ORDER BY pe.event_time DESC;
   ```

### В логах:

```bash
tail -f logs/signal_orchestrator_supabase.log | grep "Virtual\|Position\|Entry\|Exit"
```

## Troubleshooting

### Если позиции не создаются:
1. Проверьте, что таблицы созданы в Supabase
2. Проверьте права доступа к таблицам
3. Убедитесь, что сигнал проходит валидацию

### Если не входит в позицию:
1. Проверьте работу MarketPriceService
2. Убедитесь, что рыночная цена в зоне входа
3. Проверьте логи для ошибок API

### Если не закрывает по TP/SL:
1. Убедитесь, что мониторинг запущен
2. Проверьте логику расчета уровней
3. Посмотрите текущую цену vs уровни TP/SL

## Расширения

Система готова для:
- Добавления новых стратегий закрытия
- Интеграции с реальными биржами
- Анализа производительности сигналов
- ML-анализа исторических данных
- Уведомлений о событиях позиций
