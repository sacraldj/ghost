'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'

export default function SimpleLogin() {
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()

  const handleDirectLogin = async () => {
    setIsLoading(true)
    
    // Имитируем загрузку
    setTimeout(() => {
      setIsLoading(false)
      router.push('/dashboard')
    }, 1000)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#0a0a0a] via-[#1a1a1a] to-[#0f0f23] p-4">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="glass rounded-2xl p-8 w-full max-w-md text-center"
      >
        <motion.div 
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
          className="w-16 h-16 bg-gradient-to-r from-[#667eea] to-[#764ba2] rounded-xl flex items-center justify-center mx-auto mb-6 neon-glow"
        >
          <span className="text-white font-bold text-2xl">G</span>
        </motion.div>
        
        <h2 className="text-3xl font-bold gradient-text mb-4">
          GHOST Dashboard
        </h2>
        
        <p className="text-gray-400 mb-8">
          Простой вход для тестирования
        </p>

        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={handleDirectLogin}
          disabled={isLoading}
          className="w-full py-4 bg-gradient-to-r from-[#667eea] to-[#764ba2] text-white font-semibold rounded-lg hover:from-[#5a6fd8] hover:to-[#6a4190] transition-all duration-200 neon-glow disabled:opacity-50 disabled:cursor-not-allowed text-lg"
        >
          {isLoading ? (
            <div className="flex items-center justify-center space-x-3">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              <span>Вход в систему...</span>
            </div>
          ) : (
            '🚀 Войти в дашборд'
          )}
        </motion.button>

        <div className="mt-6">
          <a 
            href="/auth" 
            className="text-gray-400 hover:text-white transition-colors text-sm"
          >
            Полная аутентификация →
          </a>
        </div>

        <div className="mt-8 p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
          <p className="text-blue-400 text-sm">
            💡 Это тестовый режим для быстрого доступа к дашборду
          </p>
        </div>
      </motion.div>
    </div>
  )
}
