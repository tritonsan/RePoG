import { hostedRequest } from '@/lib/hosted-runtime';
import { hostedSession } from '@/db/store';
import { hasAcceptableBodySize, isSameOrigin } from '@/lib/session';
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest, context: { params: Promise<{ id: string }> }) {
  if (!isSameOrigin(request)) return NextResponse.json({ ok: false, failure_category: 'origin_invalid' }, { status: 403 });
  if (!hasAcceptableBodySize(request)) return NextResponse.json({ ok: false, failure_category: 'payload_too_large' }, { status: 413 });
  try {
    const { id } = await context.params;
    const session = await hostedSession(id);
    if (!session) return NextResponse.json({ ok: false, failure_category: 'session_not_found' }, { status: 404 });
    const body = await request.json() as Record<string, unknown>;
    const action = typeof body.action === 'string' ? body.action.trim().slice(0, 2000) : '';
    if (!action) return NextResponse.json({ ok: false, failure_category: 'input_invalid', failure_reason: 'Human action is required.' }, { status: 400 });
    const result = await hostedRequest(`/runtime/v1/sessions/${encodeURIComponent(session.runtime_session_id)}/human-intents`, 'POST', { operation_id: String(body.operation_id || crypto.randomUUID()), action });
    return NextResponse.json(result);
  } catch (error) {
    return NextResponse.json({ ok: false, failure_category: 'hosted_runtime_error', failure_reason: error instanceof Error ? error.message : 'Hosted runtime failed.' }, { status: 502 });
  }
}
