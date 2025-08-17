'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/app/components/ui/card'

export default function NewsImpactCorrelation() {
  return (
    <Card className="bg-gray-900 border-gray-800">
      <CardHeader>
        <CardTitle className="text-green-400">News Impact Correlation</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-gray-400">Correlation between news events and market movements</p>
        <div className="mt-4">
          <p className="text-sm text-gray-500">Analyzing correlations...</p>
        </div>
      </CardContent>
    </Card>
  )
}
