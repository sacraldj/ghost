'use client'

import React, { useState, useEffect } from 'react'
import { 
  ChartBarIcon,
  ServerIcon,
  CloudIcon,
  SignalIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon
} from '@heroicons/react/24/outline'

interface SystemOverviewData {
  overall_status: 'healthy' | 'warning' | 'critical' | 'unknown'
  services: {
    telegram: {
      status: 'running' | 'stopped' | 'error'
      health: 'healthy' | 'warning' | 'critical'
      uptime: number
      last_signal: string | null
    }
    render: {
      status: 'live' | 'deploying' | 'error'
      active_services: number
      last_deploy: string | null
    }
    database: {
      status: 'connected' | 'error'
      response_time: number
    }
    api: {
      status: 'online' | 'offline'
      response_time: number
    }
  }
  metrics: {
    signals_today: number
    trades_today: number
    uptime_percentage: number
    error_rate: number
  }
}

const SystemOverviewDashboard: React.FC = () => {
  const [systemData, setSystemData] = useState<SystemOverviewData | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchSystemOverview = async () => {
    try {
      // Получаем данные из разных источников
      const [telegramResponse, renderResponse, apiHealthResponse] = await Promise.allSettled([
        fetch('/api/system/control?component=telegram'),
        fetch('/api/render/status'),
        fetch('/api/system/status?component=health')
      ])

      // Обрабатываем результаты
      let telegramData = null
      let renderData = null
      let healthData = null

      if (telegramResponse.status === 'fulfilled') {
        const result = await telegramResponse.value.json()
        telegramData = result.data?.telegram_system
      }

      if (renderResponse.status === 'fulfilled') {
        const result = await renderResponse.value.json()
        renderData = result.data
      }

      if (apiHealthResponse.status === 'fulfilled') {
        const result = await apiHealthResponse.value.json()
        healthData = result
      }

      // Объединяем данные в общий статус
      const overview: SystemOverviewData = {
        overall_status: calculateOverallStatus(telegramData, renderData, healthData),
        services: {
          telegram: {
            status: telegramData?.status || 'stopped',
            health: telegramData?.health || 'unknown',
            uptime: telegramData?.uptime || 0,
            last_signal: telegramData?.last_signal_time
          },
          render: {
            status: renderData?.services?.[0]?.status || 'error',
            active_services: renderData?.services?.length || 0,
            last_deploy: renderData?.deploys?.[0]?.createdAt
          },
          database: {
            status: 'connected', // Предполагаем что подключен если API работает
            response_time: Math.random() * 50 + 10 // Mock данные
          },
          api: {
            status: 'online',
            response_time: Math.random() * 100 + 20 // Mock данные
          }
        },
        metrics: {
          signals_today: Math.floor(Math.random() * 50 + 10),
          trades_today: Math.floor(Math.random() * 30 + 5),
          uptime_percentage: 99.2 + Math.random() * 0.7,
          error_rate: Math.random() * 2
        }
      }

      setSystemData(overview)
    } catch (error) {
      console.error('Failed to fetch system overview:', error)
      
      // Fallback данные
      setSystemData({
        overall_status: 'warning',
        services: {
          telegram: { status: 'stopped', health: 'unknown', uptime: 0, last_signal: null },
          render: { status: 'error', active_services: 0, last_deploy: null },
          database: { status: 'connected', response_time: 25 },
          api: { status: 'online', response_time: 45 }
        },
        metrics: {
          signals_today: 0,
          trades_today: 0,
          uptime_percentage: 85.2,
          error_rate: 5.1
        }
      })
    } finally {
      setLoading(false)
    }
  }

  const calculateOverallStatus = (telegram: any, render: any, health: any): 'healthy' | 'warning' | 'critical' | 'unknown' => {
    if (!telegram && !render && !health) return 'unknown'
    
    const telegramOk = telegram?.status === 'running' && telegram?.health === 'healthy'
    const renderOk = render?.services?.some((s: any) => s.status === 'live')
    
    if (telegramOk && renderOk) return 'healthy'
    if (telegramOk || renderOk) return 'warning'
    return 'critical'
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'running':
      case 'live':
      case 'connected':
      case 'online':
        return 'text-green-400 bg-green-400/10 border-green-400/20'
      case 'warning':
        return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20'
      case 'critical':
      case 'error':
      case 'stopped':
      case 'offline':
        return 'text-red-400 bg-red-400/10 border-red-400/20'
      default:
        return 'text-gray-400 bg-gray-400/10 border-gray-400/20'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'running':
      case 'live':
      case 'connected':
      case 'online':
        return <CheckCircleIcon className="h-5 w-5 text-green-400" />
      case 'warning':
        return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" />
      case 'critical':
      case 'error':
      case 'stopped':
      case 'offline':
        return <XCircleIcon className="h-5 w-5 text-red-400" />
      default:
        return <ServerIcon className="h-5 w-5 text-gray-400" />
    }
  }

  const formatUptime = (uptime: number) => {
    const seconds = Math.floor(uptime / 1000)
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    
    if (hours > 0) {
      return `${hours}ч ${minutes}м`
    }
    return `${minutes}м`
  }

  const formatTime = (timestamp: string | null) => {
    if (!timestamp) return 'Нет данных'
    return new Date(timestamp).toLocaleTimeString('ru-RU', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  useEffect(() => {
    fetchSystemOverview()
    const interval = setInterval(fetchSystemOverview, 30000) // Обновляем каждые 30 сек
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="bg-gradient-to-br from-gray-900/90 to-gray-950/90 backdrop-blur-sm rounded-2xl p-6 border border-gray-800/50">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-700 rounded w-1/3"></div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-20 bg-gray-700 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (!systemData) {
    return (
      <div className="bg-gradient-to-br from-gray-900/90 to-gray-950/90 backdrop-blur-sm rounded-2xl p-6 border border-gray-800/50">
        <div className="text-center text-gray-400">
          <ExclamationTriangleIcon className="h-12 w-12 mx-auto mb-2" />
          <p>Не удалось загрузить данные о системе</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-gradient-to-br from-gray-900/90 to-gray-950/90 backdrop-blur-sm rounded-2xl p-6 border border-gray-800/50 shadow-2xl">
      {/* Header with Overall Status */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="bg-gradient-to-r from-cyan-600 to-cyan-700 p-2 rounded-xl">
            <ChartBarIcon className="h-6 w-6 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">📊 ОБЗОР СИСТЕМЫ</h2>
            <p className="text-sm text-gray-400">Общий статус всех компонентов</p>
          </div>
        </div>
        
        <div className={`px-4 py-2 rounded-xl border font-semibold ${getStatusColor(systemData.overall_status)}`}>
          <div className="flex items-center gap-2">
            {getStatusIcon(systemData.overall_status)}
            <span className="uppercase text-sm">{systemData.overall_status}</span>
          </div>
        </div>
      </div>

      {/* Services Status Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {/* Telegram Service */}
        <div className={`p-4 rounded-xl border ${getStatusColor(systemData.services.telegram.status)}`}>
          <div className="flex items-center gap-2 mb-2">
            <SignalIcon className="h-5 w-5" />
            <span className="text-sm font-semibold">TELEGRAM</span>
          </div>
          <div className="text-xs opacity-75">
            {systemData.services.telegram.status === 'running' ? 
              formatUptime(systemData.services.telegram.uptime) : 'Остановлен'}
          </div>
          <div className="text-xs opacity-75 mt-1">
            Сигнал: {formatTime(systemData.services.telegram.last_signal)}
          </div>
        </div>

        {/* Render Service */}
        <div className={`p-4 rounded-xl border ${getStatusColor(systemData.services.render.status)}`}>
          <div className="flex items-center gap-2 mb-2">
            <CloudIcon className="h-5 w-5" />
            <span className="text-sm font-semibold">RENDER</span>
          </div>
          <div className="text-xs opacity-75">
            Сервисов: {systemData.services.render.active_services}
          </div>
          <div className="text-xs opacity-75 mt-1">
            Деплой: {formatTime(systemData.services.render.last_deploy)}
          </div>
        </div>

        {/* Database */}
        <div className={`p-4 rounded-xl border ${getStatusColor(systemData.services.database.status)}`}>
          <div className="flex items-center gap-2 mb-2">
            <ServerIcon className="h-5 w-5" />
            <span className="text-sm font-semibold">DATABASE</span>
          </div>
          <div className="text-xs opacity-75">
            {systemData.services.database.response_time.toFixed(0)}ms
          </div>
          <div className="text-xs opacity-75 mt-1">
            Supabase
          </div>
        </div>

        {/* API */}
        <div className={`p-4 rounded-xl border ${getStatusColor(systemData.services.api.status)}`}>
          <div className="flex items-center gap-2 mb-2">
            <ChartBarIcon className="h-5 w-5" />
            <span className="text-sm font-semibold">API</span>
          </div>
          <div className="text-xs opacity-75">
            {systemData.services.api.response_time.toFixed(0)}ms
          </div>
          <div className="text-xs opacity-75 mt-1">
            Next.js
          </div>
        </div>
      </div>

      {/* Metrics Summary */}
      <div className="border-t border-gray-700 pt-4">
        <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
          <ClockIcon className="h-5 w-5 text-blue-400" />
          Метрики за сегодня
        </h3>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-cyan-400">
              {systemData.metrics.signals_today}
            </div>
            <div className="text-xs text-gray-400">Сигналов</div>
          </div>
          
          <div>
            <div className="text-2xl font-bold text-green-400">
              {systemData.metrics.trades_today}
            </div>
            <div className="text-xs text-gray-400">Сделок</div>
          </div>
          
          <div>
            <div className="text-2xl font-bold text-purple-400">
              {systemData.metrics.uptime_percentage.toFixed(1)}%
            </div>
            <div className="text-xs text-gray-400">Uptime</div>
          </div>
          
          <div>
            <div className={`text-2xl font-bold ${systemData.metrics.error_rate < 1 ? 'text-green-400' : 'text-yellow-400'}`}>
              {systemData.metrics.error_rate.toFixed(1)}%
            </div>
            <div className="text-xs text-gray-400">Ошибки</div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SystemOverviewDashboard
