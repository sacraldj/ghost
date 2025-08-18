#!/usr/bin/env node

/**
 * GHOST Virtual Trades Test Script
 * Тестирует создание и получение виртуальных сделок
 */

const API_BASE = 'http://localhost:3000/api'

// Тестовые сигналы
const testSignals = [
  {
    symbol: 'YGGUSDT',
    side: 'LONG',
    entryType: 'zone',
    entryMin: 0.6200,
    entryMax: 0.6350,
    tp1: 0.6850,
    tp2: 0.7200,
    sl: 0.5950,
    source: 'tg_binance_killers',
    sourceType: 'telegram',
    sourceName: 'Binance Killers',
    originalText: '🎯 YGGUSDT LONG\n📍 Entry: 0.6200-0.6350\n🎯 TP1: 0.6850\n🎯 TP2: 0.7200\n🛑 SL: 0.5950\n⚡ Leverage: 5-10x',
    signalReason: 'Breakout from consolidation',
    sourceLeverage: '5-10x',
    leverage: 10,
    marginUsd: 100
  },
  {
    symbol: 'BTCUSDT',
    side: 'SHORT',
    entryType: 'exact',
    entryMin: 115500,
    entryMax: 115500,
    tp1: 114200,
    tp2: 112800,
    sl: 116800,
    source: 'ghost_signals',
    sourceType: 'manual',
    sourceName: 'GHOST Signals',
    originalText: 'Manual BTC SHORT signal based on resistance rejection',
    signalReason: 'Strong resistance at 115500, expecting pullback',
    leverage: 20,
    marginUsd: 200
  },
  {
    symbol: 'ETHUSDT', 
    side: 'LONG',
    entryType: 'zone',
    entryMin: 4200,
    entryMax: 4250,
    tp1: 4380,
    tp2: 4520,
    sl: 4150,
    source: 'tg_crypto_pro',
    sourceType: 'telegram',
    sourceName: 'Crypto Pro Signals',
    originalText: '🚀 ETHUSDT LONG\n📈 Entry Zone: 4200-4250\n🎯 TP1: 4380 (50%)\n🎯 TP2: 4520 (50%)\n🛑 SL: 4150\n⚡ Leverage: 15x',
    signalReason: 'Golden cross on 4H chart',
    sourceLeverage: '15x',
    leverage: 15,
    marginUsd: 150
  }
]

// Функция для создания виртуальной сделки
async function createVirtualTrade(signal) {
  try {
    const response = await fetch(`${API_BASE}/virtual-trades`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        ...signal,
        postedTs: Date.now(),
        targets: [signal.tp1, signal.tp2]
      })
    })

    const result = await response.json()
    
    if (result.success) {
      console.log(`✅ Created virtual trade: ${signal.symbol} ${signal.side}`)
      console.log(`   ID: ${result.data.id}`)
      console.log(`   Entry: ${signal.entryMin}${signal.entryMax !== signal.entryMin ? `-${signal.entryMax}` : ''}`)
      console.log(`   TP1/TP2: ${signal.tp1}/${signal.tp2}, SL: ${signal.sl}`)
      console.log(`   Strategy: ${result.data.strategy_id}`)
      return result.data
    } else {
      console.error(`❌ Failed to create ${signal.symbol}: ${result.error}`)
      return null
    }
  } catch (error) {
    console.error(`❌ Error creating ${signal.symbol}:`, error.message)
    return null
  }
}

// Функция для получения виртуальных сделок
async function getVirtualTrades(filters = {}) {
  try {
    const params = new URLSearchParams()
    
    if (filters.status) params.append('status', filters.status)
    if (filters.symbol) params.append('symbol', filters.symbol)
    if (filters.limit) params.append('limit', filters.limit.toString())
    if (filters.strategy) params.append('strategy', filters.strategy)

    const response = await fetch(`${API_BASE}/virtual-trades?${params}`)
    const result = await response.json()
    
    if (result.success) {
      console.log(`📊 Found ${result.count} virtual trades`)
      result.data.forEach((trade, i) => {
        console.log(`\n${i + 1}. ${trade.symbol} ${trade.side} [${trade.status}]`)
        console.log(`   ID: ${trade.id}`)
        console.log(`   Entry: ${trade.entry_min}${trade.entry_max !== trade.entry_min ? `-${trade.entry_max}` : ''}`)
        console.log(`   TP1/TP2: ${trade.tp1}/${trade.tp2}, SL: ${trade.sl}`)
        console.log(`   Source: ${trade.source_name || trade.source || 'Unknown'}`)
        console.log(`   Strategy: ${trade.strategy_id}`)
        console.log(`   Created: ${new Date(trade.created_at).toLocaleString()}`)
        
        // Показываем статус симуляции
        if (trade.was_fillable !== null) {
          console.log(`   Fillable: ${trade.was_fillable ? 'YES' : 'NO'}`)
          if (trade.entry_price) {
            console.log(`   Entry Price: ${trade.entry_price}`)
            console.log(`   Position: ${trade.position_qty || 'N/A'}`)
          }
        }
        
        // Показываем результаты если есть
        if (trade.tp1_hit || trade.tp2_hit || trade.sl_hit) {
          const hits = []
          if (trade.tp1_hit) hits.push('TP1')
          if (trade.tp2_hit) hits.push('TP2')
          if (trade.sl_hit) hits.push('SL')
          console.log(`   Hits: ${hits.join(', ')}`)
          
          if (trade.pnl_net !== null) {
            console.log(`   PnL: $${trade.pnl_net} (${trade.roi_percent}%)`)
          }
        }
      })
      return result.data
    } else {
      console.error(`❌ Failed to get trades: ${result.error}`)
      return []
    }
  } catch (error) {
    console.error('❌ Error getting trades:', error.message)
    return []
  }
}

// Основная функция тестирования
async function runTests() {
  console.log('🚀 GHOST Virtual Trades Test')
  console.log('=' .repeat(50))

  // 1. Проверяем API доступность
  console.log('\n1️⃣ Testing API connectivity...')
  try {
    const response = await fetch(`${API_BASE}/virtual-trades?limit=1`)
    const result = await response.json()
    if (result.success !== undefined) {
      console.log('✅ API is accessible')
    } else {
      console.log('❌ API returned unexpected format')
      return
    }
  } catch (error) {
    console.error('❌ API not accessible:', error.message)
    console.log('💡 Make sure Next.js dev server is running (npm run dev)')
    return
  }

  // 2. Создаем тестовые сигналы
  console.log('\n2️⃣ Creating test virtual trades...')
  const createdTrades = []
  
  for (const signal of testSignals) {
    const trade = await createVirtualTrade(signal)
    if (trade) {
      createdTrades.push(trade)
    }
    await new Promise(resolve => setTimeout(resolve, 100)) // Small delay
  }

  console.log(`\n✅ Created ${createdTrades.length}/${testSignals.length} virtual trades`)

  // 3. Получаем все открытые сделки
  console.log('\n3️⃣ Fetching open virtual trades...')
  await getVirtualTrades({ status: 'sim_open', limit: 10 })

  // 4. Фильтрация по символу
  if (createdTrades.length > 0) {
    console.log('\n4️⃣ Testing symbol filter...')
    const firstSymbol = createdTrades[0].symbol
    await getVirtualTrades({ symbol: firstSymbol })
  }

  // 5. Показываем статистику
  console.log('\n5️⃣ Getting all trades (statistics)...')
  const allTrades = await getVirtualTrades({ status: 'all', limit: 50 })
  
  if (allTrades.length > 0) {
    const stats = {
      total: allTrades.length,
      sim_open: allTrades.filter(t => t.status === 'sim_open').length,
      sim_closed: allTrades.filter(t => t.status === 'sim_closed').length,
      sim_skipped: allTrades.filter(t => t.status === 'sim_skipped').length,
      longs: allTrades.filter(t => t.side === 'LONG').length,
      shorts: allTrades.filter(t => t.side === 'SHORT').length
    }

    console.log('\n📈 Virtual Trades Statistics:')
    console.log(`   Total trades: ${stats.total}`)
    console.log(`   Open simulations: ${stats.sim_open}`)
    console.log(`   Closed simulations: ${stats.sim_closed}`)
    console.log(`   Skipped: ${stats.sim_skipped}`)
    console.log(`   LONG trades: ${stats.longs}`)
    console.log(`   SHORT trades: ${stats.shorts}`)
  }

  console.log('\n🎉 Test completed!')
  console.log('\n💡 Next steps:')
  console.log('   - Check Supabase dashboard to see the data')
  console.log('   - Implement simulation engine (Этап 2)')
  console.log('   - Add real-time price monitoring')
}

// Запускаем тесты
if (require.main === module) {
  runTests().catch(console.error)
}

module.exports = { createVirtualTrade, getVirtualTrades }
