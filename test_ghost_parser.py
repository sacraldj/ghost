#!/usr/bin/env python3
"""
Тест нового GhostTestParser для канала t.me/ghostsignaltest
"""

import sys
import os
import asyncio
import logging

# Добавляем корневую папку в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from signals.parsers.ghost_test_parser import GhostTestParser
from signals.signal_orchestrator_with_supabase import SignalOrchestratorWithSupabase

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_parser_standalone():
    """Тестируем парсер отдельно"""
    print("\n🧪 Testing GhostTestParser Standalone")
    print("=" * 50)
    
    # Тестовые сигналы
    test_signals = [
        """
🚀 GHOST TEST SIGNAL #1

Symbol: BTCUSDT
Direction: LONG
Entry: $50000 - $49500
Target 1: $52000
Target 2: $54000
Stop Loss: $48000
Leverage: 10x
        """,
        """
#ETH LONG 15x
Entry: 3200
TP1: 3350
TP2: 3500
SL: 3100
        """,
        """
BTC SHORT
Entry @ $51000
Targets: 49500, 48000
Stop: 52000
        """,
        """
ADAUSDT BUY
Entry: 0.45-0.44
Target: 0.48, 0.50
Stop: 0.42
        """
    ]
    
    parser = GhostTestParser()
    
    for i, signal in enumerate(test_signals, 1):
        print(f"\n--- Test Signal {i} ---")
        print(f"Text: {signal.strip()[:100]}...")
        print(f"Can parse: {parser.can_parse(signal)}")
        
        if parser.can_parse(signal):
            result = parser.parse_signal(signal, "ghostsignaltest")
            if result:
                print(f"✅ Parsed successfully!")
                print(f"   Symbol: {result.symbol}")
                print(f"   Direction: {result.direction.value}")
                print(f"   Entry: {result.entry_zone or result.entry_single}")
                print(f"   Targets: {result.targets}")
                print(f"   Stop Loss: {result.stop_loss}")
                print(f"   Leverage: {result.leverage}")
                print(f"   Confidence: {result.confidence:.2f}")
            else:
                print("❌ Failed to parse")
        else:
            print("⚠️ Cannot parse this signal")

async def test_orchestrator_integration():
    """Тестируем интеграцию с оркестратором"""
    print("\n🔧 Testing Orchestrator Integration")
    print("=" * 50)
    
    try:
        orchestrator = SignalOrchestratorWithSupabase()
        
        # Проверяем что парсер зарегистрирован
        if 'ghostsignaltest' in orchestrator.parsers:
            print("✅ GhostTestParser registered in orchestrator")
            parser = orchestrator.parsers['ghostsignaltest']
            print(f"   Parser type: {type(parser).__name__}")
        else:
            print("❌ GhostTestParser NOT registered in orchestrator")
            return
        
        # Тестовый сигнал для полной обработки
        test_message = """
🚀 GHOST TEST

#BTC LONG 10x
Entry: 49800-50200
TP1: 52000
TP2: 54000
SL: 48500
        """
        
        print("\n📨 Processing test message through orchestrator...")
        result = await orchestrator.process_raw_signal(test_message, "ghostsignaltest")
        
        if result:
            print("✅ Message processed successfully!")
            print(f"   Signal ID: {result.signal_id}")
            print(f"   Symbol: {result.symbol}")
            print(f"   Direction: {result.direction.value}")
        else:
            print("❌ Failed to process message")
        
        # Показываем статистику
        stats = await orchestrator.get_stats()
        print(f"\n📊 Orchestrator Stats:")
        print(f"   Signals processed: {stats.get('signals_saved', 0)}")
        print(f"   V-trades saves: {stats.get('v_trades_saves', 0)}")
        print(f"   Errors: {stats.get('supabase_errors', 0)}")
        
    except Exception as e:
        print(f"❌ Error testing orchestrator: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Главная функция теста"""
    print("🧪 GHOST TEST PARSER TESTING")
    print("=" * 60)
    
    # Тест 1: Парсер отдельно
    test_parser_standalone()
    
    # Тест 2: Интеграция с оркестратором
    await test_orchestrator_integration()
    
    print("\n✅ Testing completed!")

if __name__ == "__main__":
    asyncio.run(main())
