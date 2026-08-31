import fs from 'node:fs';

const report = JSON.parse(fs.readFileSync(new URL('../evals/latest.json', import.meta.url), 'utf8'));
const passed = report.numPassedTests ?? 0;
const failed = report.numFailedTests ?? 0;
const suites = report.numTotalTestSuites ?? report.testResults?.length ?? 0;
const markdown = `# RePoG WebMCP Evaluation Report\n\n- Result: ${failed === 0 ? 'PASS' : 'FAIL'}\n- Tests passed: ${passed}\n- Tests failed: ${failed}\n- Suites: ${suites}\n\nThis deterministic suite covers tool discovery, protocol continuation, cross-genre contract parity, active-character privacy, and outcome-authority rejection.\n`;
fs.writeFileSync(new URL('../evals/latest.md', import.meta.url), markdown);
