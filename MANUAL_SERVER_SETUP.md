# 📋 Ручная настройка сервера Дарэна

> Поскольку SSH подключение недоступно, используйте эту инструкцию для ручной настройки

## 1. 📁 Файлы для копирования на сервер

Скопируйте следующие файлы в `/root/ghost_system_final/ghost_system_final_146/tools/`:

### `trades_supabase_sync.py`
```python
#!/usr/bin/env python3
"""
GHOST Trades → Supabase Sync (minimal fields)

Purpose:
- Read trades from a local SQLite database (ghost.db)
- Derive a small, stable subset of fields for charts
- Upsert into Supabase table `trades_min`

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


def read_trades(db_path: str, limit: int = 500) -> List[Dict]:
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
            items.append(row_out)
        logger.info(f"Collected {len(items)} trades from SQLite")
        return items


def upsert_trades_min(sb: Client, items: List[Dict]) -> None:
    if not items:
        return
    
    try:
        result = sb.table("trades_min").upsert(items, on_conflict="trade_id").execute()
        logger.info(f"Upserted {len(items)} trades to Supabase")
    except Exception as e:
        logger.error(f"Upsert error: {e}")


def main() -> None:
    db_path = os.getenv("GHOST_DB_PATH", "./ghost.db")
    interval = int(os.getenv("SYNC_INTERVAL_SEC", "60"))
    loop = os.getenv("SYNC_LOOP", "1") == "1"

    sb = get_supabase_client()
    if sb is None:
        return

    def one_pass():
        items = read_trades(db_path)
        upsert_trades_min(sb, items)

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
```

### `requirements.txt`
```
supabase>=2.0.0
python-dotenv>=1.0.0
```

## 2. 🔧 Команды для выполнения на сервере

Подключитесь к серверу и выполните:

```bash
# Перейдите в рабочую директорию
cd /root/ghost_system_final/ghost_system_final_146

# Проверьте наличие базы данных
ls -la ghost.db

# Создайте Python venv (если нет)
python3.10 -m venv venv310

# Активируйте venv
source venv310/bin/activate

# Установите зависимости
pip install supabase python-dotenv

# Создайте файл переменных окружения
cat > .env << 'EOF'
# Замените на ваши реальные значения
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# Путь к базе данных
GHOST_DB_PATH=./ghost.db

# Настройки синхронизации
SYNC_INTERVAL_SEC=60
SYNC_LOOP=1
EOF

echo "⚠️  ВАЖНО: Отредактируйте .env файл и добавьте ваши ключи Supabase!"
```

## 3. 🔑 Получение ключей Supabase

1. Перейдите на https://supabase.com
2. Откройте ваш проект
3. Перейдите в Settings → API
4. Скопируйте:
   - Project URL (NEXT_PUBLIC_SUPABASE_URL)
   - service_role secret (SUPABASE_SERVICE_ROLE_KEY)

## 4. ✏️ Редактирование .env файла

```bash
# Отредактируйте файл
nano .env

# Или
vim .env
```

Замените `your-project-id` и `your_service_role_key_here` на реальные значения.

## 5. 🧪 Тестирование синхронизации

```bash
# Активируйте venv
source venv310/bin/activate

# Тестовый запуск (однократно)
SYNC_LOOP=0 python tools/trades_supabase_sync.py

# Если успешно, запустите постоянную синхронизацию
python tools/trades_supabase_sync.py
```

## 6. 🔄 Автоматический запуск

### Вариант A: tmux

```bash
# Создайте новое окно tmux для синхронизации
tmux new-window -t ghost -n sync

# В новом окне запустите синхронизацию
cd /root/ghost_system_final/ghost_system_final_146
source venv310/bin/activate
python tools/trades_supabase_sync.py
```

### Вариант B: systemd service

```bash
# Создайте service файл
sudo cat > /etc/systemd/system/ghost-sync.service << 'EOF'
[Unit]
Description=GHOST Trades Sync
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/ghost_system_final/ghost_system_final_146
Environment=PATH=/root/ghost_system_final/ghost_system_final_146/venv310/bin
ExecStart=/root/ghost_system_final/ghost_system_final_146/venv310/bin/python tools/trades_supabase_sync.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Включите и запустите сервис
sudo systemctl daemon-reload
sudo systemctl enable ghost-sync
sudo systemctl start ghost-sync

# Проверьте статус
sudo systemctl status ghost-sync
```

## 7. 📊 Проверка результатов

После запуска синхронизации проверьте:

1. **Логи синхронизации:**
   ```bash
   # Смотрите логи в реальном времени
   tail -f /var/log/syslog | grep ghost
   ```

2. **Данные в Supabase:**
   - Перейдите в Supabase Dashboard
   - Откройте Table Editor
   - Проверьте таблицу `trades_min`

3. **API endpoint:**
   ```bash
   # Проверьте API вашего веб-приложения
   curl https://your-app.vercel.app/api/supabase-trades
   ```

## 🎉 Готово!

После успешной настройки:
- ✅ Трейды из SQLite синхронизируются в Supabase каждые 60 секунд
- ✅ Веб-дашборд получает данные через API
- ✅ Графики отображают актуальную статистику

## 🆘 Устранение проблем

### Ошибка "Table 'trades' not found"
```bash
# Проверьте структуру базы данных
sqlite3 ghost.db ".tables"
sqlite3 ghost.db ".schema trades"
```

### Ошибка подключения к Supabase
```bash
# Проверьте переменные окружения
cat .env

# Тестируйте подключение
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('URL:', os.getenv('NEXT_PUBLIC_SUPABASE_URL'))
print('Key:', os.getenv('SUPABASE_SERVICE_ROLE_KEY')[:10] + '...')
"
```

### Проблемы с правами доступа
```bash
# Сделайте файлы исполняемыми
chmod +x tools/trades_supabase_sync.py
chmod 600 .env
```
