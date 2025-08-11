import { NextRequest, NextResponse } from 'next/server'
import sqlite3 from 'sqlite3'
import path from 'path'

// Путь к базе данных новостей
const DB_PATH = path.join(process.cwd(), 'ghost_news.db')

// Тип для строки из базы данных
interface CriticalNewsRow {
  id: number
  source_name: string
  title: string
  content: string
  url: string
  published_at: string
  sentiment: number
  urgency: number
  is_critical: number
  priority: number
  market_impact: number
}

// Функция для инициализации базы данных
function initCriticalDatabase() {
  return new Promise((resolve, reject) => {
    const db = new sqlite3.Database(DB_PATH)
    
    db.serialize(() => {
      // Создание таблицы критических новостей
      db.run(`
        CREATE TABLE IF NOT EXISTS critical_news (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          source_name TEXT,
          title TEXT,
          content TEXT,
          url TEXT,
          published_at TIMESTAMP,
          sentiment REAL DEFAULT 0.0,
          urgency REAL DEFAULT 1.0,
          is_critical BOOLEAN DEFAULT TRUE,
          priority INTEGER DEFAULT 1,
          market_impact REAL DEFAULT 0.0,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
      `)
      
      // Создание таблицы рыночных данных
      db.run(`
        CREATE TABLE IF NOT EXISTS market_data (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          symbol TEXT,
          price REAL,
          change_24h REAL,
          volume REAL,
          timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
      `)
      
      // Создание таблицы критических алертов
      db.run(`
        CREATE TABLE IF NOT EXISTS critical_alerts (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          alert_type TEXT,
          message TEXT,
          severity INTEGER DEFAULT 1,
          is_processed BOOLEAN DEFAULT FALSE,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
      `)
      
      // Индексы для быстрого поиска
      db.run("CREATE INDEX IF NOT EXISTS idx_critical_timestamp ON critical_news(published_at)")
      db.run("CREATE INDEX IF NOT EXISTS idx_critical_source ON critical_news(source_name)")
      db.run("CREATE INDEX IF NOT EXISTS idx_market_symbol ON market_data(symbol)")
      db.run("CREATE INDEX IF NOT EXISTS idx_market_timestamp ON market_data(timestamp)")
      
      db.close()
      resolve(true)
    })
  })
}

export async function GET(request: NextRequest) {
  try {
    // Инициализируем базу данных
    await initCriticalDatabase()
    
    const { searchParams } = new URL(request.url)
    const limit = parseInt(searchParams.get('limit') || '10')
    const minutes = parseInt(searchParams.get('minutes') || '5') // По умолчанию 5 минут для критических
    const source = searchParams.get('source')
    const severity = searchParams.get('severity') // 'critical', 'urgent', 'breaking'

    // Подключение к базе данных
    const db = new sqlite3.Database(DB_PATH)
    
    return new Promise((resolve, reject) => {
      let query = `
        SELECT 
          id, source_name, title, content, url, published_at,
          sentiment, urgency, is_critical, priority, market_impact
        FROM critical_news 
        WHERE published_at >= datetime('now', '-${minutes} minutes')
      `
      
      const params: any[] = []
      
      if (source) {
        query += ' AND source_name = ?'
        params.push(source)
      }
      
      if (severity) {
        switch (severity) {
          case 'critical':
            query += ' AND (title LIKE "%BREAKING%" OR title LIKE "%URGENT%" OR title LIKE "%CRITICAL%")'
            break
          case 'urgent':
            query += ' AND urgency > 0.8'
            break
          case 'breaking':
            query += ' AND title LIKE "%BREAKING%"'
            break
        }
      }
      
      query += ' ORDER BY published_at DESC, priority ASC, urgency DESC LIMIT ?'
      params.push(limit)

      db.all(query, params, (err, rows: CriticalNewsRow[]) => {
        if (err) {
          console.error('Database error:', err)
          resolve(NextResponse.json({ error: 'Database error' }, { status: 500 }))
          return
        }

        // Преобразование данных
        const criticalNews = rows.map(row => ({
          id: row.id,
          source: row.source_name,
          title: row.title,
          content: row.content,
          url: row.url,
          publishedAt: row.published_at,
          sentiment: row.sentiment,
          urgency: row.urgency,
          isCritical: Boolean(row.is_critical),
          priority: row.priority,
          marketImpact: row.market_impact
        }))

        resolve(NextResponse.json({ 
          criticalNews,
          count: criticalNews.length,
          timestamp: new Date().toISOString(),
          message: criticalNews.length > 0 ? 'Критические новости обнаружены!' : 'Критических новостей нет'
        }))
      })
    })

  } catch (error) {
    console.error('API error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
