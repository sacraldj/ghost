"use client"

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'

interface NewsItem {
  id: string
  title: string
  content: string
  source: string
  published_at: string
  sentiment: 'positive' | 'negative' | 'neutral'
  impact_score: number
  price_correlation: number
  related_symbols: string[]
  event_type: 'announcement' | 'regulatory' | 'technical' | 'market' | 'adoption'
}

interface PricePoint {
  timestamp: string
  price: number
  volume: number
  change_percent: number
}

interface MarketEvent {
  timestamp: string
  price: number
  news_id: string
  title: string
  impact: 'high' | 'medium' | 'low'
  direction: 'up' | 'down'
}

const NewsAnalyticsTab: React.FC = () => {
  const [news, setNews] = useState<NewsItem[]>([])
  const [priceData, setPriceData] = useState<PricePoint[]>([])
  const [marketEvents, setMarketEvents] = useState<MarketEvent[]>([])
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT')
  const [timeframe, setTimeframe] = useState('24h')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadNewsData()
    loadPriceData()
  }, [selectedSymbol, timeframe])

  const loadNewsData = async () => {
    try {
      console.log(`📰 Loading news data for ${selectedSymbol} (${timeframe})...`)
      const response = await fetch(`/api/news-analytics?symbol=${selectedSymbol}&timeframe=${timeframe}`)
      const data = await response.json()
      
      console.log('📊 News analytics data received:', data)
      
      if (data.news && data.news.length > 0) {
        setNews(data.news)
        setMarketEvents(data.events || [])
        console.log(`✅ Loaded ${data.news.length} news items from ${data.source}`)
      } else {
        console.warn('⚠️ No news data received, using fallback')
        setNews(mockNewsData)
        setMarketEvents(mockMarketEvents)
      }
    } catch (error) {
      console.error('❌ Error loading news:', error)
      // Моковые данные для демонстрации
      setNews(mockNewsData)
      setMarketEvents(mockMarketEvents)
    }
  }

  const loadPriceData = async () => {
    try {
      console.log(`📈 Loading price data for ${selectedSymbol}...`)
      const response = await fetch(`/api/market-data?symbol=${selectedSymbol}&timeframe=1H&limit=24`)
      const data = await response.json()
      
      console.log('💰 Price data received:', data)
      
      if (data.price_data && data.price_data.length > 0) {
        // Конвертируем данные в нужный формат
        const prices = data.price_data.map((point: any) => ({
          timestamp: point.timestamp,
          price: point.close,
          volume: point.volume,
          change_percent: ((point.close - point.open) / point.open) * 100
        }))
        setPriceData(prices)
        console.log(`✅ Loaded ${prices.length} price points from GHOST Market Data`)
      } else {
        console.warn('⚠️ No price data received, using fallback')
        setPriceData(mockPriceData)
      }
    } catch (error) {
      console.error('❌ Error loading price data:', error)
      // Моковые данные для демонстрации
      setPriceData(mockPriceData)
    }
    setLoading(false)
  }

  const getSentimentBadge = (sentiment: string) => {
    switch (sentiment) {
      case 'positive':
        return <Badge className="bg-green-500 text-white">📈 Позитивные</Badge>
      case 'negative':
        return <Badge className="bg-red-500 text-white">📉 Негативные</Badge>
      default:
        return <Badge className="bg-gray-500 text-white">📊 Нейтральные</Badge>
    }
  }

  const getEventTypeBadge = (type: string) => {
    const types = {
      announcement: { icon: '📢', label: 'Анонсы', color: 'bg-blue-500' },
      regulatory: { icon: '⚖️', label: 'Регуляция', color: 'bg-purple-500' },
      technical: { icon: '🔧', label: 'Технические', color: 'bg-orange-500' },
      market: { icon: '📊', label: 'Рыночные', color: 'bg-green-500' },
      adoption: { icon: '🚀', label: 'Внедрение', color: 'bg-yellow-500' }
    }
    
    const eventType = types[type as keyof typeof types] || types.market
    return (
      <Badge className={`${eventType.color} text-white`}>
        {eventType.icon} {eventType.label}
      </Badge>
    )
  }

  const getImpactColor = (score: number) => {
    if (score >= 8) return 'text-red-400'
    if (score >= 6) return 'text-orange-400'
    if (score >= 4) return 'text-yellow-400'
    return 'text-gray-400'
  }

  // Моковые данные для демонстрации
  const mockNewsData: NewsItem[] = [
    {
      id: '1',
      title: '🇺🇸 Министр финансов США: Мы не собираемся покупать криптовалюту в наши резервы',
      content: 'Министр финансов США заявил о планах использовать конфискованные активы и сохранить золото как средство накопления...',
      source: 'Crypto Headlines',
      published_at: '2025-08-15T15:31:00Z',
      sentiment: 'negative',
      impact_score: 8.5,
      price_correlation: -0.75,
      related_symbols: ['BTCUSDT', 'ETHUSDT'],
      event_type: 'regulatory'
    },
    {
      id: '2',
      title: '🚀 Ethereum: Артур Хейс заявил, что закупает ETH и обещает больше не фиксировать прибыль',
      content: 'Основатель BitMEX объявил о крупных покупках ETH на сумму 6.85 млн долларов...',
      source: 'CryptoAttack',
      published_at: '2025-08-15T17:37:00Z',
      sentiment: 'positive',
      impact_score: 7.2,
      price_correlation: 0.68,
      related_symbols: ['ETHUSDT'],
      event_type: 'market'
    },
    {
      id: '3',
      title: '📊 Стоимость крипто-активов Виталика Бутерина превысила 1 млрд $',
      content: 'Портфель основателя Ethereum достиг исторического максимума на фоне роста цены ETH...',
      source: 'CryptoNews',
      published_at: '2025-08-15T16:25:00Z',
      sentiment: 'positive',
      impact_score: 6.8,
      price_correlation: 0.45,
      related_symbols: ['ETHUSDT'],
      event_type: 'market'
    },
    {
      id: '4',
      title: '🇸🇻 Инвестиционные банки Сальвадора теперь могут держать BTC в балансах',
      content: 'Новое законодательство позволяет банкам предоставлять криптовалютные услуги квалифицированным инвесторам...',
      source: 'Bitcoin Magazine',
      published_at: '2025-08-15T14:16:00Z',
      sentiment: 'positive',
      impact_score: 5.5,
      price_correlation: 0.32,
      related_symbols: ['BTCUSDT'],
      event_type: 'adoption'
    }
  ]

  const mockMarketEvents: MarketEvent[] = [
    {
      timestamp: '2025-08-15T15:31:00Z',
      price: 42850,
      news_id: '1',
      title: 'Заявление министра финансов США',
      impact: 'high',
      direction: 'down'
    },
    {
      timestamp: '2025-08-15T17:37:00Z',
      price: 43200,
      news_id: '2',
      title: 'Покупки ETH от Артура Хейса',
      impact: 'medium',
      direction: 'up'
    }
  ]

  const mockPriceData: PricePoint[] = [
    { timestamp: '2025-08-15T12:00:00Z', price: 43500, volume: 125000, change_percent: 0.5 },
    { timestamp: '2025-08-15T13:00:00Z', price: 43300, volume: 98000, change_percent: -0.46 },
    { timestamp: '2025-08-15T14:00:00Z', price: 43100, volume: 156000, change_percent: -0.46 },
    { timestamp: '2025-08-15T15:00:00Z', price: 42850, volume: 234000, change_percent: -0.58 },
    { timestamp: '2025-08-15T16:00:00Z', price: 42950, volume: 187000, change_percent: 0.23 },
    { timestamp: '2025-08-15T17:00:00Z', price: 43200, volume: 145000, change_percent: 0.58 }
  ]

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-700 rounded mb-4"></div>
          <div className="grid lg:grid-cols-2 gap-6">
            <div className="h-96 bg-gray-700 rounded"></div>
            <div className="h-96 bg-gray-700 rounded"></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6 bg-black text-white">
      {/* Заголовок и фильтры */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white mb-2">📰 Новости и анализ рынка</h1>
          <p className="text-gray-400">Корреляция новостей с движениями цены в реальном времени</p>
        </div>
        
        <div className="flex items-center space-x-4">
          <select 
            value={selectedSymbol}
            onChange={(e) => setSelectedSymbol(e.target.value)}
            className="bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white"
          >
            <option value="BTCUSDT">Bitcoin (BTC)</option>
            <option value="ETHUSDT">Ethereum (ETH)</option>
            <option value="ADAUSDT">Cardano (ADA)</option>
            <option value="SOLUSDT">Solana (SOL)</option>
          </select>
          
          <select 
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            className="bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white"
          >
            <option value="1h">1 час</option>
            <option value="4h">4 часа</option>
            <option value="24h">24 часа</option>
            <option value="7d">7 дней</option>
          </select>
        </div>
      </div>

      {/* Основной контент */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* График рынка с событиями */}
        <Card className="bg-gray-900 border-gray-800">
          <CardHeader>
            <CardTitle className="text-white flex items-center space-x-2">
              <span>📈</span>
              <span>График {selectedSymbol}</span>
              <Badge className="bg-green-500 text-white ml-2">LIVE</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="relative h-80 bg-gray-800 rounded-lg p-4">
              {/* Простой график (в реальном проекте здесь будет TradingView или Chart.js) */}
              <div className="absolute inset-4">
                <div className="text-center text-gray-400 mt-32">
                  <div className="text-lg font-bold text-white mb-2">
                    ${priceData[priceData.length - 1]?.price.toLocaleString() || '43,200'}
                  </div>
                  <div className="text-sm">Текущая цена {selectedSymbol}</div>
                  <div className="mt-4 text-xs">
                    📊 График с маркерами событий будет здесь
                  </div>
                </div>
                
                {/* Маркеры событий */}
                <div className="absolute top-4 right-4 space-y-2">
                  {marketEvents.map((event) => (
                    <div 
                      key={event.news_id}
                      className={`px-2 py-1 rounded text-xs ${
                        event.direction === 'up' 
                          ? 'bg-green-500 text-white' 
                          : 'bg-red-500 text-white'
                      }`}
                    >
                      {event.direction === 'up' ? '📈' : '📉'} {new Date(event.timestamp).toLocaleTimeString('ru-RU')}
                    </div>
                  ))}
                </div>
              </div>
            </div>
            
            {/* Статистика корреляции */}
            <div className="mt-4 grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-lg font-bold text-white">85%</div>
                <div className="text-xs text-gray-400">Точность прогнозов</div>
              </div>
              <div>
                <div className="text-lg font-bold text-green-400">+2.3%</div>
                <div className="text-xs text-gray-400">Влияние новостей</div>
              </div>
              <div>
                <div className="text-lg font-bold text-white">12</div>
                <div className="text-xs text-gray-400">Событий за 24ч</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Новости с анализом влияния */}
        <Card className="bg-gray-900 border-gray-800">
          <CardHeader>
            <CardTitle className="text-white flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span>📰</span>
                <span>Новости и события</span>
              </div>
              <Badge className="bg-blue-500 text-white">
                {news.length} новостей
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 max-h-80 overflow-y-auto">
              {news.map((item) => (
                <div key={item.id} className="border-b border-gray-800 pb-4">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <h3 className="text-white font-medium text-sm leading-tight mb-2">
                        {item.title}
                      </h3>
                      
                      <div className="flex items-center space-x-2 mb-2">
                        {getSentimentBadge(item.sentiment)}
                        {getEventTypeBadge(item.event_type)}
                      </div>
                      
                      <div className="text-xs text-gray-400 mb-2">
                        {item.source} • {new Date(item.published_at).toLocaleString('ru-RU')}
                      </div>
                    </div>
                    
                    <div className="text-right ml-4">
                      <div className={`text-sm font-bold ${getImpactColor(item.impact_score)}`}>
                        {item.impact_score.toFixed(1)}/10
                      </div>
                      <div className="text-xs text-gray-400">Влияние</div>
                    </div>
                  </div>
                  
                  {/* Анализ корреляции */}
                  <div className="bg-gray-800 rounded-lg p-3 mt-2">
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center space-x-4">
                        <div>
                          <span className="text-gray-400">Корреляция цены: </span>
                          <span className={`font-medium ${
                            item.price_correlation > 0 ? 'text-green-400' : 'text-red-400'
                          }`}>
                            {item.price_correlation > 0 ? '+' : ''}{(item.price_correlation * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-400">Символы: </span>
                          <span className="text-white">{item.related_symbols.join(', ')}</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="mt-2 text-xs text-gray-300">
                      💡 <strong>Анализ:</strong> {
                        item.sentiment === 'positive' 
                          ? 'Позитивная новость может поддержать рост цены'
                          : item.sentiment === 'negative'
                          ? 'Негативная новость может вызвать снижение цены'
                          : 'Нейтральная новость, влияние на цену минимально'
                      }
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Дополнительная аналитика */}
      <div className="grid lg:grid-cols-3 gap-6">
        <Card className="bg-gray-900 border-gray-800">
          <CardHeader>
            <CardTitle className="text-white text-sm">🎯 Прогноз на основе новостей</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-400 mb-2">📈 РОСТ</div>
              <div className="text-sm text-gray-400 mb-4">Вероятность: 73%</div>
              <div className="text-xs text-gray-300">
                На основе анализа 12 новостей за последние 24 часа
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gray-900 border-gray-800">
          <CardHeader>
            <CardTitle className="text-white text-sm">⚡ Сильнейшие события</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-400">Заявление минфина США</span>
                <span className="text-red-400">-3.2%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Покупки Артура Хейса</span>
                <span className="text-green-400">+1.8%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Новости Сальвадора</span>
                <span className="text-green-400">+0.9%</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gray-900 border-gray-800">
          <CardHeader>
            <CardTitle className="text-white text-sm">📊 Настроения рынка</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-gray-400">Позитивные</span>
                  <span className="text-green-400">60%</span>
                </div>
                <div className="w-full bg-gray-800 rounded-full h-2">
                  <div className="bg-green-500 h-2 rounded-full" style={{width: '60%'}}></div>
                </div>
              </div>
              
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-gray-400">Негативные</span>
                  <span className="text-red-400">25%</span>
                </div>
                <div className="w-full bg-gray-800 rounded-full h-2">
                  <div className="bg-red-500 h-2 rounded-full" style={{width: '25%'}}></div>
                </div>
              </div>
              
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-gray-400">Нейтральные</span>
                  <span className="text-gray-400">15%</span>
                </div>
                <div className="w-full bg-gray-800 rounded-full h-2">
                  <div className="bg-gray-500 h-2 rounded-full" style={{width: '15%'}}></div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default NewsAnalyticsTab
