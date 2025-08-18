import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

// Безопасная инициализация Supabase клиента
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || ''

let supabase: any = null
if (supabaseUrl && supabaseKey) {
  supabase = createClient(supabaseUrl, supabaseKey)
}

// Интерфейс для создания виртуальной сделки
interface CreateVirtualTradeRequest {
  // Блок 1: Идентификация
  signalId?: string
  source?: string
  sourceType?: 'telegram' | 'manual' | 'api'
  sourceName?: string
  sourceRef?: string
  originalText?: string
  signalReason?: string
  postedTs?: number

  // Блок 2: Паспорт сигнала
  symbol: string
  side: 'LONG' | 'SHORT'
  entryType?: 'zone' | 'exact'
  entryMin?: number
  entryMax?: number
  tp1?: number
  tp2?: number
  tp3?: number
  targets?: number[]
  sl?: number
  slType?: string
  sourceLeverage?: string

  // Блок 3: Параметры симуляции
  strategyId?: string
  feeRate?: number
  leverage?: number
  marginUsd?: number
  entryTimeoutSec?: number
}

// GET - получение виртуальных сделок
export async function GET(request: NextRequest) {
  try {
    if (!supabase) {
      return NextResponse.json({ 
        error: 'Supabase not configured',
        success: false 
      }, { status: 503 })
    }

    const { searchParams } = new URL(request.url)
    const status = searchParams.get('status') || 'sim_open'
    const symbol = searchParams.get('symbol')
    const limit = parseInt(searchParams.get('limit') || '50')
    const strategy = searchParams.get('strategy')

    let query = supabase
      .from('v_trades')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(limit)

    if (status !== 'all') {
      query = query.eq('status', status)
    }

    if (symbol) {
      query = query.eq('symbol', symbol.toUpperCase())
    }

    if (strategy) {
      query = query.eq('strategy_id', strategy)
    }

    const { data, error } = await query

    if (error) {
      console.error('Error fetching virtual trades:', error)
      return NextResponse.json({ 
        error: 'Failed to fetch virtual trades',
        success: false 
      }, { status: 500 })
    }

    return NextResponse.json({
      success: true,
      data: data || [],
      count: data?.length || 0,
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('Virtual trades API error:', error)
    return NextResponse.json({ 
      error: 'Internal server error',
      success: false 
    }, { status: 500 })
  }
}

// POST - создание новой виртуальной сделки
export async function POST(request: NextRequest) {
  try {
    if (!supabase) {
      return NextResponse.json({ 
        error: 'Supabase not configured',
        success: false 
      }, { status: 503 })
    }

    const body: CreateVirtualTradeRequest = await request.json()
    
    // Валидация обязательных полей
    if (!body.symbol || !body.side) {
      return NextResponse.json({ 
        error: 'Missing required fields: symbol, side',
        success: false 
      }, { status: 400 })
    }

    // Подготовка данных для вставки
    const virtualTrade = {
      // Блок 1: Идентификация
      signal_id: body.signalId,
      source: body.source,
      source_type: body.sourceType || 'manual',
      source_name: body.sourceName,
      source_ref: body.sourceRef,
      original_text: body.originalText,
      signal_reason: body.signalReason,
      posted_ts: body.postedTs || Date.now(),

      // Блок 2: Паспорт сигнала
      symbol: body.symbol.toUpperCase(),
      side: body.side,
      entry_type: body.entryType || 'zone',
      entry_min: body.entryMin,
      entry_max: body.entryMax,
      tp1: body.tp1,
      tp2: body.tp2,
      tp3: body.tp3,
      targets_json: body.targets ? JSON.stringify(body.targets) : null,
      sl: body.sl,
      sl_type: body.slType || 'hard',
      source_leverage: body.sourceLeverage,

      // Блок 3: Параметры симуляции
      strategy_id: body.strategyId || 'S_A_TP1_BE_TP2',
      strategy_version: '1',
      fee_rate: body.feeRate || 0.00055,
      leverage: body.leverage || 15,
      margin_usd: body.marginUsd || 100,
      entry_timeout_sec: body.entryTimeoutSec || 172800,

      // Устанавливаем начальный статус
      status: 'sim_open',
      tp_count_hit: 0
    }

    console.log('📊 Creating virtual trade:', {
      symbol: virtualTrade.symbol,
      side: virtualTrade.side,
      strategy: virtualTrade.strategy_id
    })

    const { data, error } = await supabase
      .from('v_trades')
      .insert([virtualTrade])
      .select()

    if (error) {
      console.error('❌ Error creating virtual trade:', error)
      return NextResponse.json({ 
        error: 'Failed to create virtual trade',
        details: error.message,
        success: false 
      }, { status: 500 })
    }

    console.log('✅ Virtual trade created successfully:', data[0]?.id)

    return NextResponse.json({
      success: true,
      data: data[0],
      message: 'Virtual trade created successfully',
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('❌ Virtual trades POST API error:', error)
    return NextResponse.json({ 
      error: 'Internal server error',
      details: error instanceof Error ? error.message : 'Unknown error',
      success: false 
    }, { status: 500 })
  }
}

// PUT - обновление виртуальной сделки (для симулятора)
export async function PUT(request: NextRequest) {
  try {
    if (!supabase) {
      return NextResponse.json({ 
        error: 'Supabase not configured',
        success: false 
      }, { status: 503 })
    }

    const body = await request.json()
    const { id, ...updateData } = body

    if (!id) {
      return NextResponse.json({ 
        error: 'Missing trade ID',
        success: false 
      }, { status: 400 })
    }

    const { data, error } = await supabase
      .from('v_trades')
      .update(updateData)
      .eq('id', id)
      .select()

    if (error) {
      console.error('Error updating virtual trade:', error)
      return NextResponse.json({ 
        error: 'Failed to update virtual trade',
        details: error.message,
        success: false 
      }, { status: 500 })
    }

    return NextResponse.json({
      success: true,
      data: data[0],
      message: 'Virtual trade updated successfully',
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('Virtual trades PUT API error:', error)
    return NextResponse.json({ 
      error: 'Internal server error',
      success: false 
    }, { status: 500 })
  }
}
