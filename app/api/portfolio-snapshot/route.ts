import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

export const runtime = 'nodejs'

// Безопасная инициализация Supabase
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://placeholder.supabase.co'
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || 'placeholder-key'

let supabase: any = null
try {
  if (supabaseUrl !== 'https://placeholder.supabase.co' && supabaseKey !== 'placeholder-key') {
    supabase = createClient(supabaseUrl, supabaseKey)
  }
} catch (error) {
  console.error('Supabase initialization error:', error)
}

interface PortfolioSnapshot {
  // Top KPIs
  aum: number
  equity: number
  pnl_mtd: number
  pnl_ytd: number
  win_rate: number
  exposure_net: number
  leverage: number
  long_exposure: number
  short_exposure: number
  
  // Active Positions
  active_positions: {
    count: number
    total_risk: number
    positions: Array<{
      id: string
      symbol: string
      side: string
      qty: number
      entry_price: number
      tp1_price?: number
      tp2_price?: number
      sl_price?: number
      roi_current: number
      risk_usd: number
      timer_seconds: number
      margin_used: number
      leverage: number
    }>
  }
  
  // Risk Snapshot
  risk_snapshot: {
    var_1d: number
    expected_shortfall_1d: number
    max_drawdown_mtd: number
    portfolio_volatility: number
  }
  
  // Performance Attribution
  performance_attribution: {
    by_strategy: Array<{
      strategy_id: string
      pnl_30d: number
      win_rate: number
      trades_count: number
    }>
    by_symbol: Array<{
      symbol: string
      pnl_30d: number
      trades_count: number
    }>
    by_exit_type: {
      tp1_pnl: number
      tp2_pnl: number
      sl_pnl: number
      manual_pnl: number
    }
  }
  
  // Execution Metrics
  execution_metrics: {
    signal_to_open_p50: number
    signal_to_open_p95: number
    entry_slippage_avg: number
    exit_slippage_avg: number
    fill_rate: number
  }
  
  // Recent Trades
  recent_trades: Array<{
    id: string
    symbol: string
    side: string
    exit_reason: string
    roi_final: number
    roi_tp1?: number
    roi_tp2?: number
    fees: number
    pnl_net: number
    opened_at: string
    closed_at: string
  }>
  
  // Cross Analysis with News
  news_correlation: {
    news_driven_trades_30d: number
    avg_news_impact_score: number
    news_accuracy: number
    recent_news_trades: Array<{
      symbol: string
      news_title: string
      predicted_impact: number
      actual_roi: number
      accuracy_score: number
      timestamp: string
    }>
  }
  
  timestamp: string
}

export async function GET(request: NextRequest): Promise<NextResponse> {
  try {
    if (!supabase) {
      return NextResponse.json(
        { error: 'Supabase not configured', success: false },
        { status: 503 }
      )
    }

    // Получаем данные из всех источников
    const [tradesResponse, newsResponse, alertsResponse] = await Promise.allSettled([
      supabase.from('trades_min').select('*').order('opened_at', { ascending: false }).limit(1000),
      supabase.from('news').select('*').order('timestamp', { ascending: false }).limit(100),
      supabase.from('system_alerts').select('*').order('timestamp', { ascending: false }).limit(50)
    ])

    const trades = tradesResponse.status === 'fulfilled' ? tradesResponse.value.data || [] : []
    const news = newsResponse.status === 'fulfilled' ? newsResponse.value.data || [] : []
    
    // Фильтруем данные по времени
    const now = new Date()
    const mtdStart = new Date(now.getFullYear(), now.getMonth(), 1)
    const ytdStart = new Date(now.getFullYear(), 0, 1)
    const last30Days = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
    
    const closedTrades = trades.filter(t => t.closed_at)
    const mtdTrades = closedTrades.filter(t => new Date(t.closed_at) >= mtdStart)
    const ytdTrades = closedTrades.filter(t => new Date(t.closed_at) >= ytdStart)
    const last30DaysTrades = closedTrades.filter(t => new Date(t.closed_at) >= last30Days)
    
    // Рассчитываем KPI
    const totalPnlMtd = mtdTrades.reduce((sum, t) => sum + (t.pnl || 0), 0)
    const totalPnlYtd = ytdTrades.reduce((sum, t) => sum + (t.pnl || 0), 0)
    const winningTrades = closedTrades.filter(t => (t.roi || 0) > 0)
    const winRate = closedTrades.length > 0 ? (winningTrades.length / closedTrades.length) * 100 : 0
    
    // Performance Attribution
    const symbolPerformance = last30DaysTrades.reduce((acc: any, trade) => {
      const symbol = trade.symbol || 'UNKNOWN'
      if (!acc[symbol]) {
        acc[symbol] = { pnl: 0, count: 0 }
      }
      acc[symbol].pnl += trade.pnl || 0
      acc[symbol].count += 1
      return acc
    }, {})
    
    // Exit type analysis
    const exitTypeAnalysis = last30DaysTrades.reduce((acc: any, trade) => {
      if (trade.tp1_hit) acc.tp1_pnl += trade.pnl || 0
      else if (trade.tp2_hit) acc.tp2_pnl += trade.pnl || 0
      else if (trade.sl_hit) acc.sl_pnl += trade.pnl || 0
      else acc.manual_pnl += trade.pnl || 0
      return acc
    }, { tp1_pnl: 0, tp2_pnl: 0, sl_pnl: 0, manual_pnl: 0 })
    
    // Risk metrics (упрощенные)
    const pnlArray = last30DaysTrades.map(t => t.pnl || 0)
    const avgPnl = pnlArray.length > 0 ? pnlArray.reduce((a, b) => a + b, 0) / pnlArray.length : 0
    const variance = pnlArray.length > 0 ? pnlArray.reduce((sum, pnl) => sum + Math.pow(pnl - avgPnl, 2), 0) / pnlArray.length : 0
    const volatility = Math.sqrt(variance)
    const var1d = avgPnl - 1.645 * volatility // 95% VaR
    
    // News correlation analysis
    const recentNews = news.slice(0, 20)
    const newsImpactScore = recentNews.reduce((sum, n) => sum + (n.impact_score || 0), 0) / Math.max(recentNews.length, 1)
    
    const snapshot: PortfolioSnapshot = {
      // Top KPIs
      aum: 50000, // Заглушка, нужен API Bybit
      equity: 50000 + totalPnlYtd,
      pnl_mtd: totalPnlMtd,
      pnl_ytd: totalPnlYtd,
      win_rate: winRate,
      exposure_net: 0, // Нужны активные позиции
      leverage: 1,
      long_exposure: 0,
      short_exposure: 0,
      
      // Active Positions
      active_positions: {
        count: 0, // Заглушка
        total_risk: 0,
        positions: []
      },
      
      // Risk Snapshot
      risk_snapshot: {
        var_1d: var1d,
        expected_shortfall_1d: var1d * 1.3,
        max_drawdown_mtd: Math.min(...mtdTrades.map(t => t.pnl || 0), 0),
        portfolio_volatility: volatility
      },
      
      // Performance Attribution
      performance_attribution: {
        by_strategy: [
          { strategy_id: 'telegram_signals', pnl_30d: totalPnlMtd, win_rate: winRate, trades_count: last30DaysTrades.length }
        ],
        by_symbol: Object.entries(symbolPerformance).map(([symbol, data]: [string, any]) => ({
          symbol,
          pnl_30d: data.pnl,
          trades_count: data.count
        })).sort((a: any, b: any) => b.pnl_30d - a.pnl_30d).slice(0, 10),
        by_exit_type: exitTypeAnalysis
      },
      
      // Execution Metrics (заглушки)
      execution_metrics: {
        signal_to_open_p50: 120, // секунды
        signal_to_open_p95: 300,
        entry_slippage_avg: 0.02,
        exit_slippage_avg: 0.03,
        fill_rate: 98.5
      },
      
      // Recent Trades
      recent_trades: closedTrades.slice(0, 10).map(trade => ({
        id: trade.trade_id || trade.id,
        symbol: trade.symbol || '',
        side: trade.side || '',
        exit_reason: trade.tp1_hit ? 'TP1' : trade.tp2_hit ? 'TP2' : trade.sl_hit ? 'SL' : 'Manual',
        roi_final: trade.roi || 0,
        roi_tp1: trade.tp1_hit ? trade.roi : undefined,
        roi_tp2: trade.tp2_hit ? trade.roi : undefined,
        fees: 0, // Нужно добавить в схему
        pnl_net: trade.pnl || 0,
        opened_at: trade.opened_at || '',
        closed_at: trade.closed_at || ''
      })),
      
      // Cross Analysis with News
      news_correlation: {
        news_driven_trades_30d: Math.floor(last30DaysTrades.length * 0.3), // Примерно 30% сделок связаны с новостями
        avg_news_impact_score: newsImpactScore,
        news_accuracy: 75.5, // Заглушка
        recent_news_trades: [] // Будет реализовано при связке news-trades
      },
      
      timestamp: new Date().toISOString()
    }

    return NextResponse.json({ success: true, data: snapshot })
    
  } catch (error) {
    console.error('Portfolio snapshot error:', error)
    return NextResponse.json(
      { error: 'Failed to generate portfolio snapshot', success: false },
      { status: 500 }
    )
  }
}
