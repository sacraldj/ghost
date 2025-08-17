'use client'

import React, { useState, useEffect } from 'react'
import { 
  CheckCircleIcon, 
  ExclamationTriangleIcon, 
  XCircleIcon,
  ArrowPathIcon,
  CpuChipIcon,
  ServerIcon,
  ClockIcon
} from '@heroicons/react/24/outline'

interface ModuleStatus {
  name: string
  status: string
  health: string
  pid: number | null
  restart_count: number
  cpu_usage: number
  memory_usage: number
  start_time: string | null
  last_health_check: string | null
  error_message?: string
}

interface SystemHealth {
  overall_status: 'healthy' | 'warning' | 'critical' | 'unknown'
  health_score: number
  issues: string[]
  modules_status: {
    total: number
    running: number
    healthy: number
    failed: number
  }
  system_metrics: {
    uptime: number
  }
}

interface SystemStatusData {
  status: string
  health: SystemHealth
  modules_summary: {
    total: number
    running: number
    healthy: number
  }
  uptime: number
  timestamp: string
}

export default function SystemMonitor() {
  const [systemStatus, setSystemStatus] = useState<SystemStatusData | null>(null)
  const [moduleDetails, setModuleDetails] = useState<Record<string, ModuleStatus>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedTab, setSelectedTab] = useState<'overview' | 'modules' | 'logs'>('overview')
  const [autoRefresh, setAutoRefresh] = useState(true)

  const fetchSystemStatus = async () => {
    try {
      const response = await fetch('/api/system/status')
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      const data = await response.json()
      setSystemStatus(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch system status')
    } finally {
      setLoading(false)
    }
  }

  const fetchModuleDetails = async () => {
    try {
      const response = await fetch('/api/system/status?component=modules')
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      const data = await response.json()
      setModuleDetails(data.modules || {})
    } catch (err) {
      console.error('Failed to fetch module details:', err)
    }
  }

  useEffect(() => {
    fetchSystemStatus()
    fetchModuleDetails()
  }, [])

  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(() => {
      fetchSystemStatus()
      if (selectedTab === 'modules') {
        fetchModuleDetails()
      }
    }, 10000) // Обновление каждые 10 секунд

    return () => clearInterval(interval)
  }, [autoRefresh, selectedTab])

  const getStatusIcon = (status: string, health: string) => {
    if (status === 'running' && health === 'healthy') {
      return <CheckCircleIcon className="h-5 w-5 text-green-500" />
    } else if (status === 'running' && health === 'unhealthy') {
      return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />
    } else if (status === 'failed') {
      return <XCircleIcon className="h-5 w-5 text-red-500" />
    } else {
      return <ArrowPathIcon className="h-5 w-5 text-gray-500 animate-spin" />
    }
  }

  const getHealthColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-500'
      case 'warning': return 'text-yellow-500'
      case 'critical': return 'text-red-500'
      default: return 'text-gray-500'
    }
  }

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400)
    const hours = Math.floor((seconds % 86400) / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    
    if (days > 0) {
      return `${days}d ${hours}h ${minutes}m`
    } else if (hours > 0) {
      return `${hours}h ${minutes}m`
    } else {
      return `${minutes}m`
    }
  }

  const formatMemory = (mb: number) => {
    if (mb > 1024) {
      return `${(mb / 1024).toFixed(1)} GB`
    }
    return `${mb.toFixed(0)} MB`
  }

  if (loading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center justify-center h-32">
          <ArrowPathIcon className="h-8 w-8 text-blue-500 animate-spin" />
          <span className="ml-2 text-gray-300">Загрузка статуса системы...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center text-red-400">
          <XCircleIcon className="h-6 w-6 mr-2" />
          <span>Ошибка загрузки: {error}</span>
        </div>
        <button
          onClick={() => {
            setLoading(true)
            fetchSystemStatus()
          }}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Повторить
        </button>
      </div>
    )
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-white flex items-center">
          <ServerIcon className="h-6 w-6 mr-2" />
          System Monitor
        </h2>
        <div className="flex items-center space-x-4">
          <label className="flex items-center text-sm text-gray-300">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="mr-2"
            />
            Auto-refresh
          </label>
          <button
            onClick={() => {
              fetchSystemStatus()
              fetchModuleDetails()
            }}
            className="p-2 bg-gray-700 rounded hover:bg-gray-600"
          >
            <ArrowPathIcon className="h-4 w-4 text-gray-300" />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex space-x-4 mb-6 border-b border-gray-700">
        {[
          { id: 'overview', label: 'Overview' },
          { id: 'modules', label: 'Modules' },
          { id: 'logs', label: 'Logs' }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setSelectedTab(tab.id as any)}
            className={`pb-2 px-1 ${
              selectedTab === tab.id
                ? 'border-b-2 border-blue-500 text-blue-400'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {selectedTab === 'overview' && systemStatus && (
        <div className="space-y-6">
          {/* System Health */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-gray-300">System Health</h3>
                <span className={`text-2xl font-bold ${getHealthColor(systemStatus.health.overall_status)}`}>
                  {systemStatus.health.health_score}%
                </span>
              </div>
              <p className={`text-sm mt-1 ${getHealthColor(systemStatus.health.overall_status)}`}>
                {systemStatus.health.overall_status.toUpperCase()}
              </p>
            </div>

            <div className="bg-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-gray-300">Orchestrator</h3>
                {getStatusIcon(systemStatus.status, 'healthy')}
              </div>
              <p className="text-sm mt-1 text-white">
                {systemStatus.status === 'running' ? 'Running' : 'Stopped'}
              </p>
            </div>

            <div className="bg-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-gray-300">Uptime</h3>
                <ClockIcon className="h-5 w-5 text-blue-500" />
              </div>
              <p className="text-sm mt-1 text-white">
                {formatUptime(systemStatus.uptime)}
              </p>
            </div>
          </div>

          {/* Modules Summary */}
          <div className="bg-gray-700 rounded-lg p-4">
            <h3 className="text-lg font-medium text-white mb-4">Modules Summary</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-white">
                  {systemStatus.modules_summary.total}
                </div>
                <div className="text-sm text-gray-300">Total</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-500">
                  {systemStatus.modules_summary.running}
                </div>
                <div className="text-sm text-gray-300">Running</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-400">
                  {systemStatus.modules_summary.healthy}
                </div>
                <div className="text-sm text-gray-300">Healthy</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-500">
                  {systemStatus.health.modules_status.failed}
                </div>
                <div className="text-sm text-gray-300">Failed</div>
              </div>
            </div>
          </div>

          {/* Issues */}
          {systemStatus.health.issues.length > 0 && (
            <div className="bg-red-900/20 border border-red-700 rounded-lg p-4">
              <h3 className="text-lg font-medium text-red-400 mb-2">Issues</h3>
              <ul className="space-y-1">
                {systemStatus.health.issues.map((issue, index) => (
                  <li key={index} className="text-sm text-red-300 flex items-center">
                    <ExclamationTriangleIcon className="h-4 w-4 mr-2" />
                    {issue}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {selectedTab === 'modules' && (
        <div className="space-y-4">
          {Object.entries(moduleDetails).map(([name, module]) => (
            <div key={name} className="bg-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center">
                  {getStatusIcon(module.status, module.health)}
                  <h3 className="text-lg font-medium text-white ml-2">{module.name}</h3>
                </div>
                <div className="flex items-center space-x-4 text-sm text-gray-300">
                  {module.pid && (
                    <span>PID: {module.pid}</span>
                  )}
                  <span>Restarts: {module.restart_count}</span>
                </div>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">Status:</span>
                  <span className="ml-2 text-white">{module.status}</span>
                </div>
                <div>
                  <span className="text-gray-400">Health:</span>
                  <span className={`ml-2 ${getHealthColor(module.health)}`}>
                    {module.health}
                  </span>
                </div>
                <div>
                  <span className="text-gray-400">CPU:</span>
                  <span className="ml-2 text-white">{module.cpu_usage.toFixed(1)}%</span>
                </div>
                <div>
                  <span className="text-gray-400">Memory:</span>
                  <span className="ml-2 text-white">{formatMemory(module.memory_usage)}</span>
                </div>
              </div>

              {module.error_message && (
                <div className="mt-2 p-2 bg-red-900/20 border border-red-700 rounded text-sm text-red-300">
                  {module.error_message}
                </div>
              )}

              {module.start_time && (
                <div className="mt-2 text-xs text-gray-400">
                  Started: {new Date(module.start_time).toLocaleString()}
                </div>
              )}
            </div>
          ))}

          {Object.keys(moduleDetails).length === 0 && (
            <div className="text-center py-8 text-gray-400">
              No modules found
            </div>
          )}
        </div>
      )}

      {selectedTab === 'logs' && (
        <div className="bg-gray-900 rounded-lg p-4">
          <div className="text-center py-8 text-gray-400">
            <ServerIcon className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>Real-time logs will be implemented in future updates</p>
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="mt-6 pt-4 border-t border-gray-700 text-xs text-gray-400">
        Last updated: {systemStatus ? new Date(systemStatus.timestamp).toLocaleString() : 'Never'}
      </div>
    </div>
  )
}
