import { getOrCreateSession } from '@/db/store';
import { scenarios } from '@/lib/scenarios';
import { hasAcceptableBodySize, isSameOrigin, withSession } from '@/lib/session';
import { NextRequest, NextResponse } from 'next/server';
export async function POST(request: NextRequest) {
  if (!isSameOrigin(request)) return NextResponse.json({ ok: false, failure_category: 'origin_invalid' }, { status: 403 });
  if (!hasAcceptableBodySize(request)) return NextResponse.json({ ok: false, failure_category: 'payload_too_large' }, { status: 413 });
  const body = request.headers.get('content-type')?.startsWith('application/json') ? await request.json() : {};
  const scenarioId = typeof body.scenario_id === 'string' && scenarios[body.scenario_id] ? body.scenario_id : 'black-gull';
  const id = crypto.randomUUID();
  await getOrCreateSession(id, scenarioId);
  return withSession(NextResponse.json({ ok: true, status: 'awaiting_join', scenario_id: scenarioId, new_session: true }), id);
}
