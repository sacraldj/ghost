import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL || '',
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''
)

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const period = searchParams.get('period') || '180d'
    const trader = searchParams.get('trader') || 'all'
    const tradingOnly = searchParams.get('trading_only') === 'true'

    // Определяем временной период
    const periodDays = period === '7d' ? 7 : period === '30d' ? 30 : period === '60d' ? 60 : period === '90d' ? 90 : period === '180d' ? 180 : 30
    const startDate = new Date()
    startDate.setDate(startDate.getDate() - periodDays)

    // Базовый фильтр для трейдеров
    let traderFilter = {}
    if (tradingOnly) {
      traderFilter = { is_active: true, is_trading: true }
    } else {
      traderFilter = { is_active: true }
    }

    // Получаем данные трейдеров
    const { data: traders, error: tradersError } = await supabase
      .from('trader_registry')
      .select('*')
      .match(traderFilter)

    if (tradersError) {
      console.error('Error fetching traders:', tradersError)
    }

    // Получаем сигналы для расчета статистики  
    let signalsQuery = supabase
      .from('signals_parsed')
      .select('*')

    if (trader !== 'all') {
      signalsQuery = signalsQuery.eq('trader_id', trader)
    }

    const { data: signals, error: signalsError } = await signalsQuery

    if (signalsError) {
      console.error('Error fetching signals:', signalsError)
    }

    // Получаем реальные торговые данные из таблицы trades
    const { data: trades, error: tradesError } = await supabase
      .from('trades')
      .select('*')
      .gte('opened_at', startDate.toISOString())

    if (tradesError) {
      console.error('Error fetching trades:', tradesError)
    }

    // Получаем данные за сегодня
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const { data: todayTrades, error: todayError } = await supabase
      .from('trades')
      .select('*')
      .gte('opened_at', today.toISOString())

    // Получаем данные за последние 7 дней
    const sevenDaysAgo = new Date()
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7)
    const { data: weekTrades, error: weekError } = await supabase
      .from('trades')
      .select('*')
      .gte('opened_at', sevenDaysAgo.toISOString())

    // Рассчитываем реальную статистику
    const totalSignals = signals?.length || 0
    const totalTrades = trades?.length || 0
    
    // Общий P&L из реальных торговых данных
    const totalPnL = trades?.reduce((sum, t) => sum + (parseFloat(t.pnl_net?.toString() || '0')), 0) || 0
    
    // Торговый объем (сумма всех margin_used)
    const tradingVolume = trades?.reduce((sum, t) => sum + (parseFloat(t.margin_used?.toString() || '0')), 0) || 0

    // P&L за сегодня
    const pnlToday = todayTrades?.reduce((sum, t) => sum + (parseFloat(t.pnl_net?.toString() || '0')), 0) || 0
    
    // P&L за 7 дней
    const pnl7d = weekTrades?.reduce((sum, t) => sum + (parseFloat(t.pnl_net?.toString() || '0')), 0) || 0

    // Разделение по long/short из реальных данных
    const longTrades = trades?.filter(t => t.side === 'LONG') || []
    const shortTrades = trades?.filter(t => t.side === 'SHORT') || []
    const pnlLong = longTrades.reduce((sum, t) => sum + (parseFloat(t.pnl_net?.toString() || '0')), 0)
    const pnlShort = shortTrades.reduce((sum, t) => sum + (parseFloat(t.pnl_net?.toString() || '0')), 0)

    // Подсчет закрытых позиций
    const closedTrades = trades?.filter(t => t.status === 'closed' || t.closed_at) || []
    const successfulTrades = closedTrades.filter(t => parseFloat(t.pnl_net?.toString() || '0') > 0)
    const successRate = closedTrades.length > 0 ? (successfulTrades.length / closedTrades.length) * 100 : 0

    const summary = {
      total_pnl: Number(totalPnL.toFixed(2)),
      trading_volume: Number(tradingVolume.toFixed(2)),
      pnl_today: Number(pnlToday.toFixed(2)),
      pnl_7d: Number(pnl7d.toFixed(2)),
      closed_orders: closedTrades.length,
      closed_positions: closedTrades.length,
      success_rate: Number(successRate.toFixed(1)),
      pnl_long: Number(pnlLong.toFixed(2)),
      pnl_short: Number(pnlShort.toFixed(2)),
      total_trades: totalTrades,
      total_signals: totalSignals
    }

    return NextResponse.json(summary)

  } catch (error) {
    console.error('Error in traders analytics summary:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
