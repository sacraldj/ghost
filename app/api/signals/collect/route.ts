/**
 * GHOST Signals Collection API
 * Endpoint для сбора сигналов от Telegram Listener
 */

import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

interface RawSignalData {
  trader_id: string
  source_msg_id?: string
  posted_at: string
  text: string
  meta?: Record<string, any>
}

interface ParsedSignalData {
  signal_id: string
  trader_id: string
  raw_id?: number
  posted_at: string
  symbol: string
  side: string
  entry_type?: string
  entry?: number
  range_low?: number
  range_high?: number
  tp1?: number
  tp2?: number
  tp3?: number
  tp4?: number
  sl?: number
  leverage_hint?: number
  timeframe_hint?: string
  confidence?: number
  parsed_at: string
  parse_version: string
  checksum: string
  is_valid: boolean
}

// POST - Сохранение нового сигнала
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { type, data } = body

    if (type === 'raw_signal') {
      return await saveRawSignal(data)
    } else if (type === 'parsed_signal') {
      return await saveParsedSignal(data)
    } else {
      return NextResponse.json(
        { error: 'Invalid signal type. Use "raw_signal" or "parsed_signal"' },
        { status: 400 }
      )
    }

  } catch (error) {
    console.error('Error in signals collect API:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

// GET - Получение статистики сбора сигналов
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const trader_id = searchParams.get('trader_id')
    const hours = parseInt(searchParams.get('hours') || '24')

    const timeFrom = new Date()
    timeFrom.setHours(timeFrom.getHours() - hours)

    // Статистика сырых сигналов
    let rawQuery = supabase
      .from('signals_raw')
      .select('*', { count: 'exact', head: true })
      .gte('created_at', timeFrom.toISOString())

    if (trader_id) {
      rawQuery = rawQuery.eq('trader_id', trader_id)
    }

    const { count: rawCount, error: rawError } = await rawQuery

    // Статистика распарсенных сигналов
    let parsedQuery = supabase
      .from('signals_parsed')
      .select('*', { count: 'exact', head: true })
      .gte('parsed_at', timeFrom.toISOString())

    if (trader_id) {
      parsedQuery = parsedQuery.eq('trader_id', trader_id)
    }

    const { count: parsedCount, error: parsedError } = await parsedQuery

    if (rawError || parsedError) {
      throw new Error('Database query error')
    }

    // Статистика по трейдерам
    const { data: traderStats, error: traderError } = await supabase
      .from('signals_raw')
      .select(`
        trader_id,
        created_at
      `)
      .gte('created_at', timeFrom.toISOString())

    const traderBreakdown = traderStats?.reduce((acc: Record<string, number>, signal) => {
      acc[signal.trader_id] = (acc[signal.trader_id] || 0) + 1
      return acc
    }, {}) || {}

    return NextResponse.json({
      period_hours: hours,
      raw_signals: rawCount || 0,
      parsed_signals: parsedCount || 0,
      parse_rate: rawCount ? Math.round((parsedCount || 0) / rawCount * 100) : 0,
      by_trader: traderBreakdown,
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('Error getting signals stats:', error)
    return NextResponse.json(
      { error: 'Failed to get statistics' },
      { status: 500 }
    )
  }
}

// Сохранение сырого сигнала
async function saveRawSignal(data: RawSignalData) {
  try {
    // Валидация данных
    if (!data.trader_id || !data.text) {
      return NextResponse.json(
        { error: 'Missing required fields: trader_id, text' },
        { status: 400 }
      )
    }

    // Подготовка данных для вставки
    const rawSignalRecord = {
      trader_id: data.trader_id,
      source_msg_id: data.source_msg_id || null,
      posted_at: data.posted_at || new Date().toISOString(),
      text: data.text,
      meta: data.meta || {},
      processed: false,
      created_at: new Date().toISOString()
    }

    // Вставка в БД
    const { data: savedSignal, error } = await supabase
      .from('signals_raw')
      .insert(rawSignalRecord)
      .select()
      .single()

    if (error) {
      console.error('Supabase insert error:', error)
      return NextResponse.json(
        { error: 'Failed to save raw signal' },
        { status: 500 }
      )
    }

    return NextResponse.json({
      success: true,
      raw_id: savedSignal.raw_id,
      message: 'Raw signal saved successfully',
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('Error saving raw signal:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

// Сохранение распарсенного сигнала
async function saveParsedSignal(data: ParsedSignalData) {
  try {
    // Валидация данных
    if (!data.signal_id || !data.trader_id || !data.symbol || !data.side) {
      return NextResponse.json(
        { error: 'Missing required fields: signal_id, trader_id, symbol, side' },
        { status: 400 }
      )
    }

    // Подготовка данных для вставки
    const parsedSignalRecord = {
      signal_id: data.signal_id,
      trader_id: data.trader_id,
      raw_id: data.raw_id || null,
      posted_at: data.posted_at || new Date().toISOString(),
      symbol: data.symbol.toUpperCase(),
      side: data.side.toUpperCase(),
      entry_type: data.entry_type || 'market',
      entry: data.entry || null,
      range_low: data.range_low || null,
      range_high: data.range_high || null,
      tp1: data.tp1 || null,
      tp2: data.tp2 || null,
      tp3: data.tp3 || null,
      tp4: data.tp4 || null,
      sl: data.sl || null,
      leverage_hint: data.leverage_hint || null,
      timeframe_hint: data.timeframe_hint || null,
      confidence: data.confidence || 0,
      parsed_at: data.parsed_at || new Date().toISOString(),
      parse_version: data.parse_version || 'v1.0',
      checksum: data.checksum,
      is_valid: data.is_valid !== false // По умолчанию true
    }

    // Вставка в БД
    const { data: savedSignal, error } = await supabase
      .from('signals_parsed')
      .insert(parsedSignalRecord)
      .select()
      .single()

    if (error) {
      console.error('Supabase insert error:', error)
      return NextResponse.json(
        { error: 'Failed to save parsed signal' },
        { status: 500 }
      )
    }

    // Обновляем raw_signal как processed
    if (data.raw_id) {
      await supabase
        .from('signals_raw')
        .update({ processed: true })
        .eq('raw_id', data.raw_id)
    }

    return NextResponse.json({
      success: true,
      signal_id: savedSignal.signal_id,
      message: 'Parsed signal saved successfully',
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('Error saving parsed signal:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

// PUT - Обновление статуса сигнала
export async function PUT(request: NextRequest) {
  try {
    const body = await request.json()
    const { signal_id, raw_id, updates } = body

    if (signal_id) {
      // Обновление parsed signal
      const { data, error } = await supabase
        .from('signals_parsed')
        .update(updates)
        .eq('signal_id', signal_id)
        .select()
        .single()

      if (error) {
        return NextResponse.json(
          { error: 'Failed to update parsed signal' },
          { status: 500 }
        )
      }

      return NextResponse.json({
        success: true,
        updated_signal: data,
        timestamp: new Date().toISOString()
      })

    } else if (raw_id) {
      // Обновление raw signal
      const { data, error } = await supabase
        .from('signals_raw')
        .update(updates)
        .eq('raw_id', raw_id)
        .select()
        .single()

      if (error) {
        return NextResponse.json(
          { error: 'Failed to update raw signal' },
          { status: 500 }
        )
      }

      return NextResponse.json({
        success: true,
        updated_signal: data,
        timestamp: new Date().toISOString()
      })

    } else {
      return NextResponse.json(
        { error: 'Missing signal_id or raw_id' },
        { status: 400 }
      )
    }

  } catch (error) {
    console.error('Error updating signal:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
