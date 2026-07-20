# World Voices — One Event, Many Truths

World Voices turns causally justified reactions into persistent in-world
communications: letters, notices, newspapers, bulletins, memoranda, legal
records, intelligence reports, rumors, propaganda, and setting-appropriate
cultural or commercial texts.

Its central rule is simple: a document may canonically exist without its
claims being objectively true. Each source communicates only from what it
could know, believe, infer, conceal, distort, or deliberately misrepresent.

## What It Is Not

World Voices is not a content quota, continuous social simulation, universal
truth narrator, or Python story generator. GPT-5.6 decides whether anyone
communicates, how information travels, what a source knows, why it speaks, and
what it writes. Deterministic tools enforce ids, revisions, lifecycle,
references, idempotency, atomic writes, and player-safe projection only.

Ordinary soft turns do no World Voices work and never scan the archive.

## Enable It In Session 0

`play_profile.yaml.world_voices` materializes five choices:

- `mode`: `off`, `manual`, `curated`, or `reactive`;
- `approval_policy`: `review_each` or `preapproved_bounded`;
- `dashboard_policy`: `off`, `delivered_only`, or
  `delivered_and_public`;
- `artifact_richness`: `concise`, `balanced`, or `rich`;
- `communication_speed`: `slow`, `mixed`, `fast`, or `setting_defined`.

The default is off and review-first. Missing configuration also means off, so
existing campaigns do not change behavior. Quick Session 0 folds the proposal
into the Starter Bundle rather than adding a questionnaire. Standard or Deep
may clarify communication infrastructure, censorship, access, institutional
media, and common private channels only when those choices matter.

## Causal Product Loop

1. A witnessed/durable event, elapsed-time trigger, message, discovery, leak,
   world-domain evaluation, or explicit request qualifies—or produces no
   communication.
2. The GM traces a believable information path, including time, distance,
   reliability, distortion, censorship, access, and failure.
3. Only relevant sources with access and motive are considered. Silence and
   delay are valid.
4. The GM separates confirmed knowledge, observation, belief, inference,
   rumor, withheld facts, deliberate falsehood, uncertainty, and what the
   source cannot know.
5. It plans audience, intent, channel, form, time, place, and practical goal.
6. It drafts in the source's stable voice and performs a private semantic
   safety review.
7. The configured approval policy decides when artifact existence becomes
   canon.
8. Recipient/channel-specific distribution is scheduled and later delivered,
   lost, intercepted, leaked, discovered, copied, quoted, altered, forged,
   archived, retracted, or superseded. Distribution archiving is explicit and
   preserves its acquisition and delivery history.
9. Only legitimately acquired documents enter Player Mode and the optional
   Dashboard projection.
10. Player replies and statements use natural chat. Drafted Player wording
    always waits for explicit approval.

## Existence, Claims, Knowledge, And Visibility

These are four different questions:

- **Existence canon:** did this document actually exist in the fiction?
- **Claim position:** what does this document assert, doubt, omit, or lie about?
- **Knowledge ownership:** who currently knows or suspects the referenced fact?
- **Player visibility:** has the character legitimately obtained the document?

`knowledge_boundaries.md` is the sole authority for current facts and holders.
World Voices references its fact ids in private claim records but never copies
objective campaign truth. Delivering a document that reveals protected
information requires the matching knowledge update in the same durable
revision.

## Lifecycle And Distribution

Artifact bodies are immutable historical Markdown files. Corrections,
retractions, replies, and superseding editions are new artifacts linked to the
original; they never erase it. Distribution records have their own recipients,
channel, timing, causal basis, status, acquisition context, and append-only
history. A scheduled or in-transit item cannot appear before acquisition.
Human-readable fictional dates are paired with coarse non-negative time
indices for deterministic authored/received ordering; the indices order events
but do not create a simulation clock.

Stable operation ids and monotonic sequences make retries idempotent. The
completed-operation ledger is not truncated, so an old operation id never
becomes valid again. Later reactions become pending consequences or triggered
world-domain evaluations; the system does not recursively generate an
unbounded response cascade.

## Player Interaction

The Dashboard is read-only. In natural play, the Player can reply, issue a
statement, circulate a rumor, publish a notice, share/hide/leak/destroy a
document, show it to someone, question authenticity, or compare accounts. If
the GM offers exact wording for the player character, it asks for approval
before canonizing it.

Player Mode shows the document, its believable acquisition context, and the
fictional situation around it—never artifact ids, fact ids, claim labels,
files, schemas, tools, or validation. Designer Mode may inspect those details.

## Dashboard Documents Tile

When enabled, the V3 `documents` tile reads only
`dashboard/assets/world_voices/catalog.json`. The projection is paginated and
each visible document has a separate bounded JSON file. Private campaign files
are never browser-readable.

The tile provides Inbox, Public, Archive, and Threads views; source/type
filters; search; browser-local unread emphasis; a responsive document reader;
controlled local skins; and Compare Accounts. Compare Accounts places only
player-known reports side by side and explicitly does not identify the GM-only
correct answer. Open reader state survives unrelated tile refreshes.

Hidden artifacts do not appear as locked entries, silhouettes, filenames,
counts, search results, or comparison candidates. Hidden changes do not cause
a Dashboard refresh. Projection files are validated on request by the
loopback-only server.

## File Ownership

| Authority | Owns |
| --- | --- |
| `knowledge_boundaries.md` | Current facts, epistemic status, and holders |
| `world_dynamics.md` | Triggered offscreen movement and evaluation timing |
| `session_log.md` | Append-only durable history |
| `current_state.yaml` | Immediate scene and continuity revision |
| character/faction notes | Stable voice, verification, and communication tendencies |
| `world_voices/index.json` | Artifact identity, private epistemic basis, lifecycle, threads, versions, distribution, operation ledger |
| `world_voices/artifacts/*.md` | In-world bodies, retained as history |
| `dashboard/assets/world_voices/` | Derived player-safe catalog/pages/documents only |
| `dashboard_state.json` | Read-only tile pointer and refresh metadata, never campaign truth |

Keep only active/pending artifact and thread references in hot preparation.
Load bodies or old threads on demand.

## Deterministic Commands

Validate all private memory and player projection:

```powershell
python tools/check_world_voices.py campaign
```

Lifecycle operations accept already-authored JSON:

```powershell
python tools/world_voices.py campaign propose --input-json '{...}'
python tools/world_voices.py campaign approve --input-json '{...}'
python tools/world_voices.py campaign schedule --input-json '{...}'
python tools/world_voices.py campaign deliver --input-json '{...}'
python tools/world_voices.py campaign archive_distribution --input-json '{...}'
python tools/world_voices.py campaign project --input-json '{...}'
```

Every mutating input includes `expected_revision`,
`expected_continuity_revision`, `operation_id`, and the next
`operation_sequence`. Durable changes may also set
`result_continuity_revision` to the next campaign revision. Player acquisition
requires `knowledge_update_confirmed` and a matching `knowledge_revision`.

After a player-visible projection, add or patch the documents tile through
`tools/update_dashboard.py` with expected source/dashboard revisions. A stale
Dashboard write is rejected rather than overwriting newer state.

## Concise Example

A crowd witnesses damage at a harbor archive. After believable information
travel, an office issues a reassuring notice, an opposition outlet questions
the official explanation, and a witness privately describes someone who only
resembled the player character. All three texts may exist; none becomes
objective truth merely because it was written. The Dashboard shows only the
accounts the character actually receives, and comparison exposes differences
without answering what the character cannot yet establish.

## Compatibility And Performance

- Missing policy or memory means off; old campaigns remain playable.
- Migration never invents historical documents or knowledge.
- No API key, MCP server, remote service, image generation, or external asset
  is required.
- Soft turns add no writes, checks, archive loads, or Dashboard work.
- Full archive reconciliation and validation belong at full distill, explicit
  audit, or direct Designer request.
- Rich artifacts may add drafting/review time only on triggered turns; exact
  latency varies by model load, document richness, and selected maintenance
  policy.
