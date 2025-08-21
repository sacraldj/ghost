import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SECRET_KEY!
)

// GET /api/signal-candles/[signalId] - получить свечи для сигнала
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ signalId: string }> }
) {
  try {
    const { signalId } = await params
    const { searchParams } = new URL(request.url)
    
    // Параметры запроса
    const limit = parseInt(searchParams.get('limit') || '500')
    const interval = searchParams.get('interval') || '1m'
    
    console.log(`📊 Fetching candles for signal: ${signalId}`)
    
    // Получаем информацию о сигнале из v_trades
    const { data: signalData, error: signalError } = await supabase
      .from('v_trades')
      .select('symbol, side, entry_min, entry_max, tp1, tp2, tp3, sl, posted_ts, created_at')
      .eq('id', signalId)
      .single()
    
    if (signalError || !signalData) {
      console.error('❌ Signal not found:', signalError)
      return NextResponse.json({ error: 'Signal not found' }, { status: 404 })
    }
    
    console.log(`✅ Found signal: ${signalData.symbol} ${signalData.side}`)
    
    // Получаем реальные свечи с Bybit
    const candlesData = await fetchBybitCandles(signalData.symbol, interval, limit)
    
    if (!candlesData || candlesData.length === 0) {
      console.log(`⚠️ No candles data for ${signalData.symbol}`)
      return NextResponse.json({
        signal: signalData,
        candles: [],
        stats: null,
        interval,
        source: 'live_bybit',
        message: 'No candles available yet'
      })
    }
    
    // Конвертируем данные в нужный формат
    const formattedCandles = candlesData.map(candle => ({
      timestamp: parseInt(candle[0]) / 1000, // Bybit возвращает ms, конвертируем в секунды
      open: parseFloat(candle[1]),
      high: parseFloat(candle[2]), 
      low: parseFloat(candle[3]),
      close: parseFloat(candle[4]),
      volume: parseFloat(candle[5]),
      quote_volume: 0,
      signal_id: signalId,
      symbol: signalData.symbol
    }))
    
    // Статистика по свечам
    const stats = formattedCandles.length > 0 ? {
      total_candles: formattedCandles.length,
      time_range: {
        start: formattedCandles[0].timestamp,
        end: formattedCandles[formattedCandles.length - 1].timestamp,
        duration_hours: Math.round((formattedCandles[formattedCandles.length - 1].timestamp - formattedCandles[0].timestamp) / 3600 * 100) / 100
      },
      price_range: {
        min: Math.min(...formattedCandles.map(c => c.low)),
        max: Math.max(...formattedCandles.map(c => c.high)),
        first: formattedCandles[0].open,
        last: formattedCandles[formattedCandles.length - 1].close
      }
    } : null
    
    console.log(`✅ Returning ${formattedCandles.length} candles for ${signalData.symbol}`)
    
    return NextResponse.json({
      signal: signalData,
      candles: formattedCandles,
      stats,
      interval,
      source: 'live_bybit'
    })
    
  } catch (error) {
    console.error('❌ API error:', error)
    return NextResponse.json({ 
      error: 'Internal server error',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}

// Функция для получения свечей с Bybit
async function fetchBybitCandles(symbol: string, interval: string, limit: number) {
  try {
    // Конвертируем интервал для Bybit
    const bybitInterval = convertIntervalToBybit(interval)
    
    const url = `https://api.bybit.com/v5/market/kline?category=linear&symbol=${symbol}&interval=${bybitInterval}&limit=${limit}`
    
    console.log(`📡 Fetching from Bybit: ${url}`)
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    if (!response.ok) {
      console.error(`❌ Bybit API error: ${response.status}`)
      return null
    }
    
    const data = await response.json()
    
    if (data.retCode === 0 && data.result && data.result.list) {
      console.log(`✅ Got ${data.result.list.length} candles from Bybit`)
      return data.result.list.reverse() // Bybit возвращает в обратном порядке
    }
    
    console.error(`❌ Invalid Bybit response:`, data)
    return null
    
  } catch (error) {
    console.error(`❌ Error fetching from Bybit:`, error)
    return null
  }
}

// Конвертация интервалов для Bybit API
function convertIntervalToBybit(interval: string): string {
  const intervalMap: Record<string, string> = {
    '1m': '1',
    '3m': '3',
    '5m': '5',
    '15m': '15',
    '30m': '30',
    '1h': '60',
    '2h': '120',
    '4h': '240',
    '6h': '360',
    '12h': '720',
    '1d': 'D',
    '1w': 'W',
    '1M': 'M'
  }
  
  return intervalMap[interval] || '1' // По умолчанию 1 минута
}

// POST endpoint для тестирования (добавление искусственных свечей)
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ signalId: string }> }
) {
  try {
    const { signalId } = await params
    const body = await request.json()
    
    // Получаем сигнал
    const { data: signalData, error } = await supabase
      .from('v_trades')
      .select('symbol')
      .eq('id', signalId)
      .single()
    
    if (error || !signalData) {
      return NextResponse.json({ error: 'Signal not found' }, { status: 404 })
    }
    
    // Возвращаем подтверждение (в реальности данные идут с Bybit)
    return NextResponse.json({ 
      message: `Using live data from Bybit for ${signalData.symbol}`,
      signalId,
      symbol: signalData.symbol
    })
    
  } catch (error) {
    console.error('API error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}