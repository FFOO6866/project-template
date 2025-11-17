'use client'

/**
 * Client-side Providers Wrapper
 *
 * Wraps the application with all necessary context providers.
 * This is a client component to allow use of React Context.
 */

import { ReactNode } from 'react'
import { AuthProvider } from '@/contexts/AuthContext'

export function Providers({ children }: { children: ReactNode }) {
  return (
    <AuthProvider>
      {children}
    </AuthProvider>
  )
}
