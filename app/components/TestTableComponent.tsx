'use client'

import { useState, useEffect } from 'react'
import SignalChart from './SignalChart'

interface ColumnSchema {
  column_name: string
  type_and_constraints: string
  description: string
  default_value?: any
  input_type: 'text' | 'number' | 'select' | 'textarea' | 'datetime'
  options?: string[]
}

const tableSchema: ColumnSchema[] = [
  { column_name: 'id', type_and_constraints: 'TEXT PRIMARY KEY', description: 'UUID виртуальной сделки', input_type: 'text', default_value: '' },
  { column_name: 'signal_id', type_and_constraints: 'TEXT', description: 'UUID исходного сообщения (если есть)', input_type: 'text', default_value: '' },
  { column_name: 'source', type_and_constraints: 'TEXT', description: 'канал/трейдер (e.g. tg_binance_killers)', input_type: 'text', default_value: '' },
  { column_name: 'source_type', type_and_constraints: 'TEXT', description: 'telegram | manual', input_type: 'select', options: ['telegram', 'manual'], default_value: 'telegram' },
  { column_name: 'source_name', type_and_constraints: 'TEXT', description: 'человекочитаемое имя канала', input_type: 'text', default_value: '' },
  { column_name: 'source_ref', type_and_constraints: 'TEXT', description: 'ссылка/ID в источнике', input_type: 'text', default_value: '' },
  { column_name: 'original_text', type_and_constraints: 'TEXT', description: 'сырой текст сигнала', input_type: 'textarea', default_value: '' },
  { column_name: 'signal_reason', type_and_constraints: 'TEXT', description: 'причина (из текста, опционально)', input_type: 'text', default_value: '' },
  { column_name: 'posted_ts', type_and_constraints: 'INTEGER', description: 'unix ms, время публикации сигнала', input_type: 'number', default_value: Math.floor(Date.now() / 1000) },
  { column_name: 'symbol', type_and_constraints: 'TEXT', description: 'XBTUSD', input_type: 'text', default_value: 'BTCUSDT' },
  { column_name: 'side', type_and_constraints: 'TEXT CHECK (side IN (\'LONG\',\'SHORT\'))', description: 'LONG / SHORT', input_type: 'select', options: ['LONG', 'SHORT'], default_value: 'LONG' },
  { column_name: 'entry_type', type_and_constraints: 'TEXT CHECK (entry_type IN (\'zone\',\'exact\')) DEFAULT \'zone\'', description: 'zone или exact (одна точка входа)', input_type: 'select', options: ['zone', 'exact'], default_value: 'zone' },
  { column_name: 'entry_min', type_and_constraints: 'REAL', description: 'нижняя граница зоны (или = entry_exact)', input_type: 'number', default_value: 0 },
  { column_name: 'entry_max', type_and_constraints: 'REAL', description: 'верхняя граница зоны (или = entry_exact)', input_type: 'number', default_value: 0 },
  { column_name: 'tp1', type_and_constraints: 'REAL', description: 'цель 1 (обычно 50%)', input_type: 'number', default_value: 0 },
  { column_name: 'tp2', type_and_constraints: 'REAL', description: 'цель 2 (обычно 50%)', input_type: 'number', default_value: 0 },
  { column_name: 'tp3', type_and_constraints: 'REAL', description: 'запасная цель (на будущее)', input_type: 'number', default_value: 0 },
  { column_name: 'targets_json', type_and_constraints: 'TEXT', description: 'все цели списком JSON', input_type: 'text', default_value: '[]' },
  { column_name: 'sl', type_and_constraints: 'REAL', description: 'стоп-лосс', input_type: 'number', default_value: 0 },
  { column_name: 'sl_type', type_and_constraints: 'TEXT DEFAULT \'hard\'', description: 'тип SL (обычно \'hard\', но можно \'mental\')', input_type: 'select', options: ['hard', 'mental'], default_value: 'hard' },
  { column_name: 'source_leverage', type_and_constraints: 'TEXT', description: 'как в тексте сигнала (например \'5-10x\')', input_type: 'text', default_value: '15x' },
  { column_name: 'strategy_id', type_and_constraints: 'TEXT DEFAULT \'S_A_TP1_BE_TP2\'', description: 'ID стратегии расчёта', input_type: 'text', default_value: 'S_A_TP1_BE_TP2' },
  { column_name: 'strategy_version', type_and_constraints: 'TEXT DEFAULT \'1\'', description: 'версия стратегии', input_type: 'text', default_value: '1' },
  { column_name: 'fee_rate', type_and_constraints: 'REAL DEFAULT 0.0005', description: 'комиссия за сделку (taker)', input_type: 'number', default_value: 0.0005 },
  { column_name: 'leverage', type_and_constraints: 'REAL DEFAULT 15', description: 'плечо (например 15x)', input_type: 'number', default_value: 15 },
  { column_name: 'margin_usd', type_and_constraints: 'REAL DEFAULT 100', description: 'сколько $ используется в сделке', input_type: 'number', default_value: 100 },
  { column_name: 'entry_timeout_sec', type_and_constraints: 'INTEGER DEFAULT 172800', description: 'сколько секунд ждём входа (по умолчанию 48ч)', input_type: 'number', default_value: 172800 },
  { column_name: 'was_fillable', type_and_constraints: 'INTEGER', description: 'достижим ли вход (цена коснулась зоны)', input_type: 'select', options: ['0', '1'], default_value: 1 },
  { column_name: 'entry_ts', type_and_constraints: 'INTEGER', description: 'unix ms, время входа в позицию', input_type: 'number', default_value: null },
  { column_name: 'entry_price', type_and_constraints: 'REAL', description: 'цена входа', input_type: 'number', default_value: null },
  { column_name: 'position_qty', type_and_constraints: 'REAL', description: 'размер позиции', input_type: 'number', default_value: null },
  { column_name: 'tp1_hit', type_and_constraints: 'INTEGER', description: 'достигнут ли TP1', input_type: 'select', options: ['0', '1'], default_value: 0 },
  { column_name: 'tp1_ts', type_and_constraints: 'INTEGER', description: 'время достижения TP1', input_type: 'number', default_value: null },
  { column_name: 'be_hit', type_and_constraints: 'INTEGER', description: 'перенесён ли SL в безубыток', input_type: 'select', options: ['0', '1'], default_value: 0 },
  { column_name: 'be_ts', type_and_constraints: 'INTEGER', description: 'время переноса в BE', input_type: 'number', default_value: null },
  { column_name: 'be_price', type_and_constraints: 'REAL', description: 'цена безубытка', input_type: 'number', default_value: null },
  { column_name: 'tp2_hit', type_and_constraints: 'INTEGER', description: 'достигнут ли TP2', input_type: 'select', options: ['0', '1'], default_value: 0 },
  { column_name: 'tp2_ts', type_and_constraints: 'INTEGER', description: 'время достижения TP2', input_type: 'number', default_value: null },
  { column_name: 'sl_hit', type_and_constraints: 'INTEGER', description: 'сработал ли стоп-лосс', input_type: 'select', options: ['0', '1'], default_value: 0 },
  { column_name: 'sl_ts', type_and_constraints: 'INTEGER', description: 'время срабатывания SL', input_type: 'number', default_value: null },
  { column_name: 'fee_open', type_and_constraints: 'REAL', description: 'комиссия за открытие', input_type: 'number', default_value: null },
  { column_name: 'fee_close', type_and_constraints: 'REAL', description: 'комиссия за закрытие', input_type: 'number', default_value: null },
  { column_name: 'fee_total', type_and_constraints: 'REAL', description: 'общая комиссия', input_type: 'number', default_value: null },
  { column_name: 'pnl_tp1', type_and_constraints: 'REAL', description: 'прибыль на TP1', input_type: 'number', default_value: null },
  { column_name: 'pnl_tp2', type_and_constraints: 'REAL', description: 'прибыль на TP2', input_type: 'number', default_value: null },
  { column_name: 'pnl_gross', type_and_constraints: 'REAL', description: 'валовая прибыль', input_type: 'number', default_value: null },
  { column_name: 'pnl_net', type_and_constraints: 'REAL', description: 'чистая прибыль', input_type: 'number', default_value: null },
  { column_name: 'roi_percent', type_and_constraints: 'REAL', description: 'ROI в процентах', input_type: 'number', default_value: null },
  { column_name: 'closed_ts', type_and_constraints: 'INTEGER', description: 'время закрытия позиции', input_type: 'number', default_value: null },
  { column_name: 'duration_sec', type_and_constraints: 'INTEGER', description: 'длительность сделки', input_type: 'number', default_value: null },
  { column_name: 'tp1_duration_sec', type_and_constraints: 'INTEGER', description: 'время до TP1', input_type: 'number', default_value: null },
  { column_name: 'tp2_duration_sec', type_and_constraints: 'INTEGER', description: 'время до TP2', input_type: 'number', default_value: null },
  { column_name: 'sl_duration_sec', type_and_constraints: 'INTEGER', description: 'время до SL', input_type: 'number', default_value: null },
  { column_name: 'status', type_and_constraints: 'TEXT', description: 'sim_open (running), sim_closed (finished), sim_skipped (not processed)', input_type: 'select', options: ['sim_open', 'sim_closed', 'sim_skipped'], default_value: 'sim_open' },
  { column_name: 'exit_reason', type_and_constraints: 'TEXT', description: 'причина выхода', input_type: 'text', default_value: '' },
  { column_name: 'tp_hit', type_and_constraints: 'TEXT', description: 'какие TP сработали', input_type: 'text', default_value: '' },
  { column_name: 'tp_count_hit', type_and_constraints: 'INTEGER', description: 'количество сработавших TP', input_type: 'number', default_value: 0 },
  { column_name: 'mfe_pct', type_and_constraints: 'REAL', description: 'максимальная благоприятная экскурсия', input_type: 'number', default_value: null },
  { column_name: 'mae_pct', type_and_constraints: 'REAL', description: 'максимальная неблагоприятная экскурсия', input_type: 'number', default_value: null },
  { column_name: 'reached_after_exit', type_and_constraints: 'TEXT', description: 'достигнутые уровни после выхода', input_type: 'text', default_value: '{}' },
  { column_name: 'created_at', type_and_constraints: 'TIMESTAMP', description: 'время создания записи', input_type: 'datetime', default_value: new Date().toISOString() },
  { column_name: 'updated_at', type_and_constraints: 'TIMESTAMP', description: 'время обновления записи', input_type: 'datetime', default_value: new Date().toISOString() }
]

export default function TestTableComponent() {
  const [selectedRecord, setSelectedRecord] = useState<any>(null)
  const [selectedSignalForChart, setSelectedSignalForChart] = useState<string | null>(null)
  const [savedRecords, setSavedRecords] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [isAutoRefresh, setIsAutoRefresh] = useState(true)
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)
  const [refreshing, setRefreshing] = useState(false)

  // Загружаем сохраненные записи при инициализации
  useEffect(() => {
    fetchSavedRecords()
  }, [])

  // Автообновление каждые 30 секунд
  useEffect(() => {
    if (!isAutoRefresh) return

    const interval = setInterval(() => {
      fetchSavedRecords(true) // true = silent refresh
    }, 30000) // 30 секунд

    return () => clearInterval(interval)
  }, [isAutoRefresh])

  const fetchSavedRecords = async (silent: boolean = false) => {
    try {
      if (!silent) {
        setLoading(true)
      } else {
        setRefreshing(true)
      }
      
      const response = await fetch('/api/test-table')
      const result = await response.json()
      if (result.data) {
        setSavedRecords(result.data)
        setLastRefresh(new Date())
      }
    } catch (error) {
      console.error('Error fetching saved records:', error)
    } finally {
      if (!silent) {
        setLoading(false)
      } else {
        setRefreshing(false)
      }
    }
  }

  const handleManualRefresh = () => {
    fetchSavedRecords(false)
  }

  const handleRecordClick = (record: any) => {
    setSelectedRecord(record)
    
    // Автоматически показываем график для выбранного сигнала
    if (record && record.id) {
      setSelectedSignalForChart(record.id)
    }
  }

  const handleTrackingToggle = (signalId: string, isTracking: boolean) => {
    // Обновляем данные таблицы при изменении статуса отслеживания
    fetchSavedRecords()
  }

  const getFieldValue = (fieldName: string) => {
    if (!selectedRecord) return ''
    const value = selectedRecord[fieldName]
    if (value === null || value === undefined) return ''
    return String(value)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gray-900/50 backdrop-blur-sm rounded-2xl p-4 border border-gray-800/50">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white">🧪 v_trades Viewer</h2>
            <p className="text-gray-400 text-sm mt-1">
              {selectedRecord 
                ? `Просмотр записи: ${selectedRecord.id?.substring(0, 8) || 'N/A'}...` 
                : 'Выберите запись из списка для просмотра графика и полей'}
            </p>
            {/* Индикатор обновления */}
            <div className="flex items-center gap-3 mt-2">
              {lastRefresh && (
                <div className="text-xs text-gray-500">
                  Обновлено: {lastRefresh.toLocaleTimeString('ru-RU')}
                </div>
              )}
              {refreshing && (
                <div className="flex items-center gap-1 text-xs text-blue-400">
                  <div className="animate-spin w-3 h-3 border border-blue-400/30 border-t-blue-400 rounded-full"></div>
                  Обновление...
                </div>
              )}
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            {/* Кнопки управления обновлением */}
            <div className="flex items-center gap-2">
              <button
                onClick={handleManualRefresh}
                disabled={loading || refreshing}
                className="flex items-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-600/50 text-white rounded-lg text-sm font-medium transition-colors"
              >
                <div className={`w-4 h-4 ${(loading || refreshing) ? 'animate-spin' : ''}`}>
                  🔄
                </div>
                Обновить
              </button>
              
              <button
                onClick={() => setIsAutoRefresh(!isAutoRefresh)}
                className={`flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                  isAutoRefresh 
                    ? 'bg-green-600 hover:bg-green-700 text-white' 
                    : 'bg-gray-600 hover:bg-gray-700 text-gray-300'
                }`}
              >
                <div className="w-4 h-4">
                  {isAutoRefresh ? '⏰' : '⏸️'}
                </div>
                {isAutoRefresh ? 'Авто (30с)' : 'Выкл'}
              </button>
            </div>

            {/* График индикатор */}
            {selectedSignalForChart && (
              <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-4 py-2 rounded-xl text-sm font-semibold shadow-lg">
                📊 График: {selectedRecord?.symbol || 'Unknown'}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Interactive Signal Chart */}
      <SignalChart 
        signalId={selectedSignalForChart} 
        onTrackingToggle={handleTrackingToggle}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Records List */}
        <div className="lg:col-span-1">
          <div className="bg-black rounded-2xl border border-gray-800 overflow-hidden">
            <div className="p-4 bg-gray-900/50 border-b border-gray-800">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-gray-300">📋 Записи v_trades</h3>
                  <div className="text-xs text-gray-500 mt-1">
                    {loading ? 'Загрузка...' : `${savedRecords.length} записей`}
                  </div>
                </div>
                {refreshing && !loading && (
                  <div className="flex items-center gap-1 text-xs text-blue-400">
                    <div className="animate-spin w-3 h-3 border border-blue-400/30 border-t-blue-400 rounded-full"></div>
                    Обновление
                  </div>
                )}
              </div>
            </div>
            
            <div className="max-h-96 overflow-y-auto">
              {loading ? (
                <div className="p-4 text-center text-gray-400">
                  <div className="animate-pulse">Загружаем записи...</div>
                </div>
              ) : savedRecords.length === 0 ? (
                <div className="p-4 text-center text-gray-500">
                  Нет записей в v_trades
                </div>
              ) : (
                <div className="divide-y divide-gray-800/30">
                  {savedRecords.map((record, index) => (
                    <div
                      key={record.id || index}
                      onClick={() => handleRecordClick(record)}
                      className={`p-3 cursor-pointer hover:bg-gray-900/30 transition-colors relative ${
                        selectedRecord?.id === record.id ? 'bg-blue-900/30 border-l-2 border-l-blue-500' : ''
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          {/* Номер сигнала */}
                          <div className="flex-shrink-0">
                            <span className="text-gray-500 text-xs font-mono leading-none">
                              {String(savedRecords.length - index).padStart(3, '0')}
                            </span>
                          </div>
                          {/* Основная информация */}
                          <div>
                            <div className="text-blue-400 font-medium text-sm">
                              {record.symbol || 'N/A'}
                            </div>
                            <div className="text-gray-400 text-xs">
                              {record.id?.substring(0, 12) || 'N/A'}...
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="flex flex-col gap-1">
                            <div className={`px-2 py-1 rounded text-xs font-medium ${
                              record.side === 'LONG' 
                                ? 'bg-green-900/50 text-green-400' 
                                : 'bg-red-900/50 text-red-400'
                            }`}>
                              {record.side || 'N/A'}
                            </div>
                            
                            {/* Status indicator */}
                            <div className={`px-2 py-1 rounded text-xs font-medium text-center ${
                              record.status === 'cancelled' || record.was_fillable === 0
                                ? 'bg-red-900/30 text-red-400 border border-red-400/20' 
                                : 'bg-green-900/30 text-green-400 border border-green-400/20'
                            }`}>
                              {record.status === 'cancelled' || record.was_fillable === 0 ? '❌ INVALID' : '✅ VALID'}
                            </div>
                            
                            <div className="text-gray-500 text-xs">
                              {record.created_at 
                                ? new Date(record.created_at).toLocaleDateString('ru-RU') 
                                : 'N/A'
                              }
                            </div>
                          </div>
                        </div>
                        
                        {/* Chart indicator */}
                        {selectedRecord?.id === record.id && (
                          <div className="absolute right-2 top-2">
                            <div className="bg-blue-500/20 text-blue-400 px-1 py-0.5 rounded text-xs">
                              📊
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Field Details Table */}
        <div className="lg:col-span-2">
          <div className="bg-black rounded-2xl border border-gray-800 overflow-hidden">
            <div className="p-4 bg-gray-900/50 border-b border-gray-800">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-gray-300">📊 Поля записи</h3>
                <div className="text-xs text-gray-500">{tableSchema.length} полей</div>
              </div>
            </div>
            
            <div className="overflow-x-auto max-h-96 overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-gray-900/50">
                  <tr className="bg-gray-900/30">
                    <th className="px-4 py-3 text-left text-gray-400 font-medium text-xs uppercase tracking-wide">
                      column_name
                    </th>
                    <th className="px-4 py-3 text-left text-gray-400 font-medium text-xs uppercase tracking-wide">
                      type_and_constraints
                    </th>
                    <th className="px-4 py-3 text-left text-gray-400 font-medium text-xs uppercase tracking-wide">
                      description
                    </th>
                    <th className="px-4 py-3 text-left text-gray-400 font-medium text-xs uppercase tracking-wide">
                      value
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800/30">
                  {tableSchema.map((field, index) => (
                    <tr 
                      key={field.column_name} 
                      className="hover:bg-gray-900/20 transition-colors"
                    >
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <span className="text-white font-medium">{field.column_name}</span>
                          {field.column_name === 'id' && (
                            <span className="text-yellow-500 text-xs">🔑</span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-blue-400 font-mono text-xs">
                          {field.type_and_constraints}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-gray-300 text-xs">
                          {field.description}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="bg-gray-800/50 rounded px-3 py-2 text-gray-300 font-mono text-xs">
                          {getFieldValue(field.column_name) || (
                            <span className="text-gray-500 italic">пусто</span>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-4 border border-gray-800/50">
          <div className="text-2xl font-bold text-blue-400">{tableSchema.length}</div>
          <div className="text-xs text-gray-400">Total Fields</div>
        </div>
        <div className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-4 border border-gray-800/50">
          <div className="text-2xl font-bold text-green-400">{savedRecords.length}</div>
          <div className="text-xs text-gray-400">Test Records</div>
        </div>
        <div className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-4 border border-gray-800/50">
          <div className="text-2xl font-bold text-yellow-400">
            {savedRecords.filter(r => r.side === 'LONG').length}
          </div>
          <div className="text-xs text-gray-400">Long Trades</div>
        </div>
        <div className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-4 border border-gray-800/50">
          <div className="text-2xl font-bold text-purple-400">
            {selectedRecord ? '1' : '0'}
          </div>
          <div className="text-xs text-gray-400">Selected</div>
        </div>
        <div className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-4 border border-gray-800/50">
          <div className="text-2xl font-bold text-cyan-400">
            {isAutoRefresh ? '⏰' : '⏸️'}
          </div>
          <div className="text-xs text-gray-400">
            {isAutoRefresh ? 'Авто обновление' : 'Ручное обновление'}
          </div>
        </div>
      </div>
    </div>
  )
}