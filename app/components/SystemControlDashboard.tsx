'use client'

import React, { useState, useEffect } from 'react'
import { 
  PlayIcon,
  StopIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  CpuChipIcon,
  ServerIcon,
  ClockIcon,
  SignalIcon,
  WifiIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline'

interface TelegramSystemStatus {
  status: 'running' | 'stopped'
  health: 'healthy' | 'warning' | 'critical' | 'unknown'
  pid: number | null
  uptime: number
  channels_count: number
  last_signal_time: string | null
  timestamp: string
}

interface SystemControlResponse {
  success: boolean
  message: string
  data?: any
  timestamp: string
}

const SystemControlDashboard: React.FC = () => {
  const [systemStatus, setSystemStatus] = useState<TelegramSystemStatus | null>(null)
  const [loading, setLoading] = useState(false)
  const [lastUpdate, setLastUpdate] = useState<string>('')
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [actionMessage, setActionMessage] = useState<string>('')

  // Загрузка статуса системы
  const fetchSystemStatus = async () => {
    try {
      const response = await fetch('/api/system/control?component=telegram')
      const result: SystemControlResponse = await response.json()
      
      if (result.success && result.data?.telegram_system) {
        setSystemStatus(result.data.telegram_system)
        setLastUpdate(new Date().toLocaleTimeString())
      }
    } catch (error) {
      console.error('Failed to fetch system status:', error)
    }
  }

  // Выполнение действия с системой
  const executeAction = async (action: 'start' | 'stop' | 'restart') => {
    setActionLoading(action)
    setActionMessage('')

    try {
      const response = await fetch('/api/system/control', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action,
          component: 'telegram'
        })
      })

      const result: SystemControlResponse = await response.json()
      setActionMessage(result.message)

      // Обновляем статус через несколько секунд
      setTimeout(() => {
        fetchSystemStatus()
      }, 2000)

    } catch (error) {
      setActionMessage(`Failed to ${action} system: ${error}`)
    } finally {
      setActionLoading(null)
      // Очищаем сообщение через 5 секунд
      setTimeout(() => {
        setActionMessage('')
      }, 5000)
    }
  }

  // Автообновление каждые 30 секунд
  useEffect(() => {
    fetchSystemStatus()
    const interval = setInterval(fetchSystemStatus, 30000)
    return () => clearInterval(interval)
  }, [])

  // Форматирование времени работы
  const formatUptime = (uptime: number): string => {
    const seconds = Math.floor(uptime / 1000)
    const minutes = Math.floor(seconds / 60)
    const hours = Math.floor(minutes / 60)
    
    if (hours > 0) {
      return `${hours}ч ${minutes % 60}м`
    } else if (minutes > 0) {
      return `${minutes}м ${seconds % 60}с`
    } else {
      return `${seconds}с`
    }
  }

  // Определение цветов статуса
  const getStatusColor = (status: string, health: string) => {
    if (status === 'running' && health === 'healthy') {
      return 'text-green-400 bg-green-400/10 border-green-400/20'
    } else if (status === 'running' && health === 'warning') {
      return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20'
    } else if (status === 'running' && health === 'critical') {
      return 'text-red-400 bg-red-400/10 border-red-400/20'
    } else {
      return 'text-gray-400 bg-gray-400/10 border-gray-400/20'
    }
  }

  const getStatusIcon = (status: string, health: string) => {
    if (status === 'running' && health === 'healthy') {
      return <CheckCircleIcon className="h-5 w-5 text-green-400" />
    } else if (status === 'running' && (health === 'warning' || health === 'critical')) {
      return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" />
    } else if (status === 'stopped') {
      return <XCircleIcon className="h-5 w-5 text-red-400" />
    } else {
      return <ServerIcon className="h-5 w-5 text-gray-400" />
    }
  }

  if (!systemStatus) {
    return (
      <div className="bg-gradient-to-br from-gray-900/90 to-gray-950/90 backdrop-blur-sm rounded-2xl p-6 border border-gray-800/50">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-700 rounded mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-700 rounded w-3/4"></div>
            <div className="h-4 bg-gray-700 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-gradient-to-br from-gray-900/90 to-gray-950/90 backdrop-blur-sm rounded-2xl p-6 border border-gray-800/50 shadow-2xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="bg-gradient-to-r from-blue-600 to-blue-700 p-2 rounded-xl">
            <ServerIcon className="h-6 w-6 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">🚀 СИСТЕМА УПРАВЛЕНИЯ</h2>
            <p className="text-sm text-gray-400">Telegram Signal Processing System</p>
          </div>
        </div>
        
        <div className="text-right">
          <div className="text-xs text-gray-400">Последнее обновление</div>
          <div className="text-sm text-white">{lastUpdate}</div>
        </div>
      </div>

      {/* Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {/* System Status */}
        <div className={`p-4 rounded-xl border ${getStatusColor(systemStatus.status, systemStatus.health)}`}>
          <div className="flex items-center gap-2 mb-2">
            {getStatusIcon(systemStatus.status, systemStatus.health)}
            <span className="text-sm font-semibold uppercase tracking-wide">
              {systemStatus.status}
            </span>
          </div>
          <div className="text-xs opacity-75">
            Health: {systemStatus.health}
          </div>
          {systemStatus.pid && (
            <div className="text-xs opacity-75">
              PID: {systemStatus.pid}
            </div>
          )}
        </div>

        {/* Uptime */}
        <div className="p-4 rounded-xl bg-blue-400/10 border border-blue-400/20">
          <div className="flex items-center gap-2 mb-2">
            <ClockIcon className="h-5 w-5 text-blue-400" />
            <span className="text-sm font-semibold text-blue-400">UPTIME</span>
          </div>
          <div className="text-lg font-bold text-white">
            {systemStatus.status === 'running' ? formatUptime(systemStatus.uptime) : '0s'}
          </div>
        </div>

        {/* Channels */}
        <div className="p-4 rounded-xl bg-purple-400/10 border border-purple-400/20">
          <div className="flex items-center gap-2 mb-2">
            <WifiIcon className="h-5 w-5 text-purple-400" />
            <span className="text-sm font-semibold text-purple-400">КАНАЛЫ</span>
          </div>
          <div className="text-lg font-bold text-white">
            {systemStatus.channels_count}
          </div>
          <div className="text-xs text-purple-300">активных</div>
        </div>

        {/* Last Signal */}
        <div className="p-4 rounded-xl bg-green-400/10 border border-green-400/20">
          <div className="flex items-center gap-2 mb-2">
            <SignalIcon className="h-5 w-5 text-green-400" />
            <span className="text-sm font-semibold text-green-400">ПОСЛЕДНИЙ СИГНАЛ</span>
          </div>
          <div className="text-sm font-bold text-white">
            {systemStatus.last_signal_time 
              ? new Date(systemStatus.last_signal_time).toLocaleTimeString()
              : 'Нет данных'
            }
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-3 mb-4">
        <button
          onClick={() => executeAction('start')}
          disabled={systemStatus.status === 'running' || actionLoading === 'start'}
          className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-500 disabled:bg-gray-600 disabled:opacity-50 text-white rounded-xl font-semibold transition-all duration-200 shadow-lg hover:shadow-xl"
        >
          {actionLoading === 'start' ? (
            <ArrowPathIcon className="h-5 w-5 animate-spin" />
          ) : (
            <PlayIcon className="h-5 w-5" />
          )}
          ЗАПУСТИТЬ
        </button>

        <button
          onClick={() => executeAction('stop')}
          disabled={systemStatus.status === 'stopped' || actionLoading === 'stop'}
          className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-500 disabled:bg-gray-600 disabled:opacity-50 text-white rounded-xl font-semibold transition-all duration-200 shadow-lg hover:shadow-xl"
        >
          {actionLoading === 'stop' ? (
            <ArrowPathIcon className="h-5 w-5 animate-spin" />
          ) : (
            <StopIcon className="h-5 w-5" />
          )}
          ОСТАНОВИТЬ
        </button>

        <button
          onClick={() => executeAction('restart')}
          disabled={actionLoading === 'restart'}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-600 disabled:opacity-50 text-white rounded-xl font-semibold transition-all duration-200 shadow-lg hover:shadow-xl"
        >
          {actionLoading === 'restart' ? (
            <ArrowPathIcon className="h-5 w-5 animate-spin" />
          ) : (
            <ArrowPathIcon className="h-5 w-5" />
          )}
          ПЕРЕЗАПУСК
        </button>

        <button
          onClick={fetchSystemStatus}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-gray-600 hover:bg-gray-500 disabled:bg-gray-700 disabled:opacity-50 text-white rounded-xl font-semibold transition-all duration-200 shadow-lg hover:shadow-xl"
        >
          <ArrowPathIcon className={`h-5 w-5 ${loading ? 'animate-spin' : ''}`} />
          ОБНОВИТЬ
        </button>
      </div>

      {/* Action Message */}
      {actionMessage && (
        <div className={`p-3 rounded-lg mb-4 ${
          actionMessage.includes('successfully') || actionMessage.includes('Success')
            ? 'bg-green-400/10 border border-green-400/20 text-green-300'
            : 'bg-red-400/10 border border-red-400/20 text-red-300'
        }`}>
          <div className="flex items-center gap-2 text-sm">
            {actionMessage.includes('successfully') || actionMessage.includes('Success') ? (
              <CheckCircleIcon className="h-5 w-5" />
            ) : (
              <ExclamationTriangleIcon className="h-5 w-5" />
            )}
            {actionMessage}
          </div>
        </div>
      )}

      {/* System Information */}
      <div className="border-t border-gray-700 pt-4">
        <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
          <DocumentTextIcon className="h-5 w-5 text-blue-400" />
          Информация о системе
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <div className="text-gray-400 mb-1">Статус системы:</div>
            <div className="text-white font-semibold capitalize">{systemStatus.status}</div>
          </div>
          
          <div>
            <div className="text-gray-400 mb-1">Состояние здоровья:</div>
            <div className="text-white font-semibold capitalize">{systemStatus.health}</div>
          </div>
          
          <div>
            <div className="text-gray-400 mb-1">Время последнего обновления:</div>
            <div className="text-white font-semibold">
              {new Date(systemStatus.timestamp).toLocaleString()}
            </div>
          </div>
          
          <div>
            <div className="text-gray-400 mb-1">Мониторинг каналов:</div>
            <div className="text-white font-semibold">
              {systemStatus.channels_count} Telegram каналов
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SystemControlDashboard
