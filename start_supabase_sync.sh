#!/bin/bash

# GHOST Supabase Sync Auto-Start Script
# Автоматическая синхронизация локальных данных с Supabase

echo "🔄 Запуск GHOST Supabase Sync..."

# Загружаем переменные окружения
if [ -f .env.local ]; then
    echo "📋 Загрузка переменных из .env.local..."
    export $(cat .env.local | grep -v '^#' | xargs)
fi

# Переходим в директорию news_engine
cd "$(dirname "$0")/news_engine"

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установите Python 3.8+"
    exit 1
fi

# Проверяем наличие Supabase зависимостей
echo "📦 Проверка Supabase зависимостей..."
python3 -c "import supabase" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Установка Supabase Python client..."
    pip3 install supabase
fi

# Проверяем переменные окружения
if [ -z "$NEXT_PUBLIC_SUPABASE_URL" ]; then
    echo "❌ NEXT_PUBLIC_SUPABASE_URL не найден в переменных окружения"
    exit 1
fi

# Проверяем новые или старые ключи
if [ -z "$SUPABASE_SECRET_KEY" ] && [ -z "$SUPABASE_SERVICE_ROLE_KEY" ]; then
    echo "❌ Supabase credentials не найдены в переменных окружения"
    echo "Добавьте в .env.local:"
    echo "NEXT_PUBLIC_SUPABASE_URL=your_supabase_url"
    echo "SUPABASE_SECRET_KEY=your_secret_key (новые ключи)"
    echo "или"
    echo "SUPABASE_SERVICE_ROLE_KEY=your_service_role_key (старые ключи)"
    exit 1
fi

echo "✅ Supabase URL: $NEXT_PUBLIC_SUPABASE_URL"
echo "✅ Supabase Key: ${SUPABASE_SECRET_KEY:-$SUPABASE_SERVICE_ROLE_KEY}"

# Останавливаем предыдущий процесс если запущен
if [ -f supabase_sync.pid ]; then
    OLD_PID=$(cat supabase_sync.pid)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "🛑 Остановка предыдущего процесса $OLD_PID..."
        kill $OLD_PID
        sleep 2
    fi
    rm -f supabase_sync.pid
fi

# Запускаем Supabase Sync
echo "🔄 Запуск Supabase Sync в фоновом режиме (каждые 30 секунд)..."
nohup python3 supabase_sync.py > supabase_sync.log 2>&1 &

# Сохраняем PID процесса
echo $! > supabase_sync.pid

echo "✅ Supabase Sync запущен (PID: $(cat supabase_sync.pid))"
echo "📋 Логи: news_engine/supabase_sync.log"
echo "🛑 Для остановки: ./stop_supabase_sync.sh"
echo "📊 Мониторинг: tail -f news_engine/supabase_sync.log"
echo ""
echo "🔄 СИНХРОНИЗАЦИЯ С SUPABASE:"
echo "  - Критические новости → Supabase"
echo "  - Обычные новости → Supabase"
echo "  - Рыночные данные → Supabase"
echo "  - Критические алерты → Supabase"
echo ""
echo "⏱️  Интервал синхронизации: 30 секунд"
