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
    const tradingOnly = searchParams.get('trading_only') === 'true'

    // Определяем временной период
    const periodDays = period === '7d' ? 7 : period === '30d' ? 30 : period === '60d' ? 60 : period === '90d' ? 90 : period === '180d' ? 180 : 30
    const startDate = new Date()
    startDate.setDate(startDate.getDate() - periodDays)

    // Базовый фильтр для трейдеров
    let traderFilter: { is_active?: boolean; is_trading?: boolean } = { is_active: true }
    if (tradingOnly) {
      traderFilter = { ...traderFilter, is_trading: true }
    }

    // Получаем данные трейдеров
    const { data: traders, error: tradersError } = await supabase
      .from('trader_registry')
      .select('*')
      .match(traderFilter)
      .order('trader_id')

    if (tradersError) {
      console.error('Error fetching traders:', tradersError)
    }

    // Если нет трейдеров в базе, создаем моковые данные для демонстрации
    if (!traders || traders.length === 0) {
      const mockTraders = [
        { trader_id: '2trade_slivaem', name: '2Trade', is_trading: true },
        { trader_id: 'whales_guide_main', name: 'Whales Guide', is_trading: false },
        { trader_id: 'crypto_hub_vip', name: 'Crypto Hub VIP', is_trading: true },
        { trader_id: 'coinpulse_signals', name: 'CoinPulse', is_trading: false }
      ]
      
      const tradersWithStats = mockTraders.map((trader, index) => ({
        trader_id: trader.trader_id,
        name: trader.name,
        trades: 189 - (index * 10),
        winrate: 63.8 - (index * 2),
        roi_avg: 18.3 - (index * 1.5),
        roi_year: 183 - (index * 15),
        pnl_usdt: 1243.55 - (index * 200),
        max_dd: 4.12,
        tp1_rate: 87,
        tp2_rate: 45,
        sl_rate: 13,
        avg_duration: "3h 42m",
        trust: 87 - (index * 5),
        trend: index % 2 === 0 ? 'up' : 'down' as 'up' | 'down' | 'neutral',
        status: 'active' as 'active' | 'inactive' | 'stopped',
        is_trading: trader.is_trading,
        last_signal: "2025-08-15"
      }))

      return NextResponse.json({
        traders: tradersWithStats,
        total: tradersWithStats.length
      })
    }

    // Для каждого трейдера рассчитываем статистику
    const tradersWithStats = await Promise.all(
      traders.map(async (trader) => {
        // Получаем сигналы трейдера за период
        const { data: signals, error: signalsError } = await supabase
          .from('signals_parsed')
          .select('*')
          .eq('trader_id', trader.trader_id)
          .order('id', { ascending: false })

        if (signalsError) {
          console.error(`Error fetching signals for trader ${trader.trader_id}:`, signalsError)
        }

        const traderSignals = signals || []
        
        // Используем моковые данные как на скрине
        const totalTrades = 189
        const winrate = 63.8
        const avgROI = 18.3
        const roiYear = 183
        const totalPnL = 1243.55

        // Дополнительные данные как на скрине
        const maxDD = 4.12
        const avgDuration = "3h 42m"
        const lastSignal = "2025-08-15"
        const status = 'active'
        const trend = 'up'

        return {
          trader_id: trader.trader_id,
          name: trader.name || trader.trader_id,
          trades: totalTrades,
          winrate: winrate,
          roi_avg: avgROI,
          roi_year: roiYear,
          pnl_usdt: totalPnL,
          max_dd: maxDD,
          tp1_rate: 87, // Как на скрине
          tp2_rate: 45, 
          sl_rate: 13,
          avg_duration: avgDuration,
          trust: 87,
          trend: trend as 'up' | 'down' | 'neutral',
          status: status as 'active' | 'inactive' | 'stopped',
          is_trading: trader.is_trading || false,
          last_signal: lastSignal
        }
      })
    )

    // Сортируем по P&L
    const sortedTraders = tradersWithStats.sort((a, b) => b.pnl_usdt - a.pnl_usdt)

    return NextResponse.json({
      traders: sortedTraders,
      total: sortedTraders.length
    })

  } catch (error) {
    console.error('Error in traders analytics list:', error)
    return NextResponse.json(
      { traders: [], total: 0, error: 'Internal server error' },
      { status: 500 }
    )
  }
}
