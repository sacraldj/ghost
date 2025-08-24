import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

// Инициализация Supabase клиента
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

interface TelegramSignal {
  timestamp: string
  source: string
  chat_id: number
  text: string
  type: string
  trigger?: string
}

interface RawMessage {
  timestamp: string
  chat_id: number
  channel_name: string
  message_id: number
  text: string
  from_user?: string
}

interface TelegramData {
  signals: TelegramSignal[]
  raw_messages: RawMessage[]
  stats: {
    total_signals: number
    total_raw: number
    last_activity: string | null
    channels_active: number
    signal_types: string[]
  }
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const limit = parseInt(searchParams.get('limit') || '20')
    const hours = parseInt(searchParams.get('hours') || '24')
    
    // Вычисляем временной диапазон
    const startTime = new Date()
    startTime.setHours(startTime.getHours() - hours)

    // Получаем обработанные сигналы из signals_parsed
    const { data: parsedSignals, error: parsedError } = await supabase
      .from('signals_parsed')
      .select(`
        signal_id,
        trader_id,
        posted_at,
        symbol,
        side,
        entry,
        tp1,
        tp2,
        sl,
        confidence,
        is_valid,
        trader_registry!inner(name, source_handle, source_type)
      `)
      .gte('posted_at', startTime.toISOString())
      .order('posted_at', { ascending: false })
      .limit(limit)

    // Получаем сырые сообщения из signals_raw
    const { data: rawMessages, error: rawError } = await supabase
      .from('signals_raw')
      .select(`
        raw_id,
        trader_id,
        posted_at,
        text,
        source_msg_id,
        trader_registry!inner(name, source_handle, source_type)
      `)
      .gte('posted_at', startTime.toISOString())
      .order('posted_at', { ascending: false })
      .limit(limit * 2) // Больше сырых сообщений

    if (parsedError) {
      console.error('Error fetching parsed signals:', parsedError)
    }

    if (rawError) {
      console.error('Error fetching raw messages:', rawError)
    }

    // Преобразуем обработанные сигналы
    const signals: TelegramSignal[] = (parsedSignals || []).map((signal: any) => ({
      timestamp: signal.posted_at,
      source: signal.trader_registry?.source_handle || signal.trader_id,
      chat_id: parseInt(signal.trader_id) || 0,
      text: `${signal.side} ${signal.symbol} @ ${signal.entry}${signal.tp1 ? ` TP1: ${signal.tp1}` : ''}${signal.sl ? ` SL: ${signal.sl}` : ''}`,
      type: detectSignalType(`${signal.side} ${signal.symbol}`),
      trigger: signal.is_valid ? 'valid' : 'invalid'
    }))

    // Преобразуем сырые сообщения
    const rawMessagesFormatted: RawMessage[] = (rawMessages || []).map((msg: any) => ({
      timestamp: msg.posted_at,
      chat_id: parseInt(msg.trader_id) || 0,
      channel_name: msg.trader_registry?.name || msg.trader_id,
      message_id: msg.raw_id,
      text: msg.text,
      from_user: msg.trader_registry?.source_handle || undefined
    }))

    // Получаем статистику активных каналов
    const { data: activeTraders, error: tradersError } = await supabase
      .from('trader_registry')
      .select('trader_id, name, source_type, is_active')
      .eq('is_active', true)
      .eq('source_type', 'telegram')

    const channelsActive = activeTraders?.length || 0

    // Определяем типы сигналов
    const signalTypes = [...new Set(signals.map(s => s.type))]

    // Находим последнюю активность
    const lastActivity = signals.length > 0 ? signals[0].timestamp : 
                        rawMessagesFormatted.length > 0 ? rawMessagesFormatted[0].timestamp : null

    const data: TelegramData = {
      signals,
      raw_messages: rawMessagesFormatted,
      stats: {
        total_signals: signals.length,
        total_raw: rawMessagesFormatted.length,
        last_activity: lastActivity,
        channels_active: channelsActive,
        signal_types: signalTypes
      }
    }

    return NextResponse.json({
      success: true,
      data,
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('Telegram signals API error:', error)
    
    // Fallback к mock данным при ошибке
    const mockData: TelegramData = {
      signals: [
        {
          timestamp: new Date(Date.now() - 10 * 60 * 1000).toISOString(),
          source: '@cryptoattack24',
          chat_id: -1001234567890,
          text: 'LONG BTCUSDT @ 43250 TP1: 44000 SL: 42800',
          type: 'trade',
          trigger: 'valid'
        },
        {
          timestamp: new Date(Date.now() - 25 * 60 * 1000).toISOString(),
          source: '@slivaeminfo',
          chat_id: -1001234567891,
          text: 'SHORT ETHUSDT @ 2650 TP1: 2600 SL: 2720',
          type: 'trade',
          trigger: 'valid'
        }
      ],
      raw_messages: [
        {
          timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
          chat_id: -1001234567890,
          channel_name: 'КриптоАтака 24',
          message_id: 12345,
          text: 'Market looking bullish for BTC, expecting breakout above 44k',
          from_user: '@cryptoattack24'
        }
      ],
      stats: {
        total_signals: 2,
        total_raw: 1,
        last_activity: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
        channels_active: 3,
        signal_types: ['trade', 'news']
      }
    }

    return NextResponse.json({
      success: true,
      data: mockData,
      error: 'Using fallback data due to database error',
      timestamp: new Date().toISOString()
    })
  }
}

function detectSignalType(text: string): string {
  const upperText = text.toUpperCase()
  if (upperText.includes('LONG') || upperText.includes('SHORT') || upperText.includes('BUY') || upperText.includes('SELL')) {
    return 'trade'
  }
  if (upperText.includes('NEWS') || upperText.includes('BREAKING') || upperText.includes('ALERT')) {
    return 'news'
  }
  if (upperText.includes('TEST') || upperText.includes('DEMO')) {
    return 'test'
  }
  return 'message'
}