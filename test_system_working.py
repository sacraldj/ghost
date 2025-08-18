#!/usr/bin/env python3
"""
Тест системы GHOST с правильными форматами сигналов
"""

import asyncio
import logging
import os
import sys

# Добавляем корневую папку в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_with_correct_signals():
    """Тестирование с правильными форматами сигналов"""
    
    logger.info("🔍 Testing GHOST with CORRECT signal formats...")
    
    from signals.signal_orchestrator_with_supabase import orchestrator_with_supabase
    
    # Тест 1: Проверка подключения к Supabase
    supabase_ok = await orchestrator_with_supabase.test_supabase_connection()
    logger.info(f"Supabase: {'✅ OK' if supabase_ok else '❌ FAILED'}")
    
    # Тест 2: Правильные форматы сигналов для каждого парсера
    test_signals = [
        # CryptoAttack24 формат (работает!)
        ("🚀🔥 #ALPINE запампили на +57% со вчерашнего вечера", "cryptoattack24"),
        
        # WhalesCrypto формат
        ("Longing #SWARMS Here\\nLong (5x - 10x)\\nEntry: $0.02569 - $0.02400\\nTargets: $0.027, $0.028, $0.030\\nStoploss: $0.02260\\nReason: Chart looks bullish", "whales_crypto_guide"),
        
        # 2Trade формат
        ("LONG #BTC/USDT\\n💰Entry: 65000 - 66000\\n🎯Target 1: 67000\\n🎯Target 2: 68500\\n❌Stop Loss: 64000", "2trade_premium"),
        
        # Crypto Hub формат 
        ("🔥TRADE ALERT🔥\\n#ETH/USDT - LONG\\nEntry Zone: 2400-2450\\nTargets: 2500 | 2600 | 2800\\nStop Loss: 2350", "crypto_hub_vip"),
    ]
    
    processed_count = 0
    
    for signal_text, trader_id in test_signals:
        logger.info(f"\\nTesting {trader_id}...")
        logger.info(f"Signal: {signal_text[:50]}...")
        
        result = await orchestrator_with_supabase.process_raw_signal(signal_text, trader_id, trader_id)
        
        if result:
            logger.info(f"✅ SUCCESS: {result.symbol} - {result.direction}")
            processed_count += 1
        else:
            logger.warning(f"⚠️ FAILED: {trader_id}")
    
    # Статистика
    stats = await orchestrator_with_supabase.get_stats()
    logger.info(f"\\n📊 FINAL STATS:")
    logger.info(f"Processed: {processed_count}/{len(test_signals)}")
    logger.info(f"Success rate: {stats['success_rate']:.1f}%")
    logger.info(f"Supabase saves: {stats['supabase_saves']}")
    
    # Тест Telegram (кратко)
    logger.info(f"\\n🔧 Testing Telegram...")
    try:
        telegram_ok = await orchestrator_with_supabase.start_telegram_listening()
        logger.info(f"Telegram: {'✅ OK' if telegram_ok else '❌ FAILED'}")
    except Exception as e:
        logger.warning(f"Telegram: ❌ Error - {e}")
    
    return processed_count > 0

if __name__ == "__main__":
    result = asyncio.run(test_with_correct_signals())
    print(f"\\n{'='*50}")
    print(f"🎯 SYSTEM STATUS: {'✅ WORKING' if result else '❌ BROKEN'}")
    print(f"{'='*50}")
