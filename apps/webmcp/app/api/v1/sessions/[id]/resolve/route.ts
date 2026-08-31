import { bridgeSession, resolveBridgeIntent } from '@/db/store';
import { hasAcceptableBodySize } from '@/lib/session';
import { bearer, safeEqual, tokenHash } from '@/lib/tokens';
import { assertAgentSchema } from '@/lib/schema-validation';
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest, context: { params: Promise<{ id: string }> }) {
  try {
    if (!hasAcceptableBodySize(request, 65_536)) return NextResponse.json({ ok: false, failure_category: 'payload_too_large' }, { status: 413 });
    const { id } = await context.params;
    const session = await bridgeSession(id);
    if (!session || !safeEqual(await tokenHash(bearer(request)), session.bridge_token_hash)) return NextResponse.json({ ok: false, failure_category: 'unauthorized' }, { status: 401 });
    const body = await request.json();
    const nextStatus = (body.next_status || (body.next_turn ? 'ready' : 'complete')) as 'ready' | 'waiting' | 'paused' | 'complete';
    const envelope = { schema_version: '1.0', intent_operation_id: body.operation_id, outcome: body.outcome, summary: body.summary, visible_consequences: body.visible_consequences, session_revision: body.expected_session_revision, next_status: nextStatus };
    assertAgentSchema('resolution', envelope);
    if (body.next_turn) assertAgentSchema('turn_brief', body.next_turn);
    const view = await resolveBridgeIntent(id, { operationId: body.operation_id, expectedSessionRevision: body.expected_session_revision, outcome: body.outcome, summary: body.summary.trim(), visibleConsequences: body.visible_consequences, nextStatus, nextTurn: body.next_turn || null });
    return NextResponse.json({ ok: true, protocol_version: '1.1', session_id: id, session_revision: view.session.revision, next_status: nextStatus, next_action: nextStatus === 'ready' ? 'commit_intent' : nextStatus === 'waiting' ? 'get_next_turn' : nextStatus === 'paused' ? 'join_session' : 'stop' });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Resolution failed.';
    const conflict = ['revision_conflict', 'intent_missing', 'turn_not_resolved', 'turn_sequence_invalid'].includes(message);
    return NextResponse.json({ ok: false, failure_category: conflict ? message : 'input_invalid', failure_reason: message }, { status: conflict ? 409 : 400 });
  }
}
