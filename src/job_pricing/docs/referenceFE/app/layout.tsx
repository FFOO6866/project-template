import type React from "react"
import { ThemeProvider } from "@/components/theme-provider"
import { Mona_Sans as FontSans } from "next/font/google"
import { cn } from "@/lib/utils"

import "@/app/globals.css"

const fontSans = FontSans({
  subsets: ["latin"],
  variable: "--font-sans",
})

export const metadata = {
  title: "Talent Verse | TPC Dashboard",
  description: "Talent and Organisation Performance Dashboard for Tsao Pao Chee",
    generator: 'v0.app'
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={cn("min-h-screen bg-background font-sans antialiased", fontSans.variable)}>
        <ThemeProvider attribute="class" defaultTheme="light" enableSystem disableTransitionOnChange>
          {children}
        </ThemeProvider>
      </body>
    </html>
  )
}
