# World Voices Playbook

Load this playbook only when a communication trigger occurs, a document reaches
the character, the Player asks what people are saying, the Player intentionally
sends or publishes something, or an existing artifact receives a plausible
reply. World Voices is a causal result or pending consequence, never a second
turn engine and never a quota.

## 1. Qualify The Trigger

Identify the durable event, prior artifact, elapsed-time threshold, discovery,
public statement, or explicit request that could cause communication. “No
communication,” silence, waiting, and private discussion are valid results.
Do not scan every actor and do not recursively resolve more than one new
communication layer in the same turn unless the Player requests a montage.

## 2. Trace Information Reach

For each genuinely relevant candidate source, establish a believable path:
direct observation, witness testimony, correspondence, reporting chain, public
media, faction intelligence, travel rumor, surveillance, investigation, leak,
interception, or deliberate misinformation. Account for fictional time,
distance, attention, reliability, distortion, censorship, access, and failure.
An actor does not react merely because the GM knows.

## 3. Choose Voices Or Silence

Choose only actors with both access and a reason to act. Reuse character,
faction, institution, office, outlet, and informal-network concepts. Consult
their stable communication tendencies and current relationships. Delay,
refusal, observation without publication, or silence may be the strongest
choice.

## 4. Build Each Bounded Perspective

Privately separate:

1. confirmed facts the source can know;
2. direct observation or evidence;
3. beliefs treated as true;
4. inferences;
5. rumors;
6. known facts withheld;
7. claims made without belief;
8. facts the source cannot know or imply;
9. uncertainty and confidence;
10. verification habits and trusted channels.

`knowledge_boundaries.md` remains the sole current fact/holder authority. The
World Voices manifest references fact ids and records artifact-specific claim
positions; it does not create objective truth. A confident lie remains a claim
inside an artifact, not campaign fact.

## 5. Plan The In-World Action

Before drafting, state privately: source, intended audience, intent, channel,
form, authored time/place, causal source event, thread, and desired practical
effect. Intent may inform, persuade, reassure, threaten, accuse, deny, evade,
recruit, request aid, order, preserve a record, shape opinion, conceal,
distract, provoke, confess, negotiate, warn, or memorialize. Decorative prose
without an audience and purpose does not qualify.

## 6. Draft And Review Semantically

Write from bounded perspective, social position, stable voice, intended
audience, setting, goals, relationships, and prior statements. Then privately
review:

- every presented fact is knowable or has an in-world reason to be asserted;
- inference is not accidentally objective narration;
- a lie has motive and risk;
- protected names stay protected;
- delivery that reveals a protected fact has a matching knowledge update;
- voice, audience, channel, reach, and timing are plausible;
- the artifact follows from a real cause;
- Player authorship is preserved.

Revise or reject unsafe work. Never expose claim classifications, fact ids, or
this review in Player Mode.

### Optional Multi-Artifact Drafting

World Voices may use structural delegation only when all of these conditions
hold:

- `play_profile.yaml.performance.semantic_parallelism` is not `off` and the
  host supports delegation;
- one already-resolved trigger or an explicit Player-requested montage calls
  for at least three genuinely independent artifacts;
- each artifact has its own source/author, audience, channel, purpose, and
  bounded knowable claims;
- the artifacts can be drafted without one depending on receipt of another.

Use no more than three read-only workers and never exceed
`performance.max_parallel_workers`. The primary agent first resolves whether
each artifact exists, traces information reach, assigns stable artifact and
operation ids, and builds a bounded author packet containing only allowed
facts, evidence, beliefs, motives, relationships, timing, voice constraints,
protected facts, forbidden implications, and the required output shape. One
worker receives one packet and returns one non-canon draft plus an explicit
claim/evidence list. It must not browse unrelated campaign memory, invent
objective truth, write files, schedule or complete delivery, update knowledge,
project a catalog, patch the Dashboard, or speak to the Player.

The primary agent remains the sole semantic reviewer and persistence owner. It
checks each proposal against current knowledge and visibility, resolves
cross-artifact contradictions that are not intentional in-world disagreement,
and applies canon/review/distribution policy serially. `review_each` drafts
remain non-canon until Designer approval. A failed, unsafe, conflicting, or
stale proposal is discarded and redrafted serially; no partial batch is
reported as complete.

Two artifacts, a reply that depends on another artifact, a Player-authored
message awaiting approval, and all ordinary single-document events remain
serial. Parallel drafting never authorizes a second reaction layer in the same
turn.

## 7. Review, Canon, And Distribution

Follow `play_profile.yaml.world_voices`:

- `off`: do not use the feature;
- `manual`: act only on a direct Designer or Player communication request;
- `curated`: consider strong triggers, but review each artifact by policy;
- `reactive`: consider relevant triggers proactively without actor-wide scans.

`review_each` requires Designer approval before existence becomes canon.
`preapproved_bounded` authorizes only causally justified, semantically reviewed
behavior within the recorded campaign policy. Artifact existence, claim truth,
current holders, Player discovery, and Dashboard visibility are separate.

Schedule a recipient- and channel-specific distribution. Delivery may be in
transit, delayed, lost, intercepted, leaked, discovered, copied, quoted,
altered, forged, archived, retracted, or superseded. Never use one global
visibility flag.

## 8. Player Delivery And Return Of Control

Show a document only when the character can publicly access, receive,
discover, intercept, or credibly hear it. If delivery reveals a protected fact,
update its knowledge holder/status in the same durable revision before Player
Mode. Hidden artifacts must be absent from Dashboard state, files, counts, and
silhouettes.

Present the artifact in-world, explain its acquisition context naturally, show
immediate affordances, and return control. Do not mention ids, files, schemas,
truth labels, validation, or tools.

## 9. Player Responses

The Player may reply, publish, share, hide, leak, destroy, show, question,
compare, or annotate through natural chat. If you draft their wording, show it
for explicit approval before canonization. Never decide their commitments.
Approved Player communication becomes an outbound artifact and later actors
may react only after it reaches them through a believable channel.

## Persistence And Performance

- Soft turns do no World Voices work.
- Artifact creation, approval, distribution changes, Player acquisition,
  retraction, supersession, and approved Player responses are durable when they
  matter later.
- Increment continuity once and append one matching durable event; cold archive
  reconciliation does not create another revision.
- Pair human-readable authored, scheduled, and completed times with coarse
  non-negative time indices so delay and ordering remain deterministic without
  implying a continuous clock.
- Keep only active/pending artifact and thread references hot. Load bodies and
  old threads on demand.
- Hidden changes never refresh the Dashboard. Player-visible delivery may
  project and patch the documents tile according to dashboard refresh policy.
- Store the same operation id forever; retries must not duplicate work.
- Worker drafts are transient proposals. Only the primary agent may persist an
  artifact, assign its final claim positions, update holders, advance
  distribution, increment continuity, or expose a player-safe projection.
