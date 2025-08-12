#!/usr/bin/env python3
"""
БЕЗОПАСНАЯ установка GHOST на сервер Дарэна
НЕ изменяет существующие файлы, только добавляет новые
"""

import paramiko
import os
import io

def safe_install_on_server():
    """Безопасно установить GHOST модули на сервер"""
    
    print("🛡️  БЕЗОПАСНАЯ установка GHOST на сервер Дарэна")
    print("=" * 60)
    print("✅ ЧТО БУДЕТ СДЕЛАНО:")
    print("  • Создать папку /ghost_addon/ (отдельно от основной системы)")
    print("  • Скопировать файлы синхронизации")
    print("  • Установить зависимости в отдельный venv")
    print("  • НЕ трогать существующие файлы Дарэна")
    print()
    print("❌ ЧТО НЕ БУДЕТ ЗАТРОНУТО:")
    print("  • Основная папка ghost_system_final")
    print("  • Файлы торговой системы")
    print("  • Конфигурации и настройки")
    print("  • Существующие процессы")
    print()
    
    confirm = input("Продолжить безопасную установку? (yes/no): ")
    if confirm.lower() not in ['yes', 'y']:
        print("Установка отменена")
        return False
    
    # SSH параметры
    hostname = "138.199.226.247"
    username = "root"
    
    try:
        # SSH подключение
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        password = os.getenv("DAREN_SSH_PASSWORD")
        if not password:
            password = input("Введите пароль SSH: ")
        
        print(f"🔌 Подключение к {hostname}...")
        ssh.connect(hostname, username=username, password=password, timeout=10)
        print("✅ SSH подключение успешно!")
        
        # Создаем отдельную папку для GHOST
        print("\n📁 Создание безопасной папки...")
        commands = [
            "mkdir -p /root/ghost_addon",
            "cd /root/ghost_addon",
            "pwd"
        ]
        
        for cmd in commands:
            stdin, stdout, stderr = ssh.exec_command(cmd)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            
            if error:
                print(f"❌ Ошибка: {error}")
                return False
            
            if "ghost_addon" in output:
                print(f"✅ Рабочая папка: {output}")
        
        # Создаем Python venv отдельно
        print("\n🐍 Создание отдельного Python окружения...")
        venv_commands = [
            "cd /root/ghost_addon",
            "python3.10 -m venv ghost_venv",
            "source ghost_venv/bin/activate && pip install --upgrade pip",
            "source ghost_venv/bin/activate && pip install supabase python-dotenv paramiko"
        ]
        
        for cmd in venv_commands:
            stdin, stdout, stderr = ssh.exec_command(cmd)
            stdout.read()  # Ждем завершения
            print(f"✅ Выполнено: {cmd.split('&&')[-1].strip()}")
        
        # Копируем файлы синхронизации
        print("\n📤 Копирование файлов...")
        sftp = ssh.open_sftp()
        
        # Читаем локальный файл синхронизации
        with open("news_engine/trades_supabase_sync.py", "r") as f:
            sync_content = f.read()
        
        # Создаем файл на сервере
        with sftp.file("/root/ghost_addon/trades_sync.py", "w") as remote_file:
            remote_file.write(sync_content)
        
        print("✅ Файл trades_sync.py скопирован")
        
        # Создаем конфигурационный файл
        config_content = """# GHOST Addon Configuration
# Отдельная конфигурация для синхронизации (НЕ влияет на основную систему)

# Supabase (заполните своими ключами)
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# Путь к основной базе данных (только чтение)
GHOST_DB_PATH=/root/ghost_system_final/ghost_system_final_146/ghost.db

# Настройки синхронизации
SYNC_INTERVAL_SEC=60
SYNC_LOOP=1
"""
        
        with sftp.file("/root/ghost_addon/.env", "w") as remote_file:
            remote_file.write(config_content)
        
        print("✅ Конфигурация .env создана")
        
        # Создаем скрипт запуска
        startup_script = """#!/bin/bash
# GHOST Addon Startup Script

cd /root/ghost_addon
source ghost_venv/bin/activate

echo "🚀 Запуск GHOST синхронизации..."
echo "📊 База данных: $GHOST_DB_PATH"
echo "🔄 Интервал: $SYNC_INTERVAL_SEC секунд"

python trades_sync.py
"""
        
        with sftp.file("/root/ghost_addon/start_sync.sh", "w") as remote_file:
            remote_file.write(startup_script)
        
        # Делаем исполняемым
        ssh.exec_command("chmod +x /root/ghost_addon/start_sync.sh")
        
        print("✅ Скрипт запуска создан")
        
        sftp.close()
        
        # Проверяем установку
        print("\n🔍 Проверка установки...")
        stdin, stdout, stderr = ssh.exec_command("ls -la /root/ghost_addon/")
        files = stdout.read().decode()
        print("📁 Установленные файлы:")
        print(files)
        
        # Создаем инструкцию
        instructions = """
🎉 GHOST безопасно установлен!

📁 Местоположение: /root/ghost_addon/
🔐 Изоляция: Полностью отдельно от основной системы

🔧 Настройка (обязательно):
1. Отредактируйте файл: nano /root/ghost_addon/.env
2. Добавьте ваши ключи Supabase
3. Сохраните файл

🚀 Запуск:
cd /root/ghost_addon
./start_sync.sh

🔄 Автозапуск в tmux:
tmux new-window -n ghost_sync 'cd /root/ghost_addon && ./start_sync.sh'

🛟 Удаление (если нужно):
rm -rf /root/ghost_addon

⚠️  ВАЖНО: Основная система Дарэна НЕ ЗАТРОНУТА!
"""
        
        print(instructions)
        
        ssh.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка установки: {e}")
        return False

def main():
    """Основная функция"""
    print("🚀 GHOST - Безопасная установка на сервер")
    
    success = safe_install_on_server()
    
    if success:
        print("\n✅ Установка завершена успешно!")
        print("📋 Следующие шаги:")
        print("1. Настройте ключи Supabase в .env")
        print("2. Запустите синхронизацию")
        print("3. Проверьте веб-дашборд")
    else:
        print("\n❌ Установка не удалась")

if __name__ == "__main__":
    main()
