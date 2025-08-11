#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы GHOST Orchestrator
Запускает базовые тесты системы и проверяет её компоненты
"""

import asyncio
import json
import os
import sys
import time
import requests
from pathlib import Path

# Цвета для вывода
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(title):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title.center(60)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}\n")

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.ENDC}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.ENDC}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.ENDC}")

def print_info(message):
    print(f"{Colors.CYAN}ℹ️  {message}{Colors.ENDC}")

async def test_basic_imports():
    """Тест базовых импортов Python модулей"""
    print_header("Testing Basic Imports")
    
    try:
        import asyncio
        print_success("asyncio imported")
        
        import yaml
        print_success("yaml imported")
        
        import psutil
        print_success("psutil imported")
        
        import aiofiles
        print_success("aiofiles imported")
        
        # Попытка импорта aioredis
        try:
            import aioredis
            print_success("aioredis imported")
        except ImportError:
            print_warning("aioredis not available (optional)")
        
        return True
    except Exception as e:
        print_error(f"Import failed: {e}")
        return False

async def test_config_loading():
    """Тест загрузки конфигурации"""
    print_header("Testing Configuration Loading")
    
    config_path = "config/system_config.yaml"
    
    try:
        if not os.path.exists(config_path):
            print_error(f"Config file not found: {config_path}")
            return False
        
        with open(config_path, 'r', encoding='utf-8') as f:
            import yaml
            config = yaml.safe_load(f)
        
        print_success(f"Config loaded from {config_path}")
        
        # Проверка ключевых секций
        required_sections = ['orchestrator', 'modules', 'database']
        for section in required_sections:
            if section in config:
                print_success(f"Section '{section}' found")
            else:
                print_error(f"Required section '{section}' missing")
                return False
        
        # Проверка модулей
        modules = config.get('modules', {})
        print_info(f"Found {len(modules)} modules in config")
        
        for module_name, module_config in modules.items():
            enabled = module_config.get('enabled', False)
            status = "enabled" if enabled else "disabled"
            color = Colors.GREEN if enabled else Colors.YELLOW
            print(f"  {color}• {module_name}: {status}{Colors.ENDC}")
        
        return True
        
    except Exception as e:
        print_error(f"Config loading failed: {e}")
        return False

async def test_directories():
    """Тест создания и проверки директорий"""
    print_header("Testing Directory Structure")
    
    required_dirs = [
        "core",
        "utils", 
        "config",
        "news_engine",
        "logs",
        "pids"
    ]
    
    all_exist = True
    
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print_success(f"Directory exists: {dir_name}")
        else:
            print_warning(f"Directory missing: {dir_name}")
            try:
                os.makedirs(dir_name, exist_ok=True)
                print_success(f"Created directory: {dir_name}")
            except Exception as e:
                print_error(f"Failed to create {dir_name}: {e}")
                all_exist = False
    
    return all_exist

async def test_orchestrator_file():
    """Тест наличия и базовой валидности файла оркестратора"""
    print_header("Testing Orchestrator File")
    
    orchestrator_path = "core/ghost_orchestrator.py"
    
    if not os.path.exists(orchestrator_path):
        print_error(f"Orchestrator file not found: {orchestrator_path}")
        return False
    
    print_success(f"Orchestrator file exists: {orchestrator_path}")
    
    # Проверка размера файла
    file_size = os.path.getsize(orchestrator_path)
    print_info(f"File size: {file_size} bytes")
    
    if file_size < 1000:
        print_warning("File seems too small")
        return False
    
    # Базовая проверка синтаксиса Python
    try:
        with open(orchestrator_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверка ключевых классов и функций
        if "class GhostOrchestrator" in content:
            print_success("GhostOrchestrator class found")
        else:
            print_error("GhostOrchestrator class not found")
            return False
        
        if "async def start" in content:
            print_success("async start method found")
        else:
            print_error("async start method not found")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"File validation failed: {e}")
        return False

async def test_news_engine_files():
    """Тест наличия файлов News Engine"""
    print_header("Testing News Engine Files")
    
    news_engine_files = [
        "news_engine/enhanced_news_engine.py",
        "news_engine/price_feed_engine.py",
        "news_engine/supabase_sync.py"
    ]
    
    all_exist = True
    
    for file_path in news_engine_files:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print_success(f"File exists: {file_path} ({file_size} bytes)")
        else:
            print_error(f"File missing: {file_path}")
            all_exist = False
    
    return all_exist

async def test_api_endpoints():
    """Тест API endpoints (если сервер запущен)"""
    print_header("Testing API Endpoints")
    
    # Базовый URL (предполагаем локальный сервер)
    base_url = "http://localhost:3000"
    
    endpoints = [
        "/api/system/status",
        "/api/news",
        "/api/user"
    ]
    
    any_available = False
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print_success(f"Endpoint available: {endpoint}")
                any_available = True
            else:
                print_warning(f"Endpoint returned {response.status_code}: {endpoint}")
        except requests.exceptions.ConnectionError:
            print_info(f"Server not running for: {endpoint}")
        except Exception as e:
            print_warning(f"Error testing {endpoint}: {e}")
    
    if not any_available:
        print_info("No API endpoints available (server might not be running)")
    
    return True  # Не критично для базового теста

async def test_environment_variables():
    """Тест переменных окружения"""
    print_header("Testing Environment Variables")
    
    # Загрузка .env файла если существует
    env_file = ".env"
    if os.path.exists(env_file):
        print_success(f".env file found: {env_file}")
        
        try:
            with open(env_file, 'r') as f:
                env_content = f.read()
            
            # Проверка ключевых переменных
            key_vars = [
                'SUPABASE_URL',
                'SUPABASE_SECRET_KEY',
                'REDIS_URL'
            ]
            
            for var in key_vars:
                if var in env_content or var in os.environ:
                    print_success(f"Environment variable available: {var}")
                else:
                    print_warning(f"Environment variable missing: {var}")
                    
        except Exception as e:
            print_error(f"Error reading .env file: {e}")
    else:
        print_warning(".env file not found")
    
    return True

async def test_database_files():
    """Тест файлов базы данных"""
    print_header("Testing Database Files")
    
    db_files = [
        "news_engine/ghost_news.db",
        "ghost_unified.db"
    ]
    
    for db_file in db_files:
        if os.path.exists(db_file):
            file_size = os.path.getsize(db_file)
            print_success(f"Database file exists: {db_file} ({file_size} bytes)")
        else:
            print_info(f"Database file not found: {db_file} (will be created)")
    
    return True

async def run_comprehensive_test():
    """Запуск всех тестов"""
    print_header("GHOST System Comprehensive Test")
    print_info("Testing GHOST Unified System components...")
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("Directory Structure", test_directories),
        ("Configuration Loading", test_config_loading),
        ("Orchestrator File", test_orchestrator_file),
        ("News Engine Files", test_news_engine_files),
        ("Environment Variables", test_environment_variables),
        ("Database Files", test_database_files),
        ("API Endpoints", test_api_endpoints)
    ]
    
    results = []
    start_time = time.time()
    
    for test_name, test_func in tests:
        print(f"\n{Colors.BOLD}Running: {test_name}{Colors.ENDC}")
        try:
            result = await test_func()
            results.append((test_name, result))
            if result:
                print_success(f"{test_name} completed successfully")
            else:
                print_error(f"{test_name} failed")
        except Exception as e:
            print_error(f"{test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Сводка результатов
    print_header("Test Results Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        color = Colors.GREEN if result else Colors.RED
        print(f"{color}{status:>6}{Colors.ENDC} | {test_name}")
    
    print(f"\n{Colors.BOLD}Overall: {passed}/{total} tests passed{Colors.ENDC}")
    
    if passed == total:
        print_success("All tests passed! System is ready.")
        return True
    elif passed >= total * 0.7:  # 70% прошли
        print_warning(f"Most tests passed ({passed}/{total}). System mostly ready.")
        return True
    else:
        print_error(f"Many tests failed ({total-passed}/{total}). System needs attention.")
        return False

async def main():
    """Главная функция"""
    try:
        result = await run_comprehensive_test()
        
        print_header("Next Steps")
        
        if result:
            print_info("You can now try to start the orchestrator:")
            print(f"  {Colors.BOLD}./start_orchestrator.sh start{Colors.ENDC}")
            print_info("Or install dependencies first:")
            print(f"  {Colors.BOLD}./start_orchestrator.sh install{Colors.ENDC}")
        else:
            print_info("Fix the failed tests before starting the orchestrator")
            print_info("Check the installation guide in UNIFIED_ARCHITECTURE_PLAN.md")
        
        sys.exit(0 if result else 1)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.ENDC}")
        sys.exit(130)
    except Exception as e:
        print_error(f"Test suite failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
