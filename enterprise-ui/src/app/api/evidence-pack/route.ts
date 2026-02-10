import { NextResponse } from 'next/server'

export async function GET() {
  const backendBase =
    process.env.ENTERPRISE_API_BASE_URL ||
    process.env.NEXT_PUBLIC_ENTERPRISE_API_BASE_URL ||
    'http://localhost:8000'

  const response = await fetch(`${backendBase}/api/evidence-pack`)
  if (!response.ok) {
    return NextResponse.json({ error: 'Failed to fetch evidence pack' }, { status: 502 })
  }

  const arrayBuffer = await response.arrayBuffer()
  return new NextResponse(arrayBuffer, {
    status: 200,
    headers: {
      'Content-Type': 'application/zip',
      'Content-Disposition': 'attachment; filename=enterprisehub-evidence-pack.zip'
    }
  })
}
