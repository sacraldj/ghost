import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

// Force Node.js runtime
export const runtime = 'nodejs'

// Безопасная инициализация Supabase клиента с fallback значениями
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://placeholder.supabase.co'
const supabaseKey = process.env.SUPABASE_SECRET_KEY || process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'placeholder-key'

// Создаем клиент только если переменные заданы правильно
let supabase: any = null
if (supabaseUrl !== 'https://placeholder.supabase.co' && supabaseKey !== 'placeholder-key') {
  supabase = createClient(supabaseUrl, supabaseKey)
}

export async function GET(request: NextRequest) {
  try {
    // Проверяем, что Supabase инициализирован
    if (!supabase) {
      return NextResponse.json({ 
        error: 'Supabase not configured',
        message: 'Environment variables not set',
        trades: []
      }, { status: 503 })
    }

    const { searchParams } = new URL(request.url)
    const limit = parseInt(searchParams.get('limit') || '50')
    const days = parseInt(searchParams.get('days') || '7')
    const status = searchParams.get('status') // 'open', 'closed', 'all'
    const symbol = searchParams.get('symbol')
    const userId = searchParams.get('user_id')

    let query = supabase
      .from('trades')
      .select('*')
      .gte('created_at', new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString())
      .order('created_at', { ascending: false })
      .limit(limit)

    // Фильтр по статусу
    if (status && status !== 'all') {
      query = query.eq('status', status)
    }

    // Фильтр по символу
    if (symbol) {
      query = query.eq('symbol', symbol.toUpperCase())
    }

    // Фильтр по пользователю
    if (userId) {
      query = query.eq('user_id', userId)
    }

    const { data, error } = await query

    if (error) {
      console.error('Supabase error:', error)
      return NextResponse.json({ error: 'Database error' }, { status: 500 })
    }

    // Преобразование данных
    const trades = data?.map(trade => ({
      id: trade.id,
      userId: trade.user_id,
      symbol: trade.symbol,
      side: trade.side,
      status: trade.status,
      entryPrice: trade.entry_price,
      exitPrice: trade.exit_price,
      quantity: trade.quantity,
      leverage: trade.leverage,
      marginUsed: trade.margin_used,
      pnl: trade.pnl,
      roi: trade.roi,
      entryTime: trade.entry_time,
      exitTime: trade.exit_time,
      createdAt: trade.created_at,
      updatedAt: trade.updated_at,
      // Новые поля из v2.0
      roiSource: trade.roi_source,
      pnlSource: trade.pnl_source,
      exitDetail: trade.exit_detail,
      pnlTp1Net: trade.pnl_tp1_net,
      pnlRestNet: trade.pnl_rest_net,
      roiTp1Real: trade.roi_tp1_real,
      roiRestReal: trade.roi_rest_real,
      roiFinalReal: trade.roi_final_real,
      bybitFeeOpen: trade.bybit_fee_open,
      bybitFeeClose: trade.bybit_fee_close,
      bybitFeeTotal: trade.bybit_fee_total
    })) || []

    // Статистика
    const stats = {
      total: trades.length,
      open: trades.filter(t => t.status === 'open').length,
      closed: trades.filter(t => t.status === 'closed').length,
      profitable: trades.filter(t => t.pnl && t.pnl > 0).length,
      totalPnl: trades.reduce((sum, t) => sum + (t.pnl || 0), 0),
      avgRoi: trades.length > 0 ? trades.reduce((sum, t) => sum + (t.roi || 0), 0) / trades.length : 0
    }

    return NextResponse.json({
      trades,
      stats,
      count: trades.length,
      timestamp: new Date().toISOString(),
      source: 'supabase',
      message: trades.length > 0 
        ? `Торговые сделки из Supabase (${days} дней)` 
        : 'Сделок нет'
    })

  } catch (error) {
    console.error('API error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    // Валидация обязательных полей
    const requiredFields = ['symbol', 'side', 'entry_price', 'quantity', 'leverage', 'margin_used']
    for (const field of requiredFields) {
      if (!body[field]) {
        return NextResponse.json({ error: `Missing required field: ${field}` }, { status: 400 })
      }
    }

    // Создание новой сделки
    const { data, error } = await supabase
      .from('trades')
      .insert([{
        user_id: body.user_id,
        symbol: body.symbol.toUpperCase(),
        side: body.side.toUpperCase(),
        status: 'open',
        entry_price: body.entry_price,
        quantity: body.quantity,
        leverage: body.leverage,
        margin_used: body.margin_used,
        entry_time: new Date().toISOString(),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }])
      .select()

    if (error) {
      console.error('Supabase error:', error)
      return NextResponse.json({ error: 'Database error' }, { status: 500 })
    }

    return NextResponse.json({
      success: true,
      trade: data[0],
      message: 'Торговая сделка создана'
    })

  } catch (error) {
    console.error('API error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
