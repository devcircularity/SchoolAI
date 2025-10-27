// app/layout.tsx (RootLayout)
import './globals.css'
import React from 'react'
import { AuthProvider } from '@/contexts/AuthContext'

export const metadata = { title: 'Olaji Chat' }

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-svh bg-neutral-50 text-neutral-900 dark:bg-neutral-950 dark:text-neutral-100 antialiased">
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  )
}