type StoredTurn = { turn_id: string; brief_json: string };

export function externalTurnStorageId(sessionId: string, runtimeTurnId: string) {
  return `${sessionId}:external:${runtimeTurnId}`;
}

export function canonicalTurnId(turn: StoredTurn) {
  try {
    const brief = JSON.parse(turn.brief_json) as { session?: { turn_id?: unknown } };
    return typeof brief.session?.turn_id === 'string' && brief.session.turn_id ? brief.session.turn_id : turn.turn_id;
  } catch {
    return turn.turn_id;
  }
}
