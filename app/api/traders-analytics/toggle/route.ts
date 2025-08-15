import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL || '',
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''
)

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { trader_id, action } = body

    if (!trader_id || !action) {
      return NextResponse.json(
        { error: 'trader_id and action are required' },
        { status: 400 }
      )
    }

    // Определяем новое состояние
    const isTrading = action === 'enable'

    // Обновляем статус трейдера в базе
    const { data, error } = await supabase
      .from('trader_registry')
      .update({ 
        is_trading: isTrading,
        updated_at: new Date().toISOString()
      })
      .eq('trader_id', trader_id)
      .select()

    if (error) {
      console.error('Error updating trader status:', error)
      return NextResponse.json(
        { error: 'Failed to update trader status' },
        { status: 500 }
      )
    }

    return NextResponse.json({
      success: true,
      trader_id,
      action,
      is_trading: isTrading,
      updated: data
    })

  } catch (error) {
    console.error('Error in traders toggle:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
