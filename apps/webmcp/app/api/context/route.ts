import { getOrCreateSession } from '@/db/store';
import { sessionContext } from '@/lib/demo';
import { sessionId, withSession } from '@/lib/session';
import { NextRequest, NextResponse } from 'next/server';
import { refreshHostedSession } from '@/lib/hosted-sync';
export async function GET(request: NextRequest) { const id = sessionId(request); let session = await getOrCreateSession(id); if (session.session.resolver_mode === 'hosted') { try { session = await refreshHostedSession(id) || session; } catch { /* Keep the last safe mirror when AWS is temporarily unavailable. */ } } return withSession(NextResponse.json(sessionContext(session), { headers: { 'Cache-Control': 'no-store' } }), id); }
