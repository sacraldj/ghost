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
    const strategy = searchParams.get('strategy') || 'tp2_sl_be'

    // Определяем временной период
    const periodDays = period === '7d' ? 7 : period === '30d' ? 30 : period === '60d' ? 60 : period === '90d' ? 90 : period === '180d' ? 180 : 30
    const startDate = new Date()
    startDate.setDate(startDate.getDate() - periodDays)

    // Базовый фильтр для трейдеров
    let traderFilter: { is_active?: boolean; is_trading?: boolean } = { is_active: true }
    if (tradingOnly) {
      traderFilter = { ...traderFilter, is_trading: true }
    }

    // Получаем ТОЛЬКО реальных трейдеров из базы
    const { data: traders, error: tradersError } = await supabase
      .from('trader_registry')
      .select('*')
      .match(traderFilter)
      .order('trader_id')

    if (tradersError) {
      console.error('Error fetching traders:', tradersError)
      return NextResponse.json({
        traders: [],
        total: 0,
        strategy: strategy,
        period: period,
        error: 'Database error'
      })
    }

    // Если нет трейдеров в базе, возвращаем пустой список (только реальные данные!)
    if (!traders || traders.length === 0) {
      return NextResponse.json({
        traders: [],
        total: 0,
        strategy: strategy,
        period: period,
        message: "No real trader data available yet. System is collecting signals..."
      })
    }

    // Для каждого трейдера рассчитываем РЕАЛЬНУЮ статистику
    const tradersWithStats = await Promise.all(
      traders.map(async (trader) => {
        // Получаем РЕАЛЬНЫЕ сигналы трейдера за период
        const { data: signals, error: signalsError } = await supabase
          .from('signals_parsed')
          .select('*')
          .eq('trader_id', trader.trader_id)
          .gte('posted_at', startDate.toISOString())
          .order('posted_at', { ascending: false })

        if (signalsError) {
          console.error(`Error fetching signals for trader ${trader.trader_id}:`, signalsError)
        }

        const traderSignals = signals || []
        
        // Получаем РЕАЛЬНЫЕ сырые сигналы для подсчета общего количества
        const { data: rawSignals, error: rawSignalsError } = await supabase
          .from('signals_raw')
          .select('signal_id')
          .eq('trader_id', trader.trader_id)
          .gte('posted_at', startDate.toISOString())

        if (rawSignalsError) {
          console.error(`Error fetching raw signals for trader ${trader.trader_id}:`, rawSignalsError)
        }

        const totalRawSignals = rawSignals ? rawSignals.length : 0
        const validSignals = traderSignals.filter(s => s.is_valid).length
        
        // Подсчет реальных результатов
        const tpSignals = traderSignals.filter(s => s.tp1 || s.tp2)
        const slSignals = traderSignals.filter(s => s.sl)
        
        const totalTrades = validSignals
        const winrate = totalTrades > 0 ? Math.round((tpSignals.length / totalTrades) * 100 * 10) / 10 : 0
        const tp1Rate = totalTrades > 0 ? Math.round((tpSignals.length / totalTrades) * 100) : 0
        const slRate = totalTrades > 0 ? Math.round((slSignals.length / totalTrades) * 100) : 0
        
        // Последний сигнал
        const lastSignalDate = traderSignals.length > 0 ? 
          new Date(traderSignals[0].posted_at).toISOString().split('T')[0] : null
        
        return {
          trader_id: trader.trader_id,
          name: trader.name || trader.trader_id,
          trades: totalTrades,
          winrate: winrate,
          roi_avg: 0, // Пока нет данных по ROI
          roi_year: 0,
          pnl_usdt: 0, // Пока нет данных по PnL
          max_dd: 0,
          tp1_rate: tp1Rate,
          tp2_rate: 0, // Пока нет разделения TP1/TP2
          sl_rate: slRate,
          avg_duration: "N/A",
          trust: Math.min(100, Math.max(0, Math.round((validSignals / Math.max(1, totalRawSignals)) * 100))),
          trend: 'neutral' as 'up' | 'down' | 'neutral',
          status: trader.is_active ? 'active' : 'inactive' as 'active' | 'inactive' | 'stopped',
          is_trading: trader.is_trading || false,
          last_signal: lastSignalDate,
          start_date: trader.created_at ? new Date(trader.created_at).toISOString().split('T')[0] : "2025-08-15",
          capital: 10000 // Фиксированный капитал для симуляции
        }
      })
    )

    // Сортируем по количеству валидных сигналов
    const sortedTraders = tradersWithStats.sort((a, b) => b.trades - a.trades)

    return NextResponse.json({
      traders: sortedTraders,
      total: sortedTraders.length,
      strategy: strategy,
      period: period,
      data_source: "real"
    })

  } catch (error) {
    console.error('Error in traders analytics list:', error)
    return NextResponse.json(
      { traders: [], total: 0, error: 'Internal server error' },
      { status: 500 }
    )
  }
}