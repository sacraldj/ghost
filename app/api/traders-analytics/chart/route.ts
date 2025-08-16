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

    // Определяем временной период
    const periodDays = period === '7d' ? 7 : period === '30d' ? 30 : period === '60d' ? 60 : period === '90d' ? 90 : period === '180d' ? 180 : 30
    const startDate = new Date()
    startDate.setDate(startDate.getDate() - periodDays)

    // Получаем сигналы для графика
    let signalsQuery = supabase
      .from('signals_parsed')
      .select('*')
      .order('parsed_at', { ascending: true })

    if (trader !== 'all') {
      signalsQuery = signalsQuery.eq('trader_id', trader)
    }

    const { data: signals, error: signalsError } = await signalsQuery

    if (signalsError) {
      console.error('Error fetching signals for chart:', signalsError)
      return NextResponse.json({ data: [] })
    }

    // Формируем данные для графика с нормализацией на $100 маржи
    let cumulativePnL = 0
    const chartData = (signals || []).map((signal) => {
      // Нормализация P&L на $100 маржи
      const marginUsed = (signal.entry_price * signal.quantity) / (signal.leverage || 1)
      const scale = marginUsed > 0 ? 100 / marginUsed : 1
      const normalizedPnL = (signal.pnl || 0) * scale
      
      cumulativePnL += normalizedPnL

      return {
        date: signal.parsed_at || signal.posted_at,
        pnl: normalizedPnL,
        cumulative_pnl: cumulativePnL,
        trader_id: signal.trader_id
      }
    })

    // Группируем по дням для более читаемого графика
    const dailyData = chartData.reduce((acc, point) => {
      const date = new Date(point.date).toISOString().split('T')[0]
      
      if (!acc[date]) {
        acc[date] = {
          date,
          pnl: 0,
          cumulative_pnl: point.cumulative_pnl,
          trades: 0
        }
      }
      
      acc[date].pnl += point.pnl
      acc[date].trades += 1
      acc[date].cumulative_pnl = point.cumulative_pnl // Берем последнее значение за день
      
      return acc
    }, {} as Record<string, any>)

    const finalData = Object.values(dailyData).sort((a: any, b: any) => 
      new Date(a.date).getTime() - new Date(b.date).getTime()
    )

    return NextResponse.json({
      data: finalData,
      period,
      trader,
      total_points: finalData.length
    })

  } catch (error) {
    console.error('Error in traders analytics chart:', error)
    return NextResponse.json(
      { data: [], error: 'Internal server error' },
      { status: 500 }
    )
  }
}
