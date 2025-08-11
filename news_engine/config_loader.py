#!/usr/bin/env python3
"""
GHOST News Engine - Config Loader
Загружает переменные окружения в конфигурацию YAML
"""

import sys
import os
import yaml
import re
from pathlib import Path
from typing import Dict, Any

class ConfigLoader:
    """Загрузчик конфигурации с поддержкой переменных окружения"""
    
    def __init__(self, config_path: str = "news_engine_config.yaml", env_path: str = None):
        self.config_path = config_path
        
        # Ищем .env файл в корне проекта
        if env_path is None:
            # Поднимаемся на 2 уровня вверх от news_engine/ до корня
            current_dir = Path(__file__).parent
            root_dir = current_dir.parent.parent
            self.env_path = root_dir / ".env"
        else:
            self.env_path = Path(env_path)
            
        self.env_vars = {}
        self.load_env_vars()
    
    def load_env_vars(self):
        """Загружает переменные окружения из .env файла"""
        env_file = Path(self.env_path)
        
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        self.env_vars[key.strip()] = value.strip()
        
        # Также загружаем из системных переменных окружения
        for key, value in os.environ.items():
            if key not in self.env_vars:
                self.env_vars[key] = value
    
    def substitute_env_vars(self, value: str) -> str:
        """Заменяет переменные окружения в строке"""
        if not isinstance(value, str):
            return value
        
        # Ищем паттерн ${VARIABLE_NAME}
        pattern = r'\$\{([^}]+)\}'
        
        def replace_var(match):
            var_name = match.group(1)
            return self.env_vars.get(var_name, f"${{{var_name}}}")
        
        return re.sub(pattern, replace_var, value)
    
    def process_value(self, value: Any) -> Any:
        """Обрабатывает значение, заменяя переменные окружения"""
        if isinstance(value, str):
            return self.substitute_env_vars(value)
        elif isinstance(value, dict):
            return {k: self.process_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.process_value(item) for item in value]
        else:
            return value
    
    def load_config(self) -> Dict[str, Any]:
        """Загружает конфигурацию с заменой переменных окружения"""
        if not Path(self.config_path).exists():
            raise FileNotFoundError(f"Конфигурационный файл не найден: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Обрабатываем все значения, заменяя переменные окружения
        processed_config = self.process_value(config)
        
        return processed_config
    
    def save_config(self, config: Dict[str, Any], output_path: str = None):
        """Сохраняет обработанную конфигурацию"""
        if output_path is None:
            output_path = self.config_path.replace('.yaml', '_processed.yaml')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)
        
        print(f"Конфигурация сохранена в: {output_path}")
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Проверяет валидность конфигурации"""
        required_sources = ['newsapi', 'cryptocompare']
        
        if 'sources' not in config:
            print("❌ Отсутствует секция 'sources' в конфигурации")
            return False
        
        for source in required_sources:
            if source not in config['sources']:
                print(f"❌ Отсутствует обязательный источник: {source}")
                return False
            
            source_config = config['sources'][source]
            if not source_config.get('enabled', False):
                print(f"⚠️  Источник {source} отключен")
            else:
                api_key = source_config.get('api_key', '')
                if not api_key or api_key.startswith('your_') or api_key.startswith('${'):
                    print(f"⚠️  Источник {source} не имеет валидного API ключа")
        
        return True
    
    def print_config_summary(self, config: Dict[str, Any]):
        """Выводит краткую сводку конфигурации"""
        print("\n📋 Сводка конфигурации GHOST News Engine:")
        print("=" * 50)
        
        if 'sources' in config:
            print(f"📰 Источники новостей: {len(config['sources'])}")
            enabled_sources = [name for name, cfg in config['sources'].items() 
                             if cfg.get('enabled', False)]
            print(f"✅ Включенные источники: {', '.join(enabled_sources)}")
        
        if 'notifications' in config:
            notif_config = config['notifications']
            if 'channels' in notif_config:
                channels = notif_config['channels']
                enabled_channels = [name for name, cfg in channels.items() 
                                  if cfg.get('enabled', False)]
                print(f"🔔 Каналы уведомлений: {', '.join(enabled_channels)}")
        
        print(f"📊 Уровень логирования: {config.get('monitoring', {}).get('log_level', 'INFO')}")
        print("=" * 50)

def main():
    """Основная функция"""
    try:
        # Поддержка аргументов командной строки
        config_path = "news_engine_config.yaml"
        if len(sys.argv) > 1:
            config_path = sys.argv[1]
        
        print(f"🔍 Загружаем конфигурацию из: {config_path}")
        
        loader = ConfigLoader(config_path)
        config = loader.load_config()
        
        # Валидация конфигурации
        if loader.validate_config(config):
            print("✅ Конфигурация загружена успешно")
            loader.print_config_summary(config)
            
            # Сохраняем обработанную конфигурацию
            loader.save_config(config)
        else:
            print("❌ Конфигурация содержит ошибки")
            
    except Exception as e:
        print(f"❌ Ошибка при загрузке конфигурации: {e}")

if __name__ == "__main__":
    main()
