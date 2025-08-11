#!/bin/bash

# GHOST Critical News Engine Auto-Start Script
# Сверхбыстрый запуск для критических новостей каждую секунду

echo "🚨 Запуск GHOST Critical News Engine..."

# Переходим в директорию news_engine
cd "$(dirname "$0")/news_engine"

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установите Python 3.8+"
    exit 1
fi

# Проверяем наличие необходимых пакетов
echo "📦 Проверка зависимостей..."
python3 -c "import aiohttp, sqlite3" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Установка зависимостей..."
    pip3 install aiohttp
fi

# Останавливаем предыдущий процесс если запущен
if [ -f critical_engine.pid ]; then
    OLD_PID=$(cat critical_engine.pid)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "🛑 Остановка предыдущего процесса $OLD_PID..."
        kill $OLD_PID
        sleep 2
    fi
    rm -f critical_engine.pid
fi

# Запускаем Critical News Engine
echo "⚡ Запуск Critical News Engine в фоновом режиме (каждую секунду)..."
nohup python3 critical_news_engine.py > critical_engine.log 2>&1 &

# Сохраняем PID процесса
echo $! > critical_engine.pid

echo "✅ Critical News Engine запущен (PID: $(cat critical_engine.pid))"
echo "📋 Логи: news_engine/critical_engine.log"
echo "🛑 Для остановки: ./stop_critical_engine.sh"
echo "📊 Мониторинг: tail -f news_engine/critical_engine.log"
echo ""
echo "🚨 КРИТИЧЕСКИЕ ИСТОЧНИКИ (каждую секунду):"
echo "  - Binance Price API"
echo "  - Coinbase Price API" 
echo "  - Breaking News API"
echo "  - Twitter Critical"
echo "  - Regulatory Alerts"
echo ""
echo "⚡ Сверхбыстрый режим: 100ms пауза между циклами"
