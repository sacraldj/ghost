import { NextRequest, NextResponse } from 'next/server'
import sqlite3 from 'sqlite3'
import { open } from 'sqlite'

// GHOST-META
const VERSION = "2.0.0"
const AUTHOR = "GHOST Team"
const DESCRIPTION = "Улучшенный API для критических новостей с фильтрами и пагинацией"

interface CriticalNewsRow {
  id: number
  topic_hash: string
  source_name: string
  title: string
  content: string
  url: string
  symbol: string
  published_at: string
  detected_at: string
  sentiment: number
  urgency: number
  is_critical: boolean
  priority: number
  market_impact: number
  price_change: number
  price_change_period: number
  regulatory_news: boolean
  alert_sent: boolean
  alert_sent_at: string
  created_at: string
}

async function initDatabase() {
  const db = await open({
    filename: 'ghost_news.db',
    driver: sqlite3.Database
  })
  
  // Включение WAL режима
  await db.exec("PRAGMA journal_mode=WAL")
  await db.exec("PRAGMA synchronous=NORMAL")
  await db.exec("PRAGMA busy_timeout=5000")
  
  // Создание таблиц если не существуют
  await db.exec(`
    CREATE TABLE IF NOT EXISTS critical_news (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      topic_hash TEXT UNIQUE,
      source_name TEXT NOT NULL,
      title TEXT NOT NULL,
      content TEXT,
      url TEXT,
      symbol TEXT,
      published_at TIMESTAMP,
      detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      sentiment REAL DEFAULT 0.0,
      urgency REAL DEFAULT 1.0,
      is_critical BOOLEAN DEFAULT TRUE,
      priority INTEGER DEFAULT 1,
      market_impact REAL DEFAULT 0.0,
      price_change REAL DEFAULT 0.0,
      price_change_period INTEGER DEFAULT 60,
      regulatory_news BOOLEAN DEFAULT FALSE,
      alert_sent BOOLEAN DEFAULT FALSE,
      alert_sent_at TIMESTAMP,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
  `)
  
  // Создание индексов
  await db.exec("CREATE INDEX IF NOT EXISTS idx_critical_news_source_published ON critical_news(source_name, published_at DESC)")
  await db.exec("CREATE INDEX IF NOT EXISTS idx_critical_news_symbol_published ON critical_news(symbol, published_at)")
  await db.exec("CREATE INDEX IF NOT EXISTS idx_critical_news_topic_hash ON critical_news(topic_hash)")
  await db.exec("CREATE INDEX IF NOT EXISTS idx_critical_news_detected_at ON critical_news(detected_at)")
  await db.exec("CREATE INDEX IF NOT EXISTS idx_critical_news_priority ON critical_news(priority)")
  await db.exec("CREATE INDEX IF NOT EXISTS idx_critical_news_regulatory ON critical_news(regulatory_news)")
  
  return db
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    
    // Парсинг параметров запроса
    const limit = parseInt(searchParams.get('limit') || '20')
    const offset = parseInt(searchParams.get('offset') || '0')
    const symbols = searchParams.get('symbols')?.split(',').filter(Boolean)
    const sources = searchParams.get('sources')?.split(',').filter(Boolean)
    const since = searchParams.get('since')
    const severity = parseInt(searchParams.get('severity') || '0')
    const regulatoryOnly = searchParams.get('regulatory_only') === 'true'
    const priceChangeMin = parseFloat(searchParams.get('price_change_min') || '0')
    
    // Валидация параметров
    if (limit < 1 || limit > 100) {
      return NextResponse.json({ error: 'limit must be between 1 and 100' }, { status: 400 })
    }
    
    if (offset < 0) {
      return NextResponse.json({ error: 'offset must be non-negative' }, { status: 400 })
    }
    
    // Инициализация базы данных
    const db = await initDatabase()
    
    // Построение WHERE clause
    const conditions: string[] = []
    const values: any[] = []
    
    if (symbols && symbols.length > 0) {
      const placeholders = symbols.map(() => '?').join(',')
      conditions.push(`symbol IN (${placeholders})`)
      values.push(...symbols)
    }
    
    if (sources && sources.length > 0) {
      const placeholders = sources.map(() => '?').join(',')
      conditions.push(`source_name IN (${placeholders})`)
      values.push(...sources)
    }
    
    if (since) {
      conditions.push(`published_at >= ?`)
      values.push(since)
    }
    
    if (severity > 0) {
      conditions.push(`priority >= ?`)
      values.push(severity)
    }
    
    if (regulatoryOnly) {
      conditions.push(`regulatory_news = 1`)
    }
    
    if (priceChangeMin > 0) {
      conditions.push(`ABS(price_change) >= ?`)
      values.push(priceChangeMin)
    }
    
    const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : ''
    
    // Подсчет общего количества записей
    const countQuery = `SELECT COUNT(*) as total FROM critical_news ${whereClause}`
    const countResult = await db.get(countQuery, values)
    const totalCount = countResult?.total || 0
    
    // Основной запрос с пагинацией
    const query = `
      SELECT 
        id, topic_hash, source_name, title, content, url, symbol,
        published_at, detected_at, sentiment, urgency, is_critical,
        priority, market_impact, price_change, price_change_period,
        regulatory_news, alert_sent, alert_sent_at, created_at
      FROM critical_news 
      ${whereClause}
      ORDER BY published_at DESC, priority DESC, urgency DESC
      LIMIT ? OFFSET ?
    `
    
    const queryValues = [...values, limit, offset]
    const rows = await db.all<CriticalNewsRow[]>(query, queryValues)
    
    // Форматирование ответа
    const news = rows.map(row => ({
      id: row.id,
      topicHash: row.topic_hash,
      source: row.source_name,
      title: row.title,
      content: row.content,
      url: row.url,
      symbol: row.symbol,
      publishedAt: row.published_at,
      detectedAt: row.detected_at,
      sentiment: row.sentiment,
      urgency: row.urgency,
      isCritical: row.is_critical,
      priority: row.priority,
      marketImpact: row.market_impact,
      priceChange: row.price_change,
      priceChangePeriod: row.price_change_period,
      regulatoryNews: row.regulatory_news,
      alertSent: row.alert_sent,
      alertSentAt: row.alert_sent_at,
      createdAt: row.created_at
    }))
    
    return NextResponse.json({
      news,
      pagination: {
        total: totalCount,
        limit,
        offset,
        hasMore: offset + limit < totalCount
      },
      filters: {
        symbols,
        sources,
        since,
        severity,
        regulatoryOnly,
        priceChangeMin
      },
      metadata: {
        version: VERSION,
        timestamp: new Date().toISOString(),
        count: news.length,
        totalCount
      }
    })
    
  } catch (error) {
    console.error('Critical News API v2 error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

// POST метод для создания тестовых данных
export async function POST(request: NextRequest) {
  try {
    const db = await initDatabase()
    
    // Создание тестовых критических новостей
    const testNews = [
      {
        topic_hash: 'test_hash_1',
        source_name: 'binance_price',
        title: '🚨 BTC price 📈 5.2%',
        content: 'Bitcoin price surged 5.2% to $45,000',
        url: 'https://binance.com/en/trade/BTCUSDT',
        symbol: 'btc',
        published_at: new Date().toISOString(),
        sentiment: 0.8,
        urgency: 1.0,
        is_critical: true,
        priority: 1,
        market_impact: 0.052,
        price_change: 5.2,
        price_change_period: 60,
        regulatory_news: false
      },
      {
        topic_hash: 'test_hash_2',
        source_name: 'breaking_news',
        title: '📰 SEC announces new crypto regulations',
        content: 'The SEC has announced new cryptocurrency regulations',
        url: 'https://sec.gov/news',
        symbol: null,
        published_at: new Date().toISOString(),
        sentiment: -0.3,
        urgency: 1.0,
        is_critical: true,
        priority: 1,
        market_impact: 0.8,
        price_change: 0.0,
        price_change_period: 60,
        regulatory_news: true
      }
    ]
    
    for (const news of testNews) {
      await db.run(`
        INSERT OR REPLACE INTO critical_news (
          topic_hash, source_name, title, content, url, symbol,
          published_at, sentiment, urgency, is_critical, priority,
          market_impact, price_change, price_change_period, regulatory_news
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `, [
        news.topic_hash, news.source_name, news.title, news.content,
        news.url, news.symbol, news.published_at, news.sentiment,
        news.urgency, news.is_critical, news.priority, news.market_impact,
        news.price_change, news.price_change_period, news.regulatory_news
      ])
    }
    
    return NextResponse.json({
      message: 'Test data created successfully',
      count: testNews.length
    })
    
  } catch (error) {
    console.error('Error creating test data:', error)
    return NextResponse.json(
      { error: 'Failed to create test data' },
      { status: 500 }
    )
  }
}
