import { env } from 'cloudflare:workers';
import { blackGullScenario, resolvePreparedTurn, scenarios } from '@/lib/scenarios';
import { sessionManifest, type AgentIntentEnvelope } from '@/lib/contracts';

export type SessionRow = { session_id: string; scenario_id: string; resolver_mode: 'fixture' | 'bridge'; manifest_json: string; bridge_token_hash: string; invite_token_hash: string; expires_at: string; status: 'awaiting_join' | 'active' | 'paused' | 'complete'; revision: number; current_turn: number; created_at: string; updated_at: string };
export type SeatRow = { seat_id: string; session_id: string; character_id: string; status: 'ready' | 'bound' | 'paused'; bound_at: string | null; updated_at: string };
export type TurnRow = { turn_id: string; session_id: string; turn_number: number; scene_id: string; source_revision: number; brief_json: string; status: 'queued' | 'open' | 'submitted' | 'resolved'; opened_at: string | null; resolved_at: string | null };
export type IntentRow = { operation_id: string; payload_digest: string; intent_payload: string; status: string; outcome: string; resolution_summary: string; visible_consequences: string; turn_id: string };
export type EventRow = { sequence: number; event_type: string; public_payload: string; seat_payload: string; created_at: string };
export type SessionView = { session: SessionRow; seat: SeatRow; turn: TurnRow; events: EventRow[] };

async function selectView(sessionId: string): Promise<SessionView> {
  const session = await env.DB.prepare('SELECT * FROM sessions WHERE session_id = ?').bind(sessionId).first<SessionRow>();
  const seat = await env.DB.prepare('SELECT * FROM session_seats WHERE session_id = ? ORDER BY seat_id LIMIT 1').bind(sessionId).first<SeatRow>();
  if (!session || !seat) throw new Error('Session could not be initialized.');
  const turn = await env.DB.prepare('SELECT * FROM turns WHERE session_id = ? AND turn_number = ?').bind(sessionId, session.current_turn).first<TurnRow>();
  if (!turn) throw new Error('Current turn is missing.');
  const events = (await env.DB.prepare('SELECT sequence, event_type, public_payload, seat_payload, created_at FROM session_events WHERE session_id = ? ORDER BY sequence').bind(sessionId).all<EventRow>()).results;
  return { session, seat, turn, events };
}

export async function getOrCreateSession(sessionId: string, requestedScenarioId = blackGullScenario.scenarioId): Promise<SessionView> {
  const existing = await env.DB.prepare('SELECT session_id FROM sessions WHERE session_id = ?').bind(sessionId).first();
  if (!existing) {
    const now = new Date().toISOString();
    const scenario = scenarios[requestedScenarioId] || blackGullScenario;
    const seatId = `${sessionId}:${scenario.character.id}`;
    await env.DB.batch([
      env.DB.prepare("INSERT OR IGNORE INTO sessions (session_id, scenario_id, resolver_mode, manifest_json, status, revision, current_turn, created_at, updated_at) VALUES (?, ?, 'fixture', ?, 'awaiting_join', 0, 1, ?, ?)").bind(sessionId, scenario.scenarioId, JSON.stringify(sessionManifest(scenario)), now, now),
      env.DB.prepare("INSERT OR IGNORE INTO session_seats (seat_id, session_id, character_id, status, updated_at) VALUES (?, ?, ?, 'ready', ?)").bind(seatId, sessionId, scenario.character.id, now),
      ...scenario.turns.map((turn, index) => env.DB.prepare('INSERT OR IGNORE INTO turns (turn_id, session_id, turn_number, scene_id, source_revision, brief_json, status, opened_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)').bind(`${sessionId}:turn-${index + 1}`, sessionId, index + 1, turn.sceneId, turn.sourceRevision, JSON.stringify(turn), index === 0 ? 'open' : 'queued', index === 0 ? now : null)),
    ]);
  }
  return selectView(sessionId);
}

export async function createBridgeSession(payload: { sessionId: string; bridgeTokenHash: string; inviteTokenHash: string; expiresAt: string; manifest: Record<string, unknown>; initialTurn: Record<string, unknown> }) {
  const characters = payload.manifest.characters as Array<Record<string, unknown>>;
  const turnSeat = payload.initialTurn.seat as Record<string, unknown>;
  const character = characters.find((item) => item.character_id === turnSeat.character_id);
  if (!character) throw new Error('The active character is not present in the session manifest.');
  const turnSession = payload.initialTurn.session as Record<string, unknown>;
  const scene = payload.initialTurn.scene as Record<string, unknown>;
  const now = new Date().toISOString();
  const turnId = String(turnSession.turn_id);
  const turnNumber = Number(turnSession.turn_number);
  const sourceRevision = Number(turnSession.revision);
  const characterId = String(character.character_id);
  await env.DB.batch([
    env.DB.prepare("INSERT INTO sessions (session_id, scenario_id, resolver_mode, manifest_json, bridge_token_hash, invite_token_hash, expires_at, status, revision, current_turn, created_at, updated_at) VALUES (?, ?, 'bridge', ?, ?, ?, ?, 'awaiting_join', 0, ?, ?, ?)").bind(payload.sessionId, String(payload.manifest.pack_id), JSON.stringify(payload.manifest), payload.bridgeTokenHash, payload.inviteTokenHash, payload.expiresAt, turnNumber, now, now),
    env.DB.prepare("INSERT INTO session_seats (seat_id, session_id, character_id, status, updated_at) VALUES (?, ?, ?, 'ready', ?)").bind(`${payload.sessionId}:${characterId}`, payload.sessionId, characterId, now),
    env.DB.prepare("INSERT INTO turns (turn_id, session_id, turn_number, scene_id, source_revision, brief_json, status, opened_at) VALUES (?, ?, ?, ?, ?, ?, 'open', ?)").bind(turnId, payload.sessionId, turnNumber, String(scene.scene_id), sourceRevision, JSON.stringify(payload.initialTurn), now),
  ]);
  return selectView(payload.sessionId);
}

export async function bridgeSession(sessionId: string) {
  return env.DB.prepare('SELECT * FROM sessions WHERE session_id = ? AND resolver_mode = ?').bind(sessionId, 'bridge').first<SessionRow>();
}

export async function acceptBridgeInvite(sessionId: string, inviteTokenHash: string) {
  const session = await env.DB.prepare('SELECT session_id, invite_token_hash, expires_at FROM sessions WHERE session_id = ? AND resolver_mode = ?').bind(sessionId, 'bridge').first<SessionRow>();
  if (!session || session.invite_token_hash !== inviteTokenHash || (session.expires_at && session.expires_at < new Date().toISOString())) return null;
  return joinSession(sessionId);
}

export async function joinSession(sessionId: string): Promise<SessionView> {
  await getOrCreateSession(sessionId);
  const now = new Date().toISOString();
  await env.DB.batch([
    env.DB.prepare("UPDATE sessions SET status = CASE WHEN status = 'complete' THEN status ELSE 'active' END, revision = CASE WHEN status IN ('awaiting_join','paused') THEN revision + 1 ELSE revision END, updated_at = ? WHERE session_id = ?").bind(now, sessionId),
    env.DB.prepare("UPDATE session_seats SET status = CASE WHEN status = 'paused' OR status = 'ready' THEN 'bound' ELSE status END, bound_at = COALESCE(bound_at, ?), updated_at = ? WHERE session_id = ?").bind(now, now, sessionId),
  ]);
  return selectView(sessionId);
}

export async function pauseSession(sessionId: string, expectedRevision: number): Promise<SessionView> {
  const now = new Date().toISOString();
  const result = await env.DB.prepare("UPDATE sessions SET status = 'paused', revision = revision + 1, updated_at = ? WHERE session_id = ? AND revision = ? AND status = 'active'").bind(now, sessionId, expectedRevision).run();
  if (!result.meta.changes) throw new Error('revision_conflict');
  await env.DB.prepare("UPDATE session_seats SET status = 'paused', updated_at = ? WHERE session_id = ?").bind(now, sessionId).run();
  return selectView(sessionId);
}

export async function findIntent(sessionId: string, operationId: string) { return env.DB.prepare('SELECT operation_id, payload_digest, intent_payload, status, outcome, resolution_summary, visible_consequences, turn_id FROM intents WHERE session_id = ? AND operation_id = ?').bind(sessionId, operationId).first<IntentRow>(); }

export async function saveResolvedTurn(sessionId: string, payload: { payloadDigest: string; intent: AgentIntentEnvelope }) {
  const view = await selectView(sessionId);
  if (view.session.status !== 'active') throw new Error('session_not_active');
  if (view.turn.turn_id !== payload.intent.expected_turn_id || view.turn.source_revision !== payload.intent.expected_source_revision || view.turn.status !== 'open') throw new Error('stale_turn');
  const scenario = scenarios[view.session.scenario_id];
  const preparedTurn = scenario.turns[view.turn.turn_number - 1];
  const resolution = resolvePreparedTurn(preparedTurn, payload.intent.action, payload.intent.speech);
  const now = new Date().toISOString();
  const nextTurn = view.turn.turn_number + 1;
  const complete = nextTurn > scenario.turns.length;
  const nextRevision = view.session.revision + 1;
  await env.DB.batch([
    env.DB.prepare("INSERT INTO intents (intent_id, session_id, turn_id, seat_id, operation_id, payload_digest, intent_payload, action, approach, speech, status, outcome, resolution_summary, visible_consequences, created_at, resolved_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'resolved', ?, ?, ?, ?, ?)").bind(`${sessionId}:${payload.intent.operation_id}`, sessionId, view.turn.turn_id, view.seat.seat_id, payload.intent.operation_id, payload.payloadDigest, JSON.stringify(payload.intent), payload.intent.action, payload.intent.approach, payload.intent.speech, resolution.outcome, resolution.summary, JSON.stringify(resolution.visibleConsequences), now, now),
    env.DB.prepare("UPDATE turns SET status = 'resolved', resolved_at = ? WHERE turn_id = ? AND status = 'open'").bind(now, view.turn.turn_id),
    env.DB.prepare('INSERT INTO session_events (event_id, session_id, sequence, event_type, public_payload, seat_payload, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)').bind(`${sessionId}:event-${nextRevision}`, sessionId, nextRevision, 'turn_resolved', JSON.stringify({ turn_number: view.turn.turn_number, summary: resolution.summary }), JSON.stringify({ operation_id: payload.intent.operation_id, outcome: resolution.outcome, visible_consequences: resolution.visibleConsequences }), now),
    env.DB.prepare('UPDATE sessions SET status = ?, current_turn = ?, revision = ?, updated_at = ? WHERE session_id = ? AND revision = ?').bind(complete ? 'complete' : 'active', complete ? view.turn.turn_number : nextTurn, nextRevision, now, sessionId, view.session.revision),
    ...(complete ? [] : [env.DB.prepare("UPDATE turns SET status = 'open', opened_at = ? WHERE session_id = ? AND turn_number = ? AND status = 'queued'").bind(now, sessionId, nextTurn)]),
  ]);
  return { view: await selectView(sessionId), resolution };
}

export async function saveBridgeIntent(sessionId: string, payload: { payloadDigest: string; intent: AgentIntentEnvelope }) {
  const view = await selectView(sessionId);
  if (view.session.resolver_mode !== 'bridge') throw new Error('resolver_mode_invalid');
  if (view.session.status !== 'active') throw new Error('session_not_active');
  if (view.turn.turn_id !== payload.intent.expected_turn_id || view.turn.source_revision !== payload.intent.expected_source_revision || view.turn.status !== 'open') throw new Error('stale_turn');
  const now = new Date().toISOString();
  const nextRevision = view.session.revision + 1;
  await env.DB.batch([
    env.DB.prepare("INSERT INTO intents (intent_id, session_id, turn_id, seat_id, operation_id, payload_digest, intent_payload, action, approach, speech, status, outcome, resolution_summary, visible_consequences, created_at, resolved_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', '', '', '[]', ?, '')").bind(`${sessionId}:${payload.intent.operation_id}`, sessionId, view.turn.turn_id, view.seat.seat_id, payload.intent.operation_id, payload.payloadDigest, JSON.stringify(payload.intent), payload.intent.action, payload.intent.approach, payload.intent.speech, now),
    env.DB.prepare("UPDATE turns SET status = 'submitted' WHERE turn_id = ? AND status = 'open'").bind(view.turn.turn_id),
    env.DB.prepare('UPDATE sessions SET revision = ?, updated_at = ? WHERE session_id = ? AND revision = ?').bind(nextRevision, now, sessionId, view.session.revision),
    env.DB.prepare('INSERT INTO session_events (event_id, session_id, sequence, event_type, public_payload, seat_payload, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)').bind(`${sessionId}:event-${nextRevision}`, sessionId, nextRevision, 'intent_pending', JSON.stringify({ turn_number: view.turn.turn_number }), JSON.stringify({ operation_id: payload.intent.operation_id, status: 'pending' }), now),
  ]);
  return { view: await selectView(sessionId), status: 'pending' as const };
}

export async function listPendingIntents(sessionId: string) {
  return (await env.DB.prepare("SELECT operation_id, turn_id, intent_payload, created_at FROM intents WHERE session_id = ? AND status = 'pending' ORDER BY created_at").bind(sessionId).all<{ operation_id: string; turn_id: string; intent_payload: string; created_at: string }>()).results.map((row) => ({ operation_id: row.operation_id, turn_id: row.turn_id, intent: JSON.parse(row.intent_payload), created_at: row.created_at }));
}

export async function resolveBridgeIntent(sessionId: string, payload: { operationId: string; expectedSessionRevision: number; outcome: string; summary: string; visibleConsequences: string[]; nextStatus?: 'ready' | 'waiting' | 'paused' | 'complete'; nextTurn?: Record<string, unknown> | null }) {
  const view = await selectView(sessionId);
  if (view.session.resolver_mode !== 'bridge') throw new Error('resolver_mode_invalid');
  if (view.session.revision !== payload.expectedSessionRevision) throw new Error('revision_conflict');
  const intent = await findIntent(sessionId, payload.operationId);
  if (!intent || intent.status !== 'pending' || intent.turn_id !== view.turn.turn_id) throw new Error('intent_missing');
  const now = new Date().toISOString();
  const nextRevision = view.session.revision + 1;
  const next = payload.nextTurn;
  const nextSession = next?.session as Record<string, unknown> | undefined;
  const nextScene = next?.scene as Record<string, unknown> | undefined;
  const nextStatus = payload.nextStatus || (next ? 'ready' : 'complete');
  if (nextStatus === 'ready' && (!next || !nextSession || !nextScene)) throw new Error('next_turn_required');
  if (nextStatus !== 'ready' && next) throw new Error('next_turn_not_allowed');
  const sessionStatus = nextStatus === 'complete' ? 'complete' : nextStatus === 'paused' ? 'paused' : 'active';
  const nextTurnNumber = nextStatus === 'ready' ? Number(nextSession?.turn_number) : view.turn.turn_number;
  const statements = [
    env.DB.prepare("UPDATE intents SET status = 'resolved', outcome = ?, resolution_summary = ?, visible_consequences = ?, resolved_at = ? WHERE session_id = ? AND operation_id = ? AND status = 'pending'").bind(payload.outcome, payload.summary, JSON.stringify(payload.visibleConsequences), now, sessionId, payload.operationId),
    env.DB.prepare("UPDATE turns SET status = 'resolved', resolved_at = ? WHERE turn_id = ? AND status = 'submitted'").bind(now, view.turn.turn_id),
    env.DB.prepare('UPDATE sessions SET status = ?, current_turn = ?, revision = ?, updated_at = ? WHERE session_id = ? AND revision = ?').bind(sessionStatus, nextTurnNumber, nextRevision, now, sessionId, view.session.revision),
    env.DB.prepare("UPDATE session_seats SET status = ?, updated_at = ? WHERE session_id = ?").bind(nextStatus === 'paused' ? 'paused' : 'bound', now, sessionId),
    env.DB.prepare('INSERT INTO session_events (event_id, session_id, sequence, event_type, public_payload, seat_payload, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)').bind(`${sessionId}:event-${nextRevision}`, sessionId, nextRevision, 'turn_resolved', JSON.stringify({ turn_number: view.turn.turn_number, summary: payload.summary }), JSON.stringify({ operation_id: payload.operationId, outcome: payload.outcome, visible_consequences: payload.visibleConsequences }), now),
  ];
  if (nextStatus === 'ready' && next && nextSession && nextScene) statements.push(env.DB.prepare("INSERT INTO turns (turn_id, session_id, turn_number, scene_id, source_revision, brief_json, status, opened_at) VALUES (?, ?, ?, ?, ?, ?, 'open', ?)").bind(String(nextSession.turn_id), sessionId, Number(nextSession.turn_number), String(nextScene.scene_id), Number(nextSession.revision), JSON.stringify(next), now));
  await env.DB.batch(statements);
  return selectView(sessionId);
}

export async function advanceBridgeSession(sessionId: string, payload: { expectedSessionRevision: number; nextStatus: 'ready' | 'paused' | 'complete'; nextTurn?: Record<string, unknown> | null }) {
  const view = await selectView(sessionId);
  if (view.session.resolver_mode !== 'bridge') throw new Error('resolver_mode_invalid');
  if (view.session.revision !== payload.expectedSessionRevision) throw new Error('revision_conflict');
  if (view.turn.status !== 'resolved') throw new Error('turn_not_resolved');
  const next = payload.nextTurn;
  const nextSession = next?.session as Record<string, unknown> | undefined;
  const nextScene = next?.scene as Record<string, unknown> | undefined;
  if (payload.nextStatus === 'ready' && (!next || !nextSession || !nextScene)) throw new Error('next_turn_required');
  if (payload.nextStatus !== 'ready' && next) throw new Error('next_turn_not_allowed');
  if (payload.nextStatus === 'ready' && Number(nextSession?.turn_number) !== view.turn.turn_number + 1) throw new Error('turn_sequence_invalid');
  const now = new Date().toISOString();
  const nextRevision = view.session.revision + 1;
  const status = payload.nextStatus === 'complete' ? 'complete' : payload.nextStatus === 'paused' ? 'paused' : 'active';
  const currentTurn = payload.nextStatus === 'ready' ? Number(nextSession?.turn_number) : view.turn.turn_number;
  const statements = [
    env.DB.prepare('UPDATE sessions SET status = ?, current_turn = ?, revision = ?, updated_at = ? WHERE session_id = ? AND revision = ?').bind(status, currentTurn, nextRevision, now, sessionId, view.session.revision),
    env.DB.prepare('UPDATE session_seats SET status = ?, updated_at = ? WHERE session_id = ?').bind(payload.nextStatus === 'paused' ? 'paused' : 'bound', now, sessionId),
    env.DB.prepare('INSERT INTO session_events (event_id, session_id, sequence, event_type, public_payload, seat_payload, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)').bind(`${sessionId}:event-${nextRevision}`, sessionId, nextRevision, 'session_advanced', JSON.stringify({ next_status: payload.nextStatus, turn_number: currentTurn }), '{}', now),
  ];
  if (payload.nextStatus === 'ready' && next && nextSession && nextScene) statements.push(env.DB.prepare("INSERT INTO turns (turn_id, session_id, turn_number, scene_id, source_revision, brief_json, status, opened_at) VALUES (?, ?, ?, ?, ?, ?, 'open', ?)").bind(String(nextSession.turn_id), sessionId, Number(nextSession.turn_number), String(nextScene.scene_id), Number(nextSession.revision), JSON.stringify(next), now));
  await env.DB.batch(statements);
  return selectView(sessionId);
}

export async function getTurnStatus(sessionId: string, operationId: string) {
  const intent = await findIntent(sessionId, operationId);
  if (!intent) return null;
  return { operation_id: intent.operation_id, status: intent.status, outcome: intent.outcome, summary: intent.resolution_summary, visible_consequences: JSON.parse(intent.visible_consequences || '[]') as string[] };
}
