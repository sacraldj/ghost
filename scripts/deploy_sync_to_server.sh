#!/bin/bash

# GHOST - Deploy Sync to Daren's Server
# Деплой синхронизации трейдов на сервер Дарэна

set -e  # Exit on any error

# Server configuration
SERVER_HOST="138.199.226.247"
SERVER_USER="root"
SERVER_PATH="/root/ghost_system_final/ghost_system_final_146"
SERVER_TOOLS_PATH="$SERVER_PATH/tools"

echo "🚀 Деплой GHOST синхронизации на сервер Дарэна..."

# Check if sync script exists
if [ ! -f "news_engine/trades_supabase_sync.py" ]; then
    echo "❌ Файл news_engine/trades_supabase_sync.py не найден"
    exit 1
fi

echo "📦 Копирование файлов на сервер..."

# Copy sync script
scp -o StrictHostKeyChecking=no \
    news_engine/trades_supabase_sync.py \
    $SERVER_USER@$SERVER_HOST:$SERVER_TOOLS_PATH/

# Copy requirements if exists
if [ -f "news_engine/requirements.txt" ]; then
    scp -o StrictHostKeyChecking=no \
        news_engine/requirements.txt \
        $SERVER_USER@$SERVER_HOST:$SERVER_TOOLS_PATH/
fi

echo "🔧 Настройка на сервере..."

# Connect to server and setup
ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST << 'EOF'
cd /root/ghost_system_final/ghost_system_final_146

echo "📍 Текущая директория: $(pwd)"

# Check if Python venv exists
if [ ! -d "venv310" ]; then
    echo "🐍 Создание Python venv..."
    python3.10 -m venv venv310
fi

# Activate venv
source venv310/bin/activate

# Install/upgrade required packages
echo "📦 Установка зависимостей..."
pip install -q supabase python-dotenv

# Check if ghost.db exists
if [ -f "ghost.db" ]; then
    echo "✅ База данных ghost.db найдена"
    # Show basic info about the database
    echo "📊 Информация о базе данных:"
    sqlite3 ghost.db "SELECT COUNT(*) as trade_count FROM trades;" 2>/dev/null || echo "  Не удалось получить количество трейдов"
else
    echo "⚠️  База данных ghost.db не найдена в $(pwd)"
    echo "📁 Содержимое директории:"
    ls -la | grep -E "\.(db|sqlite)$" || echo "  Файлы БД не найдены"
fi

# Create environment file if not exists
if [ ! -f ".env" ]; then
    echo "📝 Создание .env файла..."
    cat > .env << 'ENVEOF'
# Supabase configuration
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# Database path
GHOST_DB_PATH=./ghost.db

# Sync settings
SYNC_INTERVAL_SEC=60
SYNC_LOOP=1
ENVEOF
    echo "⚠️  Заполните .env файл своими ключами Supabase"
else
    echo "✅ Файл .env уже существует"
fi

# Make sync script executable
chmod +x tools/trades_supabase_sync.py

echo "✅ Установка завершена!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Заполните файл .env ключами Supabase"
echo "2. Запустите синхронизацию:"
echo "   cd /root/ghost_system_final/ghost_system_final_146"
echo "   source venv310/bin/activate"
echo "   python tools/trades_supabase_sync.py"
echo ""
echo "🔄 Для автоматической синхронизации добавьте в tmux:"
echo "   tmux new-window -t ghost -n sync 'cd /root/ghost_system_final/ghost_system_final_146 && source venv310/bin/activate && python tools/trades_supabase_sync.py'"

EOF

echo "🎉 Деплой завершен успешно!"
echo ""
echo "🔧 Для настройки синхронизации:"
echo "1. SSH на сервер: ssh $SERVER_USER@$SERVER_HOST"
echo "2. Перейдите в: cd $SERVER_PATH"
echo "3. Заполните .env файл ключами Supabase"
echo "4. Запустите: source venv310/bin/activate && python tools/trades_supabase_sync.py"
