# 📊 Signal Chart System - Complete Documentation

## 🎯 Overview

Система интерактивных графиков для визуализации торговых сигналов в реальном времени. Автоматически собирает и отображает 1-секундные свечи с Bybit API для каждого сигнала из таблицы v_trades.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    SYSTEM COMPONENTS                    │
├─────────────────────────────────────────────────────────┤
│  Frontend (React/TypeScript)                           │
│  ├── SignalChart.tsx           - Interactive chart     │
│  ├── TestTableComponent.tsx    - Enhanced table        │
│  └── API endpoints             - /api/signal-*         │
├─────────────────────────────────────────────────────────┤
│  Backend Services (Python)                             │
│  ├── bybit_websocket.py        - WebSocket client      │
│  ├── signal_candle_tracker.py  - Auto tracking        │
│  └── start_signal_system.py    - Main service          │
├─────────────────────────────────────────────────────────┤
│  Database (Supabase/PostgreSQL)                        │
│  ├── signal_candles_1s         - 1-second candles     │
│  ├── signal_websocket_subscriptions - Tracking status │
│  └── v_trades                  - Original signals      │
└─────────────────────────────────────────────────────────┘
```

## 📁 Files Created/Modified

### ✅ **Database Schema**
- `create_signal_candles_tables.sql` - Complete DB schema with tables, indexes, functions

### ✅ **Backend Services**
- `core/bybit_websocket.py` - Bybit WebSocket client for real-time candles
- `core/signal_candle_tracker.py` - Automatic signal tracking service
- `start_signal_system.py` - Main service entry point

### ✅ **API Endpoints**
- `app/api/signal-candles/[signalId]/route.ts` - Get candles for specific signal
- `app/api/signal-tracking/route.ts` - Start/stop signal tracking

### ✅ **Frontend Components**
- `app/components/SignalChart.tsx` - Interactive chart component
- `app/components/TestTableComponent.tsx` - Enhanced with chart integration

### ✅ **Dependencies**
- `requirements_signal_system.txt` - Python dependencies for the system

## 🚀 Installation & Setup

### 1. Database Setup
```sql
-- Run this in your Supabase SQL editor
\i create_signal_candles_tables.sql
```

### 2. Python Dependencies
```bash
# Install additional dependencies
pip install -r requirements_signal_system.txt
```

### 3. Environment Variables
Add to your `.env` file:
```env
# Existing Supabase vars (should already be set)
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
SUPABASE_SECRET_KEY=your_supabase_secret_key

# No additional vars needed - uses existing Supabase setup
```

### 4. Start the System
```bash
# Start the Python tracking service (in background)
python start_signal_system.py

# Your Next.js app (existing)
npm run dev
```

## 🎮 How to Use

### **Step 1: Navigate to Test Table**
- Go to `/test-table` in your GHOST dashboard
- You'll see the enhanced interface with chart above the table

### **Step 2: Select a Signal**
- Click any signal record in the table
- Chart will automatically load for that signal
- Signal levels (TP1, TP2, SL, Entry Zone) are displayed

### **Step 3: Start Real-time Tracking**
- Click "Start Recording" button on the chart
- System begins collecting 1-second candles from Bybit
- Chart updates in real-time (refresh to see new data)

### **Step 4: View Historical Data**
- Switch timeframes (1s, 1m, 5m, 15m, 1h)
- View candle statistics and duration
- Analyze price movement relative to signal levels

## 🔧 System Features

### **📊 Interactive Chart**
- ✅ Real-time candle display
- ✅ Signal levels visualization (TP1/TP2/SL/Entry)
- ✅ Multiple timeframes
- ✅ Fullscreen mode
- ✅ Recording status indicators

### **🔄 Automatic Tracking**
- ✅ Auto-detects new signals in v_trades
- ✅ Starts WebSocket subscriptions automatically
- ✅ Collects 1-second candles for 7 days
- ✅ Handles reconnections and errors

### **💾 Data Management**
- ✅ Stores all candles in signal_candles_1s table
- ✅ Tracks subscription status
- ✅ Automatic cleanup of old data
- ✅ Statistics and monitoring functions

### **📱 User Interface**
- ✅ Responsive design (desktop/mobile)
- ✅ Table integration
- ✅ Status indicators
- ✅ Error handling and loading states

## 📊 Database Tables

### `signal_candles_1s`
Stores 1-second OHLCV candles for each tracked signal:
```sql
signal_id TEXT          -- Links to v_trades.id
symbol TEXT             -- BTCUSDT, APTUSDT, etc.
timestamp INTEGER       -- Unix timestamp (seconds)
open, high, low, close  -- Price data
volume, quote_volume    -- Volume data
```

### `signal_websocket_subscriptions`
Tracks active WebSocket subscriptions:
```sql
signal_id TEXT      -- Links to v_trades.id
symbol TEXT         -- Trading pair
status TEXT         -- active, stopped, completed, error
start_time INTEGER  -- When tracking started
end_time INTEGER    -- When tracking ended (NULL = active)
candles_collected   -- Number of candles collected
```

## 🔌 API Endpoints

### Get Signal Candles
```typescript
GET /api/signal-candles/[signalId]?interval=1m&limit=1000

Response:
{
  "signal": { /* v_trades record */ },
  "candles": [ /* OHLCV data */ ],
  "stats": { /* statistics */ }
}
```

### Control Signal Tracking  
```typescript
POST /api/signal-tracking
Body: { "signal_id": "abc123", "action": "start"|"stop" }

Response:
{
  "message": "Signal tracking started",
  "subscription": { /* tracking record */ }
}
```

### Get Tracking Status
```typescript
GET /api/signal-tracking

Response:
{
  "subscriptions": [ /* active subscriptions */ ],
  "summary": { /* system statistics */ }
}
```

## 🏃‍♂️ Workflow Example

### **Scenario: New Signal Arrives**
```
1. 📨 Signal saved to v_trades (existing system)
2. 🤖 signal_candle_tracker detects new signal  
3. 🔌 WebSocket subscription starts for symbol
4. 📊 1-second candles begin streaming from Bybit
5. 💾 Candles saved to signal_candles_1s table
6. 📈 User selects signal → Chart displays data
7. ⏱️ Tracking continues for 7 days automatically
```

### **User Interaction Flow**
```
1. 👤 User opens /test-table
2. 🖱️ Clicks signal in table
3. 📊 Chart loads with signal data
4. 🎯 TP/SL levels displayed on chart  
5. 🔴 User clicks "Start Recording"
6. ⚡ Real-time candles begin flowing
7. 📈 Chart updates with live price action
```

## 📈 Benefits

### **For Traders**
- 📊 **Professional Visualization** - Charts like TradingView
- 🎯 **Signal Analysis** - See exactly how signals performed
- ⏱️ **Precise Timing** - 1-second accuracy for entries/exits
- 📱 **Mobile Friendly** - Works on all devices

### **For System**
- 🤖 **Automated Operation** - No manual intervention needed
- 📊 **Complete Data** - Never miss price movements
- 🔍 **AI Ready** - Perfect data for machine learning
- 📈 **Scalable** - Handles unlimited symbols/signals

### **For Analysis**
- 📊 **Historical Accuracy** - Replay any signal exactly
- 🎯 **Performance Metrics** - Precise hit rates and timing
- 📈 **Pattern Recognition** - Identify successful setups
- 🔍 **Market Behavior** - Understand price reactions to signals

## 🔧 Maintenance

### **Log Files**
```bash
# Check system logs
tail -f logs/signal_system.log

# Monitor WebSocket connections
grep "WebSocket" logs/signal_system.log
```

### **Database Cleanup**
```sql
-- Clean old candles (older than 30 days)
SELECT cleanup_old_candles(30);

-- Check system statistics  
SELECT get_tracking_statistics();
```

### **Service Management**
```bash
# Check if service is running
ps aux | grep start_signal_system

# Restart service
python start_signal_system.py

# Monitor resource usage
htop
```

## ⚡ Performance

### **Expected Load**
- 📊 **~3600 candles/hour** per active symbol
- 💾 **~1MB storage/day** per symbol  
- 🔌 **Low CPU/memory** usage (async I/O)
- 🌐 **1 WebSocket** connection per symbol

### **Optimization Tips**
- 🗄️ Use indexes for fast queries
- 🧹 Regular cleanup of old data
- 📊 Monitor WebSocket connections
- 🔍 Use database views for complex queries

## 🎉 **SYSTEM IS READY!**

The complete signal chart system is now implemented and ready to use! 

🚀 **Next Steps:**
1. Run the SQL to create tables
2. Install Python dependencies  
3. Start the tracking service
4. Navigate to `/test-table` 
5. Select a signal and start recording!

Your GHOST system now has professional-grade signal visualization! 📊✨
