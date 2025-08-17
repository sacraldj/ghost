'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/app/components/ui/card'

export default function NewsFeed() {
  const [news, setNews] = useState([])

  return (
    <Card className="bg-gray-900 border-gray-800">
      <CardHeader>
        <CardTitle className="text-green-400">News Feed</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-gray-400">Latest market news and analysis</p>
        <div className="mt-4">
          <p className="text-sm text-gray-500">Loading news...</p>
        </div>
      </CardContent>
    </Card>
  )
}
