#!/bin/bash

# GHOST Critical News Engine v2.0 - Остановка

echo "🛑 Остановка GHOST Critical News Engine v2.0..."

if [ -f critical_engine_v2.pid ]; then
    PID=$(cat critical_engine_v2.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "🛑 Остановка процесса $PID..."
        kill $PID
        sleep 2
        
        # Проверка, что процесс остановлен
        if ps -p $PID > /dev/null 2>&1; then
            echo "⚠️  Принудительная остановка процесса $PID..."
            kill -9 $PID
        fi
        
        echo "✅ Critical News Engine v2.0 остановлен"
    else
        echo "⚠️  Процесс $PID уже не запущен"
    fi
    
    rm -f critical_engine_v2.pid
else
    echo "⚠️  PID файл не найден"
fi

echo "📋 Последние логи:"
if [ -f news_engine/critical_engine_v2.log ]; then
    tail -10 news_engine/critical_engine_v2.log
else
    echo "Лог файл не найден"
fi
