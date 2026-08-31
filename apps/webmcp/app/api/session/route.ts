import { joinSession } from '@/db/store';
import { sessionContext } from '@/lib/demo';
import { isSameOrigin, sessionId, withSession } from '@/lib/session';
import { NextRequest, NextResponse } from 'next/server';
export async function POST(request: NextRequest) { const id = sessionId(request); if (!isSameOrigin(request)) return withSession(NextResponse.json({ ok: false, failure_category: 'origin_invalid' }, { status: 403 }), id); const view = await joinSession(id); return withSession(NextResponse.json({ ...sessionContext(view), joined: view.session.status !== 'complete' }), id); }
