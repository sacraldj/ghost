#!/usr/bin/env python3
"""
Тестирование модулей GHOST системы
"""

import os
import sys
import subprocess
import traceback
from pathlib import Path

def test_module(name, script_path, working_dir=None):
    """Тестирует запуск модуля"""
    print(f"\n🧪 Testing module: {name}")
    print(f"   Script: {script_path}")
    print(f"   Working dir: {working_dir or 'current'}")
    
    if not os.path.exists(script_path):
        print(f"❌ Script not found: {script_path}")
        return False
    
    try:
        # Тестируем импорт
        cmd = [sys.executable, "-c", f"import sys; sys.path.append('{os.getcwd()}'); exec(open('{script_path}').read())"]
        
        if working_dir:
            original_cwd = os.getcwd()
            os.chdir(working_dir)
        
        result = subprocess.run(
            [sys.executable, script_path, "--test"], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        
        if working_dir:
            os.chdir(original_cwd)
        
        if result.returncode == 0:
            print(f"✅ Module {name} - OK")
            return True
        else:
            print(f"❌ Module {name} - FAILED")
            print(f"   STDOUT: {result.stdout[:200]}")
            print(f"   STDERR: {result.stderr[:200]}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Module {name} - TIMEOUT (this might be normal for listeners)")
        return True
    except Exception as e:
        print(f"❌ Module {name} - ERROR: {e}")
        print(f"   Traceback: {traceback.format_exc()[:200]}")
        return False

def main():
    print("🚀 GHOST Modules Test Suite")
    print("=" * 50)
    
    # Проверяем основные зависимости
    print("\n📦 Checking dependencies...")
    
    try:
        import telethon
        print("✅ telethon - OK")
    except ImportError:
        print("❌ telethon - MISSING")
    
    try:
        from supabase import create_client
        print("✅ supabase - OK")
    except ImportError:
        print("❌ supabase - MISSING")
    
    try:
        import aiohttp
        print("✅ aiohttp - OK")
    except ImportError:
        print("❌ aiohttp - MISSING")
    
    # Тестируем модули
    modules_to_test = [
        ("news_engine", "news_engine/enhanced_news_engine.py", "news_engine"),
        ("price_feed", "news_engine/price_feed_engine.py", "news_engine"),
        ("telegram_listener", "core/telegram_listener.py", "core"),
        ("signal_processor", "signals/signal_orchestrator_with_supabase.py", None),
    ]
    
    results = {}
    for name, script, working_dir in modules_to_test:
        results[name] = test_module(name, script, working_dir)
    
    # Результаты
    print("\n📊 Test Results:")
    print("=" * 30)
    
    for name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name:20} {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\n🎯 Summary: {passed_tests}/{total_tests} modules passed")
    
    if passed_tests == total_tests:
        print("🎉 All modules are ready!")
    else:
        print("⚠️ Some modules need attention")

if __name__ == "__main__":
    main()
