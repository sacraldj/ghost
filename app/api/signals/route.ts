import { NextRequest, NextResponse } from 'next/server'
import Redis from 'ioredis'

// Инициализация Redis клиента
let redis: Redis | null = null

try {
  if (process.env.REDIS_URL) {
    redis = new Redis(process.env.REDIS_URL)
  }
} catch (error) {
  console.warn('Redis connection failed:', error)
}

interface TradingSignal {
  id: string
  channel_id: string
  channel_name: string
  trader_name: string
  message_id: number
  timestamp: string
  symbol: string
  direction: string
  entry_zone: number[]
  tp_levels: number[]
  sl_level?: number
  leverage?: number
  confidence?: number
  original_text: string
  validation_status: string
  validation_errors?: string[]
}

interface ProcessedSignal {
  original_signal_id: string
  source_channel: string
  trader_name: string
  timestamp: string
  symbol: string
  base_asset: string
  quote_asset: string
  direction: string
  entry_price: number
  entry_zone_min: number
  entry_zone_max: number
  tp1_price?: number
  tp2_price?: number
  tp3_price?: number
  sl_price?: number
  suggested_leverage?: number
  risk_reward_ratio?: number
  position_size_usd?: number
  confidence_score: number
  quality_score: number
  processing_status: string
  processing_errors?: string[]
  trader_win_rate?: number
  trader_avg_roi?: number
  current_price?: number
}

interface SignalsResponse {
  signals: (TradingSignal | ProcessedSignal)[]
  count: number
  stats: {
    total: number
    valid: number
    invalid: number
    processed: number
    pending: number
  }
  traders: {
    [key: string]: {
      signal_count: number
      win_rate?: number
      avg_roi?: number
    }
  }
  timestamp: string
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const type = searchParams.get('type') || 'all' // 'new', 'processed', 'all'
    const limit = parseInt(searchParams.get('limit') || '50')
    const trader = searchParams.get('trader')
    const symbol = searchParams.get('symbol')
    const status = searchParams.get('status')
    
    if (!redis) {
      return NextResponse.json({
        signals: [],
        count: 0,
        stats: { total: 0, valid: 0, invalid: 0, processed: 0, pending: 0 },
        traders: {},
        timestamp: new Date().toISOString(),
        error: 'Redis not available'
      })
    }
    
    let signals: (TradingSignal | ProcessedSignal)[] = []
    let stats = {
      total: 0,
      valid: 0,
      invalid: 0,
      processed: 0,
      pending: 0
    }
    
    try {
      // Получение сигналов в зависимости от типа
      if (type === 'new' || type === 'all') {
        const newSignals = await redis.lrange('ghost:signals:new', 0, limit - 1)
        for (const signalJson of newSignals) {
          try {
            const signal: TradingSignal = JSON.parse(signalJson)
            
            // Фильтрация по параметрам
            if (trader && signal.trader_name !== trader) continue
            if (symbol && signal.symbol !== symbol) continue
            if (status && signal.validation_status !== status) continue
            
            signals.push(signal)
            stats.total++
            
            // Подсчёт статистики
            if (signal.validation_status === 'valid') {
              stats.valid++
            } else if (signal.validation_status === 'invalid') {
              stats.invalid++
            } else {
              stats.pending++
            }
          } catch (e) {
            console.error('Error parsing signal:', e)
          }
        }
      }
      
      if (type === 'processed' || type === 'all') {
        const processedSignals = await redis.lrange('ghost:signals:processed', 0, limit - 1)
        for (const signalJson of processedSignals) {
          try {
            const signal: ProcessedSignal = JSON.parse(signalJson)
            
            // Фильтрация по параметрам
            if (trader && signal.trader_name !== trader) continue
            if (symbol && signal.symbol !== symbol) continue
            if (status && signal.processing_status !== status) continue
            
            signals.push(signal)
            stats.total++
            stats.processed++
          } catch (e) {
            console.error('Error parsing processed signal:', e)
          }
        }
      }
      
      // Сортировка по времени (новые сначала)
      signals.sort((a, b) => 
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      )
      
      // Ограничение результатов
      signals = signals.slice(0, limit)
      
    } catch (redisError) {
      console.error('Redis error:', redisError)
      return NextResponse.json({
        signals: [],
        count: 0,
        stats: { total: 0, valid: 0, invalid: 0, processed: 0, pending: 0 },
        traders: {},
        timestamp: new Date().toISOString(),
        error: 'Failed to fetch signals from Redis'
      })
    }
    
    // Статистика по трейдерам
    const traders: { [key: string]: any } = {}
    signals.forEach(signal => {
      const traderName = signal.trader_name
      if (!traders[traderName]) {
        traders[traderName] = {
          signal_count: 0,
          win_rate: undefined,
          avg_roi: undefined
        }
      }
      traders[traderName].signal_count++
      
      // Для обработанных сигналов добавляем статистику
      if ('trader_win_rate' in signal && signal.trader_win_rate !== undefined) {
        traders[traderName].win_rate = signal.trader_win_rate
      }
      if ('trader_avg_roi' in signal && signal.trader_avg_roi !== undefined) {
        traders[traderName].avg_roi = signal.trader_avg_roi
      }
    })
    
    const response: SignalsResponse = {
      signals,
      count: signals.length,
      stats,
      traders,
      timestamp: new Date().toISOString()
    }
    
    return NextResponse.json(response)
    
  } catch (error) {
    console.error('Signals API error:', error)
    return NextResponse.json(
      { 
        error: 'Failed to fetch signals',
        details: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString()
      }, 
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { action, signal_id, trader_name } = body
    
    if (!redis) {
      return NextResponse.json(
        { error: 'Redis not available' },
        { status: 503 }
      )
    }
    
    switch (action) {
      case 'get_trader_signals':
        if (!trader_name) {
          return NextResponse.json(
            { error: 'Trader name is required' },
            { status: 400 }
          )
        }
        
        try {
          const traderSignals = await redis.lrange(
            `ghost:signals:trader:${trader_name}`, 
            0, 100
          )
          
          const signals = traderSignals.map(signalJson => {
            try {
              return JSON.parse(signalJson)
            } catch (e) {
              return null
            }
          }).filter(Boolean)
          
          return NextResponse.json({
            trader_name,
            signals,
            count: signals.length,
            timestamp: new Date().toISOString()
          })
          
        } catch (redisError) {
          return NextResponse.json(
            { error: 'Failed to fetch trader signals' },
            { status: 500 }
          )
        }
      
      case 'get_stats':
        try {
          // Статистика обработчика сигналов
          const processorStats = await redis.hgetall('ghost:signal_processor:stats')
          
          // Статистика Telegram Listener (если доступна)
          const listenerStats = await redis.hgetall('ghost:telegram_listener:stats')
          
          return NextResponse.json({
            processor: processorStats,
            listener: listenerStats,
            timestamp: new Date().toISOString()
          })
          
        } catch (redisError) {
          return NextResponse.json(
            { error: 'Failed to fetch stats' },
            { status: 500 }
          )
        }
      
      case 'clear_queue':
        const queue = body.queue || 'ghost:signals:new'
        
        try {
          const cleared = await redis.del(queue)
          
          return NextResponse.json({
            message: `Queue ${queue} cleared`,
            cleared_items: cleared,
            timestamp: new Date().toISOString()
          })
          
        } catch (redisError) {
          return NextResponse.json(
            { error: 'Failed to clear queue' },
            { status: 500 }
          )
        }
      
      default:
        return NextResponse.json(
          { error: `Unknown action: ${action}` },
          { status: 400 }
        )
    }
    
  } catch (error) {
    console.error('Signals POST API error:', error)
    return NextResponse.json(
      { 
        error: 'Failed to process request',
        details: error instanceof Error ? error.message : 'Unknown error'
      }, 
      { status: 500 }
    )
  }
}
