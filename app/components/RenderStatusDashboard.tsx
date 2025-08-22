'use client'

import React, { useState, useEffect } from 'react'
import { 
  CloudIcon,
  ServerStackIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  CpuChipIcon,
  ClockIcon,
  ArrowPathIcon,
  BoltIcon,
  DocumentTextIcon,
  EyeIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'

interface RenderService {
  id: string
  name: string
  type: 'web_service' | 'private_service' | 'static_site' | 'cron_job' | 'background_worker'
  status: 'created' | 'build_in_progress' | 'update_in_progress' | 'live' | 'deactivated' | 'build_failed' | 'update_failed' | 'pre_deploy_in_progress' | 'pre_deploy_failed'
  deployId?: string
  url?: string
  createdAt: string
  updatedAt: string
  repo?: string
  branch?: string
  buildCommand?: string
  startCommand?: string
}

interface RenderDeploy {
  id: string
  status: 'created' | 'build_in_progress' | 'live' | 'deactivated' | 'build_failed' | 'update_failed'
  createdAt: string
  finishedAt?: string
  commitId?: string
  commitMessage?: string
}

interface RenderMetrics {
  cpu: number
  memory: number
  bandwidth: number
  requests: number
  errors: number
  uptime: number
}

interface RenderStatusData {
  services: RenderService[]
  deploys: RenderDeploy[]
  metrics?: RenderMetrics
  lastUpdate: string
  isConnected: boolean
}

const RenderStatusDashboard: React.FC = () => {
  const [renderData, setRenderData] = useState<RenderStatusData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')
  const [lastUpdate, setLastUpdate] = useState<string>('')
  const [autoRefresh, setAutoRefresh] = useState(true)

  // Загрузка данных о статусе Render
  const fetchRenderStatus = async () => {
    try {
      setLoading(true)
      setError('')
      
      const response = await fetch('/api/render/status')
      const data = await response.json()
      
      if (data.success) {
        setRenderData(data.data)
        setLastUpdate(new Date().toLocaleTimeString())
      } else {
        setError(data.message || 'Failed to fetch Render status')
      }
    } catch (err) {
      console.error('Failed to fetch Render status:', err)
      setError('Connection error')
      // Показываем mock данные при ошибке соединения
      setRenderData({
        services: [
          {
            id: 'srv-ghost-telegram-bridge',
            name: 'ghost-telegram-bridge',
            type: 'background_worker',
            status: 'live',
            url: 'https://ghost-telegram-bridge.onrender.com',
            createdAt: new Date(Date.now() - 86400000).toISOString(),
            updatedAt: new Date().toISOString(),
            repo: 'ghost',
            branch: 'main',
            startCommand: 'python start_all.py'
          },
          {
            id: 'srv-ghost-api',
            name: 'ghost-api',
            type: 'web_service',
            status: 'live',
            url: 'https://ghost-api.onrender.com',
            createdAt: new Date(Date.now() - 86400000).toISOString(),
            updatedAt: new Date().toISOString(),
            repo: 'ghost',
            branch: 'main',
            startCommand: 'python -m uvicorn api.main:app --host 0.0.0.0 --port $PORT'
          }
        ],
        deploys: [
          {
            id: 'dpl-latest',
            status: 'live',
            createdAt: new Date(Date.now() - 3600000).toISOString(),
            finishedAt: new Date(Date.now() - 3300000).toISOString(),
            commitId: 'a84afff',
            commitMessage: '🔒 Update Telegram session file'
          }
        ],
        metrics: {
          cpu: 12.3,
          memory: 256.7,
          bandwidth: 1024,
          requests: 847,
          errors: 2,
          uptime: 99.8
        },
        lastUpdate: new Date().toISOString(),
        isConnected: false
      })
    } finally {
      setLoading(false)
    }
  }

  // Автообновление каждые 30 секунд
  useEffect(() => {
    fetchRenderStatus()
    
    if (autoRefresh) {
      const interval = setInterval(fetchRenderStatus, 30000)
      return () => clearInterval(interval)
    }
  }, [autoRefresh])

  // Получение цвета статуса сервиса
  const getServiceStatusColor = (status: string) => {
    switch (status) {
      case 'live':
        return 'text-green-400 bg-green-400/10 border-green-400/20'
      case 'build_in_progress':
      case 'update_in_progress':
      case 'pre_deploy_in_progress':
        return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20'
      case 'build_failed':
      case 'update_failed':
      case 'pre_deploy_failed':
        return 'text-red-400 bg-red-400/10 border-red-400/20'
      case 'deactivated':
        return 'text-gray-400 bg-gray-400/10 border-gray-400/20'
      default:
        return 'text-blue-400 bg-blue-400/10 border-blue-400/20'
    }
  }

  // Получение иконки статуса
  const getServiceStatusIcon = (status: string) => {
    switch (status) {
      case 'live':
        return <CheckCircleIcon className="h-5 w-5 text-green-400" />
      case 'build_in_progress':
      case 'update_in_progress':
      case 'pre_deploy_in_progress':
        return <ArrowPathIcon className="h-5 w-5 text-yellow-400 animate-spin" />
      case 'build_failed':
      case 'update_failed':
      case 'pre_deploy_failed':
        return <XCircleIcon className="h-5 w-5 text-red-400" />
      case 'deactivated':
        return <ExclamationTriangleIcon className="h-5 w-5 text-gray-400" />
      default:
        return <ServerStackIcon className="h-5 w-5 text-blue-400" />
    }
  }

  // Форматирование времени
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  // Получение времени с момента деплоя
  const getTimeSince = (timestamp: string) => {
    const diff = Date.now() - new Date(timestamp).getTime()
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)
    
    if (days > 0) return `${days}д ${hours % 24}ч назад`
    if (hours > 0) return `${hours}ч ${minutes % 60}м назад`
    return `${minutes}м назад`
  }

  if (loading && !renderData) {
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
          <div className="bg-gradient-to-r from-purple-600 to-purple-700 p-2 rounded-xl">
            <CloudIcon className="h-6 w-6 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              ☁️ RENDER DEPLOYMENT STATUS
              {!renderData?.isConnected && (
                <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-1 rounded-full border border-yellow-400/30">
                  MOCK DATA
                </span>
              )}
            </h2>
            <p className="text-sm text-gray-400">Live deployment monitoring from Render.com</p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <button
            onClick={fetchRenderStatus}
            disabled={loading}
            className="p-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
          >
            <ArrowPathIcon className={`h-4 w-4 text-white ${loading ? 'animate-spin' : ''}`} />
          </button>
          
          <div className="text-right">
            <div className="text-xs text-gray-400">Обновлено</div>
            <div className="text-sm text-white">{lastUpdate}</div>
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-yellow-400/10 border border-yellow-400/20 rounded-lg">
          <div className="flex items-center gap-2 text-yellow-300 text-sm">
            <ExclamationTriangleIcon className="h-5 w-5" />
            {error} - показаны mock данные
          </div>
        </div>
      )}

      {/* Services Status */}
      {renderData?.services && renderData.services.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
            <ServerStackIcon className="h-5 w-5 text-purple-400" />
            Сервисы ({renderData.services.length})
          </h3>
          
          <div className="grid gap-3">
            {renderData.services.map((service) => (
              <div key={service.id} className={`p-4 rounded-xl border ${getServiceStatusColor(service.status)}`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    {getServiceStatusIcon(service.status)}
                    <div>
                      <div className="text-white font-semibold">{service.name}</div>
                      <div className="text-xs opacity-75 capitalize">
                        {service.type.replace('_', ' ')} • {service.status.replace('_', ' ')}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    {service.url && (
                      <a
                        href={service.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-1 bg-white/10 rounded hover:bg-white/20 transition-colors"
                      >
                        <EyeIcon className="h-4 w-4" />
                      </a>
                    )}
                    <div className="text-xs opacity-75">
                      {getTimeSince(service.updatedAt)}
                    </div>
                  </div>
                </div>
                
                {service.startCommand && (
                  <div className="text-xs font-mono bg-black/20 p-2 rounded mt-2">
                    {service.startCommand}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Deploys */}
      {renderData?.deploys && renderData.deploys.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
            <BoltIcon className="h-5 w-5 text-green-400" />
            Последние деплои
          </h3>
          
          <div className="space-y-2">
            {renderData.deploys.slice(0, 3).map((deploy) => (
              <div key={deploy.id} className="p-3 bg-gray-800/50 rounded-lg border border-gray-700/50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {getServiceStatusIcon(deploy.status)}
                    <div>
                      <div className="text-white text-sm font-semibold">
                        {deploy.commitMessage || `Deploy ${deploy.id.slice(-8)}`}
                      </div>
                      {deploy.commitId && (
                        <div className="text-xs text-gray-400 font-mono">
                          {deploy.commitId.slice(0, 7)}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="text-xs text-gray-400">
                    {getTimeSince(deploy.createdAt)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Metrics */}
      {renderData?.metrics && (
        <div className="border-t border-gray-700 pt-4">
          <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
            <ChartBarIcon className="h-5 w-5 text-blue-400" />
            Метрики производительности
          </h3>
          
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-400">
                {renderData.metrics.cpu.toFixed(1)}%
              </div>
              <div className="text-xs text-gray-400">CPU</div>
            </div>
            
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-400">
                {renderData.metrics.memory.toFixed(0)}MB
              </div>
              <div className="text-xs text-gray-400">Memory</div>
            </div>
            
            <div className="text-center">
              <div className="text-2xl font-bold text-green-400">
                {renderData.metrics.uptime.toFixed(1)}%
              </div>
              <div className="text-xs text-gray-400">Uptime</div>
            </div>
            
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-400">
                {renderData.metrics.requests}
              </div>
              <div className="text-xs text-gray-400">Requests</div>
            </div>
            
            <div className="text-center">
              <div className="text-2xl font-bold text-red-400">
                {renderData.metrics.errors}
              </div>
              <div className="text-xs text-gray-400">Errors</div>
            </div>
            
            <div className="text-center">
              <div className="text-2xl font-bold text-cyan-400">
                {(renderData.metrics.bandwidth / 1024).toFixed(1)}GB
              </div>
              <div className="text-xs text-gray-400">Bandwidth</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default RenderStatusDashboard
