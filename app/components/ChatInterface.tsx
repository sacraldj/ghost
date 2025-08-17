'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/app/components/ui/card'

export default function ChatInterface() {
  const [message, setMessage] = useState('')

  return (
    <Card className="bg-gray-900 border-gray-800">
      <CardHeader>
        <CardTitle className="text-green-400">AI Chat Interface</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="h-64 bg-gray-800 rounded p-4 overflow-y-auto">
            <p className="text-gray-400">Chat interface ready...</p>
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Ask about trading signals..."
              className="flex-1 bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white"
            />
            <button className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded text-white">
              Send
            </button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
