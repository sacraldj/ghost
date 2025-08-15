#!/usr/bin/env python3
"""
Быстрая настройка переменных окружения для Telegram
"""

import os
from dotenv import set_key, load_dotenv

def setup_telegram_env():
    """Настройка переменных окружения для Telegram"""
    print("🔧 НАСТРОЙКА TELEGRAM ПЕРЕМЕННЫХ ОКРУЖЕНИЯ")
    print("=" * 50)
    
    # Загружаем существующие переменные
    load_dotenv()
    
    env_file = '.env'
    
    # API ID
    current_api_id = os.getenv('TELEGRAM_API_ID')
    if current_api_id:
        print(f"✅ TELEGRAM_API_ID уже установлен: {current_api_id}")
    else:
        api_id = input("📱 Введите TELEGRAM_API_ID: ").strip()
        if api_id:
            set_key(env_file, 'TELEGRAM_API_ID', api_id)
            print("✅ TELEGRAM_API_ID сохранен")
    
    # API Hash
    current_api_hash = os.getenv('TELEGRAM_API_HASH')
    if current_api_hash:
        print(f"✅ TELEGRAM_API_HASH уже установлен: {current_api_hash[:10]}...")
    else:
        api_hash = input("🔐 Введите TELEGRAM_API_HASH: ").strip()
        if api_hash:
            set_key(env_file, 'TELEGRAM_API_HASH', api_hash)
            print("✅ TELEGRAM_API_HASH сохранен")
    
    # Phone
    current_phone = os.getenv('TELEGRAM_PHONE')
    if current_phone:
        print(f"✅ TELEGRAM_PHONE уже установлен: {current_phone}")
    else:
        phone = input("📞 Введите номер телефона (например +1234567890): ").strip()
        if phone:
            set_key(env_file, 'TELEGRAM_PHONE', phone)
            print("✅ TELEGRAM_PHONE сохранен")
    
    # Опционально - код (если знаете заранее)
    code = input("📱 Введите код Telegram (или Enter для автоматического получения): ").strip()
    if code:
        set_key(env_file, 'TELEGRAM_CODE', code)
        print("✅ TELEGRAM_CODE сохранен")
    
    # Опционально - пароль 2FA
    password = input("🔒 Введите пароль 2FA (или Enter если нет): ").strip()
    if password:
        set_key(env_file, 'TELEGRAM_PASSWORD', password)
        print("✅ TELEGRAM_PASSWORD сохранен")
    
    print(f"\n🎉 Настройка завершена!")
    print(f"📁 Переменные сохранены в {env_file}")
    print(f"🚀 Теперь можно запускать систему")
    
    return True

if __name__ == "__main__":
    try:
        setup_telegram_env()
    except KeyboardInterrupt:
        print("\n👋 Настройка прервана")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
