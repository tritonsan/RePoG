import { advanceBridgeSession, bridgeSession } from '@/db/store';
import { hasAcceptableBodySize } from '@/lib/session';
import { assertAgentSchema } from '@/lib/schema-validation';
import { bearer, safeEqual, tokenHash } from '@/lib/tokens';
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest, context: { params: Promise<{ id: string }> }) {
  try {
    if (!hasAcceptableBodySize(request, 65_536)) return NextResponse.json({ ok: false, failure_category: 'payload_too_large' }, { status: 413 });
    const { id } = await context.params;
    const session = await bridgeSession(id);
    if (!session || !safeEqual(await tokenHash(bearer(request)), session.bridge_token_hash)) return NextResponse.json({ ok: false, failure_category: 'unauthorized' }, { status: 401 });
    const body = await request.json();
    if (!Number.isInteger(body.expected_session_revision) || !['ready', 'paused', 'complete'].includes(body.next_status)) throw new Error('Advance envelope is invalid.');
    const nextStatus = body.next_status as 'ready' | 'paused' | 'complete';
    if (body.next_turn) assertAgentSchema('turn_brief', body.next_turn);
    const view = await advanceBridgeSession(id, { expectedSessionRevision: body.expected_session_revision, nextStatus, nextTurn: body.next_turn || null });
    return NextResponse.json({ ok: true, protocol_version: '1.1', session_id: id, session_revision: view.session.revision, next_status: nextStatus, next_action: nextStatus === 'ready' ? 'commit_intent' : nextStatus === 'paused' ? 'join_session' : 'stop' });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Advance failed.';
    const conflict = ['revision_conflict', 'turn_not_resolved', 'turn_sequence_invalid'].includes(message);
    return NextResponse.json({ ok: false, failure_category: conflict ? message : 'input_invalid', failure_reason: message }, { status: conflict ? 409 : 400 });
  }
}
