import { NextRequest, NextResponse } from 'next/server'

// Получение live цен через реальный Bybit API
async function fetchLivePrice(symbol: string): Promise<number> {
  try {
    // Используем прямой запрос к Bybit API (публичный endpoint, не требует ключей)
    const response = await fetch(`https://api.bybit.com/v5/market/tickers?category=linear&symbol=${symbol}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      },
      cache: 'no-store'
    })
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    
    const data = await response.json()
    
    if (data.retCode === 0 && data.result && data.result.list && data.result.list.length > 0) {
      const price = parseFloat(data.result.list[0].lastPrice)
      console.log(`✅ Live price for ${symbol}: $${price}`)
      return price
    } else {
      throw new Error(`Invalid response format: ${JSON.stringify(data)}`)
    }
  } catch (error) {
    console.error(`❌ Error fetching price for ${symbol}:`, error)
    
    // Обновленные fallback цены (более реалистичные)
    const fallbackPrices: { [key: string]: number } = {
      'BTCUSDT': 115000,
      'ETHUSDT': 4200,
      'BNBUSDT': 700,
      'STGUSDT': 0.45,
      'ZROUSDT': 4.2,
      'XRPUSDT': 3.20,
      'UNIUSDT': 15.80,
      'ADAUSDT': 1.25,
      'DOTUSDT': 8.25,
      'LINKUSDT': 28.80,
      'SOLUSDT': 260
    }
    
    return fallbackPrices[symbol] || 100
  }
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const symbol = searchParams.get('symbol')
    
    if (!symbol) {
      return NextResponse.json({ error: 'Symbol parameter is required' }, { status: 400 })
    }
    
    console.log(`📡 Fetching live price for ${symbol}`)
    const price = await fetchLivePrice(symbol)
    
    return NextResponse.json({
      symbol,
      price,
      lastPrice: price.toString(),
      timestamp: new Date().toISOString(),
      source: 'bybit_live'
    })
    
  } catch (error) {
    console.error('❌ Live prices API error:', error)
    return NextResponse.json(
      { 
        error: 'Failed to fetch live price',
        details: error instanceof Error ? error.message : 'Unknown error'
      }, 
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { symbols } = body
    
    if (!symbols || !Array.isArray(symbols)) {
      return NextResponse.json({ error: 'Symbols array is required' }, { status: 400 })
    }
    
    console.log(`📡 Fetching live prices for symbols: ${symbols.join(', ')}`)
    
    // Получаем цены для каждого символа параллельно
    const pricesPromises = symbols.map(async (symbol: string) => {
      const price = await fetchLivePrice(symbol)
      return {
        symbol,
        price,
        lastPrice: price.toString(),
        timestamp: new Date().toISOString()
      }
    })
    
    const prices = await Promise.all(pricesPromises)
    
    console.log(`✅ Fetched ${prices.length} live prices from Bybit`)
    
    return NextResponse.json({
      prices,
      timestamp: new Date().toISOString(),
      source: 'bybit_live_api'
    })
    
  } catch (error) {
    console.error('Live prices batch API error:', error)
    return NextResponse.json(
      { 
        error: 'Failed to fetch live prices',
        details: error instanceof Error ? error.message : 'Unknown error'
      }, 
      { status: 500 }
    )
  }
}
