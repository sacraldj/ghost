import { NextRequest, NextResponse } from 'next/server'
import { bybitClient } from '../../../lib/bybit-client'

// Получение live цен через реальный Bybit API
async function fetchLivePrice(symbol: string): Promise<number> {
  try {
    const price = await bybitClient.getPrice(symbol)
    return price
  } catch (error) {
    console.error(`Error fetching price for ${symbol}:`, error)
    
    // Fallback: базовые цены если API недоступно
    const fallbackPrices: { [key: string]: number } = {
      'BTCUSDT': 43000,
      'ETHUSDT': 2500,
      'BNBUSDT': 320,
      'STGUSDT': 0.45,
      'ZROUSDT': 4.2,
      'XRPUSDT': 0.63,
      'UNIUSDT': 10.75,
      'ADAUSDT': 0.48,
      'DOTUSDT': 7.25,
      'LINKUSDT': 15.80
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
    
    const price = await fetchLivePrice(symbol)
    
    return NextResponse.json({
      symbol,
      price,
      lastPrice: price.toString(),
      timestamp: new Date().toISOString()
    })
    
  } catch (error) {
    console.error('Live prices API error:', error)
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
    
    // Используем batch запрос к Bybit API для эффективности
    try {
      const priceMap = await bybitClient.getTickers(symbols)
      
      const prices = symbols.map((symbol: string) => ({
        symbol,
        price: priceMap[symbol] || 0,
        lastPrice: (priceMap[symbol] || 0).toString(),
        timestamp: new Date().toISOString()
      }))
      
      return NextResponse.json({
        prices,
        timestamp: new Date().toISOString(),
        source: 'bybit_api'
      })
      
    } catch (apiError) {
      console.error('Bybit API batch request failed:', apiError)
      
      // Fallback: индивидуальные запросы
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
      
      return NextResponse.json({
        prices,
        timestamp: new Date().toISOString(),
        source: 'fallback'
      })
    }
    
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
