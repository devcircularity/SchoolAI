import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const path = request.nextUrl.pathname
  
  // Only handle API routes and static files here
  // Let client-side routing handle authentication
  
  // API routes that don't require authentication
  const publicApiPaths = [
    '/api/auth/login',
    '/api/auth/register',
    '/api/health'
  ]
  
  // Check if current path is a public API route
  const isPublicApiPath = publicApiPaths.some(publicPath => 
    path.startsWith(publicPath)
  )
  
  // For API routes, you could add additional logic here if needed
  if (path.startsWith('/api/') && !isPublicApiPath) {
    // For protected API routes, you could check Authorization header
    const authHeader = request.headers.get('authorization')
    if (!authHeader?.startsWith('Bearer ')) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
  }
  
  return NextResponse.next()
}

export const config = {
  matcher: [
    // Only match API routes for server-side auth checking
    '/api/((?!auth/login|auth/register|health).*)',
  ],
}