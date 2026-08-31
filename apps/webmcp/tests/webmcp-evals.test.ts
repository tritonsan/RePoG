import { describe, expect, it, vi } from 'vitest';
import { createWebMcpTools } from '@/lib/webmcp-tools';
import { projectManifestForCharacter, protocolDirective } from '@/lib/demo';
import { sessionManifest } from '@/lib/contracts';
import { blackGullScenario, orisonFixture } from '@/lib/scenarios';
import { validateAgentSchema } from '@/lib/schema-validation';

describe('WebMCP conformance evals', () => {
  it('discovers exactly the six stable RePoG tools with untrusted server output', () => {
    const tools = createWebMcpTools(vi.fn(), vi.fn());
    expect(tools.map((tool) => tool.name)).toEqual(['repog.join_session', 'repog.get_next_turn', 'repog.recall_knowledge', 'repog.commit_intent', 'repog.get_intent_status', 'repog.pause_session']);
    expect(tools.every((tool) => tool.annotations.untrustedContentHint)).toBe(true);
    expect(tools.find((tool) => tool.name === 'repog.commit_intent')?.inputSchema).toMatchObject({ additionalProperties: false });
  });

  it('keeps protocol continuation autonomous until an explicit stop', () => {
    expect(protocolDirective('ready', 3)).toMatchObject({ next_action: 'commit_intent', requires_human: false });
    expect(protocolDirective('waiting', 4)).toMatchObject({ next_action: 'get_next_turn', retry_after_ms: 1000, requires_human: false });
    expect(protocolDirective('paused', 5)).toMatchObject({ next_action: 'join_session', stop_reason: 'session_paused', requires_human: true });
    expect(protocolDirective('complete', 6)).toMatchObject({ next_action: 'stop', stop_reason: 'session_complete' });
  });

  it('uses one canonical pack contract across fantasy and science fiction', () => {
    for (const scenario of [blackGullScenario, orisonFixture]) expect(validateAgentSchema('session_pack', sessionManifest(scenario))).toEqual({ ok: true, errors: [] });
  });

  it('projects only the active character from a multi-ready pack', () => {
    const mira = sessionManifest(blackGullScenario).characters[0];
    const iko = sessionManifest(orisonFixture).characters[0];
    const projected = projectManifestForCharacter({ schema_version: '1.0', characters: [mira, iko] }, 'mira');
    expect(projected.characters).toEqual([mira]);
    expect(JSON.stringify(projected)).not.toContain('iko');
  });

  it('rejects asserted outcomes at the canonical schema boundary', () => {
    const result = validateAgentSchema('intent', { schema_version: '1.0', operation_id: 'op-1', expected_turn_id: 'turn-1', expected_source_revision: 1, actor_id: 'mira', action_type: 'speak', action: 'Try.', approach: '', speech: '', targets: [], resource_refs: [], knowledge_refs: [], requested_effect: '', asserted_outcomes: ['It succeeds.'] });
    expect(result.ok).toBe(false);
  });
});
