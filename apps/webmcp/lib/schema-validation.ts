import type { ErrorObject, ValidateFunction } from 'ajv';
import { session_pack, turn_brief, intent, resolution } from '@/lib/generated-agent-validators.js';

const validators = {
  session_pack, turn_brief, intent, resolution,
} satisfies Record<string, ValidateFunction>;

function details(errors: ErrorObject[] | null | undefined) {
  return (errors || []).slice(0, 8).map((error) => `${error.instancePath || '/'} ${error.message || 'is invalid'}`).join('; ');
}

export function assertAgentSchema(kind: keyof typeof validators, value: unknown): asserts value is Record<string, unknown> {
  const validate = validators[kind];
  if (!validate(value)) throw new Error(`${kind} schema validation failed: ${details(validate.errors)}`);
}

export function validateAgentSchema(kind: keyof typeof validators, value: unknown) {
  const validate = validators[kind];
  const ok = Boolean(validate(value));
  return { ok, errors: ok ? [] : details(validate.errors).split('; ').filter(Boolean) };
}
