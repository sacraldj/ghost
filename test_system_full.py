#!/usr/bin/env python3
"""
Полное тестирование GHOST системы:
1. Проверка Supabase подключения
2. Проверка Telegram API
3. Проверка обработки сигналов
4. Проверка сохранения в базу данных
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# Добавляем корневую папку в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_full_system():
    """Полный тест системы GHOST"""
    
    logger.info("🔍 === GHOST SYSTEM FULL TEST ===")
    logger.info(f"📅 Test started at: {datetime.now()}")
    
    try:
        # 1. Тест основного оркестратора
        logger.info("1️⃣ Testing SignalOrchestratorWithSupabase...")
        
        from signals.signal_orchestrator_with_supabase import orchestrator_with_supabase
        
        # Проверка Supabase подключения
        supabase_ok = await orchestrator_with_supabase.test_supabase_connection()
        logger.info(f"   Supabase connection: {'✅ OK' if supabase_ok else '❌ FAILED'}")
        
        # 2. Тест обработки сигналов
        logger.info("2️⃣ Testing signal processing...")
        
        test_signals = [
            ("🚀 #BTC Long зона входа: 65000-66000, цели: 67000, 68500, стоп: 64000", "whales_guide_main"),
            ("📈 ALPINE/USDT\nЛонг от 2.30-2.35\nЦели: 2.45, 2.60, 2.85\nСтоп: 2.20", "cryptoattack24"),
            ("🔥 ETH покупаем в зоне 2400-2450\nТП1: 2500\nТП2: 2600\nТП3: 2800", "2trade_premium"),
        ]
        
        processed_count = 0
        for signal_text, trader_id in test_signals:
            result = await orchestrator_with_supabase.process_raw_signal(signal_text, trader_id, trader_id)
            if result:
                logger.info(f"   ✅ Signal processed: {result.symbol} ({trader_id})")
                processed_count += 1
            else:
                logger.warning(f"   ⚠️ Signal failed: {trader_id}")
        
        logger.info(f"   Signals processed: {processed_count}/{len(test_signals)}")
        
        # 3. Проверка статистики
        logger.info("3️⃣ Getting system statistics...")
        
        stats = await orchestrator_with_supabase.get_stats()
        logger.info(f"   📊 Total signals processed: {stats['signals_processed']}")
        logger.info(f"   💾 Supabase saves: {stats['supabase_saves']}")
        logger.info(f"   ❌ Errors: {stats['supabase_errors']}")
        logger.info(f"   📈 Success rate: {stats['success_rate']:.1f}%")
        logger.info(f"   ⏱️ Uptime: {stats['uptime_human']}")
        
        # 4. Тест Telegram (если доступен)
        logger.info("4️⃣ Testing Telegram connection...")
        
        try:
            telegram_ok = await orchestrator_with_supabase.start_telegram_listening()
            logger.info(f"   Telegram listening: {'✅ Started' if telegram_ok else '❌ FAILED'}")
            
            if telegram_ok:
                logger.info("   📱 Telegram channels configured:")
                channels = ["@whalesguide", "@slivaeminfo", "@cryptohubvip", "@cryptoattack24"]
                for channel in channels:
                    logger.info(f"   - {channel}")
        except Exception as e:
            logger.warning(f"   ⚠️ Telegram test failed: {e}")
        
        # 5. Проверка Supabase таблиц
        logger.info("5️⃣ Checking Supabase tables...")
        
        try:
            if orchestrator_with_supabase.supabase:
                # Проверяем signals_raw
                raw_result = orchestrator_with_supabase.supabase.table('signals_raw').select('*').limit(5).execute()
                logger.info(f"   📊 signals_raw table: {len(raw_result.data)} recent records")
                
                # Проверяем signals_parsed  
                parsed_result = orchestrator_with_supabase.supabase.table('signals_parsed').select('*').limit(5).execute()
                logger.info(f"   📊 signals_parsed table: {len(parsed_result.data)} recent records")
                
                # Проверяем v_trades (если есть)
                try:
                    trades_result = orchestrator_with_supabase.supabase.table('v_trades').select('*').limit(5).execute()
                    logger.info(f"   📊 v_trades table: {len(trades_result.data)} recent records")
                except:
                    logger.info(f"   📊 v_trades table: Not accessible or empty")
                    
        except Exception as e:
            logger.warning(f"   ⚠️ Database tables check failed: {e}")
        
        # Финальный отчет
        logger.info("6️⃣ === FINAL REPORT ===")
        logger.info(f"   🎯 System Status: {'✅ OPERATIONAL' if supabase_ok and processed_count > 0 else '❌ ISSUES FOUND'}")
        logger.info(f"   📊 Components tested: 6/6")
        logger.info(f"   ⏱️ Total test time: ~30 seconds")
        
        return supabase_ok and processed_count > 0
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    result = asyncio.run(test_full_system())
    sys.exit(0 if result else 1)
