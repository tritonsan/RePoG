import type { Capability, PreparedTurn, ScenarioPack } from '@/lib/scenarios';

export type AgentIntentEnvelope = {
  schema_version: '1.0'; operation_id: string; expected_turn_id: string; expected_source_revision: number;
  actor_id: string; action_type: string; action: string; approach: string; speech: string;
  targets: string[]; resource_refs: string[]; knowledge_refs: string[]; requested_effect: string; asserted_outcomes: string[];
};

export type PolicyFailure = { failure_category: 'authority_violation' | 'knowledge_violation' | 'input_invalid'; failure_reason: string };

const ID = /^[a-z0-9][a-z0-9._-]{0,63}$/;
const ACTION_CAPABILITIES: Record<string, Capability> = {
  speak: 'self.speak', move: 'self.move', use_resource: 'self.use_owned_resource', commit: 'self.personal_commitment',
  observe: 'self.observe', recall: 'self.recall', act: 'self.move', social_test: 'self.speak', investigate: 'self.observe', assist: 'self.move',
};

function text(value: unknown, name: string, maximum: number, required = false) {
  if (typeof value !== 'string') throw new Error(`${name} must be text.`);
  const clean = value.trim();
  if (required && !clean) throw new Error(`${name} must not be empty.`);
  if (clean.length > maximum) throw new Error(`${name} exceeds ${maximum} characters.`);
  return clean;
}

function identifier(value: unknown, name: string) {
  if (typeof value !== 'string' || !ID.test(value)) throw new Error(`${name} must be a stable identifier.`);
  return value;
}

function identifiers(value: unknown, name: string, maximum = 16) {
  if (!Array.isArray(value) || value.length > maximum) throw new Error(`${name} must contain at most ${maximum} identifiers.`);
  const result = value.map((item, index) => identifier(item, `${name}[${index}]`));
  if (new Set(result).size !== result.length) throw new Error(`${name} must not contain duplicates.`);
  return result;
}

function texts(value: unknown, name: string, maximumItems = 8, maximumText = 300) {
  if (!Array.isArray(value) || value.length > maximumItems) throw new Error(`${name} must contain at most ${maximumItems} items.`);
  return value.map((item, index) => text(item, `${name}[${index}]`, maximumText, true));
}

export function normalizeIntent(input: Record<string, unknown>): AgentIntentEnvelope {
  const revision = input.expected_source_revision;
  if (!Number.isInteger(revision) || Number(revision) < 0) throw new Error('expected_source_revision is invalid.');
  if (input.schema_version !== undefined && input.schema_version !== '1.0') throw new Error('schema_version must be 1.0.');
  return {
    schema_version: '1.0',
    operation_id: identifier(input.operation_id, 'operation_id'),
    expected_turn_id: text(input.expected_turn_id, 'expected_turn_id', 180, true),
    expected_source_revision: Number(revision),
    actor_id: identifier(input.actor_id, 'actor_id'),
    action_type: identifier(input.action_type, 'action_type'),
    action: text(input.action, 'action', 1200, true),
    approach: text(input.approach ?? '', 'approach', 600),
    speech: text(input.speech ?? '', 'speech', 1200),
    targets: identifiers(input.targets ?? [], 'targets'),
    resource_refs: identifiers(input.resource_refs ?? [], 'resource_refs'),
    knowledge_refs: identifiers(input.knowledge_refs ?? [], 'knowledge_refs'),
    requested_effect: text(input.requested_effect ?? '', 'requested_effect', 500),
    asserted_outcomes: texts(input.asserted_outcomes ?? [], 'asserted_outcomes'),
  };
}

export function validateIntentPolicy(pack: ScenarioPack, turn: PreparedTurn, intent: AgentIntentEnvelope): PolicyFailure | null {
  if (intent.actor_id !== pack.character.id) return { failure_category: 'authority_violation', failure_reason: 'The intent actor does not own the active Agent Seat.' };
  const required = ACTION_CAPABILITIES[intent.action_type];
  if (!required || !pack.character.capabilities.includes(required)) return { failure_category: 'authority_violation', failure_reason: 'The action type is outside this character’s declared capabilities.' };
  if (intent.targets.some((target) => !turn.entityRefs.includes(target))) return { failure_category: 'authority_violation', failure_reason: 'The intent targets an entity outside the current safe projection.' };
  if (intent.resource_refs.some((resource) => !turn.ownedResourceRefs.includes(resource))) return { failure_category: 'authority_violation', failure_reason: 'The intent uses a resource the character does not own or control.' };
  const known = new Set(turn.knowledgeIndex.map((fact) => fact.factId));
  if (intent.knowledge_refs.some((fact) => !known.has(fact))) return { failure_category: 'knowledge_violation', failure_reason: 'The intent cites knowledge outside the character projection.' };
  if (intent.asserted_outcomes.length) return { failure_category: 'authority_violation', failure_reason: 'Agents may request effects but cannot assert world outcomes.' };
  return null;
}

export function validateBridgeIntentPolicy(manifest: Record<string, unknown>, brief: Record<string, unknown>, intent: AgentIntentEnvelope): PolicyFailure | null {
  const characters = manifest.characters as Array<Record<string, unknown>>;
  const seat = brief.seat as Record<string, unknown>;
  const scene = brief.scene as Record<string, unknown>;
  const epistemic = brief.epistemic_projection as Record<string, unknown>;
  const character = characters.find((item) => item.character_id === seat.character_id) || characters[0];
  if (!character || intent.actor_id !== character.character_id) return { failure_category: 'authority_violation', failure_reason: 'The intent actor does not own the active Agent Seat.' };
  const required = ACTION_CAPABILITIES[intent.action_type];
  const capabilities = Array.isArray(character.capabilities) ? character.capabilities as string[] : [];
  if (!required || !capabilities.includes(required)) return { failure_category: 'authority_violation', failure_reason: 'The action type is outside this character’s declared capabilities.' };
  const entityRefs = Array.isArray(scene.entity_refs) ? scene.entity_refs as string[] : [];
  if (intent.targets.some((target) => !entityRefs.includes(target))) return { failure_category: 'authority_violation', failure_reason: 'The intent targets an entity outside the current safe projection.' };
  const resourceRefs = Array.isArray(scene.owned_resource_refs) ? scene.owned_resource_refs as string[] : [];
  if (intent.resource_refs.some((resource) => !resourceRefs.includes(resource))) return { failure_category: 'authority_violation', failure_reason: 'The intent uses a resource the character does not own or control.' };
  const knowledge = Array.isArray(epistemic.knowledge_index) ? epistemic.knowledge_index as Array<Record<string, unknown>> : [];
  const known = new Set(knowledge.map((fact) => String(fact.fact_id)));
  if (intent.knowledge_refs.some((fact) => !known.has(fact))) return { failure_category: 'knowledge_violation', failure_reason: 'The intent cites knowledge outside the character projection.' };
  if (intent.asserted_outcomes.length) return { failure_category: 'authority_violation', failure_reason: 'Agents may request effects but cannot assert world outcomes.' };
  return null;
}

export function sessionManifest(pack: ScenarioPack) {
  return {
    schema_version: pack.schemaVersion,
    pack_id: pack.scenarioId,
    game_contract: { title: pack.title, genre: pack.genre, tone: pack.tone, reality_rules: pack.realityRules, table_boundaries: pack.tableBoundaries },
    characters: [{
      character_id: pack.character.id, display_name: pack.character.name, role: pack.character.role, identity: pack.character.identity,
      prioritized_values: pack.character.prioritizedValues, goals: [pack.character.shortTermGoal, pack.character.longTermGoal],
      decision_rules: pack.character.decisionRules, contradictions: pack.character.contradictions, voice_examples: pack.character.voiceExamples,
      capabilities: pack.character.capabilities, forbidden_authority: pack.character.forbiddenAuthority,
      knowledge_refs: Array.from(new Set(pack.turns.flatMap((turn) => turn.knowledgeIndex.map((fact) => fact.factId)))), readiness: 'ready',
    }],
    session_policy: { max_active_seats: 1, run_policy: 'continue_until_pause_or_complete', ordinary_turn_approval: 'not_required', stop_conditions: ['session_paused', 'session_complete', 'clarification_required', 'repeated_authority_rejection'] },
  };
}
