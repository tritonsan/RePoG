import { pauseSession } from '@/db/store';
import { protocolDirective, sessionContext } from '@/lib/demo';
import { isSameOrigin, sessionId, withSession } from '@/lib/session';
import { NextRequest, NextResponse } from 'next/server';
export async function POST(request: NextRequest) { const id = sessionId(request); if (!isSameOrigin(request)) return withSession(NextResponse.json({ ok: false, failure_category: 'origin_invalid' }, { status: 403 }), id); try { const body = await request.json(); const view = await pauseSession(id, body.expected_session_revision); return withSession(NextResponse.json({ ...sessionContext(view), ...protocolDirective('paused', view.session.revision) }), id); } catch (error) { return withSession(NextResponse.json({ ok: false, failure_category: error instanceof Error ? error.message : 'input_invalid' }, { status: 409 }), id); } }
