#!/bin/bash

# GHOST News Engine Auto-Start Script
# Скрипт для автоматического запуска News Engine

echo "🚀 Запуск GHOST News Engine..."

# Переходим в директорию news_engine
cd "$(dirname "$0")/news_engine"

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установите Python 3.8+"
    exit 1
fi

# Проверяем наличие необходимых пакетов
echo "📦 Проверка зависимостей..."
python3 -c "import aiohttp, sqlite3, yaml" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Установка зависимостей..."
    pip3 install aiohttp pyyaml
fi

# Запускаем News Engine
echo "🔄 Запуск News Engine в фоновом режиме..."
nohup python3 simple_news_engine.py > news_engine.log 2>&1 &

# Сохраняем PID процесса
echo $! > news_engine.pid

echo "✅ News Engine запущен (PID: $(cat news_engine.pid))"
echo "📋 Логи: news_engine/news_engine.log"
echo "🛑 Для остановки: ./stop_news_engine.sh"
