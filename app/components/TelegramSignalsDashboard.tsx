'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/app/components/ui/card'

export default function TelegramSignalsDashboard() {
  const [signals, setSignals] = useState([])

  return (
    <Card className="bg-gray-900 border-gray-800">
      <CardHeader>
        <CardTitle className="text-green-400">Telegram Signals</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-gray-400">Telegram signals monitoring dashboard</p>
        <div className="mt-4">
          <p className="text-sm text-gray-500">Loading signals...</p>
        </div>
      </CardContent>
    </Card>
  )
}
