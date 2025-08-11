#!/bin/bash

# GHOST Supabase Sync Stop Script
# Остановка синхронизации с Supabase

echo "🛑 Остановка GHOST Supabase Sync..."

# Переходим в директорию news_engine
cd "$(dirname "$0")/news_engine"

# Проверяем наличие PID файла
if [ ! -f supabase_sync.pid ]; then
    echo "❌ PID файл не найден. Supabase Sync может быть не запущен."
    exit 1
fi

# Читаем PID
PID=$(cat supabase_sync.pid)

# Проверяем, существует ли процесс
if ! ps -p $PID > /dev/null; then
    echo "❌ Процесс с PID $PID не найден. Удаляем PID файл."
    rm -f supabase_sync.pid
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
    echo "✅ Supabase Sync успешно остановлен"
fi

# Удаляем PID файл
rm -f supabase_sync.pid

echo "✅ Остановка завершена"
echo "📊 Последние логи: tail -20 supabase_sync.log"
