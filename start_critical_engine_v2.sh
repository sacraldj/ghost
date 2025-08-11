#!/bin/bash

# GHOST Critical News Engine v2.0 - Боевая версия
# Анти-дубликаты, рейт-лимитинг, валидация, дедупликация

echo "🚨 Запуск GHOST Critical News Engine v2.0 (Боевая версия)..."

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установите Python 3.8+"
    exit 1
fi

# Проверка зависимостей
echo "📦 Проверка зависимостей..."
python3 -c "import aiohttp, yaml" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Установка зависимостей..."
    pip3 install aiohttp pyyaml
fi

# Остановка предыдущего процесса
if [ -f critical_engine_v2.pid ]; then
    OLD_PID=$(cat critical_engine_v2.pid)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "🛑 Остановка предыдущего процесса $OLD_PID..."
        kill $OLD_PID
        sleep 2
    fi
    rm -f critical_engine_v2.pid
fi

# Запуск боевой версии
echo "🚨 Запуск Critical News Engine v2.0 в фоновом режиме..."
cd news_engine
nohup python3 critical_news_engine_v2.py > critical_engine_v2.log 2>&1 &

# Сохранение PID
echo $! > ../critical_engine_v2.pid

echo "✅ Critical News Engine v2.0 запущен (PID: $(cat ../critical_engine_v2.pid))"
echo "📋 Логи: news_engine/critical_engine_v2.log"
echo "🛑 Для остановки: ./stop_critical_engine_v2.sh"
echo "📊 Мониторинг: tail -f news_engine/critical_engine_v2.log"
echo ""
echo "🚨 БОЕВЫЕ УЛУЧШЕНИЯ v2.0:"
echo "  ✅ Анти-дубликаты: topic_hash для дедупликации"
echo "  ✅ Рейт-лимитинг: per-source токены + exponential backoff"
echo "  ✅ Circuit breaker: open/half-open/close состояния"
echo "  ✅ Валидация контента: очистка HTML/эмодзи"
echo "  ✅ WAL режим SQLite: PRAGMA journal_mode=WAL"
echo "  ✅ Индексы: оптимизированные запросы"
echo "  ✅ Алерт-усталость: сгущение событий"
echo "  ✅ Часовые пояса: всё в UTC (ISO 8601)"
echo "  ✅ Регуляторные новости: вайтлист ключевых слов"
echo ""
echo "⏱️  Интервал: каждую секунду"
echo "🔄 Параллельность: 4 источника одновременно"
echo "📊 Метрики: pull_ok/pull_fail, latency, dedup_rate"
