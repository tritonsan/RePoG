# Ideas for OpenAI Build Week

Working product-idea document for the public RePoG repository.

## Scope

This document applies only to the public RePoG product: the Codex-native,
human-readable tabletop RPG workspace built around natural GM play, campaign
memory, adaptive Session 0, player-safe visuals, Dashboard V3, and Atlas V1.
It does not use the older Engine Mode experiment as the product direction.

`World Voices — One Event, Many Truths` is now the selected Build Week feature
and has moved from concept into the public product. The remaining ideas stay
as future directions; selection does not remove or rewrite their original
rationale.

## Product Principle

A strong RePoG feature should preserve the current division of responsibility:

- GPT-5.6 Sol performs semantic work: understanding long campaign context,
  reasoning across perspectives, making design judgments, and producing useful
  player-facing material.
- RePoG keeps campaign memory human-readable and local.
- The Player or Designer explicitly approves anything that would become canon.
- Small local helpers may validate safety, revisions, paths, and player-facing
  boundaries, but they should not become a second narrative engine.
- Normal play should remain natural conversation rather than system operation.

## Idea 1: RePoG Chronicle — Bring, Remember, Resume

### Concept

Allow a player to bring an existing campaign into RePoG from long transcripts,
Markdown notes, or supported exports. GPT-5.6 reconstructs the campaign into a
reviewable, human-readable memory set instead of silently treating every
extracted statement as truth.

The feature has three connected experiences:

1. **Bring Your Campaign:** identify characters, relationships, promises,
   locations, open threads, knowledge boundaries, current conditions, and the
   last playable moment.
2. **Ask the Campaign:** answer questions such as “What did I promise Ilya?”,
   “Where did I first hear this name?”, or “What does my character actually
   know?” without exposing GM-only facts.
3. **Resume Exactly:** provide a quick, character-limited, or deep recap and
   continue from the recovered scene anchor.

### GPT-5.6 Sol leverage

- Long-context synthesis across many sessions.
- Temporal, relational, and epistemic reasoning.
- Contradiction detection and uncertainty handling.
- Context-sensitive summarization for different recall depths.

### MVP

- Text, Markdown, and JSON transcript input.
- An import review separating confirmed, ambiguous, contradictory, and missing
  information.
- Explicit approval before materialization.
- Player-safe campaign questions.
- Recovery of one exact resume anchor.

### Main risk

An import must not present inference as established canon. Uncertainty and
conflicting sources need a visible review gate.

## Idea 2: World Voices — Living In-World Documents

**Status: selected and implemented as the production World Voices system.**

### Concept

Turn world reactions into authored artifacts from the limited point of view of
people and institutions inside the setting:

- newspapers and public notices;
- faction bulletins and propaganda;
- personal letters and journals;
- wanted posters and court records;
- intelligence reports and rumor sheets;
- travel guides, academic notes, and trade lists.

The same event can produce different accounts. A harbor office may describe an
archive incident as storm damage, an underground handbill may suspect a
cover-up, and an NPC may privately ask whether the player was involved. Each
artifact must remain bounded by what its author could know, infer, hide, or
misrepresent.

An artifact is canon as an object that exists in the world. Its claims are not
automatically objective truth.

### GPT-5.6 Sol leverage

- Multi-perspective reasoning over a shared history.
- Stable voice, motive, bias, and knowledge separation.
- Long-context callbacks to earlier events and relationships.
- Polished document writing and visual design judgment.

### Public RePoG fit

This builds directly on knowledge boundaries, NPC Agency Cards, faction goals,
world dynamics, causal consequences, visual policy, and the player-safe
dashboard.

### Implemented product scope

- Extensible personal, public-media, institutional, legal, intelligence, and
  cultural/commercial artifact families.
- Private bounded perspective, source event, intent, threads, versions,
  recipient/channel distribution, fictional timing, and permanent operation
  identity.
- Paginated player-safe projection with a Dashboard documents reader, local
  unread state, filters, search, threads, and Compare Accounts.
- Trigger-only generation, review/canon policy, delayed acquisition, natural
  Player responses, retraction/supersession, and full continuity/audit rules.

### Main risk

The artifact must not leak objective GM truth merely because its author sounds
confident. Source knowledge and author claims must remain separate.

## Idea 3: Generative Campaign Interface

### Concept

Advance Dashboard V3 from adaptive tile selection to a campaign-specific
interface composed by GPT-5.6.

Examples:

- a ship cross-section, crew web, tide view, and known ports for a nautical
  campaign;
- an evidence board and event timeline for an investigation;
- a faction-influence constellation for political play;
- a network map and identity/heat surface for cyberpunk;
- a research notebook and term calendar for an academy campaign.

GPT-5.6 should compose from safe UI primitives rather than writing unrestricted
runtime code. Candidate primitives include cards, timelines, maps, relationship
webs, meters, grouped lists, galleries, comparison panels, and document
viewers.

### GPT-5.6 Sol leverage

- Frontend implementation and design judgment.
- Translating a campaign profile into an information architecture.
- Inspecting and refining rendered output.
- Maintaining visual hierarchy, accessibility, and setting identity.

### MVP

- A versioned declarative layout specification.
- A bounded set of approved widget types.
- Preview, accessibility check, player-safe validation, and approval.
- One investigation layout and one relationship-focused layout.

### Main risk

Unrestricted generated JavaScript would increase security and reliability risk.
The model should compose validated UI primitives for the first version.

## Idea 4: World Systems Lab

### Concept

Let the Designer define one foundational world rule and use GPT-5.6 to propagate
its consequences through society rather than generating disconnected lore.

Example premise:

> Magic consumes personal memories.

The lab explores consequences for family, inheritance, education, law,
religion, war, medicine, class, crime, economy, and everyday behavior. It then
returns several internally coherent interpretations, identifies who benefits
and pays, and translates each interpretation into playable pressures,
factions, visible signs, and player choices.

### GPT-5.6 Sol leverage

- Deep causal and cross-domain reasoning.
- Exploring alternatives without prematurely collapsing uncertainty.
- Detecting contradictions between setting rules and play promises.
- Synthesizing a compact World Operating Model.

### MVP

- One premise and up to three candidate world models.
- Cause/effect chains, beneficiaries, costs, exceptions, and observable table
  consequences.
- Conflict review against active setting/play lenses.
- Designer selection, mixing, or revision before any result becomes durable.

### Main risk

The output can become an encyclopedia. Every accepted consequence should have
a concrete implication for play.

## Idea 5: Dynamic Lens Studio

### Concept

Allow GPT-5.6 to create reusable `custom:<slug>` setting and play lenses from a
campaign pitch instead of limiting Session 0 to pre-authored genre labels.

Example:

> Hopeful solarpunk court intrigue with Arctic survival.

The studio identifies tensions between those components, proposes distinct
interpretations, generates campaign-specific Session 0 questions, suggests a
Narrative Signature, defines research needs, and recommends optional tracking
without silently activating mechanics.

### GPT-5.6 Sol leverage

- Creative synthesis across genres and play styles.
- Conflict detection and coherent default generation.
- Designing reusable structured guidance rather than producing one-off prose.

### MVP

- Generate, review, revise, and save one custom lens.
- Required sections for play feel, questions, defaults, conflicts, research,
  narrative guidance, visual direction, and optional modules.
- Composition check against existing lenses.

### Main risk

A custom lens must materially change questions and GM behavior; a renamed list
of generic tropes is not sufficient.

## Idea 6: Director’s Room

### Concept

For major openings, climaxes, aftermaths, and transitions, let GPT-5.6 examine
the same current situation through several editorial concerns before choosing
a playable scene frame:

- player intent and authorship;
- NPC agency and independent goals;
- knowledge and presence boundaries;
- causal consequence;
- pacing and breathing room;
- spatial and visual staging;
- setup/payoff readiness;
- the moment at which control returns to the Player.

The result is not a prewritten plot. It is a better framing of the current
world state while preserving multiple player approaches.

### GPT-5.6 Sol leverage

- Long-horizon planning and revision.
- Comparing several valid scene structures.
- Synthesizing continuity, character, pacing, and presentation concerns.
- Optional deeper review with higher reasoning effort without making a
  multi-agent or API feature mandatory.

### MVP

- Trigger only for selected structural scenes.
- Produce three candidate frames and a short tradeoff analysis.
- Select one frame and discard unused candidates rather than treating them as
  future canon.

### Main risk

If used on ordinary turns, this would add latency and over-direct the game. It
must remain a structural-scene feature.

## Idea 7: Living Faction Media

### Concept

Give each important faction a public voice, internal voice, communication
channels, intended audience, propaganda habits, and information limits. When a
relevant event reaches the faction, GPT-5.6 determines how it would frame and
communicate that event.

This is a focused extension of World Voices. It turns factions from reference
notes into cultural and political actors the Player can encounter through
media, policy, rumor, recruitment, and public reaction.

### GPT-5.6 Sol leverage

- Consistent institutional voice across long campaigns.
- Reasoning about information transmission, incentives, and audience.
- Producing conflicting but internally coherent interpretations.

### MVP

- Public statement, internal memo, and rumor-channel output.
- Explicit event source and faction knowledge basis.
- One artifact only when a believable channel reaches the Player.

### Main risk

Faction media should not appear after every event or make the whole world
instantly aware of the Player.

## Idea 8: Multimodal World Inbox

### Concept

Allow players to add hand-drawn maps, portraits, place sketches, moodboards,
handwritten notes, screenshots, or character sheets. GPT-5.6 interprets the
attachment and creates a reviewable proposal instead of silently changing
canon.

Possible routes include:

- sketch to Atlas proposal;
- portrait to candidate appearance facts;
- moodboard to palette and visual-style proposal;
- handwritten note to candidate campaign facts;
- place sketch to spatial and sensory description.

### GPT-5.6 Sol leverage

- Multimodal understanding.
- Mapping visual evidence to existing campaign context.
- Distinguishing visible facts, uncertain interpretations, and design choices.

### MVP

- One image at a time.
- Per-item accept, edit, or reject.
- Sketch-to-Atlas points and routes.
- Portrait-to-appearance candidate facts.

### Main risk

Image interpretation must remain proposal-only. Unclear labels, routes, or
visual details must not become canon without confirmation.

## Idea 9: Adaptive Campaign Calibration

### Concept

At a session or arc boundary, compare Session 0 preferences with observable
play behavior and offer transparent adjustments.

Examples include dialogue balance, clue density, challenge density, breather
frequency, response length, visual cadence, dashboard tiles, turn protocol,
and the balance between exploration, social play, and conflict.

The review cites behavior without claiming to know the Player’s private
feelings. It asks for confirmation before changing the profile.

### GPT-5.6 Sol leverage

- Pattern recognition over many sessions.
- Separating repeated behavior from isolated events.
- Translating observations into coherent product-level adjustments.

### MVP

- Run only on explicit request or selected boundaries.
- Show evidence, proposed adjustment, likely effect, and a keep-current option.
- Apply only accepted profile changes.

### Main risk

Engagement is not the same as preference. The system must present observations
as questions, not psychological conclusions.

## Idea 10: Living Investigation Board

### Concept

Add a player-safe investigation surface that keeps four categories distinct:

- known evidence;
- Player-authored theories;
- contradictions;
- open questions.

GPT-5.6 can connect evidence across long history while preserving the
difference between fact, inference, rumor, and hypothesis. It must not solve the
mystery from GM-only knowledge.

### GPT-5.6 Sol leverage

- Long-context evidence synthesis.
- Temporal and relational reasoning.
- Maintaining multiple competing explanations.

### MVP

- Evidence and theory nodes.
- Source session or event labels.
- Strengthens, weakens, contradicts, and unanswered relationships.
- A Dashboard investigation tile.

### Main risk

A single hidden-fact leak can spoil a campaign. Only player-known material may
enter the board.

## Idea 11: Visual Continuity Memory

### Concept

Compare new visual drafts with accepted images and appearance notes. GPT-5.6
identifies stable details, possible continuity drift, and plausible intentional
variation.

The Player can request revision, accept a deliberate change, mark a detail as a
temporary scene variation, or promote it to new visual canon.

### GPT-5.6 Sol leverage

- Multimodal comparison across several accepted references.
- Context-sensitive distinction between contradiction and variation.
- Converting accepted visual details into concise continuity memory.

### MVP

- Character portrait continuity.
- Place-landmark continuity.
- Candidate differences grouped as consistent, possible drift, and possible
  intentional variation.

### Main risk

Lighting, pose, clothing changes, and viewpoint can create false positives. The
feature should advise, not automatically reject.

## Idea 12: Private Possibility Horizon

### Concept

At session preparation or an arc boundary, use GPT-5.6 to explore several
causally plausible trajectories for active NPCs, threads, and pressures without
turning any trajectory into a planned plot.

Each possibility states its required trigger, who could know about it, how it
could become visible, and what would invalidate it. Unused possibilities are
discarded rather than stored as facts.

### GPT-5.6 Sol leverage

- Long-horizon causal planning.
- Counterfactual comparison.
- Coordinating NPC agency, knowledge, timing, and pacing.

### MVP

- Up to three possibilities for one active pressure.
- Required trigger and visible channel for each.
- No automatic world advancement and no player-facing spoiler output.

### Main risk

The feature must support improvisation rather than encouraging the GM to force
a preferred future.

## Comparative View

| Idea | GPT-5.6 leverage | Public RePoG fit | Demo impact | Relative effort |
| --- | --- | --- | --- | --- |
| RePoG Chronicle | Very high | Very high | Very high | High |
| World Voices | Very high | Very high | Very high | Medium |
| Generative Campaign Interface | Very high | Very high | Very high | High |
| World Systems Lab | Very high | Very high | High | Medium |
| Dynamic Lens Studio | High | Very high | High | Low–medium |
| Director’s Room | Very high | High | Medium | Medium |
| Living Faction Media | Very high | Very high | High | Medium |
| Multimodal World Inbox | Very high | Very high | Very high | Medium–high |
| Adaptive Campaign Calibration | High | Very high | Medium | Low–medium |
| Living Investigation Board | Very high | Very high | High | Medium–high |
| Visual Continuity Memory | High | Very high | High | Medium |
| Private Possibility Horizon | Very high | High | Medium | Medium |

## Candidate Feature Packages

### Package A: A World That Speaks

- Flagship: World Voices.
- Supporting feature: Living Faction Media.
- Visual layer: Dashboard document artifacts.

Core message: GPT-5.6 lets every person, institution, and faction express the
world from its own limited point of view.

### Package B: Bring Any Campaign To Life

- Flagship: RePoG Chronicle.
- Supporting feature: Ask the Campaign.
- Visual layer: Living Investigation Board or timeline.

Core message: GPT-5.6 can understand, reconstruct, and safely resume a long
campaign rather than merely summarize it.

### Package C: The Campaign Designs Its Own Interface

- Flagship: Generative Campaign Interface.
- Supporting feature: Multimodal World Inbox.
- Quick semantic addition: Adaptive Campaign Calibration.

Core message: GPT-5.6 turns the campaign’s actual structure into a polished,
local, player-safe interface.

### Package D: Build Worlds From Consequences

- Flagship: World Systems Lab.
- Supporting feature: Dynamic Lens Studio.
- GM-quality layer: Director’s Room.

Core message: GPT-5.6 designs playable causal systems rather than producing
encyclopedic lore.

## OpenAI Build Week Requirement Interpretation

The official [OpenAI Build Week page](https://openai.devpost.com/) asks entrants
to create a project with Codex and GPT-5.6 and to explain in the demo how both
were used. The [Official Rules](https://openai.devpost.com/rules) also state
that an existing project may qualify when it is meaningfully extended during
the submission period using Codex and/or GPT-5.6, with dated evidence of that
work.

### Compliance floor

The published rules do not explicitly require every project to embed the
OpenAI API or invoke GPT-5.6 through a runtime API. At minimum, the project must
be built or meaningfully extended with Codex/GPT-5.6, work as demonstrated, and
provide the requested evidence, README explanation, video explanation, and
Codex `/feedback` session ID.

### Competitive bar

Merely saying “GPT-5.6 wrote the code faster” is likely a weak competitive
story. The judging criteria ask how thoroughly and skillfully the project uses
Codex, alongside product completeness, impact, and novelty. A stronger entry
makes a distinctive GPT-5.6 capability visible in the user experience and
shows why that capability materially improves the product.

### Implication for RePoG

Public RePoG already uses Codex and its selected model as the live semantic GM;
it is not only code produced by an AI assistant. A new Build Week feature does
not need to add an API-key requirement. It should instead make one or more
GPT-5.6 Sol strengths unmistakable:

- long-context campaign understanding;
- multi-perspective and epistemic reasoning;
- long-horizon planning and revision;
- multimodal interpretation;
- frontend and document design judgment;
- agentic coordination of local workspace work.

The safest strategic interpretation is therefore:

> **Being built with GPT-5.6 is enough for baseline compliance when properly
> evidenced; using GPT-5.6 as an essential, visible product capability is the
> stronger path to winning.**

## Original Evaluation (Preserved)

No final feature has been selected. RePoG Chronicle remains in consideration.
Among the newer directions, World Voices currently offers the strongest
combination of model-native reasoning, Public RePoG fit, user-visible value,
and a concise demo. Generative Campaign Interface has the highest visual and
technical ceiling but also higher implementation risk.

Content based on the official hackathon pages was rephrased for compliance with
licensing restrictions.

## Selection Update

World Voices is the selected and implemented Build Week feature. The original
comparison above remains as the decision record; the other concepts remain
future directions rather than commitments in this release.
