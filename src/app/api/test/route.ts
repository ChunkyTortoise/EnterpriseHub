// Test API route for Jorge's FastAPI backend connection
import { NextRequest, NextResponse } from 'next/server'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

export async function GET() {
  try {
    return NextResponse.json({
      status: 'success',
      message: 'Jorge Enterprise UI is running',
      platform: 'Next.js 16.1.4',
      backend: API_BASE,
      capabilities: [
        'Real-time chat interface',
        'Bot status monitoring', 
        'Supabase integration ready',
        'Socket.IO fallback configured',
        'PWA capabilities',
        'React Query caching'
      ],
      timestamp: new Date().toISOString(),
      routes: {
        jorge: '/jorge',
        home: '/',
        api: '/api/test'
      }
    })
    
  } catch (error) {
    console.error('API test failed:', error)
    
    return NextResponse.json(
      { 
        error: 'API test failed',
        details: error instanceof Error ? error.message : 'Unknown error',
        platform: 'Next.js 16.1.4',
        timestamp: new Date().toISOString()
      }, 
      { status: 500 }
    )
  }
}