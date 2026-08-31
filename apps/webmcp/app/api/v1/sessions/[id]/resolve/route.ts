import { bridgeSession, resolveBridgeIntent } from '@/db/store';
import { hasAcceptableBodySize } from '@/lib/session';
import { bearer, safeEqual, tokenHash } from '@/lib/tokens';
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest, context: { params: Promise<{ id: string }> }) {
  try {
    if (!hasAcceptableBodySize(request, 65_536)) return NextResponse.json({ ok: false, failure_category: 'payload_too_large' }, { status: 413 });
    const { id } = await context.params;
    const session = await bridgeSession(id);
    if (!session || !safeEqual(await tokenHash(bearer(request)), session.bridge_token_hash)) return NextResponse.json({ ok: false, failure_category: 'unauthorized' }, { status: 401 });
    const body = await request.json();
    if (typeof body.operation_id !== 'string' || !Number.isInteger(body.expected_session_revision) || !['accepted', 'altered', 'rejected', 'clarification_required', 'skipped', 'expired'].includes(body.outcome) || typeof body.summary !== 'string' || !Array.isArray(body.visible_consequences)) throw new Error('Resolution envelope is invalid.');
    const view = await resolveBridgeIntent(id, { operationId: body.operation_id, expectedSessionRevision: body.expected_session_revision, outcome: body.outcome, summary: body.summary.trim().slice(0, 1200), visibleConsequences: body.visible_consequences.map(String).slice(0, 16), nextTurn: body.next_turn || null });
    return NextResponse.json({ ok: true, session_id: id, session_revision: view.session.revision, next_status: view.session.status === 'complete' ? 'complete' : 'ready' });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Resolution failed.';
    const conflict = ['revision_conflict', 'intent_missing'].includes(message);
    return NextResponse.json({ ok: false, failure_category: conflict ? message : 'input_invalid', failure_reason: message }, { status: conflict ? 409 : 400 });
  }
}
