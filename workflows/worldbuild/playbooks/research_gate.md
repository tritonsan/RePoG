# Session 0 Research Gate

Load only when canon, a real place/period/profession, hard science, factual
realism, or Designer-supplied source material affects the initial playable
scale.

# Decision And Status

Classify the campaign as existing canon, real-world-specific,
genre-adjacent, fully original, or user-supplied homebrew. Ask whether to use
web research, supplied sources, conservative assumptions, or an explicit
bounded risk. Treat user-supplied homebrew as authoritative and ask before
mixing outside sources.

Record one status in `research_dossier.md`:

- `not_needed`;
- `needed_pending`;
- `partial_complete`;
- `complete`;
- `unavailable_risk_accepted`.

Also record explicit `Risk accepted: yes|no` and
`Current-scale lock permitted: yes|no`. Boilerplate or an empty note never
counts as risk acceptance. `needed_pending` cannot lock the world or enter
play. `partial_complete` is sufficient only when researched scope covers the
starting scale and the current-scale permission is explicit.

# Selective Research Delegation

Use `workflows/orchestration/WORKFLOW.md` only when all research decisions are
frozen and there are at least two independent source domains or questions.
Examples include canon timeline plus power rules, or geography/travel plus
law/profession. One narrow lookup remains serial.

Worker cap:

- Quick: two;
- Standard or Deep: three;
- never more than the active profile permits.

The coordinator creates one immutable research packet per lane with the exact
question, allowed sources, date/version scope, frozen campaign assumptions,
claims requiring evidence, protected information, and base setup revision.
Workers return evidence-linked findings, contradictions, confidence limits,
and unresolved questions. They do not write `research_dossier.md`, decide
canon, accept risk, classify player knowledge, or lock a world truth.

The coordinator compares sources, resolves conflicts conservatively, writes a
single dossier, and asks the Designer when a material ambiguity changes the
campaign promise. Unsupported claims stay open. If sub-agents are unavailable,
run the same lanes serially and preserve the same evidence/result contract.

# Handoff

After research, update the relevant interview modules from the accepted
dossier. Do not let a worker proposal silently revise an already accepted
pitch, palette, canon boundary, mechanic, or real/fictional Companion scope.
Research does not itself set readiness.

