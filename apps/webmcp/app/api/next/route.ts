import { getOrCreateSession } from '@/db/store';
import { nextTurn } from '@/lib/demo';
import { sessionId, withSession } from '@/lib/session';
import { NextRequest, NextResponse } from 'next/server';
export async function GET(request: NextRequest) { const id = sessionId(request); const view = await getOrCreateSession(id); const raw = request.nextUrl.searchParams.get('after_revision'); const after = raw === null ? undefined : Number(raw); return withSession(NextResponse.json(nextTurn(view, Number.isInteger(after) ? after : undefined), { headers: { 'Cache-Control': 'no-store' } }), id); }
