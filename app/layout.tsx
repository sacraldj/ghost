import type { Metadata, Viewport } from 'next'
import './globals.css'
import AuthProvider from './providers/AuthProvider'

export const metadata: Metadata = {
  title: 'GHOST Trading Dashboard',
  description: 'Professional Trading Platform with AI Analysis - Mobile Optimized',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'black-translucent',
    title: 'GHOST Trading'
  },
  formatDetection: {
    telephone: false,
    date: false,
    address: false,
    email: false,
    url: false
  },
  other: {
    'mobile-web-app-capable': 'yes',
    'apple-mobile-web-app-capable': 'yes',
    'apple-mobile-web-app-status-bar-style': 'black-translucent',
    'msapplication-TileColor': '#111827',
    'msapplication-navbutton-color': '#111827'
  }
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
  themeColor: '#111827'
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#0a0a0a] text-white antialiased">
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  )
}
