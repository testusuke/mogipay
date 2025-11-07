// Health check endpoint for Docker health checks
import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json(
    {
      status: 'healthy',
      service: 'MogiPay Frontend',
    },
    { status: 200 }
  );
}
