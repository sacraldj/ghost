import { NextRequest, NextResponse } from 'next/server'
import Redis from 'ioredis'

// Инициализация Redis клиента (опционально)
let redis: Redis | null = null

try {
  if (process.env.REDIS_URL) {
    redis = new Redis(process.env.REDIS_URL)
  }
} catch (error) {
  console.warn('Redis connection failed:', error)
}

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

interface SystemStatus {
  timestamp: string
  orchestrator_status: string
  system_metrics: {
    start_time: string
    total_restarts: number
    uptime: number
    modules_healthy: number
    modules_total: number
  }
  modules: Record<string, ModuleStatus>
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
    cpu_usage?: number
    memory_usage?: number
    disk_usage?: number
    uptime: number
  }
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const detail = searchParams.get('detail') === 'true'
    const component = searchParams.get('component') // 'orchestrator', 'modules', 'health'
    
    let systemStatus: SystemStatus | null = null
    
    // Получаем данные из Redis
    if (redis) {
      try {
        const statusData = await redis.get('ghost:orchestrator:status')
        if (statusData) {
          systemStatus = JSON.parse(statusData)
        }
      } catch (error) {
        console.error('Failed to get system status from Redis:', error)
      }
    }
    
    // Если данных нет в Redis, возвращаем базовый статус
    if (!systemStatus) {
      systemStatus = {
        timestamp: new Date().toISOString(),
        orchestrator_status: 'unknown',
        system_metrics: {
          start_time: new Date().toISOString(),
          total_restarts: 0,
          uptime: 0,
          modules_healthy: 0,
          modules_total: 0
        },
        modules: {}
      }
    }
    
    // Возвращаем данные в зависимости от запрошенного компонента
    switch (component) {
      case 'orchestrator':
        return NextResponse.json({
          status: systemStatus.orchestrator_status,
          metrics: systemStatus.system_metrics,
          timestamp: systemStatus.timestamp
        })
      
      case 'modules':
        return NextResponse.json({
          modules: systemStatus.modules,
          summary: {
            total: Object.keys(systemStatus.modules).length,
            running: Object.values(systemStatus.modules).filter(m => m.status === 'running').length,
            healthy: Object.values(systemStatus.modules).filter(m => m.health === 'healthy').length,
            failed: Object.values(systemStatus.modules).filter(m => m.status === 'failed').length
          },
          timestamp: systemStatus.timestamp
        })
      
      case 'health':
        const healthStatus = calculateSystemHealth(systemStatus)
        return NextResponse.json(healthStatus)
      
      default:
        // Полный статус
        if (detail) {
          return NextResponse.json(systemStatus)
        } else {
          // Краткий статус
          return NextResponse.json({
            status: systemStatus.orchestrator_status,
            health: calculateSystemHealth(systemStatus),
            modules_summary: {
              total: Object.keys(systemStatus.modules).length,
              running: Object.values(systemStatus.modules).filter(m => m.status === 'running').length,
              healthy: Object.values(systemStatus.modules).filter(m => m.health === 'healthy').length
            },
            uptime: systemStatus.system_metrics.uptime,
            timestamp: systemStatus.timestamp
          })
        }
    }
    
  } catch (error) {
    console.error('System status API error:', error)
    return NextResponse.json(
      { 
        error: 'Failed to get system status',
        details: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString()
      }, 
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const { action, module } = await request.json()
    
    // В будущем здесь можно добавить команды управления системой
    // Например: restart модуля, изменение конфигурации и т.д.
    
    switch (action) {
      case 'restart_module':
        if (!module) {
          return NextResponse.json(
            { error: 'Module name is required for restart action' },
            { status: 400 }
          )
        }
        
        // Здесь будет логика перезапуска модуля через Redis команды
        // или API вызовы к оркестратору
        return NextResponse.json({
          message: `Restart command sent for module: ${module}`,
          timestamp: new Date().toISOString()
        })
      
      case 'get_logs':
        if (!module) {
          return NextResponse.json(
            { error: 'Module name is required for logs action' },
            { status: 400 }
          )
        }
        
        // Здесь будет получение логов модуля
        return NextResponse.json({
          module,
          logs: [], // В будущем - реальные логи
          timestamp: new Date().toISOString()
        })
      
      default:
        return NextResponse.json(
          { error: `Unknown action: ${action}` },
          { status: 400 }
        )
    }
    
  } catch (error) {
    console.error('System control API error:', error)
    return NextResponse.json(
      { 
        error: 'Failed to execute system command',
        details: error instanceof Error ? error.message : 'Unknown error'
      }, 
      { status: 500 }
    )
  }
}

function calculateSystemHealth(systemStatus: SystemStatus): SystemHealth {
  const modules = Object.values(systemStatus.modules)
  const issues: string[] = []
  
  // Подсчёт статистики модулей
  const modulesStats = {
    total: modules.length,
    running: modules.filter(m => m.status === 'running').length,
    healthy: modules.filter(m => m.health === 'healthy').length,
    failed: modules.filter(m => m.status === 'failed').length
  }
  
  // Проверка проблем
  if (systemStatus.orchestrator_status !== 'running') {
    issues.push('Orchestrator is not running')
  }
  
  if (modulesStats.failed > 0) {
    issues.push(`${modulesStats.failed} module(s) failed`)
  }
  
  const unhealthyModules = modulesStats.total - modulesStats.healthy
  if (unhealthyModules > 0) {
    issues.push(`${unhealthyModules} module(s) unhealthy`)
  }
  
  // Проверка высокого количества перезапусков
  if (systemStatus.system_metrics.total_restarts > 10) {
    issues.push(`High restart count: ${systemStatus.system_metrics.total_restarts}`)
  }
  
  // Проверка CPU и памяти (если доступно)
  modules.forEach(module => {
    if (module.cpu_usage > 80) {
      issues.push(`High CPU usage in ${module.name}: ${module.cpu_usage.toFixed(1)}%`)
    }
    if (module.memory_usage > 500) { // > 500MB
      issues.push(`High memory usage in ${module.name}: ${(module.memory_usage / 1024).toFixed(1)}GB`)
    }
  })
  
  // Расчёт общего балла здоровья
  let healthScore = 100
  
  // Штрафы за проблемы
  if (systemStatus.orchestrator_status !== 'running') {
    healthScore -= 50
  }
  
  healthScore -= modulesStats.failed * 20
  healthScore -= (modulesStats.total - modulesStats.healthy) * 10
  healthScore -= Math.min(systemStatus.system_metrics.total_restarts, 10) * 2
  
  healthScore = Math.max(0, Math.min(100, healthScore))
  
  // Определение общего статуса
  let overallStatus: 'healthy' | 'warning' | 'critical' | 'unknown'
  
  if (systemStatus.orchestrator_status === 'unknown') {
    overallStatus = 'unknown'
  } else if (healthScore >= 80 && issues.length === 0) {
    overallStatus = 'healthy'
  } else if (healthScore >= 60 || modulesStats.failed === 0) {
    overallStatus = 'warning'
  } else {
    overallStatus = 'critical'
  }
  
  return {
    overall_status: overallStatus,
    health_score: healthScore,
    issues,
    modules_status: modulesStats,
    system_metrics: {
      uptime: systemStatus.system_metrics.uptime
    }
  }
}
