#!/usr/bin/env python3
"""
Исправление trader_registry - добавление недостающих трейдеров
"""

import asyncio
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def fix_trader_registry():
    """Добавляем недостающих трейдеров в trader_registry"""
    print("🔧 ИСПРАВЛЕНИЕ TRADER_REGISTRY")
    print("=" * 50)
    
    try:
        from supabase import create_client, Client
        
        # Подключаемся к Supabase
        supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_key:
            print("❌ Supabase переменные не найдены")
            return False
        
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Подключен к Supabase")
        
        # Трейдеры для добавления
        traders_to_add = [
            {
                "trader_id": "whales_guide_main",
                "name": "Whales Crypto Guide",
                "source_type": "telegram",
                "source_id": "-1001288385100",  # Реальный ID канала
                "source_handle": "@Whalesguide",
                "mode": "observe",
                "risk_profile": {
                    "size_usd": 100,
                    "leverage": 10,
                    "max_concurrent": 3,
                    "sl_cap": 5
                },
                "parsing_profile": "whales_universal",
                "is_active": True,
                "notes": "Main Whales Guide channel for crypto signals"
            },
            {
                "trader_id": "2trade_slivaem",
                "name": "2Trade - slivaeminfo",
                "source_type": "telegram",
                "source_id": "-1001234567890",
                "source_handle": "@2trade_slivaem",
                "mode": "observe",
                "risk_profile": {
                    "size_usd": 100,
                    "leverage": 8,
                    "max_concurrent": 2,
                    "sl_cap": 3
                },
                "parsing_profile": "2trade_parser",
                "is_active": True,
                "notes": "2Trade slivaem channel"
            },
            {
                "trader_id": "crypto_hub_vip",
                "name": "Crypto Hub VIP",
                "source_type": "telegram",
                "source_id": "-1001234567891",
                "source_handle": "@crypto_hub_vip",
                "mode": "observe",
                "risk_profile": {
                    "size_usd": 150,
                    "leverage": 12,
                    "max_concurrent": 4,
                    "sl_cap": 7
                },
                "parsing_profile": "vip_signals_parser",
                "is_active": True,
                "notes": "Crypto Hub VIP signals"
            },
            {
                "trader_id": "coinpulse_signals",
                "name": "CoinPulse Signals",
                "source_type": "telegram",
                "source_id": "-1001234567892",
                "source_handle": "@coinpulse_signals",
                "mode": "observe",
                "risk_profile": {
                    "size_usd": 120,
                    "leverage": 9,
                    "max_concurrent": 3,
                    "sl_cap": 4
                },
                "parsing_profile": "standard_v1",
                "is_active": True,
                "notes": "CoinPulse signals channel"
            }
        ]
        
        # Проверяем какие трейдеры уже существуют
        existing_result = supabase.table('trader_registry').select('trader_id').execute()
        existing_ids = {row['trader_id'] for row in existing_result.data}
        
        print(f"📊 Существующих трейдеров: {len(existing_ids)}")
        if existing_ids:
            print(f"   {', '.join(existing_ids)}")
        
        # Добавляем недостающих
        added_count = 0
        for trader in traders_to_add:
            if trader['trader_id'] not in existing_ids:
                try:
                    result = supabase.table('trader_registry').insert(trader).execute()
                    print(f"✅ Добавлен трейдер: {trader['trader_id']}")
                    added_count += 1
                except Exception as e:
                    print(f"❌ Ошибка добавления {trader['trader_id']}: {e}")
            else:
                print(f"⚪ Трейдер уже существует: {trader['trader_id']}")
        
        print(f"\n🎉 Добавлено трейдеров: {added_count}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    success = await fix_trader_registry()
    
    if success:
        print("\n✅ TRADER_REGISTRY ИСПРАВЛЕН!")
        print("🚀 Теперь можно записывать сигналы в Supabase")
    else:
        print("\n❌ ОШИБКА ИСПРАВЛЕНИЯ")
        print("💡 Проверьте логи выше")

if __name__ == "__main__":
    asyncio.run(main())
