#!/usr/bin/env python3
"""
GHOST News Engine - Test Configuration
Тестирует конфигурацию и API ключи
"""

import os
import sys
from pathlib import Path
from config_loader import ConfigLoader

def test_env_file():
    """Проверяет наличие и содержимое .env файла"""
    print("🔍 Проверка файла .env...")
    
    # Ищем .env в корне проекта Ghost/
    current_dir = Path(__file__).parent
    root_dir = current_dir.parent  # Поднимаемся на 1 уровень вверх от news_engine/ до Ghost/
    env_path = root_dir / ".env"
    
    if not env_path.exists():
        print(f"❌ Файл .env не найден в корне проекта: {env_path}")
        print("💡 Создайте его командой: cp env.example .env")
        return False
    
    print("✅ Файл .env найден")
    
    # Проверяем содержимое
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    api_keys = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            if 'API_KEY' in key or 'TOKEN' in key or 'SECRET' in key:
                api_keys.append((key, value))
    
    print(f"📋 Найдено {len(api_keys)} API ключей:")
    for key, value in api_keys:
        if value.startswith('your_') or value.startswith('${'):
            print(f"  ⚠️  {key}: не настроен")
        else:
            print(f"  ✅ {key}: настроен")
    
    return True

def test_config_loading():
    """Тестирует загрузку конфигурации"""
    print("\n🔍 Тестирование загрузки конфигурации...")
    
    try:
        # Используем правильный путь к конфигурации
        config_path = Path(__file__).parent.parent / "news_engine_config.yaml"
        loader = ConfigLoader(str(config_path))
        config = loader.load_config()
        print("✅ Конфигурация загружена успешно")
        return config
    except Exception as e:
        print(f"❌ Ошибка загрузки конфигурации: {e}")
        return None

def test_api_connections(config):
    """Тестирует подключения к API"""
    if not config:
        return
    
    print("\n🔍 Тестирование подключений к API...")
    
    # Простые тесты для основных API
    test_apis = [
        ('newsapi', 'NEWS_API_KEY'),
        ('cryptocompare', 'CRYPTOCOMPARE_API_KEY'),
        ('alphavantage', 'ALPHA_VANTAGE_API_KEY'),
    ]
    
    for api_name, env_key in test_apis:
        if api_name in config.get('sources', {}):
            source_config = config['sources'][api_name]
            if source_config.get('enabled', False):
                api_key = source_config.get('api_key', '')
                if api_key and not api_key.startswith('${'):
                    print(f"  ✅ {api_name}: настроен")
                else:
                    print(f"  ⚠️  {api_name}: не настроен")
            else:
                print(f"  ❌ {api_name}: отключен")
        else:
            print(f"  ❌ {api_name}: не найден в конфигурации")

def main():
    """Основная функция"""
    print("🚀 GHOST News Engine - Тест конфигурации")
    print("=" * 50)
    
    # Проверяем .env файл
    if not test_env_file():
        sys.exit(1)
    
    # Загружаем конфигурацию
    config = test_config_loading()
    if not config:
        sys.exit(1)
    
    # Тестируем API
    test_api_connections(config)
    
    # Показываем сводку
    print("\n📋 Сводка конфигурации:")
    print("=" * 50)
    
    if 'sources' in config:
        sources = config['sources']
        enabled_count = sum(1 for s in sources.values() if s.get('enabled', False))
        total_count = len(sources)
        print(f"📰 Всего источников: {total_count}")
        print(f"✅ Включенных: {enabled_count}")
        print(f"❌ Отключенных: {total_count - enabled_count}")
    
    print("\n🎯 Рекомендации:")
    if not os.getenv('NEWS_API_KEY'):
        print("  • Получите API ключ на https://newsapi.org/ (бесплатно)")
    if not os.getenv('CRYPTOCOMPARE_API_KEY'):
        print("  • Получите API ключ на https://www.cryptocompare.com/ (бесплатно)")
    if not os.getenv('ALPHA_VANTAGE_API_KEY'):
        print("  • Получите API ключ на https://www.alphavantage.co/ (бесплатно)")
    
    print("\n✅ Тест завершен!")

if __name__ == "__main__":
    main()
