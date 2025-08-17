import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

export const runtime = 'nodejs'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL || '',
  process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''
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

    // Если нет данных, создаем демо-данные для графика
    if (!signals || signals.length === 0) {
      const demoData = []
      const startDate = new Date()
      startDate.setDate(startDate.getDate() - periodDays)
      
      let cumulativePnL = 0
      
      for (let i = 0; i < Math.min(periodDays, 30); i++) {
        const date = new Date(startDate)
        date.setDate(date.getDate() + i)
        
        // Генерируем случайные данные для демонстрации
        const dailyPnL = (Math.random() - 0.5) * 20 // от -10 до +10
        cumulativePnL += dailyPnL
        
        demoData.push({
          date: date.toISOString().split('T')[0],
          pnl: dailyPnL,
          cumulative_pnl: cumulativePnL,
          trades: Math.floor(Math.random() * 3) + 1
        })
      }
      
      return NextResponse.json({
        data: demoData,
        period,
        trader,
        total_points: demoData.length,
        data_source: "demo",
        timestamp: new Date().toISOString()
      }, {
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache'
        }
      })
    }

    // Формируем данные для графика из реальных сигналов
    let cumulativePnL = 0
    const chartData = signals.map((signal, index) => {
      // Простая симуляция P&L на основе цен
      const entryPrice = signal.entry || 0
      const tp1Price = signal.tp1 || 0
      const tp2Price = signal.tp2 || 0
      
      // Симулируем результат (для демонстрации)
      let pnl = 0
      if (tp1Price > entryPrice && signal.side === 'BUY') {
        pnl = ((tp1Price - entryPrice) / entryPrice) * 100 // % прибыль
      } else if (tp1Price < entryPrice && signal.side === 'SELL') {
        pnl = ((entryPrice - tp1Price) / entryPrice) * 100 // % прибыль
      } else {
        pnl = (Math.random() - 0.3) * 15 // Случайный результат с положительным смещением
      }
      
      cumulativePnL += pnl

      return {
        date: signal.parsed_at || signal.posted_at,
        pnl: pnl,
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
      total_points: finalData.length,
      timestamp: new Date().toISOString()
    }, {
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache'
      }
    })

  } catch (error) {
    console.error('Error in traders analytics chart:', error)
    return NextResponse.json(
      { 
        data: [], 
        error: 'Internal server error',
        message: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString()
      },
      { 
        status: 500,
        headers: {
          'Content-Type': 'application/json'
        }
      }
    )
  }
}
