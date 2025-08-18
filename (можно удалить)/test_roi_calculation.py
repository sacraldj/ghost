#!/usr/bin/env python3
"""
Тестовый скрипт для проверки расчетов ROI в position_exit_tracker.py
"""

def test_roi_calculation():
    """Тестируем расчеты ROI на примере из логов"""
    
    # Данные из примера
    entry_price = 0.82230
    tp1_price = 0.8288
    tp2_price = 0.8321
    actual_exit_price = 0.83260  # цена выхода
    qty = 243.2000
    margin_used = 2.77334401
    fee_rate = 0.00055
    
    qty_half = qty / 2
    
    print("=== ТЕСТ РАСЧЕТОВ ROI ===\n")
    
    # Старый расчет (неправильный)
    print("🔴 СТАРЫЙ РАСЧЕТ (неправильный):")
    profit_tp1_old = (tp1_price - entry_price) * qty_half
    fee_tp1_old = (entry_price + tp1_price) * qty_half * fee_rate
    pnl_tp1_net_old = profit_tp1_old - fee_tp1_old
    
    # Старый расчет TP2 (неправильный - считал как будто TP2 не достигнут)
    profit_tp2_old = 0  # неправильно!
    fee_tp2_old = entry_price * 2 * qty_half * fee_rate
    pnl_tp2_net_old = -fee_tp2_old
    
    pnl_final_old = pnl_tp1_net_old + pnl_tp2_net_old
    roi_final_old = (pnl_final_old / margin_used) * 100
    
    print(f"TP1 PnL: {pnl_tp1_net_old:.4f} USDT")
    print(f"TP2 PnL: {pnl_tp2_net_old:.4f} USDT")
    print(f"Итого PnL: {pnl_final_old:.4f} USDT")
    print(f"ROI: {roi_final_old:.2f}%\n")
    
    # Новый расчет (правильный)
    print("🟢 НОВЫЙ РАСЧЕТ (правильный):")
    
    # TP1 - половина позиции закрывается по TP1
    profit_tp1_new = (tp1_price - entry_price) * qty_half
    fee_tp1_new = (entry_price + tp1_price) * qty_half * fee_rate
    pnl_tp1_net_new = profit_tp1_new - fee_tp1_new
    
    # TP2 - оставшаяся половина закрывается по TP2 (так как TP2 достигнут)
    profit_tp2_new = (tp2_price - entry_price) * qty_half
    fee_tp2_new = (entry_price + tp2_price) * qty_half * fee_rate
    pnl_tp2_net_new = profit_tp2_new - fee_tp2_new
    
    pnl_final_new = pnl_tp1_net_new + pnl_tp2_net_new
    roi_final_new = (pnl_final_new / margin_used) * 100
    
    print(f"TP1 PnL: {pnl_tp1_net_new:.4f} USDT")
    print(f"TP2 PnL: {pnl_tp2_net_new:.4f} USDT")
    print(f"Итого PnL: {pnl_final_new:.4f} USDT")
    print(f"ROI: {roi_final_new:.2f}%\n")
    
    # Расчет по фактической цене выхода
    print("📊 РАСЧЕТ ПО ФАКТИЧЕСКОЙ ЦЕНЕ ВЫХОДА:")
    
    # TP1 - половина позиции закрывается по TP1
    profit_tp1_actual = (tp1_price - entry_price) * qty_half
    fee_tp1_actual = (entry_price + tp1_price) * qty_half * fee_rate
    pnl_tp1_net_actual = profit_tp1_actual - fee_tp1_actual
    
    # TP2 - оставшаяся половина закрывается по фактической цене выхода
    profit_tp2_actual = (actual_exit_price - entry_price) * qty_half
    fee_tp2_actual = (entry_price + actual_exit_price) * qty_half * fee_rate
    pnl_tp2_net_actual = profit_tp2_actual - fee_tp2_actual
    
    pnl_final_actual = pnl_tp1_net_actual + pnl_tp2_net_actual
    roi_final_actual = (pnl_final_actual / margin_used) * 100
    
    print(f"TP1 PnL: {pnl_tp1_net_actual:.4f} USDT")
    print(f"TP2 PnL (по {actual_exit_price}): {pnl_tp2_net_actual:.4f} USDT")
    print(f"Итого PnL: {pnl_final_actual:.4f} USDT")
    print(f"ROI: {roi_final_actual:.2f}%\n")
    
    # Сравнение с данными из логов
    print("📈 СРАВНЕНИЕ С ЛОГАМИ:")
    print(f"Логи показывают ROI: 20.55%")
    print(f"Наш расчет: {roi_final_actual:.2f}%")
    print(f"Разница: {abs(roi_final_actual - 20.55):.2f}%\n")
    
    # Детальный расчет
    print("🔍 ДЕТАЛЬНЫЙ РАСЧЕТ:")
    print(f"Entry: {entry_price}")
    print(f"TP1: {tp1_price} (достигнут)")
    print(f"TP2: {tp2_price} (достигнут)")
    print(f"Exit: {actual_exit_price}")
    print(f"Qty: {qty}")
    print(f"Qty_half: {qty_half}")
    print(f"Margin: {margin_used}")
    print(f"Fee rate: {fee_rate}")
    
    print(f"\nTP1 расчет:")
    print(f"  Profit: ({tp1_price} - {entry_price}) * {qty_half} = {profit_tp1_actual:.4f}")
    print(f"  Fee: ({entry_price} + {tp1_price}) * {qty_half} * {fee_rate} = {fee_tp1_actual:.4f}")
    print(f"  Net: {profit_tp1_actual:.4f} - {fee_tp1_actual:.4f} = {pnl_tp1_net_actual:.4f}")
    
    print(f"\nTP2 расчет:")
    print(f"  Profit: ({actual_exit_price} - {entry_price}) * {qty_half} = {profit_tp2_actual:.4f}")
    print(f"  Fee: ({entry_price} + {actual_exit_price}) * {qty_half} * {fee_rate} = {fee_tp2_actual:.4f}")
    print(f"  Net: {profit_tp2_actual:.4f} - {fee_tp2_actual:.4f} = {pnl_tp2_net_actual:.4f}")
    
    print(f"\nИтого: {pnl_tp1_net_actual:.4f} + {pnl_tp2_net_actual:.4f} = {pnl_final_actual:.4f}")
    print(f"ROI: ({pnl_final_actual:.4f} / {margin_used}) * 100 = {roi_final_actual:.2f}%")

def test_be_exit():
    """Тестируем случай, когда TP2 не достигнут (выход по BE)"""
    
    print("\n" + "="*50)
    print("ТЕСТ: TP2 НЕ ДОСТИГНУТ (выход по BE)")
    print("="*50)
    
    # Данные для теста BE
    entry_price = 0.82230
    tp1_price = 0.8288
    tp2_price = 0.8321
    be_exit_price = 0.8250  # цена выхода по BE (между entry и TP1)
    qty = 243.2000
    margin_used = 2.77334401
    fee_rate = 0.00055
    
    qty_half = qty / 2
    
    print(f"Entry: {entry_price}")
    print(f"TP1: {tp1_price} (достигнут)")
    print(f"TP2: {tp2_price} (НЕ достигнут)")
    print(f"BE Exit: {be_exit_price}")
    print(f"Qty: {qty}")
    print(f"Qty_half: {qty_half}")
    
    # TP1 - половина позиции закрывается по TP1
    profit_tp1 = (tp1_price - entry_price) * qty_half
    fee_tp1 = (entry_price + tp1_price) * qty_half * fee_rate
    pnl_tp1_net = profit_tp1 - fee_tp1
    
    # TP2 - оставшаяся половина закрывается по BE цене
    profit_tp2 = (be_exit_price - entry_price) * qty_half
    fee_tp2 = (entry_price + be_exit_price) * qty_half * fee_rate
    pnl_tp2_net = profit_tp2 - fee_tp2
    
    pnl_final = pnl_tp1_net + pnl_tp2_net
    roi_final = (pnl_final / margin_used) * 100
    
    print(f"\n📊 РЕЗУЛЬТАТ:")
    print(f"TP1 PnL: {pnl_tp1_net:.4f} USDT")
    print(f"TP2 PnL (BE): {pnl_tp2_net:.4f} USDT")
    print(f"Итого PnL: {pnl_final:.4f} USDT")
    print(f"ROI: {roi_final:.2f}%")
    
    print(f"\n🔍 ДЕТАЛЬНЫЙ РАСЧЕТ:")
    print(f"TP1: ({tp1_price} - {entry_price}) * {qty_half} = {profit_tp1:.4f}")
    print(f"TP1 Fee: ({entry_price} + {tp1_price}) * {qty_half} * {fee_rate} = {fee_tp1:.4f}")
    print(f"TP1 Net: {profit_tp1:.4f} - {fee_tp1:.4f} = {pnl_tp1_net:.4f}")
    
    print(f"TP2 (BE): ({be_exit_price} - {entry_price}) * {qty_half} = {profit_tp2:.4f}")
    print(f"TP2 Fee: ({entry_price} + {be_exit_price}) * {qty_half} * {fee_rate} = {fee_tp2:.4f}")
    print(f"TP2 Net: {profit_tp2:.4f} - {fee_tp2:.4f} = {pnl_tp2_net:.4f}")

if __name__ == "__main__":
    test_roi_calculation()
    test_be_exit() 