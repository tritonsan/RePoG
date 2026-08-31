import fs from 'node:fs';
import path from 'node:path';
import Ajv2020 from 'ajv/dist/2020.js';
import standaloneCode from 'ajv/dist/standalone/index.js';

const root = path.resolve(import.meta.dirname, '..');
const schemas = {
  session_pack: 'agent-session-pack.schema.json',
  turn_brief: 'agent-turn-brief.schema.json',
  intent: 'agent-intent-envelope.schema.json',
  resolution: 'agent-resolution-envelope.schema.json',
};
const ajv = new Ajv2020({ allErrors: true, strict: true, code: { source: true, esm: true } });
const exports = {};
for (const [name, filename] of Object.entries(schemas)) {
  const schema = JSON.parse(fs.readFileSync(path.join(root, 'contracts/agent-seat/v1', filename), 'utf8'));
  ajv.addSchema(schema, name);
  exports[name] = name;
}
const notice = '/* eslint-disable */\n// Generated from canonical RePoG Agent Seat schemas. Do not edit.\n';
fs.writeFileSync(path.join(root, 'lib/generated-agent-validators.js'), notice + standaloneCode(ajv, exports));
