import { joinSession } from '@/db/store';
import { protocolDirective, sessionContext } from '@/lib/demo';
import { isSameOrigin, sessionId, withSession } from '@/lib/session';
import { NextRequest, NextResponse } from 'next/server';
export async function POST(request: NextRequest) { const id = sessionId(request); if (!isSameOrigin(request)) return withSession(NextResponse.json({ ok: false, failure_category: 'origin_invalid' }, { status: 403 }), id); const view = await joinSession(id); const status = view.session.status === 'complete' ? 'complete' : view.turn.status === 'open' ? 'ready' : 'waiting'; return withSession(NextResponse.json({ ...sessionContext(view), ...protocolDirective(status, view.session.revision), joined: view.session.status !== 'complete' }), id); }
