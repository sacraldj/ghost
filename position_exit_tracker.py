# === GHOST-META ===
# 📂 Путь: core/position_exit_tracker.py
# 📦 Назначение: Отслеживает закрытие позиции по open_trades.json → добавляет exit_time, ROI, и очищает JSON
# 🔁 Зависимости: ghost_bybit_position.get_position, ghost_write_safe, trace, get_last_exit_fill_price_safe
# 🔒 Статус: ✅ боевой v1.4 (добавлена запись входного Fill при открытии)

import json
import time
import yaml
import calendar
from datetime import datetime
from pybit.unified_trading import HTTP
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

def load_open_trades():
    try:
        with open(OPEN_TRADES_PATH) as f:
            return json.load(f)
    except:
        return []

def save_open_trades(data):
    with open(OPEN_TRADES_PATH, "w") as f:
        json.dump(data, f, indent=2)

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
    trades = load_open_trades()
    still_open = []

    for trade in trades:
        try:
            symbol = trade["symbol"]
            entry = float(trade.get("real_entry_price", 0))
            leverage = float(trade.get("real_leverage", 20))
            side = trade.get("side", "Buy")  # Long (Buy) or Short (Sell)

            pos1 = get_position(symbol)
            size1 = float(pos1.get("size", 0))
            if size1 > 0:
                # Позиция ещё открыта
                still_open.append(trade)
                continue

            # Позиция потенциально закрыта – перепроверяем спустя 3 секунды
            time.sleep(3)
            pos2 = get_position(symbol)
            size2 = float(pos2.get("size", 0))

            # 🛡 НЕ закрывать, если TP1 был, а TP2 и SL — нет, и позиция ещё активна
            if size2 > 0 and trade.get("tp1_hit") and not trade.get("tp2_hit") and not trade.get("sl_hit"):
                log_to_queue("SKIP_EXIT_TP1_ONLY", f"{symbol} | TP1 был, но позиция активна — не закрываем")
                still_open.append(trade)
                continue

            if size2 == 0:

                # 🛡 Защита: если TP1 уже достигнут, но SL ещё не перенесён — НЕ закрываем
                if trade.get("tp1_hit") and not trade.get("sl_be_moved"):
                    msg = f"{symbol} | TP1 достигнут, но SL в BE ещё не выставлен → сделка НЕ закрыта"
                    print(f"⚠️  {msg}")
                    log_to_queue("TP1_BE_HOLD", msg)
                    still_open.append(trade)
                    continue

                # Позиция закрыта (size=0) → начинаем обработку закрытия
                last_price = float(pos2.get("lastPrice", 0))
                qty = float(trade.get("position_qty", 0))
                if not entry or not qty:
                    log_to_queue("EXIT_SKIPPED", f"{symbol} | Пропущено: entry или qty = 0")
                    still_open.append(trade)
                    continue

                # 🛡  Защита: не отменяем ордера, если SL в BE ещё не перенесён
                if not trade.get("sl_be_moved"):
                    msg = f"{symbol} | SL ещё не перенесён в BE → ордера НЕ отменяем"
                    print(f"⚠️  {msg}")
                    log_to_queue("SKIP_ORDER_CANCEL", msg)
                else:
                    tp2_active = False
                    tp2_order_id = trade.get("tp2_order_id")
                    try:
                        if tp2_order_id:
                            tp2_check = session.get_open_orders(
                                category="linear",
                                symbol=symbol,
                                orderId=tp2_order_id,
                                openOnly=0
                            )
                            tp2_list = tp2_check.get("result", {}).get("list", [])
                            tp2_active = bool(tp2_list)
                            if tp2_active:
                                log_to_queue("TP2_STILL_ACTIVE", f"{symbol} | TP2 всё ещё активен, не удаляем")
                                still_open.append(trade)
                                continue
                    except Exception as e:
                        log_to_queue("TP2_CHECK_FAIL", f"{symbol} | ошибка при проверке TP2: {e}")

                    if not tp2_active:
                        try:
                            repeat_cancel_until_clean(symbol)
                            log_to_queue("ORDERS_CANCELED", f"{symbol} | все отложенные ордера отменены")
                        except Exception as e:
                            log_to_queue("ORDERS_CANCEL_FAIL", f"{symbol} | ошибка отмены ордеров: {e}")

                # 🔁 ВОЗВРАТ ВСЕХ РАСЧЁТОВ ПОЗИЦИИ
                position_value = entry * qty
                margin_used = position_value / leverage
                fee = position_value * 0.00055 * 2  # комиссия на вход+выход (0.055% каждый)

                pnl_gross = (last_price - entry) * qty
                pnl_net = pnl_gross - fee
                roi_gross = round((pnl_gross / margin_used) * 100, 2) if margin_used else 0.0
                roi_net = round((pnl_net / margin_used) * 100, 2) if margin_used else 0.0
                margin_usd = float(trade.get("margin_usd") or margin_used or 1)
                roi_plan = round((pnl_net / margin_usd) * 100, 2) if margin_usd else 0.0

                # Получаем информацию о последнем исполненном ордере выхода (цена fill)
                fill = get_last_exit_fill_price_safe(symbol)
                if fill:
                    fill_price = fill.get("price")
                    latency = fill.get("latency_ms")
                    slippage = round(fill_price - last_price, 6) if fill_price and last_price else None
                    trade["exit_price_bybit"] = fill_price
                    trade["exit_slippage"] = slippage
                    trade["exit_latency_ms"] = latency

                    if fill_price:
                        roi_bybit = round((((fill_price - entry) * qty) - fee) / margin_used * 100, 2) if margin_used else 0.0
                        trade["roi_percent_bybit"] = roi_bybit

                        # ✅ Фактический PnL (net) с учётом комиссий на вход и выход
                        fee_open = entry * qty * 0.00055
                        fee_close = fill_price * qty * 0.00055
                        fee_total = fee_open + fee_close
                        bybit_pnl_net = (fill_price - entry) * qty - fee_total

                        trade["bybit_fee_open"] = round(fee_open, 8)
                        trade["bybit_fee_close"] = round(fee_close, 8)
                        trade["bybit_fee_total"] = round(fee_total, 8)
                        trade["bybit_pnl_net"] = round(bybit_pnl_net, 5)
                else:
                    trade["exit_price_fallback"] = last_price

                # Фиксируем время выхода и статус сделки
                trade["exit_time"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                trade["status"] = "closed"  # 🛠 [PATCH]

                # 🎯 Определяем причину выхода (TP1, TP2, SL, BE, Manual)
                try:
                    tp1_hit = trade.get("tp1_hit")
                    tp2_hit = trade.get("tp2_hit")
                    sl_hit = trade.get("sl_hit")

                    if tp2_hit:
                        exit_reason = "tp2"
                    elif tp1_hit and not tp2_hit:
                        exit_reason = "tp1_be"
                    elif sl_hit:
                        exit_reason = "sl"
                    else:
                        exit_reason = "manual"

                    trade["exit_reason"] = exit_reason

                    # ⏱️ Фиксируем время достижения TP2 / SL
                    now = datetime.utcnow()
                    if exit_reason == "tp2":
                        trade["tp2_hit_time"] = now.strftime("%Y-%m-%d %H:%M:%S")
                        if trade.get("opened_at"):
                            dt_open = datetime.strptime(trade["opened_at"], "%Y-%m-%d %H:%M:%S")
                            trade["tp2_duration_sec"] = int((now - dt_open).total_seconds())
                    elif exit_reason == "sl":
                        trade["sl_hit_time"] = now.strftime("%Y-%m-%d %H:%M:%S")
                        if trade.get("opened_at"):
                            dt_open = datetime.strptime(trade["opened_at"], "%Y-%m-%d %H:%M:%S")
                            trade["sl_duration_sec"] = int((now - dt_open).total_seconds())

                except Exception as e:
                    trade["exit_reason"] = "manual"
                    log_to_queue("EXIT_REASON_FAIL", f"{symbol} → {e}")

                # 📊 ROI-сегмент: расчет TP1/TP2 с точной логикой фондового трейдера
                try:
                    tp1_price = float(trade.get("tp1_price") or 0)
                    tp2_price = float(trade.get("tp2_price") or 0)
                    sl_price = float(trade.get("sl_price") or 0)
                    entry_price = float(trade.get("real_entry_price") or 0)
                    qty = float(trade.get("position_qty") or 0)
                    fee_rate = 0.00055
                    margin_used = float(trade.get("margin_used") or 1)
                    actual_exit_price = float(trade.get("exit_price_bybit") or last_price)

                    qty_half = qty / 2

                    # TP1 - половина позиции закрывается по TP1
                    profit_tp1 = (tp1_price - entry_price) * qty_half
                    fee_tp1 = (entry_price + tp1_price) * qty_half * fee_rate
                    pnl_tp1_net = profit_tp1 - fee_tp1

                    # TP2 - оставшаяся половина закрывается по TP2 или по текущей цене (BE)
                    tp2_hit = trade.get("tp2_hit")
                    if tp2_hit:
                        # TP2 был достигнут - закрываем по TP2
                        profit_tp2 = (tp2_price - entry_price) * qty_half
                        fee_tp2 = (entry_price + tp2_price) * qty_half * fee_rate
                        pnl_tp2_net = profit_tp2 - fee_tp2
                        exit_tp2_type = "tp2"
                    else:
                        # TP2 не был достигнут - закрываем по текущей цене (BE)
                        profit_tp2 = (actual_exit_price - entry_price) * qty_half
                        fee_tp2 = (entry_price + actual_exit_price) * qty_half * fee_rate
                        pnl_tp2_net = profit_tp2 - fee_tp2
                        exit_tp2_type = "be"

                    pnl_final_real = round(pnl_tp1_net + pnl_tp2_net, 4)
                    roi_final_real = round((pnl_final_real / margin_used) * 100, 2)

                    # Stop Loss - рассчитывается на полную позицию
                    loss_sl = (entry_price - sl_price) * qty
                    fee_sl = (entry_price + sl_price) * qty * fee_rate
                    pnl_sl_net = loss_sl - fee_sl
                    roi_sl_real = round((pnl_sl_net / margin_used) * 100, 2)

                    trade["profit_tp1_real"] = round(profit_tp1, 4)
                    trade["profit_tp2_real"] = round(profit_tp2, 4)
                    trade["fee_tp1"] = round(fee_tp1, 4)
                    trade["fee_tp2"] = round(fee_tp2, 4)
                    trade["pnl_tp1_net"] = round(pnl_tp1_net, 4)
                    trade["pnl_tp2_net"] = round(pnl_tp2_net, 4)
                    trade["roi_tp1_real"] = round((pnl_tp1_net / margin_used) * 100, 2)
                    trade["roi_tp2_real"] = round((pnl_tp2_net / margin_used) * 100, 2)
                    trade["roi_final_real"] = roi_final_real
                    trade["pnl_final_real"] = pnl_final_real
                    trade["roi_sl_real"] = roi_sl_real
                    trade["tp2_exit_type"] = exit_tp2_type
                except Exception as e:
                    log_to_queue("TP_SEGMENT_CALC_FAIL", f"{symbol} → {e}")

                # 📈 Плановые ROI и доход по сигналу с учетом стратегии TP1/TP2 (половина объема)
                try:
                    lev_conf = get_leverage(trade, config_path="config/leverage_config.yaml")
                    trade["leverage_used_expected"] = lev_conf

                    tp1_price = float(trade.get("tp1_price") or 0)
                    tp2_price = float(trade.get("tp2_price") or 0)
                    sl_price = float(trade.get("sl_price") or 0)
                    entry_price = float(trade.get("real_entry_price") or 0)
                    qty = float(trade.get("position_qty") or 0)
                    margin_planned = float(trade.get("margin_usd") or trade.get("margin_used") or 1)

                    qty_half = qty / 2

                    # ROI при TP1 (половина объема)
                    roi_tp1_plan = ((tp1_price - entry_price) / entry_price) * lev_conf * 100
                    profit_tp1_plan = (tp1_price - entry_price) * qty_half

                    # ROI при TP2 (оставшаяся половина)
                    roi_tp2_plan = ((tp2_price - entry_price) / entry_price) * lev_conf * 100
                    profit_tp2_plan = (tp2_price - entry_price) * qty_half

                    # Общая ROI при TP1+TP2 (средневзвешенная по объему)
                    # TP1: 50% позиции, TP2: 50% позиции
                    roi_both_plan = round((roi_tp1_plan * 0.5 + roi_tp2_plan * 0.5), 2)
                    profit_both_plan = round(profit_tp1_plan + profit_tp2_plan, 2)

                    # ROI при Stop-Loss (на 100% позиции)
                    roi_sl_plan = ((sl_price - entry_price) / entry_price) * lev_conf * 100
                    loss_sl_plan = (entry_price - sl_price) * qty

                    # Сохраняем
                    trade["roi_planned"] = round(roi_both_plan, 2)
                    trade["roi_sl_expected"] = round(roi_sl_plan, 2)
                    trade["expected_profit_tp1"] = round(profit_tp1_plan, 2)
                    trade["expected_profit_tp2"] = round(profit_tp2_plan, 2)
                    trade["expected_profit_total"] = profit_both_plan
                    trade["expected_loss_sl"] = round(loss_sl_plan, 2)

                except Exception as e:
                    log_to_queue("PLAN_CALC_FAIL", f"{symbol} → {e}")

                # 🟡 Сохраняем order_id выхода для последующей проверки PnL через API
                trade["order_id_exit"] = (fill.get("orderId") if fill else None) or trade.get("order_id")

                # Дополняем информацию о времени открытия и длительности сделки
                try:
                    dt_open = datetime.strptime(trade["opened_at"], "%Y-%m-%d %H:%M:%S")
                    trade["weekday"] = dt_open.weekday()
                    trade["weekday_name"] = calendar.day_name[dt_open.weekday()]
                    trade["opened_at_full"] = dt_open.strftime("%Y-%m-%d %H:%M:%S")
                    try:
                        dt_close = datetime.strptime(trade["exit_time"], "%Y-%m-%d %H:%M:%S")
                        duration_sec = int((dt_close - dt_open).total_seconds())
                        trade["duration_sec"] = duration_sec
                    except Exception as e:
                        log_to_queue("DURATION_CALC_FAIL", f"{symbol} → {e}")
                        duration_sec = None
                except Exception as e:
                    log_to_queue("WEEKDAY_FAIL", f"{symbol} | {e}")

                # Финальный перерасчёт ROI и PnL (Bybit style), если есть все данные
                try:
                    if all([
                        trade.get("real_entry_price"),
                        trade.get("position_qty"),
                        trade.get("exit", {}).get("price") or trade.get("exit_price_bybit")
                    ]):
                        entry_val = float(trade["real_entry_price"])
                        pos_qty = float(trade["position_qty"])
                        lev_real = float(trade.get("real_leverage") or 20)
                        fee_rate = 0.00055
                        actual_exit_price = float(trade.get("exit", {}).get("price") or trade.get("exit_price_bybit") or last_price)

                        roi_bybit_style = ((actual_exit_price - entry_val) * lev_real) / entry_val * 100 if entry_val else 0.0
                        trade["roi_bybit_style"] = round(roi_bybit_style, 2)

                        fee_open_val = entry_val * pos_qty * fee_rate
                        fee_close_val = actual_exit_price * pos_qty * fee_rate
                        fee_total_val = fee_open_val + fee_close_val
                        pnl_net_bybit = (actual_exit_price - entry_val) * pos_qty - fee_total_val

                        trade["bybit_fee_open"] = round(fee_open_val, 8)
                        trade["bybit_fee_close"] = round(fee_close_val, 8)
                        trade["bybit_fee_total"] = round(fee_total_val, 8)
                        trade["bybit_pnl_net"] = round(pnl_net_bybit, 5)

                        # Доля комиссии от движения цены (%)
                        gross_move = pnl_net_bybit + fee_total_val
                        trade["commission_over_roi"] = round((fee_total_val / abs(gross_move)) * 100, 2) if gross_move != 0 else None

                        trade["loss_type"] = "fee_only" if trade["pnl_gross"] > 0 and trade["pnl_net"] < 0 else "price_move"

                        delta_price = abs(actual_exit_price - entry_val)
                        if roi_bybit_style == 0.0 and delta_price > entry_val * 0.001:
                            trade["anomaly_flag"] = True
                            print(f"[⚠️] ANOMALY_ROI_ZERO: Δ={delta_price:.5f}")
                    else:
                        print(f"[⛔️] EXIT_BLOCK_SKIPPED: missing values for ROI calc")
                except Exception as e:
                    print(f"[🔥] ROI_BLOCK_FAIL: {symbol} | {e}")

                # Запрашиваем точный PnL и комиссии через API закрытых сделок Bybit
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
                            log_to_queue("PNL_API_FETCHED", (
                                f"{symbol} | {trade.get('trade_id')} | ✅ PnL fetched from Bybit API: "
                                f"{trade['bybit_pnl_net_api']} USDT | Order: {item.get('orderId')}"
                            ))
                            trace("PNL_API_FETCHED", trade, where="bybit_pnl_checker")
                            found = True
                            break
                    if not found:
                        api_list = closed.get("result", {}).get("list", [])
                        if api_list:
                            fallback = api_list[0]
                            trade["bybit_pnl_net_api"] = float(fallback.get("closedPnl", 0))
                            trade["order_id_exit"] = fallback.get("orderId")
                            log_to_queue("PNL_API_USED_FIRST", (
                                f"{symbol} | {trade.get('trade_id')} | fallback API used → "
                                f"{fallback.get('orderId')}, pnl={trade['bybit_pnl_net_api']} USDT"
                            ))
                            trace("PNL_API_USED_FIRST", trade, where="bybit_pnl_checker")
                        else:
                            log_to_queue("PNL_NOT_FOUND", f"{symbol} | {trade.get('trade_id')} | ордер не найден")
                            trace("PNL_NOT_FOUND", trade, where="bybit_pnl_checker")
                except Exception as e:
                    log_to_queue("PNL_API_FAIL", f"{symbol} | {e}")

                # Определяем финальный PnL и источник данных
                final_pnl = None
                pnl_source = "unknown"
                if trade.get("bybit_pnl_net_api") is not None:
                    final_pnl = trade["bybit_pnl_net_api"]
                    pnl_source = "bybit"
                elif trade.get("bybit_pnl_net_fallback") is not None:
                    final_pnl = trade["bybit_pnl_net_fallback"]
                    pnl_source = "fallback"
                elif trade.get("bybit_pnl_net") is not None:
                    final_pnl = trade["bybit_pnl_net"]
                    pnl_source = "calc"

                # На всякий случай, дублируем order_id_exit из исходного ордера
                trade["order_id_exit"] = trade.get("order_id")

                # 🧮 Финальный ROI с учётом TP1/TP2 логики
                roi_final = trade.get("roi_final_real")
                try:
                    if roi_final is not None:
                        trade["roi_percent"] = roi_final
                        trade["roi_source"] = "real_split"
                    else:
                        trade["roi_percent"] = round((final_pnl / trade["margin_used"]) * 100, 2)
                        trade["roi_source"] = pnl_source
                except Exception:
                    trade["roi_percent"] = "?"
                    trade["roi_source"] = "fail"
                trade["roi_percent_initial"] = trade["roi_percent"]

                # 🎯 Hit-статус на основе exit_reason — только если ещё не зафиксированы
                if trade.get("tp1_hit") is not True:
                    trade["tp1_hit"] = exit_reason in ["tp1_be", "tp2"]
                if trade.get("tp2_hit") is not True:
                    trade["tp2_hit"] = exit_reason == "tp2"
                if trade.get("sl_hit") is not True:
                    trade["sl_hit"] = exit_reason == "sl"

                # Если использован fallback-подсчёт, фиксируем источник
                if trade.get("bybit_pnl_net_fallback") is not None:
                    trade["pnl_net"] = trade["bybit_pnl_net_fallback"]
                    trade["roi_source"] = "fallback"
                    trade["pnl_net_initial"] = trade["pnl_net"]

                # 🧠 Фиксация достижения TP/SL для сделки (в т.ч. multi-target)
                exit_price_val = float(trade.get("exit_price_bybit") or last_price)
                try:
                    if "strategy_2" in str(trade.get("strategy_id", "")):
                        # 🛠 [PATCH]: Отмечаем достижение целей для многоцелевой стратегии
                        trade["tp1_hit"] = True if trade["exit_reason"] == "tp" or exit_price_val >= float(trade.get("tp1_price", 0) or 0) else False
                        trade["tp2_hit"] = True if exit_price_val >= float(trade.get("tp2_price", 0) or 0) else False
                        trade["sl_hit"] = True if trade["exit_reason"] == "sl" else False
                    else:
                        trade["tp1_hit"] = True if trade.get("tp1_price") and exit_price_val >= float(trade["tp1_price"]) else False
                        trade["tp2_hit"] = True if trade.get("tp2_price") and exit_price_val >= float(trade["tp2_price"]) else False
                        trade["sl_hit"] = True if trade.get("sl_price") and exit_price_val <= float(trade["sl_price"]) else False
                    # Флаги раннего выхода (AI) на данный момент не используются
                    trade["early_exit"] = False
                    trade["early_exit_reason"] = None
                    trade["exit_explanation"] = None
                    trade["exit_ai_score"] = None
                except Exception as e:
                    log_to_queue("TP_SL_EVAL_FAIL", f"{symbol} | {e}")

                # ROI как в UI Bybit (для проверки, по позиции)
                try:
                    entry_price_val = float(trade["real_entry_price"])
                    exit_price_val = float(trade.get("exit_price_bybit") or last_price)
                    leverage_val = float(trade.get("real_leverage", 20))
                    roi_ui = ((exit_price_val - entry_price_val) / entry_price_val * leverage_val * 100) if entry_price_val else 0.0
                    trade["roi_ui"] = round(roi_ui, 2)
                except Exception as e:
                    trade["roi_ui"] = None

                # ✅ Добавляем TP/SL order_id в структуру trade перед логами и записью в БД
                trade["tp1_order_id"] = trade.get("tp1_order_id")
                trade["tp2_order_id"] = trade.get("tp2_order_id")
                trade["sl_order_id"] = trade.get("sl_order_id")

                log_to_queue("EXIT_PREVIEW_TRIGGERED", f"{symbol} | готовим предпросмотр закрытия сделки")

                # Логируем подробный предпросмотр закрытия сделки
                try:
                    def yesno(v): return "достигнуто" if v else "не достигнуто"
                    def safe(v, d="?"):
                        return v if v is not None else d

                    duration = safe(duration_sec, 0)
                    message = (
                        f"📄 <b>Trade Recorded: {symbol} | {trade.get('trade_id')}</b>\n"
                        f"🔗 Источник:          {trade.get('source_name', '—')}\n"
                        f"{'─' * 28}\n"
                        f"🟢 Entry Price:        {safe(entry):.5f}\n"
                        f"🔴 Exit Price:         {safe(last_price):.5f}\n"
                        f"📦 Qty:                {safe(qty):.4f}\n"
                        f"⚖️ Leverage:            {safe(trade.get('real_leverage'))}x\n"
                        f"💵 Margin Used:        ${safe(trade.get('margin_used'))}\n"
                        f"{'─' * 28}\n"
                        f"📇 <b>Bybit (реальные данные):</b>\n"
                        f"✅ ROI (API):          {safe(trade.get('roi_percent_bybit'))}%\n"
                        f"📉 ROI (UI):           {safe(trade.get('roi_ui'))}% | Bybit: {safe(trade.get('roi_bybit_style'))}%\n"
                        f"💸 Комиссия (факт):    {safe(trade.get('bybit_fee_total'))} USDT\n"
                        f"📤 PnL (source):       {safe(final_pnl)} USDT ({safe(pnl_source)})\n"
                        f"{'─' * 28}\n"
                        f"📈 <b>Ожидалось по сигналу:</b>\n"
                        f"• TP1: {safe(trade.get('tp1_price'))} → ROI план: {safe(trade.get('roi_planned'))}%\n"
                        f"• SL:  {safe(trade.get('sl_price'))} → ROI SL:    {safe(trade.get('roi_sl_expected'))}%\n"
                        f"💰 Profit @ TP1:      +{safe(trade.get('expected_profit_tp1'))} USDT\n"
                        f"💣 Loss   @ SL:       -{safe(trade.get('expected_loss_sl'))} USDT\n"
                        f"{'─' * 28}\n"
                        f"📉 <b>Получено (факт):</b>\n"
                        f"• ROI (Net):           {safe(trade.get('roi_percent'))}%\n"
                        f"• ROI (TP1):           {safe(trade.get('roi_tp1_real'))}%\n"
                        f"• ROI (TP2):           {safe(trade.get('roi_tp2_real'))}%\n"
                        f"• ROI (SL):            {safe(trade.get('roi_sl_real'))}%\n"
                        f"• ROI (Final):         {safe(trade.get('roi_final_real'))}%\n"
                        f"⏱️ Duration:            {duration // 60}m {duration % 60}s\n"
                        f"{'─' * 28}\n"
                        f"📌 <b>ФИНАЛ:</b>\n"
                        f"💥 РЕЗУЛЬТАТ:          {safe(final_pnl)} USDT\n"
                        f"📊 Доходность:         {safe(trade.get('roi_percent'))}% от маржи\n"
                        f"📆 Day:                {safe(trade.get('weekday_name'))} ({safe(trade.get('opened_at_full'))})\n"
                        f"🚩 Exit Reason:        {safe(trade.get('exit_reason'))} | TP2 type: {safe(trade.get('tp2_exit_type'))}\n"
                        f"{'─' * 28}\n"
                        f"📍 <b>TP/SL Статус:</b>\n"
                        f"• TP1:  {yesno(trade.get('tp1_hit'))}\n"
                        f"• TP2:  {yesno(trade.get('tp2_hit'))}\n"
                        f"• SL:   {yesno(trade.get('sl_hit'))}\n"
                        f"• Early Exit:         {safe(trade.get('early_exit'))}\n"
                    )

                    log_to_queue("EXIT_INSERT_PREVIEW", message)

                    try:
                        ghost_write_safe("trades", trade)  # сохраняем запись сделки в БД
                        trace("EXIT_RECORDED", {"symbol": symbol, "roi": roi_net, "id": trade.get("id")}, where="position_exit_tracker")
                        log_to_queue("DEAL_CLOSED", f"{symbol} | ROI: {roi_net}%")
                        print(f"[✅] WRITE_OK → {symbol}")
                    except Exception as e:
                        print(f"[❌] FINAL_EXIT_BLOCK_FAIL → {symbol} | {e}")
                        continue
                except Exception as e:
                    print(f"[❌] EXIT_INSERT_PREVIEW_FAIL → {symbol} | {e}")
                    continue

                # (Если по каким-то причинам exit_time не задан, не удаляем сделку из открытых)
                if not trade.get("exit_time"):
                    log_to_queue("EXIT_TIME_MISSING", f"{symbol} | exit_time отсутствует, сделка не удалена из списка открытых")
                    still_open.append(trade)
        except Exception as e:
            trace("EXIT_CHECK_FAIL", {"error": str(e), "symbol": trade.get("symbol"), "id": trade.get("id")}, where="position_exit_tracker")
            log_to_queue("EXIT_EXCEPTION", f"{symbol} | ошибка в блоке try: {str(e)}")

    save_open_trades(still_open)

if __name__ == "__main__":
    print("🔁 GHOST Exit Monitor запущен...")
    while True:
        check_and_close_positions()
        time.sleep(10) 