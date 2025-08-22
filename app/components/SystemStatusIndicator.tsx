'use client'

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { 
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  ServerIcon
} from '@heroicons/react/24/outline'

interface SystemStatusIndicatorProps {
  className?: string
}

interface SystemStatus {
  overall: 'healthy' | 'warning' | 'critical' | 'unknown'
  telegram: 'running' | 'stopped' | 'error'
  render: 'live' | 'deploying' | 'error'
  lastUpdate: string
}

const SystemStatusIndicator: React.FC<SystemStatusIndicatorProps> = ({ className = '' }) => {
  const [status, setStatus] = useState<SystemStatus>({
    overall: 'unknown',
    telegram: 'stopped',
    render: 'error',
    lastUpdate: new Date().toISOString()
  })
  const [loading, setLoading] = useState(false)
  const [showTooltip, setShowTooltip] = useState(false)
  const router = useRouter()

  // Получение статуса системы
  const fetchSystemStatus = async () => {
    try {
      setLoading(true)
      
      // Получаем статус разных компонентов параллельно
      const [telegramResponse, renderResponse] = await Promise.allSettled([
        fetch('/api/system/control?component=telegram'),
        fetch('/api/render/status')
      ])

      let telegramStatus = 'stopped'
      let renderStatus = 'error'

      // Обрабатываем ответ от Telegram API
      if (telegramResponse.status === 'fulfilled') {
        try {
          const telegramData = await telegramResponse.value.json()
          telegramStatus = telegramData.data?.telegram_system?.status || 'stopped'
        } catch (error) {
          console.log('Error parsing telegram response:', error)
        }
      }

      // Обрабатываем ответ от Render API
      if (renderResponse.status === 'fulfilled') {
        try {
          const renderData = await renderResponse.value.json()
          const activeServices = renderData.data?.services?.filter((s: any) => s.status === 'live')
          renderStatus = activeServices?.length > 0 ? 'live' : 'error'
        } catch (error) {
          console.log('Error parsing render response:', error)
        }
      }

      // Определяем общий статус
      let overallStatus: 'healthy' | 'warning' | 'critical' | 'unknown' = 'unknown'
      
      if (telegramStatus === 'running' && renderStatus === 'live') {
        overallStatus = 'healthy'
      } else if (telegramStatus === 'running' || renderStatus === 'live') {
        overallStatus = 'warning'
      } else {
        overallStatus = 'critical'
      }

      setStatus({
        overall: overallStatus,
        telegram: telegramStatus as any,
        render: renderStatus as any,
        lastUpdate: new Date().toISOString()
      })

    } catch (error) {
      console.error('Failed to fetch system status:', error)
      setStatus({
        overall: 'unknown',
        telegram: 'error',
        render: 'error', 
        lastUpdate: new Date().toISOString()
      })
    } finally {
      setLoading(false)
    }
  }

  // Получение цвета и иконки для статуса
  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'healthy':
        return {
          color: 'text-green-400',
          bgColor: 'bg-green-400/20 border-green-400/30',
          icon: <CheckCircleIcon className="w-4 h-4" />,
          pulse: 'animate-pulse'
        }
      case 'warning':
        return {
          color: 'text-yellow-400',
          bgColor: 'bg-yellow-400/20 border-yellow-400/30',
          icon: <ExclamationTriangleIcon className="w-4 h-4" />,
          pulse: 'animate-pulse'
        }
      case 'critical':
        return {
          color: 'text-red-400',
          bgColor: 'bg-red-400/20 border-red-400/30',
          icon: <XCircleIcon className="w-4 h-4" />,
          pulse: 'animate-pulse'
        }
      default:
        return {
          color: 'text-gray-400',
          bgColor: 'bg-gray-400/20 border-gray-400/30',
          icon: <ServerIcon className="w-4 h-4" />,
          pulse: ''
        }
    }
  }

  const statusConfig = getStatusConfig(status.overall)

  // Клик по индикатору - переход в настройки
  const handleClick = () => {
    router.push('/settings')
  }

  // Форматирование времени последнего обновления
  const formatLastUpdate = () => {
    const now = new Date()
    const lastUpdate = new Date(status.lastUpdate)
    const diffMs = now.getTime() - lastUpdate.getTime()
    const diffMins = Math.floor(diffMs / (1000 * 60))
    
    if (diffMins < 1) return 'сейчас'
    if (diffMins < 60) return `${diffMins}м назад`
    const diffHours = Math.floor(diffMins / 60)
    return `${diffHours}ч назад`
  }

  // Автообновление каждые 30 секунд
  useEffect(() => {
    fetchSystemStatus()
    const interval = setInterval(fetchSystemStatus, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div 
      className={`relative ${className}`}
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      {/* Основной индикатор */}
      <button
        onClick={handleClick}
        className={`flex items-center gap-2 px-3 py-2 rounded-lg border transition-all duration-200 hover:scale-105 ${statusConfig.bgColor} ${statusConfig.color}`}
      >
        <div className={`${loading ? 'animate-spin' : statusConfig.pulse}`}>
          {statusConfig.icon}
        </div>
        <span className="text-xs font-semibold uppercase hidden sm:inline">
          {status.overall}
        </span>
        <div className={`w-2 h-2 rounded-full ${statusConfig.color.replace('text-', 'bg-')} ${statusConfig.pulse}`}></div>
      </button>

      {/* Tooltip с подробной информацией */}
      {showTooltip && (
        <div className="absolute top-full right-0 mt-2 w-64 bg-gray-900 border border-gray-700 rounded-lg shadow-2xl z-50 p-3">
          <div className="text-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="text-white font-semibold">Статус системы</span>
              <span className="text-xs text-gray-400">{formatLastUpdate()}</span>
            </div>
            
            <div className="space-y-2">
              {/* Telegram Status */}
              <div className="flex items-center justify-between">
                <span className="text-gray-300">📡 Telegram</span>
                <span className={`text-xs font-semibold ${
                  status.telegram === 'running' ? 'text-green-400' : 'text-red-400'
                }`}>
                  {status.telegram === 'running' ? 'РАБОТАЕТ' : 'ОСТАНОВЛЕН'}
                </span>
              </div>
              
              {/* Render Status */}
              <div className="flex items-center justify-between">
                <span className="text-gray-300">☁️ Render</span>
                <span className={`text-xs font-semibold ${
                  status.render === 'live' ? 'text-green-400' : 'text-red-400'
                }`}>
                  {status.render === 'live' ? 'В СЕТИ' : 'ОШИБКА'}
                </span>
              </div>
            </div>
            
            <div className="border-t border-gray-700 mt-2 pt-2">
              <button
                onClick={handleClick}
                className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
              >
                Открыть настройки →
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default SystemStatusIndicator
