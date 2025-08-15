import GhostLayout from '@/components/GhostLayout'
import TradersDashboard from '@/components/TradersDashboard'

export default function TradersPage() {
  return (
    <GhostLayout currentPage="traders">
      <TradersDashboard />
    </GhostLayout>
  )
}

export const metadata = {
  title: 'Traders - GHOST Dashboard',
  description: 'Telegram traders performance tracking and analytics'
}
