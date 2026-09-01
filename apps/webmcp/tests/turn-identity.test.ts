import { describe, expect, it } from 'vitest';
import { canonicalTurnId, externalTurnStorageId } from '@/lib/turn-identity';

describe('external turn identity', () => {
  it('namespaces database keys without changing the runtime contract id', () => {
    const canonical = 'black-gull-turn-001';
    const first = externalTurnStorageId('site-session-a', canonical);
    const second = externalTurnStorageId('site-session-b', canonical);
    expect(first).not.toBe(second);
    expect(canonicalTurnId({ turn_id: first, brief_json: JSON.stringify({ session: { turn_id: canonical } }) })).toBe(canonical);
    expect(canonicalTurnId({ turn_id: second, brief_json: JSON.stringify({ session: { turn_id: canonical } }) })).toBe(canonical);
  });

  it('falls back safely for fixture and legacy rows', () => {
    expect(canonicalTurnId({ turn_id: 'local:turn-1', brief_json: '{}' })).toBe('local:turn-1');
    expect(canonicalTurnId({ turn_id: 'legacy', brief_json: '{broken' })).toBe('legacy');
  });
});
