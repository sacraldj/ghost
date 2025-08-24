import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SECRET_KEY!
)

export async function GET() {
  try {
    // Получаем все записи, сортируем по created_at (более надежно чем posted_ts)
    const { data, error } = await supabase
      .from('v_trades')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(50) // Ограничиваем до 50 последних записей для производительности

    if (error) {
      console.error('Supabase error:', error)
      return NextResponse.json({ error: error.message }, { status: 500 })
    }

    // Дополнительно сортируем на клиенте для гарантии
    const sortedData = data?.sort((a, b) => {
      const dateA = new Date(a.created_at || 0).getTime()
      const dateB = new Date(b.created_at || 0).getTime()
      return dateB - dateA // Новые записи сначала
    }) || []

    console.log(`📊 Test Table API: Found ${sortedData.length} records, latest: ${sortedData[0]?.symbol} ${sortedData[0]?.side} (${sortedData[0]?.created_at})`)

    return NextResponse.json({ data: sortedData })
  } catch (error) {
    console.error('API error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    // Генерируем уникальный ID
    const uniqueId = `test_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    
    // Подготавливаем данные для вставки
    const insertData = {
      id: uniqueId,
      signal_id: body.signal_id || `sig_${Date.now()}`,
      source: body.source || 'test',
      source_type: body.source_type || 'manual',
      source_name: body.source_name || 'Test Entry',
      source_ref: body.source_ref || '',
      original_text: body.original_text || '',
      signal_reason: body.signal_reason || 'Manual test entry',
      posted_ts: body.posted_ts || Math.floor(Date.now() / 1000),
      symbol: body.symbol || 'BTCUSDT',
      side: body.side || 'LONG',
      entry_type: body.entry_type || 'zone',
      entry_min: body.entry_min || 0,
      entry_max: body.entry_max || 0,
      tp1: body.tp1 || 0,
      tp2: body.tp2 || 0,
      tp3: body.tp3 || 0,
      targets_json: body.targets_json || '[]',
      sl: body.sl || 0,
      sl_type: body.sl_type || 'hard',
      source_leverage: body.source_leverage || '15x',
      strategy_id: body.strategy_id || 'S_A_TP1_BE_TP2',
      strategy_version: body.strategy_version || '1',
      fee_rate: body.fee_rate || 0.0005,
      leverage: body.leverage || 15,
      margin_usd: body.margin_usd || 100,
      entry_timeout_sec: body.entry_timeout_sec || 172800,
      was_fillable: body.was_fillable || 1
    }

    const { data, error } = await supabase
      .from('v_trades')
      .insert([insertData])
      .select()

    if (error) {
      console.error('Supabase insert error:', error)
      return NextResponse.json({ error: error.message }, { status: 500 })
    }

    return NextResponse.json({ data: data[0], message: 'Record saved successfully' })
  } catch (error) {
    console.error('API POST error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
