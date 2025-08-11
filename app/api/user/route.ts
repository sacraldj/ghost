import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

export async function GET(request: NextRequest) {
  try {
    // Получаем сессию пользователя
    const { data: { session } } = await supabase.auth.getSession()
    
    if (!session) {
      return NextResponse.json({ 
        user: null,
        trades: [],
        portfolio: {
          totalBalance: 0,
          totalPnL: 0,
          totalROI: 0,
          winRate: 0,
          totalTrades: 0
        }
      })
    }

    // Получаем данные пользователя
    const { data: userProfile } = await supabase
      .from('profiles')
      .select('*')
      .eq('id', session.user.id)
      .single()

    // Получаем активные сделки (пример данных)
    const trades = [
      {
        id: 1,
        symbol: 'BTC/USDT',
        type: 'long',
        entryPrice: 42150,
        currentPrice: 43250,
        size: 0.05,
        leverage: 20,
        pnl: 450.25,
        pnlPercent: 3.2,
        openedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        takeProfit: 44500,
        stopLoss: 41200
      },
      {
        id: 2,
        symbol: 'ETH/USDT',
        type: 'long',
        entryPrice: 2680,
        currentPrice: 2630,
        size: 0.8,
        leverage: 15,
        pnl: -120.50,
        pnlPercent: -1.8,
        openedAt: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
        takeProfit: 2750,
        stopLoss: 2580
      }
    ]

    // Статистика портфолио
    const portfolio = {
      totalBalance: 12450.75,
      totalPnL: 2340.50,
      totalROI: 11.2,
      winRate: 68.5,
      totalTrades: 35
    }

    return NextResponse.json({
      user: {
        id: session.user.id,
        email: session.user.email,
        ...userProfile
      },
      trades,
      portfolio
    })

  } catch (error) {
    console.error('API error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
