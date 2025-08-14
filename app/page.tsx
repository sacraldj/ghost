import TelegramSignalsDashboard from '../components/TelegramSignalsDashboard'

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <h1 className="text-3xl font-bold text-gray-900">
                🎯 GHOST Trading System
              </h1>
              <span className="ml-3 px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">
                Live
              </span>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-500">
                Real-time data updates
              </div>
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            </div>
          </div>
        </div>
      </header>
      
      <main className="max-w-7xl mx-auto py-6">
        <TelegramSignalsDashboard />
      </main>
      
      <footer className="bg-white border-t mt-12">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <div className="text-sm text-gray-500">
              © 2025 GHOST Trading System - Real-time Telegram Signals
            </div>
            <div className="flex space-x-4 text-sm text-gray-500">
              <span>📊 Market Data</span>
              <span>📰 News Feed</span>
              <span>📡 Live Signals</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}