import type { SessionView } from '@/db/store';
import { scenarios } from '@/lib/scenarios';
import { sessionManifest } from '@/lib/contracts';

export const PROTOCOL_VERSION = '1.1';

const visualProfiles = {
  'black-gull': {
    theme_profile: 'fantasy_noir',
    scene_art: { url: '/assets/living-table/black-gull-scene.png', alt: 'A rain-soaked cellar stair guarded beside a brass warning bell.', canon_status: 'accepted', revision: 1 },
    human_seat: { display_name: 'Arden', role: 'Black Gull investigator', portrait_url: '/assets/living-table/arden-portrait.png', portrait_alt: 'Arden, a rain-worn investigator in a dark hood.' },
    agent_portrait: { url: '/assets/living-table/mira-portrait.png', alt: 'Mira, an alert scout in rain-worn leather.', canon_status: 'accepted', revision: 1 },
    palette: { accent: 'bronze', signal: 'tide', atmosphere: 'rain' },
  },
  'orison-signal': {
    theme_profile: 'space_operatic',
    scene_art: { url: '/assets/living-table/orison-scene.png', alt: 'A low-orbit command gallery facing a disputed signal.', canon_status: 'accepted', revision: 1 },
    human_seat: { display_name: 'Station Liaison', role: 'Human player', portrait_url: '/assets/living-table/orison-human-portrait.png', portrait_alt: 'A seasoned station liaison under cool orbital light.' },
    agent_portrait: { url: '/assets/living-table/iko-portrait.png', alt: 'Iko, a focused systems envoy under cool station light.', canon_status: 'accepted', revision: 1 },
    palette: { accent: 'amber', signal: 'cyan', atmosphere: 'orbit' },
  },
} as const;

function visualProjection(scenarioId: string) {
  return visualProfiles[scenarioId as keyof typeof visualProfiles] || {
    ...visualProfiles['black-gull'],
    theme_profile: 'neutral',
  };
}

export function projectManifestForCharacter<T extends { characters: Array<Record<string, unknown>> }>(manifest: T, characterId: string) {
  const character = manifest.characters.find((item) => item.character_id === characterId);
  if (!character) throw new Error('Active character is not present in the manifest.');
  return { ...manifest, characters: [character] };
}

export function protocolDirective(status: 'ready' | 'waiting' | 'paused' | 'complete', revision: number) {
  const nextAction = status === 'ready' ? 'commit_intent' : status === 'waiting' ? 'get_next_turn' : status === 'paused' ? 'join_session' : 'stop';
  const stopReason = status === 'paused' ? 'session_paused' : status === 'complete' ? 'session_complete' : null;
  return { protocol_version: PROTOCOL_VERSION, next_action: nextAction, stop_reason: stopReason, requires_human: status === 'paused', session_revision: revision, ...(status === 'waiting' ? { retry_after_ms: 1000 } : {}) };
}

export function sessionContext(view: SessionView) {
  const scenario = scenarios[view.session.scenario_id];
  if (!scenario) {
    const manifest = JSON.parse(view.session.manifest_json) as { game_contract: { title: string }; characters: Array<Record<string, unknown>>; session_policy: Record<string, unknown> };
    const brief = JSON.parse(view.turn.brief_json) as { session: Record<string, unknown>; scene: Record<string, unknown>; seat: Record<string, unknown>; epistemic_projection: Record<string, unknown>; continuity: Record<string, unknown> };
    const projectedManifest = projectManifestForCharacter(manifest, view.seat.character_id);
    const character = projectedManifest.characters[0];
    const scene = brief.scene;
    const epistemic = brief.epistemic_projection;
    const history = view.events.filter((event) => event.event_type === 'turn_resolved').map((event) => ({ sequence: event.sequence, ...JSON.parse(event.public_payload) as object }));
    return {
      ok: true,
      protocol_version: PROTOCOL_VERSION,
      session: { session_id: view.session.session_id, scenario_id: view.session.scenario_id, resolver_mode: view.session.resolver_mode, status: view.session.status, revision: view.session.revision, current_turn: view.session.current_turn, total_turns: null },
      manifest: projectedManifest,
      seat: { seat_id: view.seat.seat_id, character_id: view.seat.character_id, display_name: character.display_name, role: character.role, status: view.seat.status, persona: { prioritized_values: character.prioritized_values, goals: character.goals, decision_rules: character.decision_rules, contradictions: character.contradictions, voice_examples: character.voice_examples, capabilities: character.capabilities, authority: character.capabilities, forbidden_authority: character.forbidden_authority } },
      turn: { turn_id: view.turn.turn_id, turn_number: view.turn.turn_number, scene_id: view.turn.scene_id, source_revision: view.turn.source_revision, status: view.turn.status, title: scene.title || `Turn ${view.turn.turn_number}` },
      brief: { summary: scene.summary, pressure: scene.pressure, perceivable_facts: scene.perceivable_facts || [], self_knowledge: epistemic.self_knowledge || [], knowledge_index: epistemic.knowledge_index || [], relevant_knowledge: (epistemic.knowledge_index as Array<{ text: string }> || []).map((fact) => fact.text), party_public_facts: epistemic.party_public_facts || [], affordances: scene.affordances || [], entity_refs: scene.entity_refs || [], owned_resource_refs: scene.owned_resource_refs || [], continuity: { ...brief.continuity, last_visible_consequences: history.at(-1)?.visible_consequences || [] } },
      visual: visualProjection(view.session.scenario_id),
      history,
    };
  }
  const turn = scenario.turns[view.turn.turn_number - 1];
  const lastEvent = view.events.at(-1);
  const lastSeatPayload = lastEvent ? JSON.parse(lastEvent.seat_payload) as { visible_consequences?: string[] } : null;
  return {
    ok: true,
    protocol_version: PROTOCOL_VERSION,
    session: { session_id: view.session.session_id, scenario_id: scenario.scenarioId, resolver_mode: view.session.resolver_mode, status: view.session.status, revision: view.session.revision, current_turn: view.session.current_turn, total_turns: scenario.turns.length },
    manifest: sessionManifest(scenario),
    seat: { seat_id: view.seat.seat_id, character_id: scenario.character.id, display_name: scenario.character.name, role: scenario.character.role, status: view.seat.status, persona: { prioritized_values: scenario.character.prioritizedValues, goals: [scenario.character.shortTermGoal, scenario.character.longTermGoal], decision_rules: scenario.character.decisionRules, contradictions: scenario.character.contradictions, voice_examples: scenario.character.voiceExamples, capabilities: scenario.character.capabilities, authority: scenario.character.authority, forbidden_authority: scenario.character.forbiddenAuthority } },
    turn: { turn_id: view.turn.turn_id, turn_number: view.turn.turn_number, scene_id: view.turn.scene_id, source_revision: view.turn.source_revision, status: view.turn.status, title: turn.title },
    brief: { summary: turn.summary, pressure: turn.pressure, perceivable_facts: turn.perceivableFacts, self_knowledge: turn.selfKnowledge, knowledge_index: turn.knowledgeIndex.map((fact) => ({ fact_id: fact.factId, text: fact.text, status: fact.status, source: fact.source, confidence: fact.confidence, learned_at_revision: fact.learnedAtRevision, last_confirmed_revision: fact.lastConfirmedRevision })), relevant_knowledge: turn.knowledgeIndex.map((fact) => fact.text), party_public_facts: turn.partyPublicFacts, affordances: turn.affordances, entity_refs: turn.entityRefs, owned_resource_refs: turn.ownedResourceRefs, continuity: { last_visible_consequences: lastSeatPayload?.visible_consequences || [] } },
    visual: visualProjection(scenario.scenarioId),
    history: view.events.map((event) => ({ sequence: event.sequence, ...JSON.parse(event.public_payload) as object })),
  };
}

export function nextTurn(view: SessionView, afterRevision?: number) {
  const context = sessionContext(view);
  let status: 'ready' | 'waiting' | 'paused' | 'complete';
  if (view.session.status === 'paused') status = 'paused'; else if (view.session.status === 'complete') status = 'complete'; else if (view.session.status === 'awaiting_join' || view.turn.status !== 'open' || afterRevision === view.session.revision) status = 'waiting'; else status = 'ready';
  return { ...context, status, ...protocolDirective(status, view.session.revision), brief: status === 'ready' ? context.brief : null };
}
