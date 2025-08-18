# === GHOST-META ===
# 📂 Путь: test_position_exit_tracker.py
# 📦 Назначение: Тестовая версия position_exit_tracker с моками
# 🔒 Статус: ✅ тестовый (v2.0)

import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

# Мокаем все зависимости
class MockSession:
    def get_executions(self, **kwargs):
        return {"result": {"list": []}}
    
    def get_closed_pnl(self, **kwargs):
        return {"result": {"list": []}}
    
    def cancel_all_orders(self, **kwargs):
        return {"result": {"list": []}}

class MockTrace:
    def __call__(self, code, data, where):
        print(f"[TRACE] {code}: {data}")

class MockLogQueue:
    def __call__(self, event, message):
        print(f"[LOG] {event}: {message}")

# Мокаем модули
sys.modules['pybit.unified_trading'] = type('MockPybit', (), {'HTTP': MockSession})()
sys.modules['core.ghost_bybit_position'] = type('MockCore', (), {'get_position': lambda x: {"size": 0, "lastPrice": 1000}})()
sys.modules['ghost_write_safe'] = type('MockGhost', (), {'ghost_write_safe': lambda x, y: None})()
sys.modules['utils.ghost_trace_logger'] = type('MockUtils', (), {'trace': MockTrace()})()
sys.modules['utils.send_to_queue'] = type('MockQueue', (), {'log_to_queue': MockLogQueue()})()
sys.modules['utils.get_last_fill_price'] = type('MockFill', (), {'get_last_exit_fill_price_safe': lambda x: None})()
sys.modules['leverage_parser'] = type('MockLeverage', (), {'get_leverage': lambda x, **kwargs: 20})()

# Создаём заглушку для конфигурации
os.makedirs("config", exist_ok=True)
with open("config/api_keys.yaml", "w") as f:
    f.write("""
bybit:
  api_key: "test_key"
  api_secret: "test_secret"
""")

# Теперь импортируем функции
from position_exit_tracker import _signed_profit, _vwap_qty_fee, _split_fills_by_legs, _calc_from_fills, _fallback_calc

def test_signed_profit():
    """Тест функции расчёта PnL с учётом направления"""
    print("🧪 Тестируем _signed_profit...")
    
    # LONG позиция
    assert _signed_profit(1000, 1100, 100, "Buy") == 10000  # +10000
    assert _signed_profit(1000, 900, 100, "Buy") == -10000   # -10000
    
    # SHORT позиция
    assert _signed_profit(1000, 900, 100, "Sell") == 10000   # +10000
    assert _signed_profit(1000, 1100, 100, "Sell") == -10000 # -10000
    
    print("✅ _signed_profit тесты пройдены")

def test_vwap_qty_fee():
    """Тест функции расчёта VWAP, количества и комиссий"""
    print("🧪 Тестируем _vwap_qty_fee...")
    
    fills = [
        {"execPrice": "1000", "execQty": "50", "execFee": "2.75"},
        {"execPrice": "1100", "execQty": "50", "execFee": "3.025"}
    ]
    
    vwap, qty, fee = _vwap_qty_fee(fills)
    
    assert abs(vwap - 1050) < 0.01  # (1000*50 + 1100*50) / 100 = 1050
    assert qty == 100
    assert abs(fee - 5.775) < 0.01  # 2.75 + 3.025
    
    print("✅ _vwap_qty_fee тесты пройдены")

def test_split_fills_by_legs():
    """Тест разделения fills на ноги"""
    print("🧪 Тестируем _split_fills_by_legs...")
    
    # Тест 1: Обычное разделение
    fills = [
        {"side": "Sell", "execPrice": "1020", "execQty": "50", "execFee": "2.805", "execTime": "1000"},
        {"side": "Sell", "execPrice": "1000.2", "execQty": "50", "execFee": "2.755", "execTime": "2000"}
    ]
    
    leg_tp1, leg_rest = _split_fills_by_legs(fills, 100, "Buy")
    
    assert len(leg_tp1) == 1
    assert len(leg_rest) == 1
    assert float(leg_tp1[0]["execQty"]) == 50
    assert float(leg_rest[0]["execQty"]) == 50
    
    # Тест 2: Overfill на границе
    fills_overfill = [
        {"side": "Sell", "execPrice": "1020", "execQty": "60", "execFee": "3.366", "execTime": "1000"}
    ]
    
    leg_tp1, leg_rest = _split_fills_by_legs(fills_overfill, 100, "Buy")
    
    assert len(leg_tp1) == 1
    assert len(leg_rest) == 1
    assert float(leg_tp1[0]["execQty"]) == 50
    assert float(leg_rest[0]["execQty"]) == 10
    
    print("✅ _split_fills_by_legs тесты пройдены")

def test_calc_from_fills():
    """Тест расчёта PnL/ROI на основе fills"""
    print("🧪 Тестируем _calc_from_fills...")
    
    # Тестовая сделка
    trade = {
        "symbol": "BTCUSDT",
        "side": "Buy",
        "real_entry_price": 1000,
        "position_qty": 100,
        "margin_used": 5000,
        "tp2_price": 1100
    }
    
    # Тестовые fills
    fills = [
        {"side": "Sell", "execPrice": "1020", "execQty": "50", "execFee": "2.805", "execTime": "1000"},
        {"side": "Sell", "execPrice": "1000.2", "execQty": "50", "execFee": "2.755", "execTime": "2000"}
    ]
    
    result = _calc_from_fills(trade, fills)
    
    assert result["roi_calc_note"] == "ok"
    assert result["roi_source"] == "fills"
    assert result["pnl_source"] == "fills"
    assert result["tp1_hit"] == True
    assert result["tp2_hit"] == False
    assert "tp1@50.0 + be@50.0" in result["exit_detail"]
    
    # Проверяем, что PnL TP1 положительный, а остатка ≈ -комиссия
    assert result["pnl_tp1_net"] > 0
    assert abs(result["pnl_rest_net"] + result["bybit_fee_close"]) < 1  # ≈ -комиссия
    
    print("✅ _calc_from_fills тесты пройдены")

def test_fallback_calc():
    """Тест fallback расчёта"""
    print("🧪 Тестируем _fallback_calc...")
    
    trade = {
        "real_entry_price": 1000,
        "position_qty": 100,
        "margin_used": 5000,
        "tp1_price": 1020,
        "tp2_price": 1100,
        "tp2_hit": False
    }
    
    result = _fallback_calc(trade, 1000.2)
    
    assert result["roi_source"] == "fallback"
    assert result["pnl_source"] == "fallback"
    assert result["roi_calc_note"] == "fallback"
    assert "tp1@50% + be@50%" in result["exit_detail"]
    
    print("✅ _fallback_calc тесты пройдены")

def test_edge_cases():
    """Тест граничных случаев"""
    print("🧪 Тестируем граничные случаи...")
    
    # Пустые fills
    trade = {"real_entry_price": 1000, "position_qty": 100, "margin_used": 5000}
    result = _calc_from_fills(trade, [])
    assert result.get("roi_calc_note") == "skip_calc: no closing fills"
    
    # Отсутствующие данные
    trade = {"real_entry_price": 0, "position_qty": 100, "margin_used": 5000}
    result = _calc_from_fills(trade, [])
    assert "missing entry/qty/margin" in result.get("roi_calc_note", "")
    
    # SHORT позиция
    trade = {
        "symbol": "BTCUSDT",
        "side": "Sell",
        "real_entry_price": 1000,
        "position_qty": 100,
        "margin_used": 5000
    }
    fills = [
        {"side": "Buy", "execPrice": "980", "execQty": "50", "execFee": "2.695", "execTime": "1000"},
        {"side": "Buy", "execPrice": "999.8", "execQty": "50", "execFee": "2.749", "execTime": "2000"}
    ]
    
    result = _calc_from_fills(trade, fills)
    assert result["roi_calc_note"] == "ok"
    assert result["pnl_tp1_net"] > 0  # SHORT: (1000 - 980) * 50 - комиссии
    
    print("✅ Граничные случаи пройдены")

def run_integration_test():
    """Интеграционный тест полного сценария"""
    print("🧪 Запускаем интеграционный тест...")
    
    # Симулируем сделку LONG с TP1 и BE
    trade = {
        "symbol": "BTCUSDT",
        "side": "Buy",
        "real_entry_price": 1000,
        "position_qty": 100,
        "margin_used": 5000,
        "tp1_price": 1020,
        "tp2_price": 1100,
        "tp1_hit": True,
        "tp2_hit": False,
        "sl_hit": False
    }
    
    # Fills: TP1 по 1020, остаток по 1000.2 (BE)
    fills = [
        {"side": "Sell", "execPrice": "1020", "execQty": "50", "execFee": "2.805", "execTime": "1000"},
        {"side": "Sell", "execPrice": "1000.2", "execQty": "50", "execFee": "2.755", "execTime": "2000"}
    ]
    
    result = _calc_from_fills(trade, fills)
    
    # Проверяем результат
    assert result["exit_reason"] == "tp1_be"
    assert result["tp1_hit"] == True
    assert result["tp2_hit"] == False
    assert result["sl_hit"] == False
    assert "tp1@50.0 + be@50.0" in result["exit_detail"]
    
    # Проверяем PnL
    pnl_tp1_expected = (1020 - 1000) * 50 - (1000 * 50 * 0.00055) - (1020 * 50 * 0.00055)
    pnl_rest_expected = (1000.2 - 1000) * 50 - (1000 * 50 * 0.00055) - (1000.2 * 50 * 0.00055)
    
    assert abs(result["pnl_tp1_net"] - pnl_tp1_expected) < 0.01
    assert abs(result["pnl_rest_net"] - pnl_rest_expected) < 0.01
    
    print("✅ Интеграционный тест пройден")
    print(f"📊 Результат: TP1 PnL = {result['pnl_tp1_net']:.2f}, Rest PnL = {result['pnl_rest_net']:.2f}")
    print(f"📈 Финальный ROI = {result['roi_final_real']:.2f}%")

def main():
    """Запуск всех тестов"""
    print("🚀 Запуск тестов fills-first логики v2.0")
    print("=" * 50)
    
    try:
        test_signed_profit()
        test_vwap_qty_fee()
        test_split_fills_by_legs()
        test_calc_from_fills()
        test_fallback_calc()
        test_edge_cases()
        run_integration_test()
        
        print("=" * 50)
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("✅ Fills-first логика работает корректно")
        
    except Exception as e:
        print(f"❌ ОШИБКА В ТЕСТАХ: {e}")
        raise

if __name__ == "__main__":
    main()
