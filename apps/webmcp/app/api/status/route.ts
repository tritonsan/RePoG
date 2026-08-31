import { getOrCreateSession, getTurnStatus } from '@/db/store';
import { sessionId, withSession } from '@/lib/session';
import { NextRequest, NextResponse } from 'next/server';
export async function GET(request: NextRequest) {
  const id = sessionId(request); await getOrCreateSession(id);
  const operationId = request.nextUrl.searchParams.get('operation_id') || '';
  const resolution = operationId ? await getTurnStatus(id, operationId) : null;
  return withSession(NextResponse.json({ ok: true, operation_id: operationId || null, status: resolution?.status || 'not_found', resolution }, { headers: { 'Cache-Control': 'no-store' } }), id);
}
