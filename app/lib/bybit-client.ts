import crypto from 'crypto'

interface BybitTickerResponse {
  retCode: number
  retMsg: string
  result: {
    list: Array<{
      symbol: string
      lastPrice: string
      prevPrice24h: string
      price24hPcnt: string
      highPrice24h: string
      lowPrice24h: string
      volume24h: string
      turnover24h: string
    }>
  }
}

interface BybitPositionResponse {
  retCode: number
  retMsg: string
  result: {
    list: Array<{
      symbol: string
      side: string
      size: string
      positionValue: string
      entryPrice: string
      markPrice: string
      unrealisedPnl: string
      cumRealisedPnl: string
      leverage: string
      positionIdx: number
      tradeMode: number
    }>
  }
}

class BybitClient {
  private apiKey: string
  private apiSecret: string
  private baseUrl: string

  constructor() {
    this.apiKey = process.env.BYBIT_API_KEY || ''
    this.apiSecret = process.env.BYBIT_API_SECRET || ''
    this.baseUrl = 'https://api.bybit.com'
  }

  private generateSignature(params: string, timestamp: string): string {
    const data = timestamp + this.apiKey + '5000' + params
    return crypto.createHmac('sha256', this.apiSecret).update(data).digest('hex')
  }

  private async makeRequest(endpoint: string, params: Record<string, any> = {}): Promise<any> {
    if (!this.apiKey || !this.apiSecret) {
      throw new Error('Bybit API credentials not configured')
    }

    const timestamp = Date.now().toString()
    const queryString = new URLSearchParams(params).toString()
    const signature = this.generateSignature(queryString, timestamp)

    const headers = {
      'X-BAPI-API-KEY': this.apiKey,
      'X-BAPI-SIGN': signature,
      'X-BAPI-SIGN-TYPE': '2',
      'X-BAPI-TIMESTAMP': timestamp,
      'X-BAPI-RECV-WINDOW': '5000',
      'Content-Type': 'application/json'
    }

    const url = `${this.baseUrl}${endpoint}${queryString ? '?' + queryString : ''}`
    
    try {
      const response = await fetch(url, {
        method: 'GET',
        headers,
        cache: 'no-store'
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      
      if (data.retCode !== 0) {
        throw new Error(`Bybit API Error ${data.retCode}: ${data.retMsg}`)
      }

      return data
    } catch (error) {
      console.error('Bybit API request failed:', error)
      throw error
    }
  }

  // Получить live цены для символов
  async getTickers(symbols?: string[]): Promise<Record<string, number>> {
    try {
      const params: Record<string, any> = {
        category: 'linear' // USDT Perpetual
      }

      // Если символы не указаны, получаем все тикеры
      // Если указаны - делаем отдельные запросы для каждого (Bybit V5 API особенность)
      if (symbols && symbols.length > 0) {
        const priceMap: Record<string, number> = {}
        
        // Делаем параллельные запросы для каждого символа
        const pricePromises = symbols.map(async (symbol) => {
          try {
            const symbolParams = { ...params, symbol }
            const response: BybitTickerResponse = await this.makeRequest('/v5/market/tickers', symbolParams)
            
            if (response.result.list.length > 0) {
              return {
                symbol,
                price: parseFloat(response.result.list[0].lastPrice)
              }
            }
            return { symbol, price: 0 }
          } catch (error) {
            console.error(`Error fetching price for ${symbol}:`, error)
            return { symbol, price: 0 }
          }
        })
        
        const results = await Promise.all(pricePromises)
        
        results.forEach(({ symbol, price }) => {
          priceMap[symbol] = price
        })
        
        return priceMap
      }

      // Если символы не указаны, получаем все тикеры
      const response: BybitTickerResponse = await this.makeRequest('/v5/market/tickers', params)
      
      const priceMap: Record<string, number> = {}
      
      response.result.list.forEach(ticker => {
        priceMap[ticker.symbol] = parseFloat(ticker.lastPrice)
      })

      return priceMap
    } catch (error) {
      console.error('Error fetching Bybit tickers:', error)
      throw error
    }
  }

  // Получить одну цену для символа
  async getPrice(symbol: string): Promise<number> {
    try {
      const prices = await this.getTickers([symbol])
      return prices[symbol] || 0
    } catch (error) {
      console.error(`Error fetching price for ${symbol}:`, error)
      throw error
    }
  }

  // Получить позиции пользователя
  async getPositions(): Promise<any[]> {
    try {
      const params = {
        category: 'linear',
        settleCoin: 'USDT'
      }

      const response: BybitPositionResponse = await this.makeRequest('/v5/position/list', params)
      
      return response.result.list.filter(position => 
        parseFloat(position.size) > 0 // Только открытые позиции
      )
    } catch (error) {
      console.error('Error fetching Bybit positions:', error)
      throw error
    }
  }

  // Получить баланс аккаунта
  async getBalance(): Promise<Record<string, any>> {
    try {
      const params = {
        accountType: 'UNIFIED'
      }

      const response = await this.makeRequest('/v5/account/wallet-balance', params)
      
      const balance = response.result.list[0]
      const usdtCoin = balance.coin.find((c: any) => c.coin === 'USDT')
      
      return {
        totalBalance: parseFloat(usdtCoin?.walletBalance || '0'),
        availableBalance: parseFloat(usdtCoin?.availableBalance || '0'),
        unrealizedPnl: parseFloat(usdtCoin?.unrealisedPnl || '0')
      }
    } catch (error) {
      console.error('Error fetching Bybit balance:', error)
      throw error
    }
  }

  // Проверить подключение к API
  async testConnection(): Promise<boolean> {
    try {
      await this.makeRequest('/v5/market/time')
      return true
    } catch (error) {
      console.error('Bybit connection test failed:', error)
      return false
    }
  }
}

export const bybitClient = new BybitClient()
export default BybitClient
