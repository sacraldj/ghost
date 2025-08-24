'use client'

import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { Activity, AlertCircle, ArrowLeft } from 'lucide-react'
import { Suspense } from 'react'

function AuthErrorContent() {
  const searchParams = useSearchParams()
  const error = searchParams.get('error')

  const getErrorMessage = (errorType: string | null) => {
    switch (errorType) {
      case 'Configuration':
        return 'There is a problem with the server configuration.'
      case 'AccessDenied':
        return 'You do not have permission to access this application.'
      case 'Verification':
        return 'The verification token has expired or has already been used.'
      case 'Default':
      default:
        return 'An error occurred during authentication. Please try again.'
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-black to-gray-900 flex items-center justify-center p-4">
      {/* Background Pattern */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_1px_1px,rgba(255,255,255,0.1)_1px,transparent_0)] bg-[length:50px_50px] opacity-20" />
      
      <div className="w-full max-w-md relative">
        {/* Main Card */}
        <div className="bg-gradient-to-br from-gray-900/95 to-gray-950/95 backdrop-blur-xl rounded-3xl border border-gray-800/50 shadow-2xl p-8">
          {/* Logo & Header */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-gradient-to-r from-red-600 via-red-700 to-red-800 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
              <AlertCircle className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-white via-red-100 to-gray-300 bg-clip-text text-transparent mb-2">
              Authentication Error
            </h1>
            <p className="text-gray-400 text-sm">
              Something went wrong during sign in
            </p>
          </div>

          {/* Error Message */}
          <div className="mb-8 p-4 bg-red-900/20 border border-red-800/50 rounded-xl">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="text-red-300 font-medium mb-1">Error Details</h3>
                <p className="text-red-300/80 text-sm">
                  {getErrorMessage(error)}
                </p>
                {error && (
                  <p className="text-red-400/60 text-xs mt-2">
                    Error Code: {error}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="space-y-4">
            <Link
              href="/auth/signin"
              className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-medium py-4 px-6 rounded-2xl transition-all duration-300 shadow-lg hover:shadow-xl flex items-center justify-center gap-3 active:scale-98"
            >
              <ArrowLeft className="w-5 h-5" />
              Back to Sign In
            </Link>

            <Link
              href="/auth/signup"
              className="w-full bg-gray-800/50 hover:bg-gray-700/50 text-gray-300 hover:text-white font-medium py-4 px-6 rounded-2xl transition-all duration-300 border border-gray-700/50 hover:border-gray-600/50 flex items-center justify-center gap-3 active:scale-98"
            >
              Create New Account
            </Link>
          </div>

          {/* Help Text */}
          <div className="mt-8 text-center">
            <p className="text-gray-500 text-xs">
              If you continue to experience issues, please contact support.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-6">
          <p className="text-gray-500 text-xs">
            © 2024 GHOST Trading. Secure authentication system.
          </p>
        </div>
      </div>
    </div>
  )
}

function LoadingFallback() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-black to-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md relative">
        <div className="bg-gradient-to-br from-gray-900/95 to-gray-950/95 backdrop-blur-xl rounded-3xl border border-gray-800/50 shadow-2xl p-8">
          <div className="text-center">
            <div className="w-16 h-16 bg-gradient-to-r from-red-600 via-red-700 to-red-800 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
              <AlertCircle className="w-8 h-8 text-white animate-pulse" />
            </div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-white via-red-100 to-gray-300 bg-clip-text text-transparent mb-2">
              Loading...
            </h1>
            <p className="text-gray-400 text-sm">
              Please wait while we process your request
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function AuthErrorPage() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <AuthErrorContent />
    </Suspense>
  )
}
