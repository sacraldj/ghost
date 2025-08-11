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

interface PriceDataPoint {
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  ma20?: number
  ma50?: number
  rsi?: number
}

interface NewsEvent {
  id: string
  timestamp: string
  title: string
  impact: 'HIGH' | 'MEDIUM' | 'LOW'
  sentiment: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL'
  price_impact: number
  keywords: string[]
  source: string
}

interface TradingSignal {
  id: string
  timestamp: string
  symbol: string
  direction: 'LONG' | 'SHORT'
  entry_price: number
  confidence: number
  trader: string
  status: 'ACTIVE' | 'FILLED' | 'CANCELLED'
}

interface MarketDataResponse {
  symbol: string
  timeframe: string
  price_data: PriceDataPoint[]
  news_events: NewsEvent[]
  trading_signals: TradingSignal[]
  current_price: number
  price_change_24h: number
  volume_24h: number
  market_cap?: number
  timestamp: string
}

// Симуляция технических индикаторов
function calculateMA(prices: number[], period: number): number[] {
  const ma: number[] = []
  for (let i = 0; i < prices.length; i++) {
    if (i < period - 1) {
      ma.push(0)
    } else {
      const sum = prices.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0)
      ma.push(sum / period)
    }
  }
  return ma
}

function calculateRSI(prices: number[], period: number = 14): number[] {
  const rsi: number[] = []
  
  for (let i = 0; i < prices.length; i++) {
    if (i < period) {
      rsi.push(50) // Нейтральное значение для первых точек
      continue
    }
    
    const priceChanges = []
    for (let j = i - period + 1; j <= i; j++) {
      priceChanges.push(prices[j] - prices[j - 1])
    }
    
    const gains = priceChanges.filter(change => change > 0)
    const losses = priceChanges.filter(change => change < 0).map(loss => Math.abs(loss))
    
    const avgGain = gains.length > 0 ? gains.reduce((a, b) => a + b, 0) / period : 0
    const avgLoss = losses.length > 0 ? losses.reduce((a, b) => a + b, 0) / period : 0
    
    if (avgLoss === 0) {
      rsi.push(100)
    } else {
      const rs = avgGain / avgLoss
      rsi.push(100 - (100 / (1 + rs)))
    }
  }
  
  return rsi
}

// Генерация демо данных для цен
function generatePriceData(symbol: string, timeframe: string, points: number = 100): PriceDataPoint[] {
  const data: PriceDataPoint[] = []
  const now = new Date()
  
  // Базовые цены для разных символов
  const basePrices: { [key: string]: number } = {
    'BTCUSDT': 43000,
    'ETHUSDT': 2500,
    'BNBUSDT': 320,
    'STGUSDT': 0.45,
    'ZROUSDT': 4.2
  }
  
  let basePrice = basePrices[symbol] || 100
  const prices: number[] = []
  
  // Интервалы в миллисекундах
  const intervals: { [key: string]: number } = {
    '1M': 60000,
    '5M': 300000,
    '15M': 900000,
    '1H': 3600000,
    '4H': 14400000,
    '1D': 86400000
  }
  
  const interval = intervals[timeframe] || 3600000
  
  for (let i = points; i >= 0; i--) {
    const timestamp = new Date(now.getTime() - i * interval).toISOString()
    
    // Симуляция движения цены с трендом и волатильностью
    const trend = Math.sin(i / 20) * 0.001 // Медленный тренд
    const volatility = (Math.random() - 0.5) * 0.02 // ±1% волатильность
    const noise = (Math.random() - 0.5) * 0.005 // Шум
    
    basePrice *= (1 + trend + volatility + noise)
    prices.push(basePrice)
    
    // Генерация OHLC данных
    const high = basePrice * (1 + Math.random() * 0.01)
    const low = basePrice * (1 - Math.random() * 0.01)
    const open = i === points ? basePrice : data[data.length - 1]?.close || basePrice
    const close = basePrice
    const volume = Math.random() * 1000000 + 100000
    
    data.push({
      timestamp,
      open,
      high,
      low,
      close,
      volume
    })
  }
  
  // Добавляем технические индикаторы
  const closePrices = data.map(d => d.close)
  const ma20 = calculateMA(closePrices, 20)
  const ma50 = calculateMA(closePrices, 50)
  const rsi = calculateRSI(closePrices)
  
  data.forEach((point, index) => {
    point.ma20 = ma20[index]
    point.ma50 = ma50[index]
    point.rsi = rsi[index]
  })
  
  return data
}

// Генерация демо новостей
function generateNewsEvents(symbol: string): NewsEvent[] {
  const news: NewsEvent[] = []
  const now = new Date()
  
  const newsTemplates = [
    {
      title: "LayerZero Foundation предложил приобрести Stargate",
      keywords: ["LayerZero", "STG", "ZRO", "DeFi", "Acquisition"],
      source: "CryptoAttack"
    },
    {
      title: "Bitcoin ETF shows record inflows this week",
      keywords: ["Bitcoin", "ETF", "Institutional", "Investment"],
      source: "CoinDesk"
    },
    {
      title: "Major whale wallet moves 10,000 BTC to unknown address",
      keywords: ["Bitcoin", "Whale", "Movement", "Market"],
      source: "WhaleAlert"
    },
    {
      title: "New DeFi protocol raises $50M in Series A funding",
      keywords: ["DeFi", "Funding", "Investment", "Protocol"],
      source: "TechCrunch"
    },
    {
      title: "Regulatory news impacts cryptocurrency markets",
      keywords: ["Regulation", "Government", "Policy", "Market"],
      source: "Reuters"
    }
  ]
  
  // Генерируем 5-10 новостных событий за последние 24 часа
  for (let i = 0; i < Math.floor(Math.random() * 6) + 5; i++) {
    const template = newsTemplates[Math.floor(Math.random() * newsTemplates.length)]
    const timestamp = new Date(now.getTime() - Math.random() * 86400000).toISOString() // Последние 24 часа
    
    const impacts = ['HIGH', 'MEDIUM', 'LOW'] as const
    const sentiments = ['POSITIVE', 'NEGATIVE', 'NEUTRAL'] as const
    
    news.push({
      id: `news_${i}_${Date.now()}`,
      timestamp,
      title: template.title,
      impact: impacts[Math.floor(Math.random() * impacts.length)],
      sentiment: sentiments[Math.floor(Math.random() * sentiments.length)],
      price_impact: (Math.random() - 0.5) * 8, // ±4% максимальное воздействие
      keywords: template.keywords,
      source: template.source
    })
  }
  
  return news.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
}

// Генерация демо торговых сигналов
function generateTradingSignals(symbol: string): TradingSignal[] {
  const signals: TradingSignal[] = []
  const now = new Date()
  
  const traders = ['CryptoExpert', 'TradingPro', 'SignalMaster', 'AlphaTrader', 'MarketGuru']
  const statuses = ['ACTIVE', 'FILLED', 'CANCELLED'] as const
  
  // Генерируем 3-8 сигналов за последние 4 часа
  for (let i = 0; i < Math.floor(Math.random() * 6) + 3; i++) {
    const timestamp = new Date(now.getTime() - Math.random() * 14400000).toISOString() // Последние 4 часа
    
    // Примерные цены для разных символов
    const basePrices: { [key: string]: number } = {
      'BTCUSDT': 43000,
      'ETHUSDT': 2500,
      'BNBUSDT': 320,
      'STGUSDT': 0.45,
      'ZROUSDT': 4.2
    }
    
    const basePrice = basePrices[symbol] || 100
    const priceVariation = (Math.random() - 0.5) * 0.02 // ±1% от базовой цены
    
    signals.push({
      id: `signal_${i}_${Date.now()}`,
      timestamp,
      symbol,
      direction: Math.random() > 0.5 ? 'LONG' : 'SHORT',
      entry_price: basePrice * (1 + priceVariation),
      confidence: Math.random() * 40 + 60, // 60-100%
      trader: traders[Math.floor(Math.random() * traders.length)],
      status: statuses[Math.floor(Math.random() * statuses.length)]
    })
  }
  
  return signals.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const symbol = searchParams.get('symbol') || 'BTCUSDT'
    const timeframe = searchParams.get('timeframe') || '1H'
    const limit = parseInt(searchParams.get('limit') || '100')
    
    // Генерация данных (в продакшене будут реальные данные из Binance/Bybit API)
    const priceData = generatePriceData(symbol, timeframe, limit)
    const newsEvents = generateNewsEvents(symbol)
    const tradingSignals = generateTradingSignals(symbol)
    
    // Расчет текущих метрик
    const currentPrice = priceData[priceData.length - 1]?.close || 0
    const previousPrice = priceData[priceData.length - 2]?.close || currentPrice
    const priceChange24h = ((currentPrice - previousPrice) / previousPrice) * 100
    
    const volume24h = priceData.reduce((sum, point) => sum + point.volume, 0)
    
    // Попытка получить кэшированные данные из Redis
    if (redis) {
      try {
        const cacheKey = `market_data:${symbol}:${timeframe}`
        const cachedData = await redis.get(cacheKey)
        
        if (cachedData) {
          console.log('Returning cached market data')
          return NextResponse.json(JSON.parse(cachedData))
        }
        
        // Кэшируем новые данные на 1 минуту
        const responseData: MarketDataResponse = {
          symbol,
          timeframe,
          price_data: priceData,
          news_events: newsEvents,
          trading_signals: tradingSignals,
          current_price: currentPrice,
          price_change_24h: priceChange24h,
          volume_24h: volume24h,
          timestamp: new Date().toISOString()
        }
        
        await redis.setex(cacheKey, 60, JSON.stringify(responseData))
        
        return NextResponse.json(responseData)
        
      } catch (redisError) {
        console.warn('Redis operation failed:', redisError)
      }
    }
    
    // Возвращаем данные без кэширования
    const responseData: MarketDataResponse = {
      symbol,
      timeframe,
      price_data: priceData,
      news_events: newsEvents,
      trading_signals: tradingSignals,
      current_price: currentPrice,
      price_change_24h: priceChange24h,
      volume_24h: volume24h,
      timestamp: new Date().toISOString()
    }
    
    return NextResponse.json(responseData)
    
  } catch (error) {
    console.error('Market data API error:', error)
    return NextResponse.json(
      { 
        error: 'Failed to fetch market data',
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
    const { action, symbol, timeframe } = body
    
    if (!redis) {
      return NextResponse.json(
        { error: 'Redis not available' },
        { status: 503 }
      )
    }
    
    switch (action) {
      case 'clear_cache':
        try {
          const pattern = symbol && timeframe 
            ? `market_data:${symbol}:${timeframe}`
            : 'market_data:*'
          
          const keys = await redis.keys(pattern)
          if (keys.length > 0) {
            await redis.del(...keys)
          }
          
          return NextResponse.json({
            message: `Cache cleared for pattern: ${pattern}`,
            cleared_keys: keys.length,
            timestamp: new Date().toISOString()
          })
          
        } catch (redisError) {
          return NextResponse.json(
            { error: 'Failed to clear cache' },
            { status: 500 }
          )
        }
      
      case 'get_cache_info':
        try {
          const keys = await redis.keys('market_data:*')
          const cacheInfo = []
          
          for (const key of keys) {
            const ttl = await redis.ttl(key)
            cacheInfo.push({ key, ttl })
          }
          
          return NextResponse.json({
            cache_entries: cacheInfo,
            total_keys: keys.length,
            timestamp: new Date().toISOString()
          })
          
        } catch (redisError) {
          return NextResponse.json(
            { error: 'Failed to get cache info' },
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
    console.error('Market data POST API error:', error)
    return NextResponse.json(
      { 
        error: 'Failed to process request',
        details: error instanceof Error ? error.message : 'Unknown error'
      }, 
      { status: 500 }
    )
  }
}
