'use client'

import { useState, useEffect } from 'react'
import GhostLayoutExact from '@/app/components/GhostLayoutExact'
import SystemControlDashboard from '@/app/components/SystemControlDashboard'
import { 
  Cog6ToothIcon,
  ServerIcon,
  BellIcon,
  ShieldCheckIcon,
  CircleStackIcon,
  KeyIcon
} from '@heroicons/react/24/outline'

export default function SettingsPage() {
  const [isClient, setIsClient] = useState(false)
  const [activeTab, setActiveTab] = useState('system')

  useEffect(() => {
    setIsClient(true)
  }, [])

  if (!isClient) {
    return <div className="min-h-screen bg-black" />
  }

  const tabs = [
    { id: 'system', name: 'Управление системой', icon: ServerIcon },
    { id: 'notifications', name: 'Уведомления', icon: BellIcon },
    { id: 'security', name: 'Безопасность', icon: ShieldCheckIcon },
    { id: 'database', name: 'База данных', icon: CircleStackIcon },
    { id: 'api', name: 'API ключи', icon: KeyIcon },
  ]

  return (
    <GhostLayoutExact currentPage="settings">
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-gradient-to-br from-gray-900/90 to-gray-950/90 backdrop-blur-sm rounded-2xl p-6 border border-gray-800/50 shadow-2xl">
          <div className="flex items-center gap-4">
            <div className="bg-gradient-to-r from-purple-600 to-purple-700 p-3 rounded-xl">
              <Cog6ToothIcon className="h-8 w-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">⚙️ НАСТРОЙКИ СИСТЕМЫ</h1>
              <p className="text-gray-400 mt-1">Управление и конфигурация Ghost Trading System</p>
            </div>
          </div>
        </div>

        {/* Tabs Navigation */}
        <div className="bg-gradient-to-br from-gray-900/90 to-gray-950/90 backdrop-blur-sm rounded-2xl border border-gray-800/50 shadow-2xl">
          <div className="flex overflow-x-auto scrollbar-hide">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-3 px-6 py-4 text-sm font-semibold whitespace-nowrap border-b-2 transition-all duration-200 ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-400 bg-blue-500/10'
                      : 'border-transparent text-gray-400 hover:text-white hover:bg-gray-800/50'
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  {tab.name}
                </button>
              )
            })}
          </div>
        </div>

        {/* Tab Content */}
        <div className="space-y-6">
          {activeTab === 'system' && (
            <div className="space-y-6">
              <SystemControlDashboard />
              
              {/* Additional System Settings */}
              <div className="bg-gradient-to-br from-gray-900/90 to-gray-950/90 backdrop-blur-sm rounded-2xl p-6 border border-gray-800/50 shadow-2xl">
                <h3 className="text-xl font-semibold text-white mb-4">🔧 Дополнительные настройки</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  
                  {/* Auto Start */}
                  <div className="p-4 rounded-xl bg-gray-800/30 border border-gray-700/50">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-white font-semibold">Автозапуск</span>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" className="sr-only peer" defaultChecked />
                        <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                      </label>
                    </div>
                    <p className="text-sm text-gray-400">Автоматически запускать систему при деплойменте на Render</p>
                  </div>

                  {/* Health Checks */}
                  <div className="p-4 rounded-xl bg-gray-800/30 border border-gray-700/50">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-white font-semibold">Health Checks</span>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" className="sr-only peer" defaultChecked />
                        <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                      </label>
                    </div>
                    <p className="text-sm text-gray-400">Мониторинг здоровья системы каждые 30 секунд</p>
                  </div>

                  {/* Error Recovery */}
                  <div className="p-4 rounded-xl bg-gray-800/30 border border-gray-700/50">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-white font-semibold">Авто-восстановление</span>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" className="sr-only peer" defaultChecked />
                        <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                      </label>
                    </div>
                    <p className="text-sm text-gray-400">Автоматически перезапускать при критических ошибках</p>
                  </div>

                </div>
              </div>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="bg-gradient-to-br from-gray-900/90 to-gray-950/90 backdrop-blur-sm rounded-2xl p-6 border border-gray-800/50 shadow-2xl">
              <h3 className="text-xl font-semibold text-white mb-4">🔔 Настройки уведомлений</h3>
              <div className="space-y-4">
                <div className="p-4 rounded-xl bg-gray-800/30 border border-gray-700/50">
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-white font-semibold">Email уведомления</span>
                      <p className="text-sm text-gray-400">Получать уведомления о критических ошибках</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" className="sr-only peer" />
                      <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="bg-gradient-to-br from-gray-900/90 to-gray-950/90 backdrop-blur-sm rounded-2xl p-6 border border-gray-800/50 shadow-2xl">
              <h3 className="text-xl font-semibold text-white mb-4">🔒 Настройки безопасности</h3>
              <p className="text-gray-400">Настройки безопасности будут добавлены позже.</p>
            </div>
          )}

          {activeTab === 'database' && (
            <div className="bg-gradient-to-br from-gray-900/90 to-gray-950/90 backdrop-blur-sm rounded-2xl p-6 border border-gray-800/50 shadow-2xl">
              <h3 className="text-xl font-semibold text-white mb-4">🗄️ Настройки базы данных</h3>
              <p className="text-gray-400">Настройки базы данных будут добавлены позже.</p>
            </div>
          )}

          {activeTab === 'api' && (
            <div className="bg-gradient-to-br from-gray-900/90 to-gray-950/90 backdrop-blur-sm rounded-2xl p-6 border border-gray-800/50 shadow-2xl">
              <h3 className="text-xl font-semibold text-white mb-4">🔑 API ключи</h3>
              <p className="text-gray-400">Управление API ключами будет добавлено позже.</p>
            </div>
          )}
        </div>
      </div>
    </GhostLayoutExact>
  )
}
