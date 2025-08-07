#!/usr/bin/env node

const { PrismaClient } = require('@prisma/client')
const { createClient } = require('@supabase/supabase-js')

const prisma = new PrismaClient()

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY
)

async function initDatabase() {
  console.log('🚀 Инициализация базы данных GHOST...')
  
  try {
    // Генерируем Prisma клиент
    console.log('📦 Генерация Prisma клиента...')
    const { execSync } = require('child_process')
    execSync('npx prisma generate', { stdio: 'inherit' })
    
    // Отправляем схему в Supabase
    console.log('📤 Отправка схемы в Supabase...')
    execSync('npx prisma db push', { stdio: 'inherit' })
    
    console.log('✅ База данных успешно инициализирована!')
    
    // Создаем тестовые данные
    await createTestData()
    
  } catch (error) {
    console.error('❌ Ошибка при инициализации базы данных:', error)
    process.exit(1)
  } finally {
    await prisma.$disconnect()
  }
}

async function createTestData() {
  console.log('📝 Создание тестовых данных...')
  
  try {
    // Создаем тестовые новости
    const testNews = [
      {
        title: 'Bitcoin ETF Approval Expected This Week',
        content: 'The SEC is expected to approve the first Bitcoin ETF this week, which could lead to significant institutional adoption.',
        url: 'https://example.com/bitcoin-etf-approval',
        source: 'Reuters',
        published_at: new Date(),
        category: 'regulation',
        influence_score: 0.95,
        market_impact: 0.9,
        sentiment_score: 0.8,
        urgency_score: 0.9,
        reach_score: 0.95,
        credibility_score: 0.95,
        keywords: ['bitcoin', 'etf', 'sec', 'approval'],
        entities: ['SEC', 'Bitcoin', 'ETF'],
        summary: 'Major Bitcoin ETF approval expected, bullish for BTC',
        is_important: true,
        priority_level: 10
      },
      {
        title: 'Ethereum Layer 2 Solutions See Record Growth',
        content: 'Ethereum Layer 2 solutions are experiencing unprecedented growth, with TVL reaching new highs.',
        url: 'https://example.com/ethereum-layer2-growth',
        source: 'CoinDesk',
        published_at: new Date(),
        category: 'technology',
        influence_score: 0.85,
        market_impact: 0.8,
        sentiment_score: 0.7,
        urgency_score: 0.7,
        reach_score: 0.8,
        credibility_score: 0.85,
        keywords: ['ethereum', 'layer2', 'defi', 'growth'],
        entities: ['Ethereum', 'Layer 2', 'DeFi'],
        summary: 'Ethereum L2 growth signals strong fundamentals',
        is_important: true,
        priority_level: 8
      },
      {
        title: 'Federal Reserve Signals Potential Rate Cuts',
        content: 'The Federal Reserve has indicated potential interest rate cuts in the coming months.',
        url: 'https://example.com/fed-rate-cuts',
        source: 'Bloomberg',
        published_at: new Date(),
        category: 'macro',
        influence_score: 0.9,
        market_impact: 0.7,
        sentiment_score: 0.6,
        urgency_score: 0.8,
        reach_score: 0.9,
        credibility_score: 0.95,
        keywords: ['federal reserve', 'interest rates', 'macro'],
        entities: ['Federal Reserve', 'Interest Rates'],
        summary: 'Fed rate cuts could be bullish for crypto markets',
        is_important: true,
        priority_level: 9
      }
    ]
    
    for (const news of testNews) {
      await prisma.newsEvent.create({
        data: news
      })
    }
    
    console.log(`✅ Создано ${testNews.length} тестовых новостей`)
    
    // Создаем тестовые твиты
    const testTweets = [
      {
        tweet_id: '1234567890',
        author: 'elonmusk',
        author_name: 'Elon Musk',
        text: 'Bitcoin is the future of money',
        created_at: new Date(),
        influence_score: 0.98,
        sentiment_score: 0.8,
        keyword_score: 0.9,
        engagement_score: 0.95,
        retweet_count: 50000,
        like_count: 200000,
        reply_count: 5000,
        quote_count: 3000,
        categories: ['crypto', 'bitcoin'],
        keywords: ['bitcoin', 'money', 'future']
      },
      {
        tweet_id: '1234567891',
        author: 'VitalikButerin',
        author_name: 'Vitalik Buterin',
        text: 'Ethereum scaling solutions are making great progress',
        created_at: new Date(),
        influence_score: 0.95,
        sentiment_score: 0.7,
        keyword_score: 0.8,
        engagement_score: 0.85,
        retweet_count: 15000,
        like_count: 80000,
        reply_count: 2000,
        quote_count: 1500,
        categories: ['crypto', 'ethereum'],
        keywords: ['ethereum', 'scaling', 'progress']
      }
    ]
    
    for (const tweet of testTweets) {
      await prisma.influentialTweet.create({
        data: tweet
      })
    }
    
    console.log(`✅ Создано ${testTweets.length} тестовых твитов`)
    
    // Создаем рыночные данные
    const marketData = [
      {
        symbol: 'BTC',
        price: 43250.50,
        volume: 28450000000,
        market_cap: 850000000000,
        rsi: 65.5,
        macd: 0.8,
        bollinger_upper: 44500,
        bollinger_lower: 42000,
        sentiment_score: 0.75,
        news_count: 15,
        positive_news: 12,
        negative_news: 2
      },
      {
        symbol: 'ETH',
        price: 2650.30,
        volume: 15800000000,
        market_cap: 320000000000,
        rsi: 58.2,
        macd: 0.6,
        bollinger_upper: 2750,
        bollinger_lower: 2550,
        sentiment_score: 0.8,
        news_count: 12,
        positive_news: 10,
        negative_news: 1
      }
    ]
    
    for (const data of marketData) {
      await prisma.marketData.create({
        data: data
      })
    }
    
    console.log(`✅ Создано ${marketData.length} записей рыночных данных`)
    
  } catch (error) {
    console.error('❌ Ошибка при создании тестовых данных:', error)
  }
}

// Запускаем инициализацию
if (require.main === module) {
  initDatabase()
}

module.exports = { initDatabase }
