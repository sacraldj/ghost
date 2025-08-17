import { NextRequest, NextResponse } from 'next/server'
import { bybitClient } from '../../../lib/bybit-client'

export async function GET(request: NextRequest) {
  try {
    console.log('Testing Bybit API connection...')
    
    // Тест подключения
    const isConnected = await bybitClient.testConnection()
    
    if (!isConnected) {
      return NextResponse.json({
        success: false,
        error: 'Failed to connect to Bybit API',
        timestamp: new Date().toISOString()
      }, { status: 500 })
    }

    // Тест получения цен
    const testSymbols = ['BTCUSDT', 'ETHUSDT']
    const prices = await bybitClient.getTickers(testSymbols)
    
    // Тест получения баланса (если API ключи валидные)
    let balance = null
    try {
      balance = await bybitClient.getBalance()
    } catch (balanceError) {
      console.warn('Balance fetch failed (maybe read-only API keys):', balanceError)
    }

    return NextResponse.json({
      success: true,
      connection: 'OK',
      prices: prices,
      balance: balance,
      api_keys_configured: !!(process.env.BYBIT_API_KEY && process.env.BYBIT_API_SECRET),
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('Bybit API test failed:', error)
    
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
      api_keys_configured: !!(process.env.BYBIT_API_KEY && process.env.BYBIT_API_SECRET),
      timestamp: new Date().toISOString()
    }, { status: 500 })
  }
}
