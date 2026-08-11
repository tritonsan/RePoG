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

# Run Before Canon-Dependent Options

Once the Player names an existing universe, a real place/period, or supplied
homebrew, run this gate before presenting any option set whose content depends
on that source. Power bands, threat scale, travel and communication limits,
institutions, currency, and tonal examples are all source-dependent. Offering
them from memory lets the Player accept a promise built on unverified claims,
which later collides with canon policy and forces a redesign.

Until a claim is verified, either look it up or mark it as unverified in the
same message. Never present an unverified source claim as settled fact, and
never let one become durable truth.

This applies to every named external source, not only fictional canon: a real
place, period, or profession, a scientific basis, and Designer-supplied homebrew
all create source-dependent claims.

# Research Passes

Research is not a single gate crossed once. It runs as bounded passes.

**Anchor pass.** Immediately after the world anchor, before any
source-dependent option is offered. Scope: the structural layer the rest of the
interview rests on—world rules, hard limits, what is absent or impossible,
capability calibration for the candidate scales, native register, and character
grammar when the cast is original. Nothing here depends on tone or player
fantasy, so it is safe to run before the rest of the promise.

**Triggered pass.** Whenever an accepted answer opens a source-dependent
question the dossier does not answer, run a narrow pass bounded to that one
question before the dependent truth is locked. A chosen profession, an
unfamiliar institution, a specific technology, a medical or legal limit, or a
newly named place all qualify.

Keep a triggered pass narrow: one question, a small lookup. Breadth is what
makes research slow, and a wide pass mid-interview also invites scope drift.
Use `workflows/orchestration/WORKFLOW.md` only for the genuinely multi-domain
case already described below.

Record every pass in the dossier: which accepted answer triggered it, the exact
question, what was verified with references, and what stays open. Findings are
appended; earlier verified entries are not rewritten to fit a later answer.

Permission already granted for the same source scope is not requested again. A
new source domain, or a widening of the accepted scope, needs its own
budget-exempt permission turn. Status returns to `partial_complete` whenever a
new open question affects the current scale, and durable truth waits for the
explicit current-scale permission.

# Cast Scope Tiers

Research scope depends on how much of the source's cast and timeline is in
play. Establish this stance here, because it decides what must be looked up.
Canon Policy later inherits it and locks the detailed rules; it does not ask the
stance again.

- **`full_canon`** — canon characters, events, and timeline are live. Research
  the world rules and limits, the timeline anchor, the relevant canon cast and
  institutional leadership, and the established events the opening depends on.
- **`canon_world_original_cast`** — the setting's structure, era, and rules are
  canon, but the people are original. Research the structural layer and the
  source's character grammar: archetypes, how ability and reputation are
  expressed, naming conventions, and what a dangerous or ordinary figure looks
  like. Canon biographies stay out of scope; the grammar does not, because
  original characters must still feel native.
- **`genre_adjacent_original`** — an original world inspired by the genre.
  Research only genre conventions, register, and any real-world basis the
  Player asked for. Do not run canon lookups.

# Scope Bound And Register

Bound every lookup to the initial playable scale. A long-running source can
absorb unlimited reading; anything outside that scale stays an open question
rather than an invented answer.

Record the source's native register: how much absurdity, spectacle, comedy,
brutality, or procedural detail belongs to it, and what narration would feel
foreign even when every fact is correct. Native register is the default. The
Player may deliberately diverge from it, and that choice wins, but record it as
an explicit divergence so later turns neither drift back to the native register
nor slide further away from the accepted one.

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

# In-Play Research

Source questions do not stop when Session 0 ends. A scene can reach a rule, a
place, a profession, or an institution the dossier never settled, and the honest
options are narrow: ask, assume conservatively, or look it up. Decide which during
setup, because deciding mid-scene costs the Player time and attention.

Record one policy in `research_dossier.md`:

- `off` — never search during play. An unresolved question goes to the Designer or
  takes a conservative assumption and stays an open question.
- `ask_first` — offer a lookup when the answer would change durable truth, then
  wait for a yes.
- `bounded_auto` — run a narrow lookup without asking, but only when the question
  blocks durable truth or would otherwise create a source contradiction.

The guards hold under every policy. Search only for the one question in the way;
never widen scope mid-turn. Never search for flavor, atmosphere, or a detail the
scene can simply avoid. Record the result as a research pass with its references
and open remainder, exactly as a setup pass would be recorded. An unresolved
answer stays open rather than becoming invented canon. The source permission from
the interview still applies, so the same source scope is not re-authorized; a new
source domain or a widened scope needs its own permission turn.

State the cost when offering this: a lookup adds roughly ten to forty seconds to
that turn, and more when several pages are needed. In Player Mode this stays
invisible beyond a brief natural wait; do not narrate searching, tools, or
sources.

# Handoff

After research, update the relevant interview modules from the accepted
dossier. Do not let a worker proposal silently revise an already accepted
pitch, palette, canon boundary, mechanic, or real/fictional Companion scope.
Research does not itself set readiness.

Fill the dossier's source-derived sections before dependent truth is locked:
cast scope and closeness, timeline anchor, world rules and hard limits, what is
absent or impossible, authority and social structure, capability bands for the
chosen scale, travel and news speed, economy, institution types, native
register, character grammar when the cast is original, protected source facts,
and unresolved questions. Keep facts and references; do not copy long passages.

Those constraints then feed Canon Policy, Palette, and World Truths without
re-asking the Player for permission already granted here.

