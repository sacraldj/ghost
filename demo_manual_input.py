#!/usr/bin/env python3
"""
Демонстрация системы ручного ввода кода авторизации
БЕЗ реального подключения к Telegram
"""

import os
import sys

# Добавляем текущую директорию в path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def demo_manual_code_input():
    """Демонстрация функции ручного ввода кода"""
    try:
        from core.telegram_auto_auth import TelegramAutoAuth
        
        print("🎭 ДЕМОНСТРАЦИЯ РУЧНОГО ВВОДА КОДА")
        print("=" * 40)
        print("Это демонстрация БЕЗ реального подключения к Telegram")
        print("-" * 40)
        
        # Создаем экземпляр auth для демонстрации
        auth = TelegramAutoAuth("12345", "test_hash", "+1234567890", interactive=True)
        
        print("\n🔍 Вызываем функцию get_manual_code_input...")
        code = auth.get_manual_code_input("+1234567890")
        
        if code:
            print(f"\n✅ Получен код: {code}")
            print("🔍 Проверим валидность кода:")
            
            if code.isdigit() and len(code) == 5:
                print("✅ Код корректный: 5 цифр")
            elif code.isdigit():
                print(f"⚠️ Код содержит {len(code)} цифр (ожидается 5)")
            else:
                print("❌ Код содержит нецифровые символы")
        else:
            print("❌ Код не был введен или ввод прерван")
            
    except KeyboardInterrupt:
        print("\n❌ Демо прервано пользователем")
    except Exception as e:
        print(f"❌ Ошибка демонстрации: {e}")

def show_feature_overview():
    """Показать обзор новых возможностей"""
    print("\n🚀 НОВЫЕ ВОЗМОЖНОСТИ СИСТЕМЫ АВТОРИЗАЦИИ")
    print("=" * 50)
    
    features = [
        "🛡️ Защита от многократных подключений (max 3 попытки в день)",
        "⏰ Ограничение попыток в час (max 2 попытки)",
        "🔄 Автоматический fallback на ручной ввод после 3 неудачных попыток",
        "🔑 Ручной ввод кода авторизации при неудаче автоматического",
        "🔒 Ручной ввод пароля 2FA при отсутствии в переменных окружения",
        "📊 Детальное логирование всех попыток авторизации",
        "🚫 Автоматическая обработка FloodWaitError блокировок",
        "⚙️ Настраиваемый интерактивный/неинтерактивный режим"
    ]
    
    for i, feature in enumerate(features, 1):
        print(f"{i:2d}. {feature}")
    
    print("\n💡 РЕЖИМЫ РАБОТЫ:")
    print("   interactive=True  - включает ручной ввод (по умолчанию)")
    print("   interactive=False - только автоматический режим")
    
    print("\n🔧 ИСПОЛЬЗОВАНИЕ:")
    print("   # Стандартное подключение с ручным вводом")
    print("   client = await create_auto_auth_client()")
    print("   ")
    print("   # Только автоматический режим (для серверов)")
    print("   client = await create_auto_auth_client(interactive=False)")

def show_protection_status():
    """Показать текущий статус защиты"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        from core.telegram_rate_limiter import TelegramRateLimiter
        
        rate_limiter = TelegramRateLimiter()
        phone = os.getenv('TELEGRAM_PHONE')
        
        if phone:
            print(f"\n🛡️ СТАТУС ЗАЩИТЫ ДЛЯ {phone}")
            print("-" * 40)
            
            can_attempt, reason = rate_limiter.can_attempt_auth(phone)
            stats = rate_limiter.get_stats(phone)
            
            if can_attempt:
                print("✅ Попытки авторизации РАЗРЕШЕНЫ")
            else:
                print("🚫 Попытки авторизации ЗАБЛОКИРОВАНЫ")
                print(f"   Причина: {reason}")
            
            print(f"\n📊 Статистика:")
            print(f"   Попыток сегодня: {stats['attempts_today']}/{stats['max_attempts_per_day']}")
            print(f"   Попыток в этом часу: {stats['attempts_this_hour']}/{stats['max_attempts_per_hour']}")
            print(f"   Успешных: {stats['successful_today']}")
            print(f"   Неудачных: {stats['failed_today']}")
            
            if stats['is_blocked']:
                hours = stats['block_remaining_seconds'] // 3600
                minutes = (stats['block_remaining_seconds'] % 3600) // 60
                print(f"   🚫 Блокировка: {hours}ч {minutes}м")
        else:
            print("\n⚠️ TELEGRAM_PHONE не найден в .env")
            
    except Exception as e:
        print(f"\n❌ Ошибка проверки статуса: {e}")

def main():
    """Главная функция демонстрации"""
    print("🎯 ДЕМОНСТРАЦИЯ УЛУЧШЕННОЙ СИСТЕМЫ АВТОРИЗАЦИИ TELEGRAM")
    print("🔧 С ручным вводом и защитой от блокировок")
    print("=" * 65)
    
    # Показываем обзор возможностей
    show_feature_overview()
    
    # Показываем статус защиты
    show_protection_status()
    
    # Предлагаем протестировать ручной ввод
    print("\n" + "="*50)
    choice = input("❓ Протестировать функцию ручного ввода кода? (y/N): ").strip().lower()
    
    if choice in ['y', 'yes', 'да', 'у']:
        demo_manual_code_input()
    else:
        print("⏭️ Демонстрация ручного ввода пропущена")
    
    print("\n✅ Демонстрация завершена!")
    print("\n💡 Для полного тестирования используйте: python test_manual_auth.py")

if __name__ == "__main__":
    main()
