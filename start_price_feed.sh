#!/bin/bash

# GHOST Price Feed Engine - Скрипт запуска
# Запуск модуля сбора ценовых данных

echo "🚀 Запуск GHOST Price Feed Engine..."

# Переход в директорию news_engine
cd "$(dirname "$0")/news_engine"

# Проверка существования файла
if [ ! -f "price_feed_engine.py" ]; then
    echo "❌ Ошибка: файл price_feed_engine.py не найден"
    exit 1
fi

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Ошибка: Python3 не установлен"
    exit 1
fi

# Проверка зависимостей
echo "📦 Проверка зависимостей..."
python3 -c "import aiohttp, pandas, numpy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Предупреждение: некоторые зависимости не установлены"
    echo "   Установите: pip3 install aiohttp pandas numpy"
fi

# Создание PID файла
PID_FILE="price_feed_engine.pid"

# Проверка, не запущен ли уже процесс
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "⚠️  Price Feed Engine уже запущен (PID: $PID)"
        echo "   Для остановки используйте: ./stop_price_feed.sh"
        exit 1
    else
        echo "🧹 Удаление устаревшего PID файла..."
        rm -f "$PID_FILE"
    fi
fi

# Запуск движка
echo "🔄 Запуск Price Feed Engine..."
nohup python3 price_feed_engine.py > price_feed_engine.log 2>&1 &

# Сохранение PID
echo $! > "$PID_FILE"

# Проверка запуска
sleep 2
if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
    echo "✅ Price Feed Engine успешно запущен (PID: $(cat "$PID_FILE"))"
    echo "📊 Логи: news_engine/price_feed_engine.log"
    echo "🛑 Для остановки: ./stop_price_feed.sh"
else
    echo "❌ Ошибка запуска Price Feed Engine"
    rm -f "$PID_FILE"
    exit 1
fi
