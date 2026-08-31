import { createBridgeSession } from '@/db/store';
import { hasAcceptableBodySize } from '@/lib/session';
import { bearer, randomToken, safeEqual, tokenHash } from '@/lib/tokens';
import { env } from 'cloudflare:workers';
import { NextRequest, NextResponse } from 'next/server';

function validate(manifest: unknown, turn: unknown) {
  if (!manifest || typeof manifest !== 'object' || !turn || typeof turn !== 'object') throw new Error('manifest and initial_turn are required.');
  const pack = manifest as Record<string, unknown>;
  const brief = turn as Record<string, unknown>;
  if (pack.schema_version !== '1.0' || typeof pack.pack_id !== 'string') throw new Error('Agent Session Pack v1 is required.');
  const characters = pack.characters;
  if (!Array.isArray(characters) || !characters.length) throw new Error('At least one ready character is required.');
  const policy = pack.session_policy as Record<string, unknown> | undefined;
  if (!policy || policy.max_active_seats !== 1) throw new Error('Only one active Agent Seat is supported.');
  const session = brief.session as Record<string, unknown> | undefined;
  const scene = brief.scene as Record<string, unknown> | undefined;
  const seat = brief.seat as Record<string, unknown> | undefined;
  if (brief.schema_version !== '1.0' || !session || !scene || !seat || typeof session.turn_id !== 'string' || !Number.isInteger(session.turn_number) || !Number.isInteger(session.revision) || typeof scene.scene_id !== 'string') throw new Error('Agent Turn Brief v1 is invalid.');
  if (!characters.some((character) => (character as Record<string, unknown>).character_id === seat.character_id)) throw new Error('The initial turn seat is not present in the manifest.');
}

export async function POST(request: NextRequest) {
  try {
    if (!hasAcceptableBodySize(request, 65_536)) return NextResponse.json({ ok: false, failure_category: 'payload_too_large' }, { status: 413 });
    const bootstrap = String((env as unknown as Record<string, unknown>).REPOG_RELAY_BOOTSTRAP_KEY || '');
    if (!bootstrap) return NextResponse.json({ ok: false, failure_category: 'relay_not_configured' }, { status: 503 });
    if (!safeEqual(bearer(request), bootstrap)) return NextResponse.json({ ok: false, failure_category: 'unauthorized' }, { status: 401 });
    const body = await request.json();
    validate(body.manifest, body.initial_turn);
    const sessionId = `relay-${crypto.randomUUID()}`;
    const bridgeToken = randomToken();
    const inviteToken = randomToken();
    const expiresAt = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString();
    await createBridgeSession({ sessionId, bridgeTokenHash: await tokenHash(bridgeToken), inviteTokenHash: await tokenHash(inviteToken), expiresAt, manifest: body.manifest, initialTurn: body.initial_turn });
    return NextResponse.json({ ok: true, session_id: sessionId, bridge_token: bridgeToken, invite_url: `${request.nextUrl.origin}/?session=${encodeURIComponent(sessionId)}&invite=${encodeURIComponent(inviteToken)}`, expires_at: expiresAt });
  } catch (error) {
    return NextResponse.json({ ok: false, failure_category: 'input_invalid', failure_reason: error instanceof Error ? error.message : 'Invalid relay session.' }, { status: 400 });
  }
}
