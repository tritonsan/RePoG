import { getOrCreateSession } from '@/db/store';
import { sessionContext } from '@/lib/demo';
import { sessionId, withSession } from '@/lib/session';
import { NextRequest, NextResponse } from 'next/server';
export async function GET(request: NextRequest) { const id = sessionId(request); const session = await getOrCreateSession(id); return withSession(NextResponse.json(sessionContext(session), { headers: { 'Cache-Control': 'no-store' } }), id); }
