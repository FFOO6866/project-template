"use client"

import { Button } from "@/components/ui/button"
import { UserIcon, LogOutIcon, SettingsIcon, BellIcon } from "@/components/icons"
import { Badge } from "@/components/ui/badge"
import Image from "next/image"

export function Header() {
  return (
    <header className="bg-white border-b border-slate-200/60 shadow-sm backdrop-blur-sm">
      <div className="max-w-[1600px] mx-auto px-6 py-4">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-4">
              {/* Actual Horme Hardware Logo */}
              <div className="flex items-center space-x-4">
                <Image
                  src="/images/horme-logo.png"
                  alt="Horme Hardware"
                  width={180}
                  height={60}
                  className="h-12 w-auto"
                />
                <div className="border-l border-slate-300 pl-4">
                  <p className="text-sm font-semibold text-red-600">AI Sales Assistant</p>
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <Button variant="ghost" size="sm" className="relative hover:bg-red-50">
              <BellIcon className="w-4 h-4 text-slate-600" />
              <Badge className="absolute -top-1 -right-1 w-2 h-2 p-0 bg-red-500"></Badge>
            </Button>

            <Button variant="ghost" size="sm" className="hover:bg-red-50">
              <SettingsIcon className="w-4 h-4 text-slate-600" />
            </Button>

            <div className="flex items-center space-x-3 pl-4 border-l border-slate-200">
              <div className="w-8 h-8 bg-gradient-to-br from-amber-600 to-amber-700 rounded-full flex items-center justify-center">
                <UserIcon className="w-4 h-4 text-white" />
              </div>
              <div className="text-sm">
                <div className="font-medium text-slate-900">John Smith</div>
                <div className="text-slate-500 text-xs">Sales Representative</div>
              </div>
            </div>

            <Button
              variant="outline"
              size="sm"
              className="ml-2 border-red-200 text-red-700 hover:bg-red-50 bg-transparent"
            >
              <LogOutIcon className="w-4 h-4 mr-2" />
              Sign Out
            </Button>
          </div>
        </div>
      </div>
    </header>
  )
}
