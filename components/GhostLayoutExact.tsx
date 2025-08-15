"use client"

import React, { useState } from 'react'
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar'
import { Button } from './ui/button'

interface GhostLayoutExactProps {
  children: React.ReactNode
  currentPage?: 'traders' | 'tasks' | 'messages' | 'goals' | 'groups' | 'settings'
  userName?: string
  userRole?: string
  onPageChange?: (page: string) => void
}

const GhostLayoutExact: React.FC<GhostLayoutExactProps> = ({ 
  children, 
  currentPage = 'traders',
  userName = 'Angela Lee',
  userRole = '@anglae',
  onPageChange
}) => {
  const [searchQuery, setSearchQuery] = useState('')

  const menuItems = [
    {
      id: 'traders',
      icon: '👥',
      label: 'Traders',
      active: currentPage === 'traders'
    },
    {
      id: 'tasks',
      icon: '📋',
      label: 'My Tasks',
      active: currentPage === 'tasks'
    },
    {
      id: 'messages',
      icon: '💬',
      label: 'Message',
      active: currentPage === 'messages'
    },
    {
      id: 'goals',
      icon: '📰',
      label: 'News',
      active: currentPage === 'goals'
    },
    {
      id: 'groups',
      icon: '👥',
      label: 'Groups',
      active: currentPage === 'groups'
    },
    {
      id: 'settings',
      icon: '⚙️',
      label: 'Settings',
      active: currentPage === 'settings'
    }
  ]

  return (
    <div className="flex h-screen bg-black text-white">
      {/* Левая боковая панель - точно как на скрине */}
      <div className="w-64 bg-gray-900 flex flex-col">
        {/* Логотип GHOST */}
        <div className="p-6">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center">
              <span className="text-black font-bold text-sm">G</span>
            </div>
            <span className="text-xl font-bold text-white">GHOST</span>
          </div>
        </div>

        {/* Профиль пользователя */}
        <div className="px-6 pb-6">
          <div className="flex items-center space-x-3">
            <Avatar className="w-10 h-10">
              <AvatarFallback className="bg-orange-500 text-white text-sm font-medium">
                AL
              </AvatarFallback>
            </Avatar>
            <div>
              <div className="text-white font-medium">Angela Lee</div>
              <div className="text-gray-400 text-sm">@anglae</div>
            </div>
          </div>
        </div>

        {/* Меню навигации */}
        <nav className="flex-1 px-4">
          <div className="space-y-1">
            {menuItems.map((item) => (
              <button
                key={item.id}
                onClick={() => onPageChange?.(item.id)}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-left transition-all duration-200 ${
                  item.active
                    ? 'bg-yellow-500 text-black font-medium'
                    : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                }`}
              >
                <span className="text-lg">{item.icon}</span>
                <span className="text-sm">{item.label}</span>
              </button>
            ))}
          </div>
        </nav>

        {/* Кнопка выхода */}
        <div className="p-4">
          <button className="w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-gray-300 hover:bg-gray-800 hover:text-white transition-colors">
            <span className="text-lg">🚪</span>
            <span className="text-sm">Log Out</span>
          </button>
        </div>
      </div>

      {/* Основная область контента */}
      <div className="flex-1 flex flex-col">
        {/* Верхняя панель - точно как на скрине */}
        <header className="bg-gray-900 px-6 py-4 flex items-center justify-between">
          {/* Приветствие */}
          <div>
            <h1 className="text-xl font-semibold text-white">
              Hello, {userName.split(' ')[0]}!
            </h1>
            <p className="text-sm text-gray-400">
              Welcome back, let's explore now!
            </p>
          </div>

          {/* Правая часть */}
          <div className="flex items-center space-x-4">
            {/* Поиск */}
            <div className="relative">
              <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">
                🔍
              </div>
              <input
                type="text"
                placeholder="Search here"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="bg-gray-800 border border-gray-700 rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-yellow-500 w-64"
              />
            </div>

            {/* Иконки уведомлений */}
            <button className="text-gray-400 hover:text-white p-2">
              🔔
            </button>

            <button className="text-gray-400 hover:text-white p-2">
              ⚙️
            </button>

            {/* Язык/регион */}
            <div className="flex items-center space-x-2 text-sm text-gray-400">
              <div className="w-6 h-6 rounded-full bg-red-500 flex items-center justify-center text-xs">
                🇺🇸
              </div>
              <span>Eng (US)</span>
              <span>▼</span>
            </div>
          </div>
        </header>

        {/* Основной контент */}
        <main className="flex-1 overflow-auto bg-black">
          {children}
        </main>
      </div>
    </div>
  )
}

export default GhostLayoutExact
