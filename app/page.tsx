'use client'

import { useState } from 'react'
import Link from 'next/link'
import TelegramSignalsDashboard from '../components/TelegramSignalsDashboard'

export default function Home() {
  const [activeTab, setActiveTab] = useState('overview')

  const tabs = [
    {
      id: 'overview',
      name: 'Overview',
      icon: '🎯',
      description: 'System Status & Quick Stats'
    },
    {
      id: 'signals',
      name: 'Live Signals',
      icon: '📡',
      description: 'Real-time Trading Signals'
    },
    {
      id: 'portfolio',
      name: 'Portfolio',
      icon: '💼',
      description: 'Trading Performance'
    },
    {
      id: 'news',
      name: 'News',
      icon: '📰',
      description: 'Market News & Analysis'
    }
  ]

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <div className="space-y-6">
            {/* System Status Cards */}
            <div className="grid md:grid-cols-4 gap-6">
              <div className="glass rounded-xl p-6">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-green-500/20 rounded-lg flex items-center justify-center">
                    <span className="text-green-400 text-xl">✅</span>
                  </div>
                  <div>
                    <h3 className="text-white font-semibold">System Status</h3>
                    <p className="text-green-400 text-sm">All Systems Online</p>
                  </div>
                </div>
              </div>
              
              <div className="glass rounded-xl p-6">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
                    <span className="text-blue-400 text-xl">📊</span>
                  </div>
                  <div>
                    <h3 className="text-white font-semibold">Active Signals</h3>
                    <p className="text-blue-400 text-sm">15 Live Signals</p>
                  </div>
                </div>
              </div>
              
              <div className="glass rounded-xl p-6">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
                    <span className="text-purple-400 text-xl">🎯</span>
                  </div>
                  <div>
                    <h3 className="text-white font-semibold">Success Rate</h3>
                    <p className="text-purple-400 text-sm">78.5% Win Rate</p>
                  </div>
                </div>
              </div>
              
              <div className="glass rounded-xl p-6">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-yellow-500/20 rounded-lg flex items-center justify-center">
                    <span className="text-yellow-400 text-xl">💰</span>
                  </div>
                  <div>
                    <h3 className="text-white font-semibold">Total PnL</h3>
                    <p className="text-yellow-400 text-sm">+$12,450</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Welcome Section */}
            <div className="glass rounded-xl p-8 text-center">
              <h2 className="text-3xl font-bold gradient-text mb-4">
                Welcome to GHOST Trading System
              </h2>
              <p className="text-gray-300 text-lg mb-6 max-w-2xl mx-auto">
                Professional-grade cryptocurrency trading platform with real-time Telegram signals, 
                advanced portfolio management, and AI-powered market analysis.
              </p>
              <div className="flex justify-center space-x-4">
                <Link
                  href="/dashboard"
                  className="px-6 py-3 bg-gradient-to-r from-[#667eea] to-[#764ba2] text-white rounded-lg hover:from-[#5a6fd8] hover:to-[#6a4190] transition-all duration-200 font-semibold"
                >
                  Open Full Dashboard
                </Link>
                <button
                  onClick={() => setActiveTab('signals')}
                  className="px-6 py-3 border border-white/20 text-white rounded-lg hover:bg-white/5 transition-all duration-200 font-semibold"
                >
                  View Live Signals
                </button>
              </div>
            </div>
          </div>
        )
      
      case 'signals':
        return <TelegramSignalsDashboard />
      
      case 'portfolio':
        return (
          <div className="glass rounded-xl p-8 text-center">
            <h2 className="text-2xl font-bold text-white mb-4">Portfolio Overview</h2>
            <p className="text-gray-400 mb-6">
              Access full portfolio features in the complete dashboard
            </p>
            <Link
              href="/dashboard"
              className="inline-block px-6 py-3 bg-gradient-to-r from-[#667eea] to-[#764ba2] text-white rounded-lg hover:from-[#5a6fd8] hover:to-[#6a4190] transition-all duration-200 font-semibold"
            >
              Open Portfolio Dashboard
            </Link>
          </div>
        )
      
      case 'news':
        return (
          <div className="glass rounded-xl p-8 text-center">
            <h2 className="text-2xl font-bold text-white mb-4">Market News</h2>
            <p className="text-gray-400 mb-6">
              Get real-time market news and analysis in the full dashboard
            </p>
            <Link
              href="/dashboard"
              className="inline-block px-6 py-3 bg-gradient-to-r from-[#667eea] to-[#764ba2] text-white rounded-lg hover:from-[#5a6fd8] hover:to-[#6a4190] transition-all duration-200 font-semibold"
            >
              Open News Dashboard
            </Link>
          </div>
        )
      
      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0a0a] via-[#1a1a1a] to-[#0f0f23]">
      {/* Header */}
      <header className="glass border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-[#667eea] to-[#764ba2] rounded-xl flex items-center justify-center neon-glow">
                <span className="text-white font-bold text-lg">G</span>
              </div>
              <span className="text-2xl font-bold gradient-text">GHOST Trading System</span>
              <span className="ml-3 px-2 py-1 bg-green-500/20 text-green-400 text-xs font-medium rounded-full">
                Live
              </span>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-400">
                Real-time data updates
              </div>
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            </div>
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <nav className="bg-black/20 backdrop-blur-md border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex space-x-2 py-4">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  group relative flex items-center space-x-3 px-4 py-3 rounded-xl 
                  transition-all duration-300 ease-out min-w-max
                  ${activeTab === tab.id 
                    ? 'bg-gradient-to-r from-[#667eea] to-[#764ba2] text-white shadow-lg shadow-[#667eea]/20' 
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                  }
                `}
              >
                <span className="text-lg">{tab.icon}</span>
                <div className="text-left">
                  <div className="text-sm font-medium">{tab.name}</div>
                  <div className="text-xs opacity-70 mt-0.5">
                    {tab.description}
                  </div>
                </div>
                
                {/* Active indicator */}
                {activeTab === tab.id && (
                  <div className="absolute -bottom-6 left-1/2 transform -translate-x-1/2">
                    <div className="w-1.5 h-1.5 bg-white rounded-full"></div>
                  </div>
                )}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
        <div className="min-h-[calc(100vh-12rem)]">
          {renderTabContent()}
        </div>
      </main>
      
      <footer className="glass border-t border-white/10 mt-12">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <div className="text-sm text-gray-400">
              © 2025 GHOST Trading System - Professional Crypto Trading Platform
            </div>
            <div className="flex space-x-4 text-sm text-gray-400">
              <span>📊 Live Data</span>
              <span>📰 News Feed</span>
              <span>📡 Real-time Signals</span>
              <span>🤖 AI Analysis</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}