import { bridgeSession, listPendingIntents } from '@/db/store';
import { bearer, safeEqual, tokenHash } from '@/lib/tokens';
import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest, context: { params: Promise<{ id: string }> }) {
  const { id } = await context.params;
  const session = await bridgeSession(id);
  if (!session || !safeEqual(await tokenHash(bearer(request)), session.bridge_token_hash)) return NextResponse.json({ ok: false, failure_category: 'unauthorized' }, { status: 401 });
  return NextResponse.json({ ok: true, session_id: id, session_revision: session.revision, status: session.status, intents: await listPendingIntents(id) }, { headers: { 'Cache-Control': 'no-store' } });
}
