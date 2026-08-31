import { acceptBridgeInvite } from '@/db/store';
import { hasAcceptableBodySize, isSameOrigin, withSession } from '@/lib/session';
import { tokenHash } from '@/lib/tokens';
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  if (!isSameOrigin(request)) return NextResponse.json({ ok: false, failure_category: 'origin_invalid' }, { status: 403 });
  if (!hasAcceptableBodySize(request)) return NextResponse.json({ ok: false, failure_category: 'payload_too_large' }, { status: 413 });
  const body = await request.json();
  if (typeof body.session_id !== 'string' || typeof body.invite_token !== 'string') return NextResponse.json({ ok: false, failure_category: 'input_invalid' }, { status: 400 });
  const view = await acceptBridgeInvite(body.session_id, await tokenHash(body.invite_token));
  if (!view) return NextResponse.json({ ok: false, failure_category: 'invite_invalid' }, { status: 401 });
  return withSession(NextResponse.json({ ok: true, session_id: body.session_id, status: view.session.status }), body.session_id);
}
