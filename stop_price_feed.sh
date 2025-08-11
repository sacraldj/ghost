#!/bin/bash

# GHOST Price Feed Engine - Скрипт остановки
# Остановка модуля сбора ценовых данных

echo "🛑 Остановка GHOST Price Feed Engine..."

# Переход в директорию news_engine
cd "$(dirname "$0")/news_engine"

# PID файл
PID_FILE="price_feed_engine.pid"

# Проверка существования PID файла
if [ ! -f "$PID_FILE" ]; then
    echo "⚠️  PID файл не найден. Price Feed Engine не запущен."
    exit 0
fi

# Чтение PID
PID=$(cat "$PID_FILE")

# Проверка, запущен ли процесс
if ! ps -p $PID > /dev/null 2>&1; then
    echo "⚠️  Процесс с PID $PID не найден. Удаление PID файла..."
    rm -f "$PID_FILE"
    exit 0
fi

# Остановка процесса
echo "🔄 Остановка процесса (PID: $PID)..."
kill $PID

# Ожидание завершения
sleep 3

# Проверка, остановился ли процесс
if ps -p $PID > /dev/null 2>&1; then
    echo "⚠️  Процесс не остановился. Принудительная остановка..."
    kill -9 $PID
    sleep 1
fi

# Проверка финального состояния
if ps -p $PID > /dev/null 2>&1; then
    echo "❌ Не удалось остановить процесс (PID: $PID)"
    exit 1
else
    echo "✅ Price Feed Engine успешно остановлен"
    rm -f "$PID_FILE"
fi
