#!/usr/bin/env python3
"""
Тестирование подключения к серверу Дарэна для получения данных
"""

import paramiko
import sqlite3
import os
from datetime import datetime

def test_connection():
    """Протестировать подключение и скачать данные"""
    
    print("🔐 Тестирование подключения к серверу Дарэна...")
    
    hostname = "138.199.226.247"
    username = "root"
    password = "Twiister1"
    remote_db_path = "/root/ghost_system_final/ghost_system_final_146/ghost.db"
    
    try:
        # SSH подключение
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        print(f"🔌 Подключение к {hostname}...")
        ssh.connect(hostname, username=username, password=password, timeout=10)
        print("✅ SSH подключение успешно!")
        
        # Проверяем файлы на сервере
        print("\n📁 Проверка файлов на сервере...")
        stdin, stdout, stderr = ssh.exec_command("ls -la /root/ghost_system_final/ghost_system_final_146/")
        files = stdout.read().decode()
        
        if "ghost.db" in files:
            print("✅ База данных ghost.db найдена")
            
            # Получаем размер файла
            stdin, stdout, stderr = ssh.exec_command(f"ls -lh {remote_db_path}")
            file_info = stdout.read().decode()
            print(f"📊 Информация о файле: {file_info.strip()}")
            
        else:
            print("❌ База данных ghost.db не найдена")
            print("📋 Доступные файлы:")
            print(files)
            return False
        
        # Скачиваем базу данных
        print(f"\n📥 Скачивание базы данных...")
        local_db_path = "./ghost_server_real.db"
        
        sftp = ssh.open_sftp()
        sftp.get(remote_db_path, local_db_path)
        sftp.close()
        
        print(f"✅ База данных скачана: {local_db_path}")
        
        # Анализируем содержимое
        print(f"\n📊 Анализ данных...")
        with sqlite3.connect(local_db_path) as conn:
            cursor = conn.cursor()
            
            # Получаем схему таблицы trades
            cursor.execute("PRAGMA table_info(trades)")
            columns = cursor.fetchall()
            print(f"📋 Колонок в таблице trades: {len(columns)}")
            
            # Показываем некоторые колонки
            print("🏷️  Основные колонки:")
            for col in columns[:10]:  # Первые 10 колонок
                print(f"  • {col[1]} ({col[2]})")
            
            if len(columns) > 10:
                print(f"  ... и еще {len(columns) - 10} колонок")
            
            # Считаем трейды
            cursor.execute("SELECT COUNT(*) FROM trades")
            total_trades = cursor.fetchone()[0]
            print(f"\n📈 Всего трейдов: {total_trades}")
            
            if total_trades > 0:
                # Последние 3 трейда
                cursor.execute("""
                    SELECT symbol, side, entry_price, opened_at 
                    FROM trades 
                    WHERE symbol IS NOT NULL
                    ORDER BY opened_at DESC 
                    LIMIT 3
                """)
                recent_trades = cursor.fetchall()
                
                print("🔥 Последние трейды:")
                for trade in recent_trades:
                    symbol, side, price, time = trade
                    print(f"  • {symbol} {side} @ {price} ({time})")
                
                # Статистика по символам
                cursor.execute("""
                    SELECT symbol, COUNT(*) as count 
                    FROM trades 
                    WHERE symbol IS NOT NULL
                    GROUP BY symbol 
                    ORDER BY count DESC 
                    LIMIT 5
                """)
                symbols = cursor.fetchall()
                
                print("\n📊 Топ символы:")
                for symbol, count in symbols:
                    print(f"  • {symbol}: {count} трейдов")
        
        # Создаем тестовые данные для API
        print(f"\n🔄 Создание тестовых данных для API...")
        create_test_api_data(local_db_path)
        
        ssh.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def create_test_api_data(db_path):
    """Создать тестовые данные для API из реальной БД"""
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Получаем реальные трейды
            cursor.execute("""
                SELECT 
                    id, symbol, side, entry_price, exit_price,
                    pnl_net, roi_percent, opened_at, closed_at
                FROM trades 
                WHERE symbol IS NOT NULL
                ORDER BY opened_at DESC 
                LIMIT 10
            """)
            trades = cursor.fetchall()
            
            # Создаем JSON данные
            api_data = []
            for trade in trades:
                trade_data = {
                    "trade_id": trade[0],
                    "symbol": trade[1],
                    "side": trade[2],
                    "entry_price": trade[3],
                    "exit_price": trade[4],
                    "pnl": trade[5],
                    "roi": trade[6],
                    "opened_at": trade[7],
                    "closed_at": trade[8],
                    "synced_at": datetime.now().isoformat()
                }
                api_data.append(trade_data)
            
            # Сохраняем для тестирования API
            import json
            os.makedirs("news_engine/output", exist_ok=True)
            
            with open("news_engine/output/real_trades.json", "w") as f:
                json.dump(api_data, f, indent=2, default=str)
            
            print(f"✅ Сохранено {len(api_data)} реальных трейдов для API")
            
    except Exception as e:
        print(f"❌ Ошибка создания API данных: {e}")

def main():
    """Основная функция"""
    print("🚀 GHOST - Тестирование сервера Дарэна")
    print("=" * 50)
    
    success = test_connection()
    
    if success:
        print("\n🎉 Тестирование успешно!")
        print("\n📋 Следующие шаги:")
        print("1. Настройте Supabase ключи")
        print("2. Запустите синхронизацию")
        print("3. Проверьте веб-дашборд")
    else:
        print("\n❌ Тестирование не удалось")

if __name__ == "__main__":
    main()
