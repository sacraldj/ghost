import { NextRequest, NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

// API для получения Telegram сигналов из listener
export const runtime = 'nodejs'

const SIGNALS_FILE = path.join(process.cwd(), 'news_engine', 'output', 'signals.json')
const RAW_LOG_FILE = path.join(process.cwd(), 'news_engine', 'output', 'raw_logbook.json')

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

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const limit = parseInt(searchParams.get('limit') || '50')
    const type = searchParams.get('type') // 'signals' | 'raw' | 'all'
    const hours = parseInt(searchParams.get('hours') || '24')

    const result: any = {
      signals: [],
      raw_messages: [],
      stats: {
        total_signals: 0,
        total_raw: 0,
        last_activity: null
      },
      timestamp: new Date().toISOString()
    }

    // Загружаем сигналы
    if (type !== 'raw') {
      try {
        if (fs.existsSync(SIGNALS_FILE)) {
          const signalsData = fs.readFileSync(SIGNALS_FILE, 'utf-8')
          const signals: TelegramSignal[] = JSON.parse(signalsData)
          
          // Фильтр по времени
          const cutoffTime = new Date(Date.now() - hours * 60 * 60 * 1000)
          const recentSignals = signals
            .filter(s => new Date(s.timestamp) > cutoffTime)
            .slice(-limit)
            .reverse() // Новые сначала
          
          result.signals = recentSignals
          result.stats.total_signals = recentSignals.length
          
          if (recentSignals.length > 0) {
            result.stats.last_activity = recentSignals[0].timestamp
          }
        }
      } catch (error) {
        console.warn('Error reading signals file:', error)
      }
    }

    // Загружаем сырые сообщения
    if (type !== 'signals') {
      try {
        if (fs.existsSync(RAW_LOG_FILE)) {
          const rawData = fs.readFileSync(RAW_LOG_FILE, 'utf-8')
          const rawMessages: RawMessage[] = JSON.parse(rawData)
          
          // Фильтр по времени
          const cutoffTime = new Date(Date.now() - hours * 60 * 60 * 1000)
          const recentRaw = rawMessages
            .filter(m => new Date(m.timestamp) > cutoffTime)
            .slice(-limit)
            .reverse() // Новые сначала
          
          result.raw_messages = recentRaw
          result.stats.total_raw = recentRaw.length
          
          if (recentRaw.length > 0 && !result.stats.last_activity) {
            result.stats.last_activity = recentRaw[0].timestamp
          }
        }
      } catch (error) {
        console.warn('Error reading raw messages file:', error)
      }
    }

    // Дополнительная статистика
    result.stats.channels_active = Array.from(
      new Set([
        ...result.signals.map((s: TelegramSignal) => s.source),
        ...result.raw_messages.map((m: RawMessage) => m.channel_name)
      ])
    ).length

    result.stats.signal_types = Array.from(
      new Set(result.signals.map((s: TelegramSignal) => s.type))
    )

    return NextResponse.json({
      success: true,
      data: result,
      message: `Loaded ${result.stats.total_signals} signals and ${result.stats.total_raw} raw messages`
    })

  } catch (error) {
    console.error('Telegram signals API error:', error)
    return NextResponse.json({
      success: false,
      error: 'Failed to load Telegram data',
      data: {
        signals: [],
        raw_messages: [],
        stats: {
          total_signals: 0,
          total_raw: 0,
          last_activity: null,
          channels_active: 0,
          signal_types: []
        }
      }
    }, { status: 500 })
  }
}

// POST endpoint для ручного добавления сигналов (для тестирования)
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { text, source, type = 'manual' } = body

    if (!text || !source) {
      return NextResponse.json({
        success: false,
        error: 'Text and source are required'
      }, { status: 400 })
    }

    const signal: TelegramSignal = {
      timestamp: new Date().toISOString(),
      source,
      chat_id: -1,
      text,
      type,
      trigger: 'manual'
    }

    // Читаем существующие сигналы
    let signals: TelegramSignal[] = []
    if (fs.existsSync(SIGNALS_FILE)) {
      try {
        const signalsData = fs.readFileSync(SIGNALS_FILE, 'utf-8')
        signals = JSON.parse(signalsData)
      } catch (error) {
        console.warn('Error reading existing signals:', error)
      }
    }

    // Добавляем новый сигнал
    signals.push(signal)

    // Ограничиваем количество сигналов
    if (signals.length > 100) {
      signals = signals.slice(-100)
    }

    // Создаем директорию если не существует
    const outputDir = path.dirname(SIGNALS_FILE)
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true })
    }

    // Сохраняем обновленные сигналы
    fs.writeFileSync(SIGNALS_FILE, JSON.stringify(signals, null, 2))

    return NextResponse.json({
      success: true,
      message: 'Signal added successfully',
      signal
    })

  } catch (error) {
    console.error('Error adding signal:', error)
    return NextResponse.json({
      success: false,
      error: 'Failed to add signal'
    }, { status: 500 })
  }
}
