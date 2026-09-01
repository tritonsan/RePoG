import { getOrCreateSession, getTurnStatus } from '@/db/store';
import { sessionId, withSession } from '@/lib/session';
import { NextRequest, NextResponse } from 'next/server';
import { refreshHostedSession } from '@/lib/hosted-sync';
export async function GET(request: NextRequest) {
  const id = sessionId(request); const view = await getOrCreateSession(id); if (view.session.resolver_mode === 'hosted') { try { await refreshHostedSession(id); } catch { /* report the last persisted intent status */ } }
  const operationId = request.nextUrl.searchParams.get('operation_id') || '';
  const resolution = operationId ? await getTurnStatus(id, operationId) : null;
  const status = resolution?.status || 'not_found';
  return withSession(NextResponse.json({ ok: true, protocol_version: '1.1', operation_id: operationId || null, status, resolution, next_action: status === 'pending' ? 'get_intent_status' : status === 'resolved' ? 'get_next_turn' : 'stop', stop_reason: status === 'not_found' ? 'intent_not_found' : null, requires_human: false, ...(status === 'pending' ? { retry_after_ms: 1000 } : {}) }, { headers: { 'Cache-Control': 'no-store' } }), id);
}
