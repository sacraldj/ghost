#!/usr/bin/env python3
"""
БЕЗОПАСНОЕ подключение к серверу Дарэна
Только читает данные, НЕ изменяет файлы на сервере
"""

import paramiko
import sqlite3
import json
import os
from datetime import datetime
import tempfile

def safe_download_db():
    """Безопасно скачать копию базы данных с сервера"""
    
    print("🔐 БЕЗОПАСНОЕ подключение к серверу Дарэна...")
    print("📋 Действия:")
    print("  ✅ Скачать КОПИЮ ghost.db")
    print("  ❌ НЕ изменять файлы на сервере")
    print("  ❌ НЕ влиять на работу системы")
    
    # SSH параметры
    hostname = "138.199.226.247"
    username = "root"
    remote_db_path = "/root/ghost_system_final/ghost_system_final_146/ghost.db"
    
    try:
        # Создаем SSH клиент
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        print(f"🔌 Подключение к {hostname}...")
        
        # Пробуем подключиться с паролем из переменных окружения
        password = os.getenv("DAREN_SSH_PASSWORD")
        if not password:
            password = input("Введите пароль SSH: ")
        
        ssh.connect(hostname, username=username, password=password, timeout=10)
        
        print("✅ SSH подключение успешно!")
        
        # Проверяем существование базы данных
        stdin, stdout, stderr = ssh.exec_command(f"ls -la {remote_db_path}")
        output = stdout.read().decode()
        
        if "ghost.db" not in output:
            print(f"❌ База данных не найдена: {remote_db_path}")
            return False
            
        print(f"📊 База данных найдена: {remote_db_path}")
        
        # Скачиваем базу данных в временный файл
        local_db_path = "./ghost_server_live.db"
        
        print(f"📥 Скачивание базы данных...")
        sftp = ssh.open_sftp()
        sftp.get(remote_db_path, local_db_path)
        sftp.close()
        
        print(f"✅ База данных скачана: {local_db_path}")
        
        # Проверяем содержимое
        with sqlite3.connect(local_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM trades")
            trade_count = cursor.fetchone()[0]
            
            print(f"📈 Найдено {trade_count} трейдов в базе данных")
            
            # Показываем последние 3 трейда
            cursor.execute("""
                SELECT symbol, side, entry_price, opened_at 
                FROM trades 
                ORDER BY opened_at DESC 
                LIMIT 3
            """)
            recent_trades = cursor.fetchall()
            
            print("📋 Последние трейды:")
            for trade in recent_trades:
                symbol, side, price, time = trade
                print(f"  • {symbol} {side} @ {price} ({time})")
        
        ssh.close()
        return True
        
    except paramiko.AuthenticationException:
        print("❌ Ошибка аутентификации SSH")
        return False
    except paramiko.SSHException as e:
        print(f"❌ Ошибка SSH: {e}")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def sync_to_supabase():
    """Синхронизировать данные в Supabase"""
    print("\n🔄 Синхронизация с Supabase...")
    
    # Используем наш готовый скрипт синхронизации
    os.environ["GHOST_DB_PATH"] = "./ghost_server_live.db"
    os.environ["SYNC_LOOP"] = "0"  # Одноразовая синхронизация
    
    try:
        import subprocess
        result = subprocess.run([
            "python3", "news_engine/trades_supabase_sync.py"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Синхронизация с Supabase успешна!")
            print(result.stdout)
        else:
            print("❌ Ошибка синхронизации:")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Ошибка запуска синхронизации: {e}")

def main():
    """Основная функция"""
    print("🚀 GHOST - Безопасное подключение к серверу Дарэна")
    print("=" * 60)
    
    # Проверяем переменные окружения Supabase
    if not os.getenv("NEXT_PUBLIC_SUPABASE_URL"):
        print("⚠️  Переменные Supabase не настроены")
        print("📝 Создайте .env.local с ключами Supabase")
        return
    
    # Скачиваем базу данных
    if safe_download_db():
        print("\n" + "=" * 60)
        
        # Синхронизируем с Supabase
        sync_to_supabase()
        
        print("\n🎉 Готово! Данные обновлены в веб-дашборде")
        print("🌐 Откройте http://localhost:3000/dashboard")
    else:
        print("\n❌ Не удалось подключиться к серверу")

if __name__ == "__main__":
    main()
