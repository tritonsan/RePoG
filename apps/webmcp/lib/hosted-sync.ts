import { hostedSession, syncHostedSession } from '@/db/store';
import { hostedRequest } from '@/lib/hosted-runtime';

type Snapshot = { ok: boolean; status: string; revision: number; turn_number: number; manifest: Record<string, unknown>; turn: Record<string, unknown> };
type Events = { ok: boolean; events: Array<Record<string, unknown>> };

export async function refreshHostedSession(siteSessionId: string) {
  const session = await hostedSession(siteSessionId);
  if (!session) return null;
  const runtimeId = encodeURIComponent(session.runtime_session_id);
  const [snapshot, eventFeed] = await Promise.all([
    hostedRequest<Snapshot>(`/runtime/v1/sessions/${runtimeId}`),
    hostedRequest<Events>(`/runtime/v1/sessions/${runtimeId}/events`),
  ]);
  return syncHostedSession(siteSessionId, snapshot, eventFeed.events);
}
