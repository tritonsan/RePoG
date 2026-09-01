import { getOrCreateSession } from '@/db/store';
import { nextTurn } from '@/lib/demo';
import { sessionId, withSession } from '@/lib/session';
import { NextRequest, NextResponse } from 'next/server';
import { refreshHostedSession } from '@/lib/hosted-sync';
export async function GET(request: NextRequest) { const id = sessionId(request); let view = await getOrCreateSession(id); if (view.session.resolver_mode === 'hosted') { try { view = await refreshHostedSession(id) || view; } catch { /* bounded long-poll uses the last safe mirror */ } } const raw = request.nextUrl.searchParams.get('after_revision'); const after = raw === null ? undefined : Number(raw); return withSession(NextResponse.json(nextTurn(view, Number.isInteger(after) ? after : undefined), { headers: { 'Cache-Control': 'no-store' } }), id); }
