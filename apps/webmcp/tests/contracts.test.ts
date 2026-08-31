import { describe, expect, it } from 'vitest';
import { normalizeIntent, sessionManifest, validateIntentPolicy } from '@/lib/contracts';
import { blackGullScenario, orisonFixture } from '@/lib/scenarios';

function intent(overrides: Record<string, unknown> = {}) {
  return normalizeIntent({
    schema_version: '1.0', operation_id: 'mira-turn-1', expected_turn_id: 'session:turn-1', expected_source_revision: 12,
    actor_id: 'mira', action_type: 'social_test', action: 'Test the guard with the low tide phrase.', approach: 'Indirect', speech: 'Low tide.',
    targets: ['guard'], resource_refs: ['black-gull-ring'], knowledge_refs: ['black-gull-low-tide'], requested_effect: 'Observe the reaction.', asserted_outcomes: [],
    ...overrides,
  });
}

describe('Agent Seat v1 contracts', () => {
  it('uses the same manifest shape for fantasy and science-fiction fixtures', () => {
    for (const scenario of [blackGullScenario, orisonFixture]) {
      const manifest = sessionManifest(scenario);
      expect(manifest.schema_version).toBe('1.0');
      expect(manifest.session_policy.max_active_seats).toBe(1);
      expect(manifest.characters[0].character_id).toBe(scenario.character.id);
    }
  });

  it('accepts a bounded character intent', () => {
    expect(validateIntentPolicy(blackGullScenario, blackGullScenario.turns[0], intent())).toBeNull();
  });

  it('rejects actor, knowledge, target, resource, and outcome authority violations', () => {
    const cases = [
      intent({ actor_id: 'arden' }),
      intent({ knowledge_refs: ['gm-secret'] }),
      intent({ targets: ['hidden-mastermind'] }),
      intent({ resource_refs: ['guard-sword'] }),
      intent({ asserted_outcomes: ['The guard obeys.'] }),
    ];
    for (const candidate of cases) expect(validateIntentPolicy(blackGullScenario, blackGullScenario.turns[0], candidate)).not.toBeNull();
  });

  it('rejects unknown action capabilities by default', () => {
    expect(validateIntentPolicy(blackGullScenario, blackGullScenario.turns[0], intent({ action_type: 'rewrite_world' }))?.failure_category).toBe('authority_violation');
  });
});
