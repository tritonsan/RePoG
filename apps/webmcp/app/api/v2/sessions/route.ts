import { createHostedMirror } from '@/db/store';
import { hostedRequest } from '@/lib/hosted-runtime';
import { hasAcceptableBodySize, isSameOrigin, withSession } from '@/lib/session';
import { NextRequest, NextResponse } from 'next/server';

type RuntimeSession = { ok: boolean; session_id: string; status: string; expires_at: string; manifest: Record<string, unknown>; initial_turn: Record<string, unknown> };

export async function POST(request: NextRequest) {
  const siteSessionId = crypto.randomUUID();
  try {
    if (!isSameOrigin(request)) return NextResponse.json({ ok: false, failure_category: 'origin_invalid' }, { status: 403 });
    if (!hasAcceptableBodySize(request)) return NextResponse.json({ ok: false, failure_category: 'payload_too_large' }, { status: 413 });
    const body = await request.json() as Record<string, unknown>;
    const mode = body.mode === 'quick_forge' ? 'quick_forge' : 'prepared';
    const result = await hostedRequest<RuntimeSession>('/runtime/v1/sessions', 'POST', {
      mode,
      site_session_id: siteSessionId,
      webmcp_opt_in: body.webmcp_opt_in === true,
      forge_prompt: typeof body.forge_prompt === 'string' ? body.forge_prompt.slice(0, 2000) : '',
    });
    await createHostedMirror({ sessionId: siteSessionId, runtimeSessionId: result.session_id, runtimeStatus: result.status, expiresAt: result.expires_at, manifest: result.manifest, initialTurn: result.initial_turn });
    return withSession(NextResponse.json({ ok: true, session_id: siteSessionId, runtime_session_id: result.session_id, status: result.status }), siteSessionId);
  } catch (error) {
    return NextResponse.json({ ok: false, failure_category: 'hosted_runtime_error', failure_reason: error instanceof Error ? error.message : 'Hosted runtime failed.' }, { status: 502 });
  }
}
