"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { AlertCircle, Loader2, LogIn } from "lucide-react"
import { apiClient } from "@/lib/api-client"
import { AuthenticationError } from "@/lib/api-errors"
import Image from "next/image"

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      // Real API authentication - NO MOCK DATA
      const response = await apiClient.login({
        email,
        password
      })

      console.log("Login successful:", response)

      // Store JWT token in localStorage
      if (response.access_token) {
        localStorage.setItem('access_token', response.access_token)
      }

      // Redirect to dashboard
      router.push('/')
    } catch (err: any) {
      setLoading(false)

      if (err instanceof AuthenticationError) {
        setError("Invalid email or password")
      } else {
        setError(err.message || "Login failed. Please try again.")
      }

      console.error("Login error:", err)
    }
  }

  const handleQuickLogin = (userEmail: string, userPassword: string) => {
    setEmail(userEmail)
    setPassword(userPassword)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-amber-50/20 to-red-50/10 flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        {/* Logo Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-gradient-to-br from-amber-600 to-red-600 rounded-lg flex items-center justify-center">
                <span className="text-2xl font-bold text-white">H</span>
              </div>
              <div>
                <h1 className="text-3xl font-bold text-slate-900">HORME</h1>
                <p className="text-xs text-slate-600 uppercase tracking-wider">Hardware</p>
              </div>
            </div>
          </div>
          <h2 className="text-xl font-semibold text-slate-900">AI Sales Assistant</h2>
          <p className="text-slate-600 mt-1">Sign in to continue</p>
        </div>

        {/* Login Card */}
        <Card className="border-slate-200 shadow-xl shadow-slate-200/50">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl font-bold text-slate-900 flex items-center">
              <LogIn className="w-5 h-5 mr-2 text-amber-600" />
              Sign In
            </CardTitle>
            <CardDescription className="text-slate-600">
              Enter your credentials to access your account
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleLogin} className="space-y-4">
              {/* Error Message */}
              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-start">
                  <AlertCircle className="w-5 h-5 text-red-600 mr-2 flex-shrink-0 mt-0.5" />
                  <p className="text-red-700 text-sm">{error}</p>
                </div>
              )}

              {/* Email Field */}
              <div className="space-y-2">
                <Label htmlFor="email" className="text-slate-900 font-medium">
                  Email Address
                </Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="border-slate-300 focus:border-amber-500 focus:ring-amber-500"
                  disabled={loading}
                />
              </div>

              {/* Password Field */}
              <div className="space-y-2">
                <Label htmlFor="password" className="text-slate-900 font-medium">
                  Password
                </Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="border-slate-300 focus:border-amber-500 focus:ring-amber-500"
                  disabled={loading}
                />
              </div>

              {/* Login Button */}
              <Button
                type="submit"
                className="w-full bg-gradient-to-r from-amber-600 to-red-600 hover:from-amber-700 hover:to-red-700 text-white font-semibold py-2.5"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Signing in...
                  </>
                ) : (
                  <>
                    <LogIn className="w-4 h-4 mr-2" />
                    Sign In
                  </>
                )}
              </Button>
            </form>

            {/* Divider */}
            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-200"></div>
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-white px-2 text-slate-500">Quick Access</span>
              </div>
            </div>

            {/* Quick Login Buttons */}
            <div className="space-y-2">
              <Button
                type="button"
                variant="outline"
                className="w-full border-amber-200 text-amber-700 hover:bg-amber-50"
                onClick={() => handleQuickLogin("josh.peh@horme.com.sg", "JoshPeh@2025")}
                disabled={loading}
              >
                <User className="w-4 h-4 mr-2" />
                Login as Josh Peh
              </Button>
              <Button
                type="button"
                variant="outline"
                className="w-full border-slate-300 text-slate-700 hover:bg-slate-50"
                onClick={() => handleQuickLogin("admin@horme.com.sg", "Admin@2025")}
                disabled={loading}
              >
                <Shield className="w-4 h-4 mr-2" />
                Login as Admin
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <p className="text-center text-sm text-slate-600 mt-6">
          Powered by AI • Horme Hardware © 2025
        </p>
      </div>
    </div>
  )
}

// Import User and Shield icons
import { User, Shield } from "lucide-react"
