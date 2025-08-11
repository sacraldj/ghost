#!/bin/bash

# GHOST Database Sync Script
# Синхронизация баз данных между news_engine и корневой папкой

echo "🔄 Синхронизация баз данных GHOST..."

# Проверяем наличие баз данных
if [ ! -f "news_engine/ghost_news.db" ]; then
    echo "❌ База данных news_engine/ghost_news.db не найдена"
    exit 1
fi

# Копируем базу из news_engine в корневую папку
echo "📋 Копирование базы данных..."
cp news_engine/ghost_news.db ghost_news.db

# Проверяем размеры файлов
NEWS_SIZE=$(stat -f%z news_engine/ghost_news.db)
ROOT_SIZE=$(stat -f%z ghost_news.db)

echo "📊 Размеры баз данных:"
echo "  news_engine/ghost_news.db: $NEWS_SIZE байт"
echo "  ghost_news.db: $ROOT_SIZE байт"

if [ "$NEWS_SIZE" -eq "$ROOT_SIZE" ]; then
    echo "✅ Синхронизация успешна"
else
    echo "❌ Ошибка синхронизации"
    exit 1
fi

# Проверяем количество записей
CRITICAL_COUNT=$(sqlite3 ghost_news.db "SELECT COUNT(*) FROM critical_news;" 2>/dev/null || echo "0")
NEWS_COUNT=$(sqlite3 ghost_news.db "SELECT COUNT(*) FROM news_items;" 2>/dev/null || echo "0")

echo "📈 Статистика:"
echo "  Критических новостей: $CRITICAL_COUNT"
echo "  Обычных новостей: $NEWS_COUNT"

echo "✅ Синхронизация завершена"
