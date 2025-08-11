#!/bin/bash

# GHOST News Engine Stop Script
# Скрипт для остановки News Engine

echo "🛑 Остановка GHOST News Engine..."

# Переходим в директорию news_engine
cd "$(dirname "$0")/news_engine"

# Проверяем наличие PID файла
if [ ! -f news_engine.pid ]; then
    echo "❌ PID файл не найден. News Engine может быть не запущен."
    exit 1
fi

# Читаем PID
PID=$(cat news_engine.pid)

# Проверяем, существует ли процесс
if ! ps -p $PID > /dev/null; then
    echo "❌ Процесс с PID $PID не найден. Удаляем PID файл."
    rm -f news_engine.pid
    exit 1
fi

# Останавливаем процесс
echo "🔄 Остановка процесса $PID..."
kill $PID

# Ждем завершения процесса
sleep 2

# Проверяем, остановился ли процесс
if ps -p $PID > /dev/null; then
    echo "⚠️  Процесс не остановился, принудительно завершаем..."
    kill -9 $PID
else
    echo "✅ News Engine успешно остановлен"
fi

# Удаляем PID файл
rm -f news_engine.pid

echo "✅ Остановка завершена"
