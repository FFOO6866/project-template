'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useRouter } from 'next/navigation'

interface User {
  id: number
  email: string
  username: string
  full_name: string
  role: string
  is_active: boolean
  is_verified: boolean
  is_superuser: boolean
  department?: string
  job_title?: string
}

interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  getAccessToken: () => string | null
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const TOKEN_KEY = 'job_pricing_access_token'
const REFRESH_TOKEN_KEY = 'job_pricing_refresh_token'
const USER_KEY = 'job_pricing_user'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    const loadUser = () => {
      try {
        const storedUser = localStorage.getItem(USER_KEY)
        const token = localStorage.getItem(TOKEN_KEY)
        if (storedUser && token) {
          setUser(JSON.parse(storedUser))
        }
      } catch (error) {
        console.error('Failed to load user:', error)
      } finally {
        setIsLoading(false)
      }
    }
    loadUser()
  }, [])

  const login = async (username: string, password: string) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ username, password }),
      })

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Login failed' }))
        throw new Error(error.detail || 'Login failed')
      }

      const tokens: AuthTokens = await response.json()
      localStorage.setItem(TOKEN_KEY, tokens.access_token)
      localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token)

      const tokenPayload = JSON.parse(atob(tokens.access_token.split('.')[1]))
      const userData: User = {
        id: tokenPayload.sub,
        email: tokenPayload.email,
        username: username,
        full_name: tokenPayload.email.split('@')[0],
        role: tokenPayload.role,
        is_active: true,
        is_verified: true,
        is_superuser: tokenPayload.role === 'admin',
      }

      setUser(userData)
      localStorage.setItem(USER_KEY, JSON.stringify(userData))
      router.push('/job-pricing')
    } catch (error) {
      console.error('Login error:', error)
      throw error
    }
  }

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    setUser(null)
    router.push('/login')
  }

  const getAccessToken = (): string | null => {
    if (typeof window === 'undefined') return null
    return localStorage.getItem(TOKEN_KEY)
  }

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    getAccessToken,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
