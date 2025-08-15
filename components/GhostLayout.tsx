"use client"

import React, { useState } from 'react'
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar'
import { Button } from './ui/button'
import { Badge } from './ui/badge'

interface GhostLayoutProps {
  children: React.ReactNode
  currentPage?: 'traders' | 'signals' | 'news' | 'messages' | 'goals' | 'groups' | 'settings'
  userName?: string
  userRole?: string
}

const GhostLayout: React.FC<GhostLayoutProps> = ({ 
  children, 
  currentPage = 'traders',
  userName = 'Layla Odam',
  userRole = '@anglae'
}) => {
  const [searchQuery, setSearchQuery] = useState('')

  const menuItems = [
    {
      id: 'traders',
      icon: '👥',
      label: 'Traders',
      active: currentPage === 'traders',
      href: '/traders'
    },
    {
      id: 'tasks',
      icon: '🎯',
      label: 'My Tasks',
      active: false,
      href: '/tasks'
    },
    {
      id: 'messages',
      icon: '💬',
      label: 'Message',
      active: currentPage === 'messages',
      href: '/messages'
    },
    {
      id: 'goals',
      icon: '⭐',
      label: 'Goals',
      active: currentPage === 'goals',
      href: '/goals'
    },
    {
      id: 'groups',
      icon: '👥',
      label: 'Groups',
      active: currentPage === 'groups',
      href: '/groups'
    },
    {
      id: 'settings',
      icon: '⚙️',
      label: 'Settings',
      active: currentPage === 'settings',
      href: '/settings'
    }
  ]

  return (
    <div className="flex h-screen bg-black text-white">
      {/* Sidebar */}
      <div className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-gray-800">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center">
              <span className="text-black font-bold text-sm">G</span>
            </div>
            <span className="text-xl font-bold">GHOST</span>
          </div>
        </div>

        {/* User Profile */}
        <div className="p-6 border-b border-gray-800">
          <div className="flex items-center space-x-3">
            <Avatar className="w-10 h-10">
              <AvatarImage src="/api/placeholder/40/40" />
              <AvatarFallback className="bg-gray-700 text-white">
                {userName.split(' ').map(n => n[0]).join('')}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1">
              <div className="font-medium text-white">{userName}</div>
              <div className="text-sm text-gray-400">{userRole}</div>
            </div>
          </div>
        </div>

        {/* Navigation Menu */}
        <nav className="flex-1 p-4">
          <div className="space-y-2">
            {menuItems.map((item) => {
              return (
                <button
                  key={item.id}
                  className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-left transition-colors ${
                    item.active
                      ? 'bg-yellow-500 text-black font-medium'
                      : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                  }`}
                >
                  <span className="text-lg">{item.icon}</span>
                  <span>{item.label}</span>
                </button>
              )
            })}
          </div>
        </nav>

        {/* Logout */}
        <div className="p-4 border-t border-gray-800">
          <button className="w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-gray-300 hover:bg-gray-800 hover:text-white transition-colors">
            <span className="text-lg">🚪</span>
            <span>Log Out</span>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Top Header */}
        <header className="bg-gray-900 border-b border-gray-800 px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Welcome Message */}
            <div>
              <h1 className="text-xl font-semibold text-white">
                Hello, {userName.split(' ')[0]}!
              </h1>
              <p className="text-sm text-gray-400">
                Welcome back, let's explore now!
              </p>
            </div>

            {/* Right Side */}
            <div className="flex items-center space-x-4">
              {/* Search */}
              <div className="relative">
                <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">
                  🔍
                </div>
                <input
                  type="text"
                  placeholder="Search here"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="bg-gray-800 border border-gray-700 rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-yellow-500 w-64"
                />
              </div>

              {/* Notifications */}
              <Button variant="ghost" size="sm" className="text-gray-400 hover:text-white">
                🔔
              </Button>

              {/* Settings */}
              <Button variant="ghost" size="sm" className="text-gray-400 hover:text-white">
                ⚙️
              </Button>

              {/* Language/Region */}
              <div className="flex items-center space-x-2 text-sm text-gray-400">
                <div className="w-6 h-6 rounded-full bg-red-500 flex items-center justify-center">
                  <span className="text-xs text-white">🇺🇸</span>
                </div>
                <span>Eng (US)</span>
                <span>▼</span>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  )
}

export default GhostLayout
