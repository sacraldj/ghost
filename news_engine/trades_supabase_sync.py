#!/usr/bin/env python3
"""
GHOST Trades → Supabase Sync (full + minimal)

Purpose:
- Read trades from a local SQLite database (ghost.db)
- Derive a small, stable subset of fields for charts
- Upsert into Supabase table `trades_min`
- Optionally mirror full table `trades` when FULL_SYNC=1

Environment:
- NEXT_PUBLIC_SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_SECRET_KEY)
- GHOST_DB_PATH (default: ./ghost.db)

Notes:
- This script does NOT recalculate PnL/ROI. It mirrors current values.
- Safe to run on server (read-only to SQLite). Upserts by `trade_id`.
"""

import os
import sqlite3
import time
import logging
from typing import Dict, List
from datetime import datetime
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("trades_sync")


def get_supabase_client() -> Client | None:
    url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("SUPABASE_SECRET_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        logger.error("Supabase env missing. NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY required")
        return None
    return create_client(url, key)


def read_trades(db_path: str, limit: int = 500, full: bool = False) -> List[Dict]:
    if not os.path.exists(db_path):
        logger.error(f"SQLite DB not found: {db_path}")
        return []

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row

        # Try to guess available columns
        cols = [r[1] for r in conn.execute("PRAGMA table_info(trades)").fetchall()]
        if not cols:
            logger.warning("Table 'trades' not found")
            return []

        # Minimal field mapping with graceful fallbacks
        def has(c: str) -> bool:
            return c in cols

        if full:
            selected = cols  # mirror all columns
        else:
            selected = [c for c in [
            "id", "trade_id", "symbol", "side", "entry_price", "exit_price",
            "pnl_net", "pnl_final_real", "roi_percent", "roi_final_real",
            "opened_at", "closed_at", "tp1_hit", "tp2_hit", "sl_hit",
        ] if has(c)]

        query = f"SELECT {', '.join(selected)} FROM trades ORDER BY opened_at DESC LIMIT ?"
        rows = conn.execute(query, (limit,)).fetchall()

        items: List[Dict] = []
        for r in rows:
            row = dict(r)
            # Normalize field names
            row_out = {
                "id": row.get("id"),
                "trade_id": row.get("trade_id") or row.get("id"),
                "symbol": row.get("symbol"),
                "side": row.get("side"),
                "entry_price": row.get("entry_price"),
                "exit_price": row.get("exit_price"),
                "pnl": row.get("pnl_final_real") or row.get("pnl_net"),
                "roi": row.get("roi_final_real") or row.get("roi_percent"),
                "opened_at": row.get("opened_at"),
                "closed_at": row.get("closed_at"),
                "tp1_hit": row.get("tp1_hit"),
                "tp2_hit": row.get("tp2_hit"),
                "sl_hit": row.get("sl_hit"),
                "synced_at": datetime.utcnow().isoformat(),
            }
            if full:
                # merge all original columns for full mirror
                row_out.update(row)
            items.append(row_out)
        logger.info(f"Collected {len(items)} trades from SQLite")
        return items


def upsert_trades_min(sb: Client, items: List[Dict]) -> None:
    if not items:
        return
    # Upsert by trade_id when possible, else by id
    # Ensure table `trades_min` with unique constraint on trade_id or (id)
    try:
        # Chunk to avoid payload limits
        CHUNK = 100
        for i in range(0, len(items), CHUNK):
            chunk = items[i : i + CHUNK]
            res = sb.table("trades_min").upsert(chunk, on_conflict="trade_id").execute()
            logger.info(f"Upserted {len(chunk)} rows -> {len(res.data or [])}")
    except Exception as e:
        logger.error(f"Upsert error: {e}")


def upsert_trades_full(sb: Client, items: List[Dict]) -> None:
    if not items:
        return
    try:
        CHUNK = 100
        for i in range(0, len(items), CHUNK):
            chunk = items[i : i + CHUNK]
            res = sb.table("trades").upsert(chunk, on_conflict="id").execute()
            logger.info(f"Upserted FULL {len(chunk)} rows -> {len(res.data or [])}")
    except Exception as e:
        logger.error(f"Upsert FULL error: {e}")


def main() -> None:
    db_path = os.getenv("GHOST_DB_PATH", "./ghost.db")
    interval = int(os.getenv("SYNC_INTERVAL_SEC", "60"))
    loop = os.getenv("SYNC_LOOP", "1") == "1"
    full = os.getenv("FULL_SYNC", "0") == "1"

    sb = get_supabase_client()
    if sb is None:
        return

    def one_pass():
        items = read_trades(db_path, full=full)
        upsert_trades_min(sb, items)
        if full:
            upsert_trades_full(sb, items)

    if loop:
        logger.info(f"Starting sync loop. DB={db_path} interval={interval}s")
        while True:
            try:
                one_pass()
            except Exception as e:
                logger.error(f"Sync pass failed: {e}")
            time.sleep(interval)
    else:
        one_pass()


if __name__ == "__main__":
    main()


