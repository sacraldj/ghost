'use client'

import { useState, useEffect } from 'react'
import { Button } from './ui/button'

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
  const [formData, setFormData] = useState<Record<string, any>>(() => {
    const initialData: Record<string, any> = {}
    tableSchema.forEach(field => {
      initialData[field.column_name] = field.default_value
    })
    return initialData
  })
  const [saving, setSaving] = useState(false)
  const [savedRecords, setSavedRecords] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  // Загружаем сохраненные записи при инициализации
  useEffect(() => {
    fetchSavedRecords()
  }, [])

  const fetchSavedRecords = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/test-table')
      const result = await response.json()
      if (result.data) {
        setSavedRecords(result.data)
      }
    } catch (error) {
      console.error('Error fetching saved records:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (fieldName: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [fieldName]: value
    }))
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      // Генерируем уникальный ID если не заполнен
      if (!formData.id) {
        formData.id = `trade_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      }

      const response = await fetch('/api/test-table', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      })
      
      const result = await response.json()
      
      if (response.ok) {
        alert('✅ Record saved successfully!')
        // Сбрасываем форму
        const resetData: Record<string, any> = {}
        tableSchema.forEach(field => {
          resetData[field.column_name] = field.default_value
        })
        setFormData(resetData)
        // Обновляем список записей
        await fetchSavedRecords()
      } else {
        alert('❌ Error: ' + result.error)
      }
    } catch (error) {
      console.error('Error saving record:', error)
      alert('❌ Network error')
    } finally {
      setSaving(false)
    }
  }

  const renderInput = (field: ColumnSchema) => {
    const value = formData[field.column_name] ?? ''
    const commonClasses = "w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm"

    switch (field.input_type) {
      case 'select':
        return (
          <select
            className={commonClasses}
            value={value}
            onChange={(e) => handleInputChange(field.column_name, e.target.value)}
          >
            {field.options?.map(option => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        )
      
      case 'number':
        return (
          <input
            type="number"
            step="any"
            className={commonClasses}
            value={value || ''}
            onChange={(e) => handleInputChange(field.column_name, e.target.value ? parseFloat(e.target.value) : null)}
            placeholder={field.description}
          />
        )
      
      case 'textarea':
        return (
          <textarea
            className={commonClasses}
            rows={2}
            value={value}
            onChange={(e) => handleInputChange(field.column_name, e.target.value)}
            placeholder={field.description}
          />
        )
      
      case 'datetime':
        return (
          <input
            type="datetime-local"
            className={commonClasses}
            value={value ? new Date(value).toISOString().slice(0, 16) : ''}
            onChange={(e) => handleInputChange(field.column_name, e.target.value ? new Date(e.target.value).toISOString() : '')}
          />
        )
      
      default: // text
        return (
          <input
            type="text"
            className={commonClasses}
            value={value}
            onChange={(e) => handleInputChange(field.column_name, e.target.value)}
            placeholder={field.description}
          />
        )
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gray-900/50 backdrop-blur-sm rounded-2xl p-4 border border-gray-800/50">
        <h2 className="text-lg font-semibold text-white">💾 Add New Record to v_trades</h2>
        <p className="text-gray-400 text-sm mt-1">Заполните поля и нажмите Save для сохранения в Supabase</p>
      </div>

      {/* Editable Table */}
      <div className="bg-black rounded-2xl border border-gray-800 overflow-hidden">
        <div className="p-4 bg-gray-900/50 border-b border-gray-800">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-medium text-gray-300">СИГНАЛ - 2TRADE</h2>
            <div className="text-xs text-gray-500">{tableSchema.length} columns</div>
          </div>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
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
                    {renderInput(field)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Save Button Under Table */}
      <div className="bg-gray-900/50 backdrop-blur-sm rounded-2xl p-4 border border-gray-800/50">
        <div className="flex justify-center">
          <Button
            onClick={handleSave}
            disabled={saving}
            className="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white px-8 py-3 rounded-lg font-semibold text-lg"
          >
            {saving ? '💾 Сохранение...' : '💾 Сохранить'}
          </Button>
        </div>
      </div>

      {/* Saved Records List */}
      <div className="bg-black rounded-2xl border border-gray-800 overflow-hidden">
        <div className="p-4 bg-gray-900/50 border-b border-gray-800">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white">📋 Сохраненные записи</h2>
            <div className="text-sm text-gray-400">
              {loading ? 'Загружаем...' : `${savedRecords.length} записей`}
            </div>
          </div>
        </div>
        
        {loading ? (
          <div className="p-8 text-center text-gray-400">
            <div className="animate-pulse">Загружаем записи...</div>
          </div>
        ) : savedRecords.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            Пока нет сохраненных записей. Создайте первую запись выше!
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-900/30">
                  <th className="px-4 py-3 text-left text-gray-400 font-medium text-xs uppercase tracking-wide">
                    ID
                  </th>
                  <th className="px-4 py-3 text-left text-gray-400 font-medium text-xs uppercase tracking-wide">
                    Symbol
                  </th>
                  <th className="px-4 py-3 text-left text-gray-400 font-medium text-xs uppercase tracking-wide">
                    Side
                  </th>
                  <th className="px-4 py-3 text-left text-gray-400 font-medium text-xs uppercase tracking-wide">
                    Entry Min
                  </th>
                  <th className="px-4 py-3 text-left text-gray-400 font-medium text-xs uppercase tracking-wide">
                    Entry Max
                  </th>
                  <th className="px-4 py-3 text-left text-gray-400 font-medium text-xs uppercase tracking-wide">
                    TP1
                  </th>
                  <th className="px-4 py-3 text-left text-gray-400 font-medium text-xs uppercase tracking-wide">
                    TP2
                  </th>
                  <th className="px-4 py-3 text-left text-gray-400 font-medium text-xs uppercase tracking-wide">
                    SL
                  </th>
                  <th className="px-4 py-3 text-left text-gray-400 font-medium text-xs uppercase tracking-wide">
                    Status
                  </th>
                  <th className="px-4 py-3 text-left text-gray-400 font-medium text-xs uppercase tracking-wide">
                    Created
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/30">
                {savedRecords.map((record, index) => (
                  <tr key={record.id || index} className="hover:bg-gray-900/20 transition-colors">
                    <td className="px-4 py-3 text-gray-300 font-mono text-xs">
                      {record.id?.substring(0, 8)}...
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-blue-400 font-medium">{record.symbol || 'N/A'}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        record.side === 'LONG' 
                          ? 'bg-green-900/50 text-green-400' 
                          : 'bg-red-900/50 text-red-400'
                      }`}>
                        {record.side || 'N/A'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-300">{record.entry_min || 'N/A'}</td>
                    <td className="px-4 py-3 text-gray-300">{record.entry_max || 'N/A'}</td>
                    <td className="px-4 py-3 text-green-400">{record.tp1 || 'N/A'}</td>
                    <td className="px-4 py-3 text-green-400">{record.tp2 || 'N/A'}</td>
                    <td className="px-4 py-3 text-red-400">{record.sl || 'N/A'}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        record.status === 'sim_open' 
                          ? 'bg-blue-900/50 text-blue-400' 
                          : record.status === 'sim_closed'
                          ? 'bg-gray-900/50 text-gray-400'
                          : 'bg-yellow-900/50 text-yellow-400'
                      }`}>
                        {record.status || 'N/A'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-400 text-xs">
                      {record.created_at 
                        ? new Date(record.created_at).toLocaleDateString('ru-RU')
                        : 'N/A'
                      }
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-4 border border-gray-800/50">
          <div className="text-2xl font-bold text-blue-400">{tableSchema.length}</div>
          <div className="text-xs text-gray-400">Total Fields</div>
        </div>
        <div className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-4 border border-gray-800/50">
          <div className="text-2xl font-bold text-green-400">{savedRecords.length}</div>
          <div className="text-xs text-gray-400">Saved Records</div>
        </div>
        <div className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-4 border border-gray-800/50">
          <div className="text-2xl font-bold text-yellow-400">
            {savedRecords.filter(r => r.side === 'LONG').length}
          </div>
          <div className="text-xs text-gray-400">Long Trades</div>
        </div>
        <div className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-4 border border-gray-800/50">
          <div className="text-2xl font-bold text-purple-400">
            {savedRecords.filter(r => r.side === 'SHORT').length}
          </div>
          <div className="text-xs text-gray-400">Short Trades</div>
        </div>
      </div>
    </div>
  )
}
