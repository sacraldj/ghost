import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

export async function GET(request: NextRequest) {
  try {
    const today = new Date().toISOString().split('T')[0] // YYYY-MM-DD

    // Fetch today's closed trades
    const { data: trades, error } = await supabase
      .from('trades')
      .select(`
        pnl_net,
        bybit_pnl_net_api,
        realized_pnl,
        verdict,
        closed_at,
        opened_at,
        roi_percent
      `)
      .eq('status', 'closed')
      .gte('closed_at', `${today}T00:00:00.000Z`)
      .lt('closed_at', `${today}T23:59:59.999Z`)

    if (error) {
      console.error('Supabase error:', error)
      return NextResponse.json({ error: 'Database error' }, { status: 500 })
    }

    if (!trades || trades.length === 0) {
      return NextResponse.json({
        realized_pnl: 0,
        win_rate: 0,
        total_trades: 0,
        winning_trades: 0,
        losing_trades: 0,
        avg_duration: '0h 0m',
        avg_roi: 0
      })
    }

    // Calculate statistics
    const totalTrades = trades.length
    const winningTrades = trades.filter(t => {
      const pnl = parseFloat(t.bybit_pnl_net_api || t.pnl_net || t.realized_pnl || '0')
      return pnl > 0
    }).length
    
    const losingTrades = trades.filter(t => {
      const pnl = parseFloat(t.bybit_pnl_net_api || t.pnl_net || t.realized_pnl || '0')
      return pnl < 0
    }).length

    const winRate = totalTrades > 0 ? (winningTrades / totalTrades) * 100 : 0

    // Calculate total realized PnL
    const totalRealizedPnL = trades.reduce((sum, trade) => {
      const pnl = parseFloat(trade.bybit_pnl_net_api || trade.pnl_net || trade.realized_pnl || '0')
      return sum + pnl
    }, 0)

    // Calculate average ROI
    const avgROI = trades.reduce((sum, trade) => {
      const roi = parseFloat(trade.roi_percent || '0')
      return sum + roi
    }, 0) / totalTrades

    // Calculate average trade duration
    const durations = trades
      .filter(t => t.opened_at && t.closed_at)
      .map(t => {
        const opened = new Date(t.opened_at)
        const closed = new Date(t.closed_at)
        return closed.getTime() - opened.getTime()
      })

    let avgDuration = '0h 0m'
    if (durations.length > 0) {
      const avgMs = durations.reduce((sum, d) => sum + d, 0) / durations.length
      const hours = Math.floor(avgMs / (1000 * 60 * 60))
      const minutes = Math.floor((avgMs % (1000 * 60 * 60)) / (1000 * 60))
      avgDuration = `${hours}h ${minutes}m`
    }

    return NextResponse.json({
      realized_pnl: totalRealizedPnL,
      win_rate: winRate,
      total_trades: totalTrades,
      winning_trades: winningTrades,
      losing_trades: losingTrades,
      avg_duration: avgDuration,
      avg_roi: avgROI
    })

  } catch (error) {
    console.error('Error fetching today stats:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
