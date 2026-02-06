import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  return NextResponse.json({
    status: 'success',
    message: 'Next.js Jorge Platform API Ready',
    timestamp: new Date().toISOString(),
    platform: 'Jorge Real Estate AI',
    backend_connection: 'pending_fastapi_startup'
  })
}

export async function POST(request: NextRequest) {
  const body = await request.json()

  return NextResponse.json({
    status: 'received',
    message: 'Jorge API endpoint processing request',
    received_data: body,
    timestamp: new Date().toISOString()
  })
}