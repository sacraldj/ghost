import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

export const runtime = 'nodejs'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL || '',
  process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''
)

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ traderId: string }> }
) {
  try {
    const { traderId } = await params

    // Получаем информацию о трейдере
    const { data: trader, error: traderError } = await supabase
      .from('trader_registry')
      .select('*')
      .eq('trader_id', traderId)
      .single()

    if (traderError) {
      console.error('Error fetching trader:', traderError)
    }

    // Получаем все сигналы трейдера
    const { data: signals, error: signalsError } = await supabase
      .from('signals_parsed')
      .select('*')
      .eq('trader_id', traderId)
      .order('id', { ascending: false })

    if (signalsError) {
      console.error('Error fetching signals:', signalsError)
    }

    // Если нет данных, создаем моковые для демонстрации
    const mockSignals = [
      {
        id: '1',
        symbol: 'BTCUSDT',
        side: 'BUY',
        entry_price: 43250.0,
        targets: [44000, 45000, 46000],
        stop_loss: 42000,
        pnl: 156.75,
        roi: 3.6,
        status: 'tp1',
        created_at: '2025-08-15T10:30:00Z',
        closed_at: '2025-08-15T14:20:00Z',
        duration: '3h 50m'
      },
      {
        id: '2',
        symbol: 'ETHUSDT',
        side: 'SELL',
        entry_price: 2650.0,
        targets: [2600, 2550, 2500],
        stop_loss: 2700,
        pnl: -89.32,
        roi: -3.4,
        status: 'sl',
        created_at: '2025-08-15T08:15:00Z',
        closed_at: '2025-08-15T11:45:00Z',
        duration: '3h 30m'
      },
      {
        id: '3',
        symbol: 'ADAUSDT',
        side: 'BUY',
        entry_price: 0.385,
        targets: [0.395, 0.405, 0.420],
        stop_loss: 0.375,
        pnl: 234.56,
        roi: 6.1,
        status: 'tp2',
        created_at: '2025-08-14T16:20:00Z',
        closed_at: '2025-08-15T09:10:00Z',
        duration: '16h 50m'
      },
      {
        id: '4',
        symbol: 'SOLUSDT',
        side: 'BUY',
        entry_price: 145.20,
        targets: [150, 155, 160],
        stop_loss: 140,
        pnl: 78.90,
        roi: 5.4,
        status: 'active',
        created_at: '2025-08-15T12:00:00Z',
        duration: '2h 15m'
      },
      {
        id: '5',
        symbol: 'XRPUSDT',
        side: 'SELL',
        entry_price: 0.52,
        targets: [0.51, 0.50, 0.49],
        stop_loss: 0.535,
        pnl: 45.67,
        roi: 8.8,
        status: 'tp1',
        created_at: '2025-08-14T20:30:00Z',
        closed_at: '2025-08-15T06:45:00Z',
        duration: '10h 15m'
      }
    ]

    // Рассчитываем статистику по монетам
    const pnlBySymbol: Record<string, any> = {}
    
    mockSignals.forEach(signal => {
      if (!pnlBySymbol[signal.symbol]) {
        pnlBySymbol[signal.symbol] = {
          symbol: signal.symbol,
          trades: 0,
          pnl: 0,
          wins: 0
        }
      }
      
      pnlBySymbol[signal.symbol].trades += 1
      pnlBySymbol[signal.symbol].pnl += signal.pnl
      if (signal.pnl > 0) {
        pnlBySymbol[signal.symbol].wins += 1
      }
    })

    // Добавляем winrate для каждой монеты
    Object.keys(pnlBySymbol).forEach(symbol => {
      const data = pnlBySymbol[symbol]
      data.winrate = (data.wins / data.trades) * 100
    })

    // Общая статистика
    const totalPnL = mockSignals.reduce((sum, s) => sum + s.pnl, 0)
    const successfulSignals = mockSignals.filter(s => s.pnl > 0).length
    const winrate = (successfulSignals / mockSignals.length) * 100
    const avgROI = mockSignals.reduce((sum, s) => sum + s.roi, 0) / mockSignals.length

    const result = {
      trader_id: traderId,
      name: trader?.name || traderId,
      is_trading: trader?.is_trading || false,
      total_signals: mockSignals.length,
      total_pnl: totalPnL,
      winrate: winrate,
      avg_roi: avgROI,
      signals: mockSignals,
      pnl_by_symbol: pnlBySymbol
    }

    return NextResponse.json(result, {
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache'
      }
    })

  } catch (error) {
    console.error('Error in trader details:', error)
    return NextResponse.json(
      { 
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
