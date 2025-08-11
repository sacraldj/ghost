#!/bin/bash

# GHOST Critical News Engine Stop Script
# Остановка сверхбыстрого News Engine

echo "🛑 Остановка GHOST Critical News Engine..."

# Переходим в директорию news_engine
cd "$(dirname "$0")/news_engine"

# Проверяем наличие PID файла
if [ ! -f critical_engine.pid ]; then
    echo "❌ PID файл не найден. Critical News Engine может быть не запущен."
    exit 1
fi

# Читаем PID
PID=$(cat critical_engine.pid)

# Проверяем, существует ли процесс
if ! ps -p $PID > /dev/null; then
    echo "❌ Процесс с PID $PID не найден. Удаляем PID файл."
    rm -f critical_engine.pid
    exit 1
fi

# Останавливаем процесс
echo "🔄 Остановка процесса $PID..."
kill $PID

# Ждем завершения процесса
sleep 3

# Проверяем, остановился ли процесс
if ps -p $PID > /dev/null; then
    echo "⚠️  Процесс не остановился, принудительно завершаем..."
    kill -9 $PID
    sleep 1
else
    echo "✅ Critical News Engine успешно остановлен"
fi

# Удаляем PID файл
rm -f critical_engine.pid

echo "✅ Остановка завершена"
echo "📊 Последние логи: tail -20 critical_engine.log"
