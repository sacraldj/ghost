-- Minimal table for charts (safe, derived later can expand)

create table if not exists trades_min (
  trade_id text primary key,
  id text,
  symbol text,
  side text,
  entry_price numeric,
  exit_price numeric,
  pnl numeric,
  roi numeric,
  opened_at timestamptz,
  closed_at timestamptz,
  tp1_hit boolean,
  tp2_hit boolean,
  sl_hit boolean,
  synced_at timestamptz default now()
);

alter table trades_min enable row level security;
create policy "public read trades_min" on trades_min for select using (true);

-- Optional indexes
create index if not exists idx_trades_min_symbol on trades_min(symbol);
create index if not exists idx_trades_min_opened_at on trades_min(opened_at);


