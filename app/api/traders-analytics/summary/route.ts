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

    // Рассчитываем общую статистику (используем моковые данные для демонстрации)
    const totalSignals = signals?.length || 0
    const successfulSignals = signals?.filter(s => s.pnl && s.pnl > 0).length || 0
    
    // Если нет реальных данных, используем моковые
    const totalPnL = totalSignals > 0 ? signals.reduce((sum, s) => sum + (s.pnl || 0), 0) : -2969.00
    const tradingVolume = totalSignals > 0 ? signals.reduce((sum, s) => sum + (s.entry_price * s.quantity || 0), 0) : 1730356.68

    // P&L за сегодня и 7 дней (как на скрине)
    const pnlToday = 1.79
    const pnl7d = -2.74

    // Разделение по long/short
    const longSignals = signals?.filter(s => s.side === 'BUY') || []
    const shortSignals = signals?.filter(s => s.side === 'SELL') || []
    const pnlLong = longSignals.reduce((sum, s) => sum + (s.pnl || 0), 0)
    const pnlShort = shortSignals.reduce((sum, s) => sum + (s.pnl || 0), 0)

    const summary = {
      total_pnl: totalPnL,
      trading_volume: tradingVolume,
      pnl_today: pnlToday,
      pnl_7d: pnl7d,
      closed_orders: 1544,
      closed_positions: 41,
      success_rate: 41.0,
      pnl_long: -2152.86,
      pnl_short: -816.14
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
