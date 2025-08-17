'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import GhostLayout from '@/app/components/GhostLayout'
import TraderDetailModal from '@/app/components/TraderDetailModal'

export default function TraderDetailPage() {
  const params = useParams()
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [traderExists, setTraderExists] = useState(false)
  
  const traderId = params.traderId as string

  useEffect(() => {
    // Проверяем существует ли трейдер
    checkTraderExists()
  }, [traderId])

  const checkTraderExists = async () => {
    try {
      const response = await fetch(`/api/traders?traderId=${traderId}`)
      const data = await response.json()
      
      // Проверяем существует ли трейдер
      if (data.success && data.trader) {
        setTraderExists(true)
      } else {
        // Для демо - всегда показываем трейдера
        setTraderExists(true)
      }
    } catch (error) {
      console.error('Error checking trader:', error)
      // Для демо - всегда показываем трейдера
      setTraderExists(true)
    }
    setLoading(false)
  }

  const handleClose = () => {
    router.push('/')
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="animate-spin w-8 h-8 border-4 border-yellow-500 border-t-transparent rounded-full"></div>
          <div className="text-yellow-500 font-bold">Loading Trader Details...</div>
        </div>
      </div>
    )
  }

  if (!traderExists) {
    return (
      <GhostLayout currentPage="traders">
        <div className="p-6">
          <div className="max-w-2xl mx-auto text-center">
            <div className="text-6xl mb-4">❌</div>
            <h1 className="text-2xl font-bold text-white mb-2">Трейдер не найден</h1>
            <p className="text-gray-400 mb-6">
              Трейдер с ID "{traderId}" не существует в системе.
            </p>
            <button
              onClick={handleClose}
              className="bg-yellow-500 text-black px-6 py-3 rounded-lg font-medium hover:bg-yellow-400 transition-colors"
            >
              ← Вернуться к списку трейдеров
            </button>
          </div>
        </div>
      </GhostLayout>
    )
  }

  return (
    <GhostLayout currentPage="traders">
      <div className="relative">
        {/* Используем TraderDetailModal как полноэкранный компонент */}
        <TraderDetailModal
          traderId={traderId}
          isOpen={true}
          onClose={handleClose}
        />
        
        {/* Фон для имитации модального окна */}
        <div className="fixed inset-0 bg-black bg-opacity-30 -z-10"></div>
      </div>
    </GhostLayout>
  )
}
