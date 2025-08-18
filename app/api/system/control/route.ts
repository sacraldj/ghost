import { NextRequest, NextResponse } from 'next/server'
import { spawn, exec } from 'child_process'
import { promises as fs } from 'fs'
import path from 'path'

interface SystemControlRequest {
  action: 'start' | 'stop' | 'restart' | 'status'
  component?: 'telegram' | 'news' | 'all'
}

interface SystemControlResponse {
  success: boolean
  message: string
  data?: any
  timestamp: string
}

// Хранение PID процессов
const PIDS_FILE = path.join(process.cwd(), 'pids', 'system.json')
const SYSTEM_STATUS_FILE = path.join(process.cwd(), 'logs', 'system_control.json')

async function ensurePidsDir() {
  const pidsDir = path.dirname(PIDS_FILE)
  try {
    await fs.mkdir(pidsDir, { recursive: true })
  } catch (error) {
    // Directory already exists, that's ok
  }
}

async function savePids(pids: Record<string, number>) {
  await ensurePidsDir()
  await fs.writeFile(PIDS_FILE, JSON.stringify(pids, null, 2))
}

async function loadPids(): Promise<Record<string, number>> {
  try {
    const data = await fs.readFile(PIDS_FILE, 'utf-8')
    return JSON.parse(data)
  } catch (error) {
    return {}
  }
}

async function saveSystemStatus(status: any) {
  const logsDir = path.dirname(SYSTEM_STATUS_FILE)
  try {
    await fs.mkdir(logsDir, { recursive: true })
  } catch (error) {
    // Directory already exists
  }
  await fs.writeFile(SYSTEM_STATUS_FILE, JSON.stringify(status, null, 2))
}

async function checkProcessExists(pid: number): Promise<boolean> {
  return new Promise((resolve) => {
    exec(`ps -p ${pid}`, (error) => {
      resolve(!error)
    })
  })
}

async function startTelegramSystem(): Promise<{ success: boolean; message: string; pid?: number }> {
  return new Promise((resolve) => {
    // Запускаем start_all.py в фоне
    const child = spawn('python3', ['start_all.py'], {
      cwd: process.cwd(),
      detached: true,
      stdio: ['ignore', 'pipe', 'pipe']
    })

    child.unref() // Позволяет основному процессу завершиться

    // Сохраняем PID
    if (child.pid) {
      savePids({ telegram_system: child.pid }).catch(console.error)
    }

    // Даем время на запуск
    setTimeout(async () => {
      if (child.pid && await checkProcessExists(child.pid)) {
        resolve({
          success: true,
          message: `Ghost Telegram System started successfully (PID: ${child.pid})`,
          pid: child.pid
        })
      } else {
        resolve({
          success: false,
          message: 'Failed to start Ghost Telegram System'
        })
      }
    }, 3000)

    child.on('error', (error) => {
      resolve({
        success: false,
        message: `Failed to start system: ${error.message}`
      })
    })
  })
}

async function stopTelegramSystem(): Promise<{ success: boolean; message: string }> {
  const pids = await loadPids()
  const telegramPid = pids.telegram_system

  if (!telegramPid) {
    return {
      success: false,
      message: 'No Telegram system PID found'
    }
  }

  return new Promise((resolve) => {
    exec(`kill ${telegramPid}`, async (error) => {
      if (error) {
        resolve({
          success: false,
          message: `Failed to stop system: ${error.message}`
        })
      } else {
        // Удаляем PID из файла
        delete pids.telegram_system
        await savePids(pids)
        
        resolve({
          success: true,
          message: `Ghost Telegram System stopped successfully (PID: ${telegramPid})`
        })
      }
    })
  })
}

async function getSystemStatus() {
  const pids = await loadPids()
  const telegramPid = pids.telegram_system
  
  let isRunning = false
  let healthStatus = 'unknown'
  
  if (telegramPid) {
    isRunning = await checkProcessExists(telegramPid)
    if (isRunning) {
      // Проверяем health endpoint
      try {
        const response = await fetch('http://localhost:8000/health', {
          signal: AbortSignal.timeout(2000)
        })
        healthStatus = response.ok ? 'healthy' : 'warning'
      } catch (error) {
        healthStatus = 'warning'
      }
    }
  }

  // Получаем дополнительную информацию о системе
  let channelsCount = 0
  let lastSignalTime = null
  
  try {
    // Чтение статуса каналов из логов
    const logsPath = path.join(process.cwd(), 'logs', 'ghost_unified_system.log')
    const logs = await fs.readFile(logsPath, 'utf-8')
    
    // Подсчет каналов
    const channelMatches = logs.match(/Added channel:/g)
    channelsCount = channelMatches ? channelMatches.length : 0
    
    // Последний сигнал
    const signalMatches = logs.match(/Signal detected from .+ (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})/g)
    if (signalMatches && signalMatches.length > 0) {
      const lastMatch = signalMatches[signalMatches.length - 1]
      const timeMatch = lastMatch.match(/(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})/)
      if (timeMatch) {
        lastSignalTime = timeMatch[1]
      }
    }
  } catch (error) {
    console.log('Could not read system logs:', error)
  }

  return {
    status: isRunning ? 'running' : 'stopped',
    health: healthStatus,
    pid: isRunning ? telegramPid : null,
    uptime: isRunning ? Date.now() - (pids.start_time || Date.now()) : 0,
    channels_count: channelsCount,
    last_signal_time: lastSignalTime,
    timestamp: new Date().toISOString()
  }
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const component = searchParams.get('component') || 'all'
    
    const systemStatus = await getSystemStatus()
    
    const response: SystemControlResponse = {
      success: true,
      message: 'System status retrieved successfully',
      data: {
        telegram_system: systemStatus,
        component,
      },
      timestamp: new Date().toISOString()
    }

    return NextResponse.json(response)
  } catch (error) {
    console.error('System control GET error:', error)
    return NextResponse.json({
      success: false,
      message: 'Failed to get system status',
      timestamp: new Date().toISOString()
    }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body: SystemControlRequest = await request.json()
    const { action, component = 'telegram' } = body
    
    let result: { success: boolean; message: string; pid?: number }

    switch (action) {
      case 'start':
        if (component === 'telegram' || component === 'all') {
          result = await startTelegramSystem()
          
          // Сохраняем время запуска
          if (result.success) {
            const pids = await loadPids()
            pids.start_time = Date.now()
            await savePids(pids)
          }
        } else {
          result = { success: false, message: 'Unknown component' }
        }
        break

      case 'stop':
        if (component === 'telegram' || component === 'all') {
          result = await stopTelegramSystem()
        } else {
          result = { success: false, message: 'Unknown component' }
        }
        break

      case 'restart':
        if (component === 'telegram' || component === 'all') {
          const stopResult = await stopTelegramSystem()
          await new Promise(resolve => setTimeout(resolve, 2000)) // Ждем 2 секунды
          const startResult = await startTelegramSystem()
          
          result = {
            success: stopResult.success && startResult.success,
            message: `Restart: ${stopResult.message} -> ${startResult.message}`,
            pid: startResult.pid
          }
        } else {
          result = { success: false, message: 'Unknown component' }
        }
        break

      case 'status':
        const status = await getSystemStatus()
        result = {
          success: true,
          message: 'Status retrieved',
        }
        
        return NextResponse.json({
          success: true,
          message: 'System status retrieved',
          data: status,
          timestamp: new Date().toISOString()
        })

      default:
        result = { success: false, message: `Unknown action: ${action}` }
    }

    // Сохраняем статус операции
    await saveSystemStatus({
      last_action: action,
      last_action_time: new Date().toISOString(),
      last_action_result: result,
      component
    })

    const response: SystemControlResponse = {
      ...result,
      timestamp: new Date().toISOString()
    }

    return NextResponse.json(response)
    
  } catch (error) {
    console.error('System control POST error:', error)
    return NextResponse.json({
      success: false,
      message: 'System control operation failed',
      timestamp: new Date().toISOString()
    }, { status: 500 })
  }
}
