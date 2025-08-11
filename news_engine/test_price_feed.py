#!/usr/bin/env python3
"""
Тестирование GHOST Price Feed Engine
Проверка основных функций модуля сбора ценовых данных
"""

import asyncio
import sqlite3
import time
from datetime import datetime, timezone, timedelta
from price_feed_engine import PriceFeedEngine, PriceData, Candle

async def test_price_fetch():
    """Тест получения цен"""
    print("🧪 Тест получения цен...")
    
    engine = PriceFeedEngine()
    
    try:
        # Создание сессии
        await engine._create_session()
        
        # Тест получения цен с Binance
        print("  📊 Тест Binance API...")
        btc_binance = await engine._fetch_binance_price("BTC")
        if btc_binance:
            print(f"    ✅ BTC Binance: ${btc_binance.price:,.2f}")
        else:
            print("    ❌ Не удалось получить цену BTC с Binance")
        
        eth_binance = await engine._fetch_binance_price("ETH")
        if eth_binance:
            print(f"    ✅ ETH Binance: ${eth_binance.price:,.2f}")
        else:
            print("    ❌ Не удалось получить цену ETH с Binance")
        
        # Тест получения цен с Coinbase
        print("  📊 Тест Coinbase API...")
        btc_coinbase = await engine._fetch_coinbase_price("BTC")
        if btc_coinbase:
            print(f"    ✅ BTC Coinbase: ${btc_coinbase.price:,.2f}")
        else:
            print("    ❌ Не удалось получить цену BTC с Coinbase")
        
        eth_coinbase = await engine._fetch_coinbase_price("ETH")
        if eth_coinbase:
            print(f"    ✅ ETH Coinbase: ${eth_coinbase.price:,.2f}")
        else:
            print("    ❌ Не удалось получить цену ETH с Coinbase")
        
        # Тест получения всех цен
        print("  📊 Тест получения всех цен...")
        all_prices = await engine._fetch_all_prices()
        print(f"    ✅ Получено {len(all_prices)} цен")
        
        # Закрытие сессии
        await engine._close_session()
        
        return True
        
    except Exception as e:
        print(f"    ❌ Ошибка: {e}")
        return False

def test_database_operations():
    """Тест операций с базой данных"""
    print("🧪 Тест операций с базой данных...")
    
    try:
        engine = PriceFeedEngine()
        
        # Создание тестовых данных
        test_price = PriceData(
            symbol="BTC",
            price=50000.0,
            volume=100.0,
            timestamp=datetime.now(timezone.utc),
            source="test",
            bid=49999.0,
            ask=50001.0,
            high_24h=51000.0,
            low_24h=49000.0
        )
        
        # Тест сохранения
        print("  💾 Тест сохранения ценовых данных...")
        if engine._save_price_data(test_price):
            print("    ✅ Ценовые данные сохранены")
        else:
            print("    ❌ Ошибка сохранения")
            return False
        
        # Тест буферизации
        print("  📦 Тест буферизации...")
        engine._add_to_buffer(test_price)
        if len(engine.price_buffer["BTC"]) > 0:
            print("    ✅ Данные добавлены в буфер")
        else:
            print("    ❌ Ошибка буферизации")
            return False
        
        # Тест формирования свечей
        print("  🕯️  Тест формирования свечей...")
        candles = engine._form_candles("BTC", "1m")
        if candles:
            print(f"    ✅ Сформировано {len(candles)} свечей")
        else:
            print("    ⚠️  Свечи не сформированы (ожидаемо для одного теста)")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Ошибка: {e}")
        return False

def test_candle_formation():
    """Тест формирования свечей"""
    print("🧪 Тест формирования свечей...")
    
    try:
        engine = PriceFeedEngine()
        
        # Создание тестовых данных для разных временных точек
        base_time = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        
        test_prices = []
        for i in range(10):
            price_data = PriceData(
                symbol="BTC",
                price=50000.0 + i * 100,  # Разные цены
                volume=100.0 + i * 10,
                timestamp=base_time + timedelta(minutes=i),
                source="test"
            )
            test_prices.append(price_data)
        
        # Добавление в буфер
        for price in test_prices:
            engine._add_to_buffer(price)
        
        # Тест формирования свечей для разных интервалов
        intervals = ["1m", "5m", "15m", "1h"]
        
        for interval in intervals:
            candles = engine._form_candles("BTC", interval)
            print(f"  📊 {interval}: {len(candles)} свечей")
            
            if candles:
                for candle in candles[:2]:  # Показываем первые 2 свечи
                    print(f"    🕯️  {candle.open_time} - {candle.close_time}: "
                          f"O:{candle.open_price:.0f} H:{candle.high_price:.0f} "
                          f"L:{candle.low_price:.0f} C:{candle.close_price:.0f}")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Ошибка: {e}")
        return False

async def test_integration():
    """Интеграционный тест"""
    print("🧪 Интеграционный тест...")
    
    try:
        engine = PriceFeedEngine()
        
        # Получение последних цен
        print("  📊 Получение последних цен...")
        latest_prices = await engine.get_latest_prices()
        for symbol, price_data in latest_prices.items():
            print(f"    ✅ {symbol}: ${price_data.price:,.2f} ({price_data.source})")
        
        # Получение свечей
        print("  🕯️  Получение свечей...")
        candles = await engine.get_candles("BTC", "1h", 5)
        print(f"    ✅ Получено {len(candles)} часовых свечей")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Ошибка: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестов GHOST Price Feed Engine\n")
    
    tests = [
        ("Получение цен", test_price_fetch),
        ("Операции с БД", test_database_operations),
        ("Формирование свечей", test_candle_formation),
        ("Интеграция", test_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Тест: {test_name}")
        print('='*50)
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте {test_name}: {e}")
            results.append((test_name, False))
    
    # Вывод результатов
    print(f"\n{'='*50}")
    print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print('='*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nИтого: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены успешно!")
    else:
        print("⚠️  Некоторые тесты не пройдены")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(main())
