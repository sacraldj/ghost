import { NextRequest, NextResponse } from 'next/server'
import { createClient, SupabaseClient } from '@supabase/supabase-js'

// Force Node.js runtime
export const runtime = 'nodejs'

// Безопасная инициализация Supabase клиента
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || ''

let supabase: SupabaseClient | null = null

// Инициализируем Supabase только если есть все переменные
if (supabaseUrl && supabaseKey && supabaseUrl !== 'https://placeholder.supabase.co') {
  try {
    supabase = createClient(supabaseUrl, supabaseKey)
  } catch (error) {
    console.error('Failed to initialize Supabase:', error)
  }
}

export async function GET(request: NextRequest) {
  try {
    // Проверяем, что Supabase инициализирован
    if (!supabase) {
      return NextResponse.json({ 
        error: 'Supabase not configured',
        signals: [],
        count: 0,
        message: 'Environment variables not set'
      }, { status: 503 })
    }

    const { searchParams } = new URL(request.url)
    const limit = parseInt(searchParams.get('limit') || '50')
    const status = searchParams.get('status') // valid, suspicious, all
    const symbol = searchParams.get('symbol')
    const direction = searchParams.get('direction') // LONG, SHORT
    const source = searchParams.get('source') // источник сигнала
    const hours = parseInt(searchParams.get('hours') || '24') // за последние N часов

    // Строим запрос к signals_parsed без джойнов (чтобы избежать ошибок)
    let query = supabase
      .from('signals_parsed')
      .select('*')
      .gte('posted_at', new Date(Date.now() - hours * 60 * 60 * 1000).toISOString())
      .order('posted_at', { ascending: false })
      .limit(limit)

    // Фильтры
    if (status && status !== 'all') {
      if (status === 'valid') {
        query = query.eq('is_valid', true)
      } else if (status === 'invalid') {
        query = query.eq('is_valid', false)
      }
    }

    if (symbol) {
      query = query.eq('symbol', symbol.toUpperCase())
    }

    if (direction) {
      query = query.eq('side', direction.toUpperCase())
    }

    if (source) {
      query = query.eq('source_id', source)
    }

    const { data, error } = await query

    if (error) {
      console.error('Supabase error:', error)
      return NextResponse.json({ 
        error: 'Database error',
        signals: [],
        count: 0 
      }, { status: 500 })
    }

    // Обрабатываем и форматируем данные с правильными полями
    const signals = data?.map(signal => ({
      id: signal.signal_id || signal.id,
      symbol: signal.symbol,
      direction: signal.side, // side вместо direction
      signalType: signal.side,
      
      // Цены и уровни (с правильными именами полей)
      entryPrice: signal.entry,
      entryLevels: signal.range_low && signal.range_high ? [signal.range_low, signal.range_high] : [],
      stopLoss: signal.sl,
      takeProfitLevels: [signal.tp1, signal.tp2, signal.tp3, signal.tp4].filter(tp => tp !== null),
      
      // Риск-менеджмент
      leverage: signal.leverage_hint,
      confidenceScore: signal.confidence || 0.5,
      riskRewardRatio: signal.entry && signal.sl && signal.tp1 
        ? ((signal.tp1 - signal.entry) / (signal.entry - signal.sl)).toFixed(2)
        : null,
      
      // Временные данные
      signalTimestamp: signal.posted_at,
      timeframe: signal.timeframe_hint,
      
      // Анализ
      technicalReason: null, // Нет в схеме
      tags: [], // Нет в схеме
      validationStatus: signal.is_valid ? 'valid' : 'invalid',
      parsingConfidence: signal.confidence || 0.5,
      
      // Источник (базовая информация, так как джойны недоступны)
      source: {
        name: 'Telegram Channel',
        code: signal.source_id || 'unknown',
        reliabilityScore: 0.75
      },
      
      // Инструмент (базовая информация, так как таблица instruments недоступна)
      instrument: {
        symbol: signal.symbol,
        name: `${signal.symbol} Future`,
        exchange: 'BINANCE'
      },
      
      // Сырые данные (базовая информация, так как джойны недоступны)
      rawMessage: {
        text: `Сигнал ${signal.direction} по ${signal.symbol}`,
        timestamp: signal.signal_timestamp,
        sentiment: 0.5
      },
      
      // Статус исполнения (если есть связанные сделки)
      executionStatus: 'pending', // TODO: добавить джойн к trades
      
      // Рассчитанные поля
      potentialProfit: signal.entry && signal.tp1 
        ? ((signal.tp1 - signal.entry) / signal.entry * 100).toFixed(2)
        : null,
      potentialLoss: signal.entry && signal.sl
        ? ((signal.entry - signal.sl) / signal.entry * 100).toFixed(2)
        : null,
      
      // Время с момента сигнала
      ageMinutes: Math.floor((Date.now() - new Date(signal.posted_at).getTime()) / (1000 * 60))
    })) || []

    // Статистика
    const stats = {
      total: signals.length,
      byDirection: {
        LONG: signals.filter(s => s.direction === 'LONG').length,
        SHORT: signals.filter(s => s.direction === 'SHORT').length
      },
      byStatus: {
        valid: signals.filter(s => s.validationStatus === 'valid').length,
        suspicious: signals.filter(s => s.validationStatus === 'suspicious').length
      },
      bySource: signals.reduce((acc, s) => {
        const source = s.source.code
        acc[source] = (acc[source] || 0) + 1
        return acc
      }, {} as Record<string, number>),
      avgConfidence: signals.length > 0 
        ? (signals.reduce((sum, s) => sum + (s.confidenceScore || 0), 0) / signals.length).toFixed(2)
        : '0.00',
      recentSignals: signals.filter(s => s.ageMinutes < 60).length // За последний час
    }

    // Топ символы
    const topSymbols = signals.reduce((acc, s) => {
      acc[s.symbol] = (acc[s.symbol] || 0) + 1
      return acc
    }, {} as Record<string, number>)

    const sortedSymbols = Object.entries(topSymbols)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 10)
      .map(([symbol, count]) => ({ symbol, count }))

    return NextResponse.json({
      signals,
      stats,
      topSymbols: sortedSymbols,
      count: signals.length,
      timestamp: new Date().toISOString(),
      source: 'supabase_advanced',
      filters: {
        hours,
        status,
        symbol,
        direction,
        source,
        limit
      },
      message: signals.length > 0 
        ? `Найдено ${signals.length} сигналов за последние ${hours} часов` 
        : 'Сигналов не найдено'
    })

  } catch (error) {
    console.error('API error:', error)
    return NextResponse.json({
      error: 'Internal server error',
        signals: [],
      count: 0 
    }, { status: 500 })
  }
}

// POST для создания нового сигнала (для тестирования)
export async function POST(request: NextRequest) {
  try {
    if (!supabase) {
      return NextResponse.json({ error: 'Supabase not configured' }, { status: 503 })
    }

    const body = await request.json()
    
    // Валидация обязательных полей
    const requiredFields = ['symbol', 'direction', 'signal_type']
    for (const field of requiredFields) {
      if (!body[field]) {
        return NextResponse.json({ error: `Missing required field: ${field}` }, { status: 400 })
      }
    }

    // Получаем ID источника (по умолчанию - whales_crypto_guide)
    const sourceResult = await supabase
      .from('signal_sources')
      .select('source_id')
      .eq('source_id', body.source_code || 'whales_guide_main')
      .single()

    if (!sourceResult.data) {
      return NextResponse.json({ error: 'Signal source not found' }, { status: 404 })
    }

    // Создание нового сигнала
    const signalData = {
      source_id: sourceResult.data.id,
      signal_type: body.signal_type.toUpperCase(),
      symbol: body.symbol.toUpperCase(),
      direction: body.direction.toUpperCase(),
      entry_price: body.entry_price,
      entry_levels: body.entry_levels || [],
      stop_loss: body.stop_loss,
      take_profit_levels: body.take_profit_levels || [],
      leverage: body.leverage,
      confidence_score: body.confidence_score || 0.5,
      signal_timestamp: new Date().toISOString(),
      technical_reason: body.technical_reason,
      timeframe: body.timeframe,
      parsing_method: 'manual',
      parser_version: 'v1.0.0',
      validation_status: 'valid',
      tags: body.tags || []
    }

    const { data, error } = await supabase
      .from('signals_parsed')
      .insert([signalData])
      .select()

    if (error) {
      console.error('Supabase error:', error)
      return NextResponse.json({ error: 'Database error' }, { status: 500 })
    }

    return NextResponse.json({
      success: true,
      signal: data[0],
      message: 'Торговый сигнал создан успешно'
    })

  } catch (error) {
    console.error('API error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}