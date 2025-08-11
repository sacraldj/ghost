import { NextRequest, NextResponse } from 'next/server'
import sqlite3 from 'sqlite3'
import path from 'path'

// Путь к базе данных новостей
const DB_PATH = path.join(process.cwd(), 'ghost_news.db')

// Функция для инициализации базы данных
function initDatabase() {
  return new Promise((resolve, reject) => {
    const db = new sqlite3.Database(DB_PATH)
    
    db.serialize(() => {
      // Создание таблицы новостей
      db.run(`
        CREATE TABLE IF NOT EXISTS news_items (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          item_type TEXT NOT NULL,
          source_name TEXT,
          author TEXT,
          title TEXT,
          content TEXT,
          published_at TIMESTAMP,
          url TEXT,
          external_id TEXT,
          influence REAL DEFAULT 0.0,
          sentiment REAL DEFAULT 0.0,
          urgency REAL DEFAULT 0.0,
          source_trust REAL DEFAULT 0.5,
          source_type TEXT DEFAULT 'unknown',
          category TEXT,
          keywords TEXT,
          entities TEXT,
          summary TEXT,
          is_important BOOLEAN DEFAULT FALSE,
          priority_level INTEGER DEFAULT 1,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          content_hash TEXT,
          UNIQUE(item_type, external_id, source_name, title, published_at)
        )
      `)
      
      // Создание индексов
      db.run("CREATE INDEX IF NOT EXISTS idx_published_at ON news_items(published_at)")
      db.run("CREATE INDEX IF NOT EXISTS idx_source_name ON news_items(source_name)")
      db.run("CREATE INDEX IF NOT EXISTS idx_sentiment ON news_items(sentiment)")
      db.run("CREATE INDEX IF NOT EXISTS idx_influence ON news_items(influence)")
      db.run("CREATE INDEX IF NOT EXISTS idx_urgency ON news_items(urgency)")
      
      // Таблица доверия к источникам
      db.run(`
        CREATE TABLE IF NOT EXISTS source_trust (
          source_name TEXT PRIMARY KEY,
          trust_score REAL DEFAULT 0.5,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
      `)
      
      // Вставка тестовых данных если таблица пустая
      db.get("SELECT COUNT(*) as count FROM news_items", (err, row) => {
        if (err) {
          reject(err)
          return
        }
        
        if (row.count === 0) {
          // Добавляем тестовые новости
          const testNews = [
            {
              item_type: 'news',
              source_name: 'CoinTelegraph',
              author: 'Test Author',
              title: 'Bitcoin reaches new all-time high as institutional adoption grows',
              content: 'Bitcoin has reached a new all-time high as institutional adoption continues to grow...',
              published_at: new Date().toISOString(),
              url: 'https://example.com/news1',
              external_id: 'test1',
              influence: 0.8,
              sentiment: 0.7,
              urgency: 0.6,
              source_trust: 0.75,
              source_type: 'crypto_media',
              is_important: true,
              priority_level: 1
            },
            {
              item_type: 'news',
              source_name: 'Reuters',
              author: 'Financial Reporter',
              title: 'Ethereum upgrade boosts DeFi ecosystem development',
              content: 'The latest Ethereum upgrade has significantly boosted the DeFi ecosystem...',
              published_at: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
              url: 'https://example.com/news2',
              external_id: 'test2',
              influence: 0.9,
              sentiment: 0.6,
              urgency: 0.5,
              source_trust: 0.95,
              source_type: 'media',
              is_important: true,
              priority_level: 2
            },
            {
              item_type: 'news',
              source_name: 'CryptoNews',
              author: 'Crypto Analyst',
              title: 'Market shows mixed signals as regulatory uncertainty persists',
              content: 'The crypto market is showing mixed signals as regulatory uncertainty continues...',
              published_at: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
              url: 'https://example.com/news3',
              external_id: 'test3',
              influence: 0.6,
              sentiment: -0.2,
              urgency: 0.4,
              source_trust: 0.65,
              source_type: 'crypto_media',
              is_important: false,
              priority_level: 3
            }
          ]
          
          const stmt = db.prepare(`
            INSERT INTO news_items(
              item_type, source_name, author, title, content, 
              published_at, url, external_id, influence, sentiment,
              urgency, source_trust, source_type, is_important, priority_level
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
          `)
          
          testNews.forEach(news => {
            stmt.run(
              news.item_type, news.source_name, news.author, news.title,
              news.content, news.published_at, news.url, news.external_id,
              news.influence, news.sentiment, news.urgency, news.source_trust,
              news.source_type, news.is_important, news.priority_level
            )
          })
          
          stmt.finalize()
        }
        
        db.close()
        resolve(true)
      })
    })
  })
}

export async function GET(request: NextRequest) {
  try {
    // Инициализируем базу данных
    await initDatabase()
    
    const { searchParams } = new URL(request.url)
    const limit = parseInt(searchParams.get('limit') || '50')
    const minutes = parseInt(searchParams.get('minutes') || '60')
    const source = searchParams.get('source')
    const sentiment = searchParams.get('sentiment') // 'positive', 'negative', 'neutral'

    // Подключение к базе данных
    const db = new sqlite3.Database(DB_PATH)
    
    return new Promise((resolve, reject) => {
      let query = `
        SELECT 
          id, item_type, source_name, author, title, content,
          published_at, url, external_id, influence, sentiment,
          urgency, source_trust, source_type, category,
          is_important, priority_level, created_at
        FROM news_items 
        WHERE published_at >= datetime('now', '-${minutes} minutes')
      `
      
      const params: any[] = []
      
      if (source) {
        query += ' AND source_name = ?'
        params.push(source)
      }
      
      if (sentiment) {
        switch (sentiment) {
          case 'positive':
            query += ' AND sentiment > 0.1'
            break
          case 'negative':
            query += ' AND sentiment < -0.1'
            break
          case 'neutral':
            query += ' AND sentiment BETWEEN -0.1 AND 0.1'
            break
        }
      }
      
      query += ' ORDER BY published_at DESC, priority_level DESC, influence DESC LIMIT ?'
      params.push(limit)

      db.all(query, params, (err, rows) => {
        if (err) {
          console.error('Database error:', err)
          resolve(NextResponse.json({ error: 'Database error' }, { status: 500 }))
          return
        }

        // Преобразование данных
        const news = rows.map(row => ({
          id: row.id,
          type: row.item_type,
          source: row.source_name,
          author: row.author,
          title: row.title,
          content: row.content,
          publishedAt: row.published_at,
          url: row.url,
          influence: row.influence,
          sentiment: row.sentiment,
          urgency: row.urgency,
          sourceTrust: row.source_trust,
          sourceType: row.source_type,
          category: row.category,
          isImportant: Boolean(row.is_important),
          priorityLevel: row.priority_level,
          createdAt: row.created_at
        }))

        resolve(NextResponse.json({ 
          news,
          count: news.length,
          timestamp: new Date().toISOString()
        }))
      })
    })

  } catch (error) {
    console.error('API error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
