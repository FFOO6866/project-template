import { NextResponse } from 'next/server';

/**
 * Health check endpoint for Docker container monitoring
 * Used by docker-compose health checks to verify frontend is running
 */
export async function GET() {
  return NextResponse.json(
    {
      status: 'healthy',
      service: 'horme-frontend',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
    },
    { status: 200 }
  );
}
