"use client"

import { useRouter } from "next/navigation"
import { useEffect } from "react"

export default function Home() {
  const router = useRouter()

  useEffect(() => {
    // Redirect to job pricing page
    router.push("/job-pricing")
  }, [router])

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <h1 className="text-2xl font-bold mb-4">Dynamic Job Pricing Engine</h1>
        <p className="text-gray-600">Redirecting...</p>
      </div>
    </div>
  )
}
