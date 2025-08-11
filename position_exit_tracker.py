# === GHOST-META ===
# 📂 Путь: core/position_exit_tracker.py
# 📦 Назначение: Отслеживает закрытие позиции, корректный расчёт PNL/ROI на основе fills
# 🔒 Статус: ✅ боевой (v2.0 - fills-first + fallback)
# 🤝 Зависимости: pybit.unified_trading.HTTP, ghost_write_safe, utils.ghost_trace_logger.trace, utils.send_to_queue.log_to_queue, utils.bybit_api.get_executions|get_closed_pnl, utils.get_last_fill_price, leverage_parser.get_leverage

import json
import time
import yaml
import calendar
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from pybit.unified_trading import HTTP

# --- GHOST deps (заглушки импорта: замени на реальные модули проекта) ---
from core.ghost_bybit_position import get_position
from ghost_write_safe import ghost_write_safe
from utils.ghost_trace_logger import trace
from utils.send_to_queue import log_to_queue
from utils.get_last_fill_price import get_last_exit_fill_price_safe
from leverage_parser import get_leverage

# === API Подключение к Bybit ===
with open("config/api_keys.yaml") as f:
    keys = yaml.safe_load(f)["bybit"]

session = HTTP(api_key=keys["api_key"], api_secret=keys["api_secret"])

OPEN_TRADES_PATH = "output/open_trades.json"
FEE_RATE = 0.00055
BE_EPS = 0.0002  # 2 bps допуск для BE

def _load_open_trades() -> List[Dict[str, Any]]:
    try:
        with open(OPEN_TRADES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _save_open_trades(data: List[Dict[str, Any]]) -> None:
    try:
        with open(OPEN_TRADES_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        trace("OPEN_TRADES_WRITE_FAIL", {"err": str(e)}, "position_exit_tracker")

def _signed_profit(entry: float, exit_price: float, qty: float, side: str) -> float:
    """Вычисляет PnL с учётом направления позиции"""
    side_l = str(side).lower()
    if side_l in ("sell", "short"):
        return (entry - exit_price) * qty
    return (exit_price - entry) * qty

def _vwap_qty_fee(fills: List[Dict[str, Any]]) -> Tuple[float, float, float]:
    """Вычисляет VWAP, общее количество и сумму комиссий из fills"""
    if not fills:
        return 0.0, 0.0, 0.0
    
    total_qty = sum(float(f.get("execQty", 0)) for f in fills)
    total_value = sum(float(f.get("execPrice", 0)) * float(f.get("execQty", 0)) for f in fills)
    total_fee = sum(float(f.get("execFee", 0)) for f in fills)
    
    vwap = total_value / total_qty if total_qty > 0 else 0.0
    return vwap, total_qty, total_fee

def _split_fills_by_legs(fills: List[Dict[str, Any]], qty_total: float, side: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Разделяет fills на TP1 (50%) и остаток (50%)"""
    if not fills:
        return [], []
    
    # Фильтруем закрывающие fills
    closing_side = "Sell" if side.lower() in ("buy", "long") else "Buy"
    closing_fills = [f for f in fills if f.get("side") == closing_side and float(f.get("execQty", 0)) > 0]
    
    if not closing_fills:
        return [], []
    
    # Сортируем по времени исполнения
    closing_fills.sort(key=lambda x: int(x.get("execTime", 0)))
    
    qty_tp1 = qty_total / 2.0
    leg_tp1 = []
    leg_rest = []
    current_qty = 0.0
    
    for fill in closing_fills:
        fill_qty = float(fill.get("execQty", 0))
        fill_price = float(fill.get("execPrice", 0))
        
        if current_qty < qty_tp1:
            # Ещё не достигли границы TP1
            remaining_tp1 = qty_tp1 - current_qty
            if fill_qty <= remaining_tp1:
                # Весь fill идёт в TP1
                leg_tp1.append(fill)
                current_qty += fill_qty
            else:
                # Разделяем fill
                tp1_part = {
                    **fill,
                    "execQty": str(remaining_tp1),
                    "execPrice": str(fill_price),
                    "execFee": str(float(fill.get("execFee", 0)) * (remaining_tp1 / fill_qty))
                }
                rest_part = {
                    **fill,
                    "execQty": str(fill_qty - remaining_tp1),
                    "execPrice": str(fill_price),
                    "execFee": str(float(fill.get("execFee", 0)) * ((fill_qty - remaining_tp1) / fill_qty))
                }
                leg_tp1.append(tp1_part)
                leg_rest.append(rest_part)
                current_qty = qty_tp1
        else:
            # Всё остальное идёт в остаток
            leg_rest.append(fill)
    
    return leg_tp1, leg_rest

def _get_executions(symbol: str, start_time: int, end_time: int) -> List[Dict[str, Any]]:
    """Получает executions (fills) от Bybit API"""
    try:
        all_fills = []
        cursor = None
        
        while True:
            params = {
                "category": "linear",
                "symbol": symbol,
                "startTime": start_time,
                "endTime": end_time,
                "limit": 1000
            }
            if cursor:
                params["cursor"] = cursor
            
            response = session.get_executions(**params)
            result = response.get("result", {})
            fills = result.get("list", [])
            
            if not fills:
                break
                
            all_fills.extend(fills)
            
            # Проверяем, есть ли следующая страница
            if not result.get("nextPageCursor"):
                break
            cursor = result["nextPageCursor"]
            
            # Защита от бесконечного цикла
            if len(all_fills) > 10000:
                trace("FILLS_FETCH_LIMIT", {"symbol": symbol, "count": len(all_fills)}, "position_exit_tracker")
                break
        
        trace("FILLS_FETCH_OK", {"symbol": symbol, "count": len(all_fills)}, "position_exit_tracker")
        return all_fills
        
    except Exception as e:
        trace("FILLS_FETCH_FAIL", {"symbol": symbol, "err": str(e)}, "position_exit_tracker")
        return []

def _calc_from_fills(trade: Dict[str, Any], fills: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Вычисляет PnL/ROI на основе fills"""
    if not fills:
        return {}
    
    symbol = trade.get("symbol", "")
    side = trade.get("side", "Buy")
    entry_price = float(trade.get("real_entry_price", 0))
    qty_total = float(trade.get("position_qty", 0))
    margin_used = float(trade.get("margin_used", 0))
    
    if not entry_price or not qty_total or not margin_used:
        return {"roi_calc_note": "skip_calc: missing entry/qty/margin"}
    
    # Разделяем fills на ноги
    leg_tp1, leg_rest = _split_fills_by_legs(fills, qty_total, side)
    
    if not leg_tp1 and not leg_rest:
        return {"roi_calc_note": "skip_calc: no closing fills"}
    
    # Вычисляем VWAP и комиссии для каждой ноги
    vwap_tp1, qty_tp1, fee_tp1_exit = _vwap_qty_fee(leg_tp1)
    vwap_rest, qty_rest, fee_rest_exit = _vwap_qty_fee(leg_rest)
    
    # Комиссии входа (распределяем пропорционально)
    entry_fee_total = float(trade.get("entry_fee_total", 0))
    if entry_fee_total > 0:
        fee_tp1_entry = entry_fee_total * (qty_tp1 / qty_total)
        fee_rest_entry = entry_fee_total * (qty_rest / qty_total)
    else:
        fee_tp1_entry = 0.0
        fee_rest_entry = 0.0
    
    # PnL для каждой ноги
    pnl_tp1_gross = _signed_profit(entry_price, vwap_tp1, qty_tp1, side)
    pnl_tp1_net = pnl_tp1_gross - fee_tp1_entry - fee_tp1_exit
    
    pnl_rest_gross = _signed_profit(entry_price, vwap_rest, qty_rest, side)
    pnl_rest_net = pnl_rest_gross - fee_rest_entry - fee_rest_exit
    
    # Финальные значения
    pnl_final_real = pnl_tp1_net + pnl_rest_net
    roi_final_real = (pnl_final_real / margin_used) * 100 if margin_used else 0.0
    
    # Определяем тип второй ноги
    exit_tp2_type = "be" if abs(vwap_rest - entry_price) <= entry_price * BE_EPS else "tp2/manual"
    
    # Определяем exit_reason
    tp2_price = float(trade.get("tp2_price", 0))
    exit_reason = "manual"
    
    if tp2_price > 0:
        # Проверяем, соответствует ли вторая нога TP2
        if abs(vwap_rest - tp2_price) <= tp2_price * 0.001:  # 0.1% допуск
            exit_reason = "tp2"
        elif abs(vwap_rest - entry_price) <= entry_price * BE_EPS:
            exit_reason = "tp1_be"
    
    # Формируем exit_detail
    exit_detail = f"fills: tp1@{qty_tp1:.1f} + {exit_tp2_type}@{qty_rest:.1f}"
    
    return {
        "pnl_tp1_net": round(pnl_tp1_net, 6),
        "pnl_rest_net": round(pnl_rest_net, 6),
        "pnl_final_real": round(pnl_final_real, 6),
        "roi_tp1_real": round((pnl_tp1_net / margin_used) * 100, 4) if margin_used else 0.0,
        "roi_rest_real": round((pnl_rest_net / margin_used) * 100, 4) if margin_used else 0.0,
        "roi_final_real": round(roi_final_real, 4),
        "exit_reason": exit_reason,
        "exit_detail": exit_detail,
        "roi_source": "fills",
        "pnl_source": "fills",
        "roi_calc_note": "ok",
        "bybit_fee_open": round(fee_tp1_entry + fee_rest_entry, 8),
        "bybit_fee_close": round(fee_tp1_exit + fee_rest_exit, 8),
        "bybit_fee_total": round(fee_tp1_entry + fee_rest_entry + fee_tp1_exit + fee_rest_exit, 8),
        "tp1_hit": True if leg_tp1 else False,
        "tp2_hit": exit_reason == "tp2",
        "sl_hit": False,  # Будет переопределено ниже
        "early_exit": False
    }

def _fallback_calc(trade: Dict[str, Any], exit_price: float) -> Dict[str, Any]:
    """Fallback расчёт на основе существующей логики"""
    entry_price = float(trade.get("real_entry_price", 0))
    qty = float(trade.get("position_qty", 0))
    side = trade.get("side", "Buy")
    margin_used = float(trade.get("margin_used", 0))
    tp1_price = float(trade.get("tp1_price", 0))
    tp2_price = float(trade.get("tp2_price", 0))
    
    if not entry_price or not qty or not margin_used:
        return {"roi_calc_note": "skip_fallback: missing entry/qty/margin"}
    
    qty_half = qty / 2.0
    fee_in_half = entry_price * qty_half * FEE_RATE
    
    # Нога A (TP1 50%)
    exit_a = tp1_price or exit_price
    fee_out_a = exit_a * qty_half * FEE_RATE
    pnl_a = _signed_profit(entry_price, exit_a, qty_half, side) - fee_in_half - fee_out_a
    
    # Нога B (остаток 50%)
    if trade.get("tp2_hit"):
        exit_b = tp2_price or exit_price
    else:
        exit_b = exit_price
    
    fee_out_b = exit_b * qty_half * FEE_RATE
    pnl_b = _signed_profit(entry_price, exit_b, qty_half, side) - fee_in_half - fee_out_b
    
    pnl_final = pnl_a + pnl_b
    roi_final = (pnl_final / margin_used) * 100 if margin_used else 0.0
    
    exit_tp2_type = "be" if abs(exit_b - entry_price) <= entry_price * BE_EPS else "tp2/manual"
    
    return {
        "pnl_tp1_net": round(pnl_a, 6),
        "pnl_tp2_net": round(pnl_b, 6),
        "pnl_final_real": round(pnl_final, 6),
        "roi_final_real": round(roi_final, 4),
        "exit_detail": f"tp1@50% + {exit_tp2_type}@50%",
        "roi_source": "fallback",
        "pnl_source": "fallback",
        "roi_calc_note": "fallback"
    }

def _duration_sec(trade: Dict[str, Any], exit_dt: datetime) -> Optional[int]:
    """Вычисляет длительность сделки в секундах"""
    try:
        if not trade.get("opened_at"):
            return None
        opened = datetime.strptime(trade["opened_at"], "%Y-%m-%d %H:%M:%S")
        return int((exit_dt - opened).total_seconds())
    except Exception:
        return None

def _preview_message(trade: Dict[str, Any], exit_price: float, final_pnl: float, pnl_source: str, duration_sec: Optional[int]) -> str:
    """Формирует сообщение предпросмотра закрытия сделки"""
    def yn(v): return "достигнуто" if v else "не достигнуто"
    def s(v, d="—"):
        if v is None: return d
        if isinstance(v, float):
            try: return f"{v:.5f}"
            except: return str(v)
        return str(v)

    symbol = trade.get("symbol", "UNKNOWN")
    msg = (
        f"📄 Trade Recorded: {symbol} | {trade.get('trade_id')}\n"
        f"🔗 Источник:          {trade.get('source_name','—')}\n"
        f"{'─'*28}\n"
        f"🟢 Entry Price:        {s(trade.get('real_entry_price'))}\n"
        f"🔴 Exit Price:         {exit_price:.5f}\n"
        f"📦 Qty:                {s(trade.get('position_qty'))}\n"
        f"⚖ Leverage:            {s(trade.get('real_leverage'))}x\n"
        f"💵 Margin Used:        ${s(trade.get('margin_used'))}\n"
        f"{'─'*28}\n"
        f"📇 Bybit (реальные данные):\n"
        f"📉 ROI (UI):           {s(trade.get('roi_ui'))}%\n"
        f"💸 Комиссия (факт):    {s(trade.get('bybit_fee_total'))} USDT\n"
        f"📤 PnL (source):       {final_pnl} USDT ({pnl_source})\n"
        f"{'─'*28}\n"
        f"📉 Получено (факт):\n"
        f"• ROI (TP1):           {s(trade.get('roi_tp1_real'))}%\n"
        f"• ROI (TP2):           {s(trade.get('roi_tp2_real'))}%\n"
        f"• ROI (Final):         {s(trade.get('roi_final_real'))}%\n"
        f"⏱ Duration:            {duration_sec//60 if duration_sec else 0}m {duration_sec%60 if duration_sec else 0}s\n"
        f"{'─'*28}\n"
        f"📌 ФИНАЛ:\n"
        f"💥 РЕЗУЛЬТАТ:          {final_pnl} USDT\n"
        f"📊 Доходность:         {s(trade.get('roi_final_real'))}% от маржи\n"
        f"🚩 Exit Reason:        {trade.get('exit_reason','manual')} | {trade.get('exit_detail','—')}\n"
        f"{'─'*28}\n"
        f"📍 TP/SL Статус:\n"
        f"• TP1:  {yn(trade.get('tp1_hit'))}\n"
        f"• TP2:  {yn(trade.get('tp2_hit'))}\n"
        f"• SL:   {yn(trade.get('sl_hit'))}\n"
    )
    return msg

def cancel_all_orders_both_idx(symbol):
    """Отменяет все активные ордера по позиции (для обоих индексов)"""
    for idx in [0, 1]:
        try:
            session.cancel_all_orders(category="linear", symbol=symbol, position_idx=idx)
            log_to_queue("SL_CANCEL_IDX", f"{symbol} | cancel по idx={idx}")
        except Exception as e:
            log_to_queue("SL_CANCEL_FAIL", f"{symbol} | idx={idx} | {e}")

def repeat_cancel_until_clean(symbol):
    """Повторяет отмену всех ордеров несколько раз для полного удаления"""
    print(f"🔥 Старт цикла отмены ордеров для {symbol}")
    for i in range(10):
        try:
            session.cancel_all_orders(category="linear", symbol=symbol, position_idx=0)
            session.cancel_all_orders(category="linear", symbol=symbol, position_idx=1)
            log_to_queue("SL_FORCE_LOOP", f"{symbol} | отмена повтор {i+1}")
            time.sleep(2)
        except Exception as e:
            print(f"❌ CANCEL LOOP ERROR {symbol}: {e}")
    print(f"✅ Цикл отмены ордеров завершён для {symbol}")

def check_and_close_positions():
    """Основная функция отслеживания закрытия позиций"""
    trades = _load_open_trades()
    still_open = []

    for trade in trades:
        try:
            symbol = trade["symbol"]
            entry = float(trade.get("real_entry_price", 0))
            leverage = float(trade.get("real_leverage", 20))
            side = trade.get("side", "Buy")

            pos1 = get_position(symbol)
            size1 = float(pos1.get("size", 0))
            if size1 > 0:
                still_open.append(trade)
                continue

            # Перепроверяем спустя 3 секунды
            time.sleep(3)
            pos2 = get_position(symbol)
            size2 = float(pos2.get("size", 0))

            # Защита от преждевременного закрытия
            if size2 > 0 and trade.get("tp1_hit") and not trade.get("tp2_hit") and not trade.get("sl_hit"):
                log_to_queue("SKIP_EXIT_TP1_ONLY", f"{symbol} | TP1 был, но позиция активна — не закрываем")
                still_open.append(trade)
                continue

            if size2 == 0:
                # Позиция закрыта - начинаем обработку
                last_price = float(pos2.get("lastPrice", 0))
                qty = float(trade.get("position_qty", 0))
                if not entry or not qty:
                    log_to_queue("EXIT_SKIPPED", f"{symbol} | Пропущено: entry или qty = 0")
                    still_open.append(trade)
                    continue

                # Отмена ордеров (если SL уже перенесён в BE)
                if trade.get("sl_be_moved"):
                        try:
                            repeat_cancel_until_clean(symbol)
                            log_to_queue("ORDERS_CANCELED", f"{symbol} | все отложенные ордера отменены")
                        except Exception as e:
                            log_to_queue("ORDERS_CANCEL_FAIL", f"{symbol} | ошибка отмены ордеров: {e}")

                # Получаем fills от Bybit API
                exit_dt = datetime.utcnow()
                opened_at = trade.get("opened_at")
                
                fills = []
                if opened_at:
                    try:
                        opened_dt = datetime.strptime(opened_at, "%Y-%m-%d %H:%M:%S")
                        start_time = int(opened_dt.timestamp() * 1000) - 300000  # -5 минут
                        end_time = int(exit_dt.timestamp() * 1000) + 60000      # +1 минута
                        fills = _get_executions(symbol, start_time, end_time)
                    except Exception as e:
                        trace("FILLS_FETCH_EXCEPTION", {"symbol": symbol, "err": str(e)}, "position_exit_tracker")

                # Вычисляем PnL/ROI
                calc_result = {}
                if fills:
                    calc_result = _calc_from_fills(trade, fills)
                    if calc_result.get("roi_calc_note") == "ok":
                        trace("FILLS_CALC_OK", {"symbol": symbol}, "position_exit_tracker")
                    else:
                        trace("FILLS_PARTIAL_FALLBACK", {"symbol": symbol, "note": calc_result.get("roi_calc_note")}, "position_exit_tracker")
                else:
                    trace("FILLS_FETCH_EMPTY", {"symbol": symbol}, "position_exit_tracker")
                
                # Fallback если fills недоступны
                if not calc_result or calc_result.get("roi_calc_note") != "ok":
                    calc_result = _fallback_calc(trade, last_price)
                    trace("FALLBACK_CALC_USED", {"symbol": symbol}, "position_exit_tracker")

                # Базовые поля
                trade["exit_time"] = exit_dt.strftime("%Y-%m-%d %H:%M:%S")
                trade["status"] = "closed"

                # Применяем результаты расчёта
                trade.update(calc_result)

                # Получаем последний fill для дополнительной информации
                fill = None
                try:
                    fill = get_last_exit_fill_price_safe(symbol)
                except Exception as e:
                    trace("FILL_FETCH_FAIL", {"symbol": symbol, "err": str(e)}, "position_exit_tracker")

                if fill and fill.get("price"):
                    trade["exit_price_bybit"] = float(fill["price"])
                    trade["exit_slippage"] = round(float(fill["price"]) - last_price, 6) if last_price else None
                    trade["exit_latency_ms"] = fill.get("latency_ms")
                    trade["order_id_exit"] = fill.get("orderId")

                # Определяем exit_reason если не задан
                if not trade.get("exit_reason"):
                    tp1_hit = trade.get("tp1_hit")
                    tp2_hit = trade.get("tp2_hit")
                    sl_hit = trade.get("sl_hit")

                    if tp2_hit:
                        trade["exit_reason"] = "tp2"
                    elif sl_hit:
                        trade["exit_reason"] = "sl"
                    elif tp1_hit:
                        trade["exit_reason"] = "tp1_be"
                    else:
                    trade["exit_reason"] = "manual"

                # Получаем PnL через API
                try:
                    if trade.get("order_id"):
                        closed = session.get_closed_pnl(category="linear", symbol=symbol, limit=20)
                    else:
                        closed = {"result": {"list": []}}
                    
                    found = False
                    for item in closed.get("result", {}).get("list", []):
                        if item.get("orderId") in [trade.get("order_id"), trade.get("order_id_exit")]:
                            trade["bybit_pnl_net_api"] = float(item.get("closedPnl", 0))
                            trade["bybit_fee_total_api"] = float(item.get("cumCommission", 0))
                            trade["bybit_avg_entry_api"] = float(item.get("avgEntryPrice", 0))
                            trade["bybit_avg_exit_api"] = float(item.get("avgExitPrice", 0))
                            trade["bybit_closed_size"] = float(item.get("closedSize", 0))
                            trade["order_id_exit"] = item.get("orderId")
                            
                            # Сравнение с нашими расчётами
                            if trade.get("pnl_final_real") is not None:
                                diff = abs(trade["bybit_pnl_net_api"] - trade["pnl_final_real"])
                                if diff > 0.01:  # Допуск 1 цент
                                    trace("FILLS_VS_API_MISMATCH", {
                                        "symbol": symbol,
                                        "our_pnl": trade["pnl_final_real"],
                                        "api_pnl": trade["bybit_pnl_net_api"],
                                        "diff": diff
                                    }, "position_exit_tracker")
                            
                            log_to_queue("PNL_API_FETCHED", f"{symbol} | PnL from API: {trade['bybit_pnl_net_api']} USDT")
                            found = True
                            break
                    
                    if not found:
                        log_to_queue("PNL_NOT_FOUND", f"{symbol} | ордер не найден в API")
                        
                except Exception as e:
                    log_to_queue("PNL_API_FAIL", f"{symbol} | {e}")

                # Определяем финальный PnL и источник
                final_pnl = None
                pnl_source = "unknown"
                
                if trade.get("bybit_pnl_net_api") is not None:
                    final_pnl = trade["bybit_pnl_net_api"]
                    pnl_source = "bybit"
                elif trade.get("pnl_final_real") is not None:
                    final_pnl = trade["pnl_final_real"]
                    pnl_source = trade.get("pnl_source", "calc")

                # Дополнительные поля
                try:
                    dt_open = datetime.strptime(trade["opened_at"], "%Y-%m-%d %H:%M:%S")
                    trade["weekday"] = dt_open.weekday()
                    trade["weekday_name"] = calendar.day_name[dt_open.weekday()]
                    trade["opened_at_full"] = dt_open.strftime("%Y-%m-%d %H:%M:%S")
                    
                    duration_sec = _duration_sec(trade, exit_dt)
                    if duration_sec is not None:
                        trade["duration_sec"] = duration_sec
                        
                except Exception as e:
                    log_to_queue("DURATION_CALC_FAIL", f"{symbol} | {e}")

                # ROI UI (проверочное)
                try:
                    entry_price_val = float(trade.get("real_entry_price") or 0)
                    lev = float(trade.get("real_leverage") or 1)
                    exit_price_used = float(trade.get("exit_price_bybit") or last_price)
                    
                    if entry_price_val > 0:
                        roi_ui = ((exit_price_used - entry_price_val) / entry_price_val) * lev * 100.0
                    trade["roi_ui"] = round(roi_ui, 2)
                except Exception:
                    trade["roi_ui"] = None

                # Предпросмотр и запись
                log_to_queue("EXIT_PREVIEW_TRIGGERED", f"{symbol} | готовим предпросмотр закрытия сделки")

                try:
                    duration = _duration_sec(trade, exit_dt)
                    preview = _preview_message(trade, last_price, final_pnl or 0, pnl_source, duration)
                    log_to_queue("EXIT_INSERT_PREVIEW", preview)

                    ghost_write_safe("trades", trade)
                    trace("EXIT_RECORDED", {"symbol": symbol, "roi": trade.get("roi_final_real"), "id": trade.get("id")}, "position_exit_tracker")
                    log_to_queue("DEAL_CLOSED", f"{symbol} | ROI: {trade.get('roi_final_real')}%")
                    print(f"[✅] WRITE_OK → {symbol}")
                    
                except Exception as e:
                    print(f"[❌] EXIT_INSERT_PREVIEW_FAIL → {symbol} | {e}")
                    continue

        except Exception as e:
            trace("EXIT_CHECK_FAIL", {"error": str(e), "symbol": trade.get("symbol"), "id": trade.get("id")}, "position_exit_tracker")
            log_to_queue("EXIT_EXCEPTION", f"{trade.get('symbol', 'UNKNOWN')} | ошибка в блоке try: {str(e)}")

    _save_open_trades(still_open)

if __name__ == "__main__":
    print("🔁 GHOST Exit Monitor v2.0 (fills-first) запущен...")
    while True:
        check_and_close_positions()
        time.sleep(10) 