// middleware.ts - Fixed with correct login paths
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const path = request.nextUrl.pathname
  
  // Public routes that don't require authentication
  const publicPaths = [
    '/',  // Root page handles both public and authenticated users
    '/login',           // Fixed: Your actual login page
    '/signup',          // Fixed: Your actual signup page  
    '/forgot-password', // Fixed: Your password reset page
    '/reset-password',  // Fixed: Your password reset completion page
    '/auth/login',      // Keep legacy if needed
    '/auth/register',   // Keep legacy if needed
    '/api/auth/login', 
    '/api/auth/register',
    '/api/auth/forgot-password',    // Fixed: Add password reset endpoints
    '/api/auth/verify-reset-token', // Fixed: Add token verification
    '/api/auth/reset-password',     // Fixed: Add password reset completion
    '/api/public/chat',
    '/api/public/health',
    '/_next',           // Fixed: Add Next.js internal routes
    '/favicon.ico',     // Fixed: Add favicon
    '/static'           // Fixed: Add static files
  ]
  
  // Check if current path is public (exact match or starts with)
  const isPublicPath = publicPaths.some(publicPath => {
    if (publicPath.endsWith('/')) {
      return path.startsWith(publicPath)
    }
    return path === publicPath || path.startsWith(publicPath + '/')
  })
  
  if (isPublicPath) {
    return NextResponse.next()
  }
  
  // For protected routes, check for auth token
  // Check both cookie and localStorage-style tokens
  const tokenFromCookie = request.cookies.get('auth-token')?.value
  const tokenFromAuth = request.cookies.get('token')?.value
  
  if (!tokenFromCookie && !tokenFromAuth) {
    // Redirect unauthenticated users to login instead of root
    return NextResponse.redirect(new URL('/login', request.url))
  }
  
  return NextResponse.next()
}

export const config = {
  matcher: [
    // Match all paths except Next.js internals and static files
    '/((?!_next/static|_next/image|favicon.ico|.*\\..*).*)',
  ],
}