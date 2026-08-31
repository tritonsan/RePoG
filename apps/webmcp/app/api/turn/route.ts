import { findIntent, getOrCreateSession, saveBridgeIntent, saveResolvedTurn } from '@/db/store';
import { normalizeIntent, validateBridgeIntentPolicy, validateIntentPolicy } from '@/lib/contracts';
import { scenarios } from '@/lib/scenarios';
import { hasAcceptableBodySize, isSameOrigin, sessionId, withSession } from '@/lib/session';
import { assertAgentSchema } from '@/lib/schema-validation';
import { NextRequest, NextResponse } from 'next/server';

async function digest(payload: unknown) { const bytes = new TextEncoder().encode(JSON.stringify(payload)); const result = await crypto.subtle.digest('SHA-256', bytes); return Array.from(new Uint8Array(result), (byte) => byte.toString(16).padStart(2, '0')).join(''); }
export async function POST(request: NextRequest) {
  const id = sessionId(request);
  try {
    if (!isSameOrigin(request)) return withSession(NextResponse.json({ ok: false, failure_category: 'origin_invalid', failure_reason: 'Turn requests must come from this site.' }, { status: 403 }), id);
    if (!hasAcceptableBodySize(request)) return withSession(NextResponse.json({ ok: false, failure_category: 'payload_too_large', failure_reason: 'Turn request exceeds the 16 KiB limit.' }, { status: 413 }), id);
    if (!request.headers.get('content-type')?.toLowerCase().startsWith('application/json')) throw new Error('Content-Type must be application/json.');
    const normalized = normalizeIntent(await request.json());
    assertAgentSchema('intent', normalized);
    const view = await getOrCreateSession(id);
    const scenario = scenarios[view.session.scenario_id];
    const policyFailure = scenario
      ? validateIntentPolicy(scenario, scenario.turns[view.turn.turn_number - 1], normalized)
      : validateBridgeIntentPolicy(JSON.parse(view.session.manifest_json), JSON.parse(view.turn.brief_json), normalized);
    if (policyFailure) return withSession(NextResponse.json({ ok: false, ...policyFailure }, { status: 409 }), id);
    const payloadDigest = await digest(normalized);
    const existing = await findIntent(id, normalized.operation_id);
    if (existing) {
      if (existing.payload_digest !== payloadDigest) return withSession(NextResponse.json({ ok: false, failure_category: 'operation_conflict', failure_reason: 'operation_id was reused with a different turn.' }, { status: 409 }), id);
      return withSession(NextResponse.json({ ok: true, protocol_version: '1.1', operation_id: normalized.operation_id, status: existing.status, next_action: existing.status === 'pending' ? 'get_intent_status' : 'get_next_turn', idempotent: true }), id);
    }
    if (view.session.resolver_mode === 'bridge') {
      const saved = await saveBridgeIntent(id, { payloadDigest, intent: normalized });
      return withSession(NextResponse.json({ ok: true, protocol_version: '1.1', operation_id: normalized.operation_id, status: saved.status, session_revision: saved.view.session.revision, next_status: 'waiting', next_action: 'get_intent_status', stop_reason: null, requires_human: false, retry_after_ms: 1000, idempotent: false }), id);
    }
    const saved = await saveResolvedTurn(id, { payloadDigest, intent: normalized });
    const nextStatus = saved.view.session.status === 'complete' ? 'complete' : 'ready';
    return withSession(NextResponse.json({ ok: true, protocol_version: '1.1', operation_id: normalized.operation_id, status: 'resolved', outcome: saved.resolution.outcome, resolution: { summary: saved.resolution.summary, visible_consequences: saved.resolution.visibleConsequences }, session_revision: saved.view.session.revision, next_status: nextStatus, next_action: nextStatus === 'complete' ? 'stop' : 'get_next_turn', stop_reason: nextStatus === 'complete' ? 'session_complete' : null, requires_human: false, idempotent: false }), id);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Invalid turn request.';
    const conflict = ['stale_turn', 'session_not_active', 'revision_conflict'].includes(message);
    return withSession(NextResponse.json({ ok: false, failure_category: conflict ? message : 'input_invalid', failure_reason: conflict ? 'Refresh or resume the session before acting.' : message }, { status: conflict ? 409 : 400 }), id);
  }
}
