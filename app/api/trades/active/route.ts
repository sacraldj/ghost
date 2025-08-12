import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

export async function GET(request: NextRequest) {
  try {
    // Fetch active trades from Supabase
    const { data: trades, error } = await supabase
      .from('trades')
      .select(`
        id,
        trade_id,
        symbol,
        side,
        real_entry_price,
        position_qty,
        margin_used,
        leverage,
        tp1_price,
        tp2_price,
        sl_price,
        opened_at,
        status
      `)
      .eq('status', 'open')
      .order('opened_at', { ascending: false })

    if (error) {
      console.error('Supabase error:', error)
      return NextResponse.json({ error: 'Database error' }, { status: 500 })
    }

    // Transform data for frontend
    const activeTrades = trades?.map(trade => ({
      id: trade.id,
      trade_id: trade.trade_id,
      symbol: trade.symbol,
      side: trade.side,
      real_entry_price: parseFloat(trade.real_entry_price || '0'),
      position_qty: parseFloat(trade.position_qty || '0'),
      margin_used: parseFloat(trade.margin_used || '0'),
      leverage: parseFloat(trade.leverage || '1'),
      tp1_price: trade.tp1_price ? parseFloat(trade.tp1_price) : null,
      tp2_price: trade.tp2_price ? parseFloat(trade.tp2_price) : null,
      sl_price: trade.sl_price ? parseFloat(trade.sl_price) : null,
      opened_at: trade.opened_at
    })) || []

    return NextResponse.json(activeTrades)
  } catch (error) {
    console.error('Error fetching active trades:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
