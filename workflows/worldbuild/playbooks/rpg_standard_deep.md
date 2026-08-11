# RPG Standard And Deep Session 0

Load only after the router selects RPG Standard or Deep.

Schema-v7 RPG Standard completes the 21-module reciprocity core in 21–30
content decisions. Set `question_target` inside that range and keep every pack
lifecycle list empty. Schema-v7 RPG Deep uses the same core plus only
triggered adaptive packs; set an initial target from 30–45 and do not exceed 45
without separately recorded extension approval.

An active schema-v1–v6 Standard/Deep campaign retains its legacy 17-module and
approval behavior unless the Player explicitly approves migration. Do not
silently restart or renumber an in-progress legacy interview.

The schema-v7 causal order is:

`campaign promise -> character seed -> character-aware world scaffold -> Deep expansion when selected -> two-way reciprocity pass -> design approval -> materialized preparation -> player-safe preparation review -> preparation approval -> readiness`

# Decision Accounting

Each named module contains at least one content decision. The first accepted
completion of that decision increments `questions_completed`; a genuinely
separate follow-up may consume another decision within the route budget.
Revising an already completed decision increments `setup_revision` but never
increments `questions_completed` again.

Every accepted decision or revision is persisted in the same turn: write the
semantic owner, update `session_zero.md`, increment `setup_revision`, and sync
`play_profile.yaml.source_setup_revision`. Do not defer accepted module truth
to finalization and do not run full validation after every question.

The experience/depth gates do not count. Research execution, evidence review,
and every explicit source-scope or unavailable-source risk permission remain
budget-exempt separate turns and revisions. Deep checkpoints and extension
permissions are also control turns rather than hidden content decisions.

Modules 19, 20, and 21 complete only when the Player accepts the named review.
Displaying a proposal, draft, or prepared result does not itself count as
acceptance.

Each module is one decision boundary under the router's shared Player Chooses /
Coordinator Realizes / Player Reviews contract. A follow-up consumes another
decision only when it passes that contract's independent-follow-up test and the
route budget still has capacity; clarification, an `accept|mix|change` exchange,
implementation-field collection, and factual correction stay inside the module
already in progress. Never convert a semantic owner's field list into a
question list.

# Schema-V7 Core Pipeline

## Character Seed And Contracts

1. **Campaign Promise And Player Fantasy:** split this module by kind. The first
   decision is the frame: which universe, real place and period, original world,
   or supplied homebrew; which slice of it the campaign starts in; and the
   declared reach—`contained`, `regional`, `long_journey`, or `episodic`—with the
   stated destination when there is one. These are one natural answer, and the
   reach decides how the rest of the interview is framed. The second, separately
   counted decision is the experience: emotional tone, promised play, desired
   player fantasy, dominant feel, and what the campaign must not become. Ask it
   only after the frame is settled, and never fold either decision into a system
   or presentation contract.

   The declared reach is an intent, not a guarantee: it sets preparation depth
   and question framing, never the outcome, and no scene bends to keep the
   ambition on schedule. Macro depth scales with it—a contained reach keeps the
   macro frame thin, while a long journey deepens it and opens later regions
   through staged research passes instead of researching everything at once.
   Record it in `world.md` and let module 15 inherit it. When the anchor names an existing universe,
   a real place/period, or supplied homebrew, ask the source and research
   permission right here as a budget-exempt permission turn and run
   `research_gate.md` before offering any source-dependent option, then prepare
   contextual bundle options from verified ground. Module 2 records the resulting
   classification, scope, status, and risk without asking again.
2. **Research Need And Source Boundary:** classify canon, real-world,
   homebrew, genre-adjacent, or original grounding; establish source scope,
   bound it to the initial playable scale, and record the cast scope stance—
   `full_canon`, `canon_world_original_cast`, or `genre_adjacent_original`—
   because it decides what must be looked up. Those three stances presuppose a
   source, so a fully original setting takes none of them: record the
   `fully_original` classification and leave the cast scope unset, since there is
   no source cast to scope and nothing to look up. Load `research_gate.md` before
   dependent truth when needed. Each unresolved source or risk permission stays
   a budget-exempt separate turn.
3. **Agency, Authorship, And Content Boundaries:** split this module by kind.
   Ask the content boundary first and alone, using the standard category set in
   `boundaries.md` with open, fade, or avoid for each, "everything open" as a
   real answer, and both guarantees said out loud: a limit may be added at any
   time including mid-play, and adding one is never a cost. Never place it in a
   card, and never let a card acceptance set it.

   The separately counted decision is the authorship and consequence stance, with
   its two axes kept independent: who authors the character's inner life, past,
   and decisions, and whether permanent loss is in play or consequences stay
   heavy but recoverable. Derive the character-side approval triggers from those
   two answers instead of asking for a list: fully player-owned authorship means
   every GM-authored inner state, past fact, relationship, or decision about the
   character needs approval, while permanent loss in play is pre-authorized and
   needs no separate approval each time. Record the derived triggers in
   `boundaries.md`. World-side creation authority belongs to module 18.
   Clarification is a default rather than a question—ask before anything
   consequential or irreversible, infer cosmetic detail, show it at review—and
   the Player may change it in play. Character-specific limits, such as which
   past facts are protected, are settled at modules 4–5 by applying this stance
   instead of asking for it again.
4. **Character Identity, Current Desire, And Why Now:** run this module as a
   short ordered sequence rather than one broad question, because the world's
   reactions and the opening are built from it. Each part is one question and one
   counted decision:

   - **4a identity core:** name, concept, and what they do now. Feeds world
     placement and how strangers address them.
   - **4b character surface:** the concrete physical basics—gender or
     presentation, age, height, weight or frame, body type and condition, and
     distinguishing features—plus the most striking quality, physical or not;
     appearance direction; manner and habits; how they express themselves; and
     anything else the Player considers essential. Ask the basics plainly; they
     settle physical resolution, concealment and disguise plausibility, how
     strangers guess age and standing, and visual continuity. Ask about the character, not
     about how others should react to them. Record it in `player.md` and derive
     the public read—assumptions, who relaxes and who bristles, what they can
     pass as—from it. That derivation feeds NPC first reactions and social
     friction, and it is revised whenever the Player adds to the character.
   - **4c desire and why now:** the immediate desire and the reason action
     matters at the opening scale this week rather than last year. Feeds the
     opening hook and its pressure.

   Apply the module-3 authorship stance rather than re-asking it: note which past
   facts the Player marks as protected and which relationships may be invented.
   Under fully player-owned authorship, an axis the Player leaves open stays
   blank and is asked when it becomes load-bearing—never filled by inference.
5. **Competence, Limitation, Social Position, And Change Appetite:** run this as
   an ordered sequence for the same reason:

   - **5a capability grounding and reliable competence:** ask the resolution
     grounding here, because how competence is expressed depends on it:
     `fictional`, `bands`, or `numeric`. Module 6 inherits the answer and does not
     ask again.

     With `numeric` or `bands`, derive two to four candidate stat sets from the
     researched world and the declared starting stage rather than importing a
     generic set—omit capabilities the stage has not reached, add setting-specific
     axes when it warrants them—and let the Player accept, mix, or change one.
     Starting distribution has one constraint: every declared axis receives at
     least one point, and there is no per-axis cap. Ask separately whether the
     setting carries capabilities the axes cannot describe—a fruit power, a force
     discipline, a school of signs—and when it does, give that layer its own pool of
     special ability points recorded in `rules.md`, so a special power never competes
     with ordinary competence for the same currency. Where the setting has no such
     layer, do not invent one.
     Author each axis before any distribution: what it covers, what it does not,
     and what a low, middle, and defining value look like in this setting. Show
     those meanings to the Player, because numbers chosen against unexplained
     labels are guesses. Keep each to one line so the block can stay in hot
     context during play.
     Derive the point total and the low/middle/defining bands from the accepted
     axis count and starting level instead of reusing a fixed classic total, state
     them, and ask how many points the Player wants to spend. Record the accepted
     axes in `rules.md` so validation follows that set. Then derive the reliable
     competence and what clean success looks like from the distribution and
     confirm it, rather than interviewing each capability separately.

     With `fictional`, establish the same competence in prose with no stat work.

     A Player may deliberately choose a competence that runs against their
     distribution; record the tension as accepted rather than correcting it.
     Either way, the result feeds the clean-success space.

     Whatever model is accepted becomes binding in play, not decoration. Write it
     in the compact form the GM keeps hot, and expect resolution to name the axis
     or capability an action leans on, read the opposition on the same scale, and
     refuse narration that contradicts it.
   - **5b real limit:** scope this by the accepted grounding. Under `fictional`,
     ask for the limit, its cost, and the counterplay channel, since nothing else
     records them. Under `numeric` or `bands`, the low end of the accepted
     distribution already states the mechanical limit, its cost, and how
     opposition presses it—derive and show that instead of asking, because
     restating a weak axis back to the Player as a question is duplication.

     What remains is only what the sheet cannot express: an obligation or debt, a
     vow or refusal, a physical or mental condition, a fear, or the cost of being
     recognized. Ask for that once. If the Player has nothing to add, skip it and
     spend no decision; the derived limits stand on their own and no limitation is
     invented to fill the slot. Under fully player-owned authorship these
     non-mechanical limits are never inferred.
   - **5c position:** starting capability position, belonging, access, isolation,
     and who already knows them. Feeds natural presence and who reacts.
   - **5d what gets tested:** ask which parts of this character the campaign
     should press on and which must be left alone. This is pressure direction, and
     it cannot be derived: the promise gives tone and fantasy, not which weakness
     the world leans into. The second half matters as much as the first—a
     thematic "do not touch here" is not a content boundary and nothing else
     records it.

     Do not ask for growth permissions here. Cadence, reward mix, and whether
     advancement pauses for an explicit choice belong to module 15; permission for
     permanent change is inherited from the module-3 consequence stance; adding a
     new stat axis is a stage-boundary revision asked when that stage arrives, not
     blind at setup. Palette covers world and tone content, while this covers the
     character's own traits. Feeds where preparation places pressure, and the
     progression gates that module 15 then calibrates.
6. **Play And System Contract:** inherit the resolution grounding and any
   accepted stat axes from module 5a instead of asking again, then split what
   remains by kind. Bundling these together is what makes the module feel generic,
   because it mixes how much the engine tracks with what the campaign is about and
   how tense it feels.

   - **6a simulation fidelity:** how much the engine actually tracks. Offer two to
     four cards built only from the profile's tracking settings—the enabled
     mechanics modules, `dice_mode`, inventory, time, travel, and wound
     tracking—with no tone or pacing content. Each card states which instrument
     every setting turns on and what it obliges during play, per the fidelity
     table in `rules.md`; a setting absent from the accepted card stays off and no
     precision is invented for it. Say the cost plainly: heavier tracking roughly
     doubles turn length, and a dashboard, which is the only place the Player sees
     tracked values, adds one to two minutes when it refreshes. Recommend a
     dashboard at high fidelity without enabling it by default.
   - **6b play mix:** what the campaign spends its time on, and the failure
     stance. This is content, not fidelity. Build the options from the setting's
     own recurring scene types rather than from a generic social, exploration,
     conflict, travel list: name the situations this world actually produces at
     this stage, the institutions that appear in them, and the shape its typical
     trouble takes. Failure stance is the form of a failed attempt—partial success
     with a price, redirection, or hard loss—while how severe loss may become was
     already settled as the consequence stance and is not re-asked.
   - **6c pace and pressure:** pacing, challenge density, breather frequency, and
     breather exit policy. State outright that fidelity does not set tension: a
     fully tracked campaign may run calm, and a light one may run relentless.
     Describe the rhythm in the setting's own units—its arcs, journeys, seasons, or
     shifts—rather than in abstract tempo words alone.

   In Standard, keep 6b and 6c as one decision to protect the 21–30 budget; Deep
   asks all three separately. Turn Protocol and semantic parallelism ride with 6a
   as performance settings. Fidelity may change later at a stage boundary, recorded
   as a revision.
7. **Presentation And Visual Contract:** split voice from optional layers, and
   inherit rather than re-ask—interiority policy comes from module 3, breather
   settings from 6c, and the setting's native register from the dossier.

   - **7a narration voice:** let the Player choose by ear, not by label. Write the
     same short moment from this campaign two to four times in different voices,
     two or three sentences each, and ask which one reads right. Do not present
     point of view, tense, camera, prose density, or response length as a
     vocabulary list; derive those selectors from the accepted sample and show what
     was recorded. Ask the Player directly what they dislike in narration, since
     `avoid_habits` is a validated field that only they can fill well. Derive the
     three Narrative Signature anchors and the sensory focus from the accepted
     sample and the native register, then confirm them—readiness requires exactly
     three meaningful anchors, so they are authored here rather than left empty.
     Keep the operative values in the profile, which is hot every turn, and let
     `storytelling.md` carry the explanation.

     Then write the wanted and unwanted GM behavior records in `boundaries.md`. No
     module has owned them, so they stay empty, and they are the most directly
     usable instruction a GM can hold: concrete responses rather than adjectives.
     Take the wanted lines from what the accepted sample actually did—returned
     control at a concrete moment, let a silence stand, named what the character
     could see and stopped there—and the unwanted lines from the dislikes answer
     together with the samples the Player turned down, which are free evidence
     nothing currently uses. Two or three lines each is enough, in the Player's own
     words where they gave them.

     Show two or three examples before asking what they dislike, because that
     question asked cold produces an adjective. Examples make the shape clear:
     every NPC speaking in the same register, a scene that summarizes the action
     the Player was about to take, a question appended to the end of every turn.
   - **7b optional layers:** Dashboard, image generation, and World Voices are
     independent authorizations, each explicitly on or off, never bundled into the
     voice choice and never enabling one another. State each cost when offering
     it: a Dashboard refresh adds roughly one to two minutes, an image draft or
     revision one to three, accepted placement one to two, while World Voices
     stays dormant until triggered. Say the host dependency too: image generation
     works only when the running tool or model can produce images, and a dashboard's
     data is written either way while viewing it needs the local server. If a
     capability is absent, record that layer as unavailable rather than enabled and
     note it can be turned on later. Recommend a Dashboard when tracking fidelity
     is high, because it is the only place the Player sees tracked values, but do
     not enable it by default. Any layer may take its own counted follow-up when
     its authorization is materially independent and the budget permits.

   The coordinator realizes all subordinate presentation, refresh, placement,
   art-direction, and communication fields.
8. **Canon Policy:** inherit the cast scope stance and researched limits from
   module 2 rather than asking for them again. Lock the remaining policy: the
   exact allowed era, continuity, elements, closeness, contradiction policy, and
   approval boundary supported by current research. A requested change to the
   cast scope stance is a revision of module 2.

   Because this module lives on the dossier's open questions, settle the in-play
   research policy here too: `off`, `ask_first`, or `bounded_auto` as described in
   `research_gate.md`. Say what it costs—a lookup adds roughly ten to forty seconds
   to that turn—and what it protects, which is a scene reaching a source question
   nobody answered during setup. The interview's source permission carries over, so
   this decides timing rather than re-authorizing the source.
9. **Palette:** inherit the campaign promise, hard boundaries, authorship
   limits, accepted presentation behavior, avoid habits, and canon constraints.
   Ask only about unresolved creative elements, or present one compact proposed
   palette for acceptance or change. Phrase every line in plain language in the
   Player's own language, describing what it would mean in play—appearing rarely,
   staying at the edges, being asked about first—rather than showing the internal
   yes, no, or maybe label. File the classification in `palette.md` afterward. Never ask the Player to
   re-consent to a hard boundary, silently weaken a No into Maybe, or treat
   Maybe as permission already granted. A requested hard-boundary change is a
   revision to its owning earlier module.

## Character-Aware World Scaffold

10. **World Truths And Operating Model:** use the accepted character seed,
    research, canon, and palette to propose a small playable World Operating
    Model. Ask the Player to accept, mix, or change its governing truths and
    meaningful exceptions—not to fill society, authority, economy, travel,
    powers/technology, belief, danger, history, daily-life, and misconception
    fields one by one. The coordinator authors the cause/effect cards,
    beneficiaries, costs, visible channels, exceptions, misconceptions,
    daily-life implications, and lens conflict resolution. Only a genuinely
    independent salient truth may consume a follow-up decision.

    Decide the world at macro scale here even when the character is local.
    Establish a bounded macro frame in `world.md`: the era anchor, who holds
    large-scale power and what could upset it, and the visible channels through
    which the macro reaches the local slice—news, prices, patrols, migration,
    levies, rumor. A few lines each; a frame, not an encyclopedia. The macro must
    not require the character to matter to it, and the local slice needs at least
    one legible link to it.
11. **Scale, Everyday Life, Access, And Routes:** ask the starting aperture and
    nothing else. Everything this module used to list is owned elsewhere and must
    not be asked again here: governing truths and the channels that carry the macro
    belong to module 10, what moves without the character to module 12, places and
    routines to module 14, travel cost and route knowledge to `location_network`,
    and the opening scene's own place and arrival to module 17. A module that asks
    for fields other modules own is a form, and the interview contract forbids
    treating a module as a form.

    The aperture is a real decision because it changes preparation depth and how a
    Player who walks away from the opening is met. Offer two to four contextual
    cards on how much world is live at the start: a tight opening where one
    settlement and its surroundings are prepared and anything further opens when
    the Player reaches for it, or a wide one where the region is already available
    and movement needs no permission. Say what each costs—a tight aperture prepares
    deeply and improvises when the Player leaves early, a wide one spreads the same
    preparation thinner.

    Ask the second half in the same decision, because it is what gives the first
    half teeth: reaching past the live boundary either opens smoothly, with the
    world prepared on demand and no penalty for curiosity, or is itself a
    consequential act, where distance spends real time and leaving loses ground
    here. Neither answer restricts where the Player may go.

    This feeds the act scope in module 17, the graph the route layer builds, and how
    much is prepared before play. When `location_network` is active, resolve it
    before treating travel structure as settled.
12. **Independent Issues And World Dynamics:** active/impending problems and
    bounded domains that would exist and move without the character: who
    benefits, who suffers, visible signs, ignored movement, and open dramatic
    questions. Include two to four large movements that belong to the macro
    frame, each with the channel that makes it visible locally, so a later
    zoom-out finds a world already in motion.

    A selection here sets salience, not exclusivity, and it must not narrow the
    world into a single track. Keep every unselected candidate as a dormant domain
    with the trigger that would surface it. Give each selected issue three or four
    side conditions—secondary effects, second-order consequences, and what would
    shift its direction—so later turns improvise from prepared material instead of
    following one line. Give each one counter-current as well: something that looks
    like it contradicts the issue yet fits this world, such as a decent officer
    inside a corrupt branch. Record no predetermined resolution.
13. **Factions And Institutions:** ask which initially relevant force or
    conflict pattern should matter at the opening scale. The Player chooses or
    changes the salient forces and their high-level relationship to play. The
    coordinator authors public masks, stable desires, methods, capabilities,
    resources, representatives, key places, pressure tactics, knowledge
    boundaries, owning domains, and independent next movements.

    Also fill the macro seats the setting implies—top-tier powers, ranking
    officers, sanctioned or tolerated figures—with named occupants at roster
    detail: name and title, seat, one line of disposition and method, current
    large-scale movement, and where their reach could touch the local slice. Four
    to eight is enough, one or two lines each, recorded in the macro frame rather
    than as full character notes. Under `canon_world_original_cast` the seats
    come from the source and the occupants are original. A roster figure
    graduates to a character note with a filled Agency Card before it appears
    onstage or speaks; until then it stays a consistent offstage reference so
    later mentions do not contradict each other.
14. **Faces, Places, And Independent Relationships:** resolve `character_foundation`
    first when it is active, and `group` when a crew or company is intended. Personal
    places, private routines, and relationship roles depend on the character's
    interior; an ecology built before it is derived from the world alone and will not
    answer the person at its centre. Then, before proposing any face,
    check the dossier's character grammar and its record of which peoples are
    plausible at this stage and place. Run a narrow research pass when either is
    thin. Names, titles, cultural flavor, and species must be checked against the
    source, the structure already established, the chosen location, and the live
    issue—not invented ad hoc. Populations are gated by stage and place: a people
    the world contains somewhere does not therefore appear here, and an excluded
    one is recorded with its reason. Reputational titles follow the source's own
    rule for who earns them, so ordinary working people do not carry grand ones.

    Then present a small player-facing social and spatial ecology that realizes the
    accepted world and forces. The Player accepts, mixes, or changes which known faces, places,
    and relationship roles should matter. The coordinator authors their
    independent work, desire, obligations, routines, availability, natural
    presence, routes, affordances, continuity and agency cards, appearance,
    gated knowledge, cast entries, and relationship records, so that no face or
    place becomes a quest-delivery ornament. Do not interview the Player through
    NPC or place schema fields.
15. **Progression And Rewards:** resolve `mechanics_progression` here when it is
    active, since this module supplies its remaining inputs. Inherit the declared
    reach from module 1 to
    calibrate the highest closure level in play, what the character wants tested
    from module 5d, and the permanent-change permission from module 3. Do not ask
    for any of those again.

    Ask two separate things in plain language, because the profile keeps them
    separate and validation requires them to agree: at which closure growth arrives,
    named in the setting's own unit rather than as an abstract level, and how it
    arrives—carried inside the fiction, or through a short pause where the Player
    chooses. A closed cadence requires a closed presentation, and an open cadence
    requires one of the two open presentations.

    Progression runs on three tracks and no more: stat points, special ability
    points where the setting has a layer outside the axes, and fictional
    capabilities earned in play. Every closure offer therefore takes one of three
    shapes—points to spend, a capability earned in the fiction, or points plus an
    ability recognized from how the Player has actually been playing. Under
    fictional grounding the same three shapes are recorded in prose without numbers,
    and the Player still chooses. Unspent points and unrealized capabilities are
    never lost: they stay in the live progression state and surface at the next
    closure.

    Then instantiate the reward pool for this setting in `progression.md`: the
    concrete capability, access, standing, equipment, knowledge, and world-state
    rewards this world actually offers at this stage. Categories are not rewards, and
    an empty instantiation produces generic ones. Reward vocabulary stays inside the
    accepted system—declared axes and scale under numeric grounding, named bands
    under banded, recorded competence under fictional—and no reward may use a
    mechanic the campaign left off. A new axis belongs to a stage boundary, not to an
    arc reward. This module also owns the reward mix, recognition channels, allied
    advancement, and power-creep limits.

## Reciprocity, Opening, And Approval

16. **Character–World Reciprocity Pass:** derive two to four coherent
    reciprocity or intersection patterns from modules 1–15 and completed Deep
    packs. Ask the Player to accept, mix, or change the proposed intersection and
    relationship pattern. Preserve the anchor or isolation stance already
    accepted in module 5; unresolved explicit isolation is never inferred. The
    coordinator performs the actual scaffold revision and realizes the
    character-originated anchor or approved isolation consequences, the
    independently moving issue/domain, their playable intersection, competence
    affordance, limitation/counterplay channel, place/routine relationship, and
    belonging/obligation/friction/opportunity with independently motivated
    people or factions. Module 19 remains the integrated design review.
17. **Starting Situation Design:** frame the first act before composing the scene
    inside it, because an opening with no act around it leaves the campaign with
    nothing to close against. `next_act_prep.md` frames every act after the first
    and `first_session.md` covers only the opening situation, so the first act is
    the one act nothing else prepares. Fill the Arc Compass in `threads.md` from
    material modules 10–16 already produced: the act's question, the pressures it
    runs on, what is planted, what would make a climax reachable, and what would
    close it. Then fill its scope in names rather than categories—which places
    this act can reach, which people belong to it, what is already in motion as it
    opens, and what stays true if the character does nothing. Scope is the test of
    whether an act exists: a single place and one person is an opening, not an act.
    Leave the closure record empty; it is written when the act actually closes.

    Then present two to four coherent player-safe
    opening shapes. Each shows its place/routine/arrival premise, known and
    visible context, intersection trigger, scene mode, pressure or calm
    affordance, competence/limitation opportunity, and neutral action space. The
    Player accepts one, mixes named parts, or requests a change. The coordinator
    authors exact routes, traffic, availability, naturally present cast and their
    reasons, hidden limits, knowledge classification, and causal scene wiring.
    This is the approved opening design, not yet a claim that all preparation is
    written.
18. **Continuity, Ownership, And Preparation Contract:** ask one ongoing
    world-side creation-authority decision, and bind it to the creation tiers the
    ledger already tracks so the answer changes something. The threshold is either
    supporting-and-above, major-only, or nothing with everything shown at review.
    Ask it in plain language—whether a recurring face needs permission, or only a
    major new force—never in tier codes. Incidental colour is always free, every
    named creation is logged with its tier, and a supporting or major figure needs
    its full note and voice axes before speaking. When a scene wants something above
    the threshold, ask or build the scene without it; silent creation is not an
    option. Inherit the character-side triggers derived at module 3 and do not ask
    about them again. Do not reopen
    research permissions, hard authorship or content boundaries, mechanics or
    performance choices, canon policy, or advancement. The coordinator locks
    research/canon/power/knowledge/reveal/creation/relationship/distill/
    advancement ownership, backstory boundaries, source precedence, player-safe
    review scope, hidden exclusions, materialization responsibilities, and the
    selected performance cadence without asking the Player to assign
    implementation owners.
19. **Reciprocity Design Review:** show one coherent player-safe synthesis of
    modules 1–18 and every completed/defaulted Deep pack, together with the
    consolidated record of what was defaulted and what was deferred. Checkpoints
    showed those defaults in fragments as they accrued; this is the only place the
    Player weighs the whole set against a finished design, and the last point where
    changing one is free, since module 20 materializes on top of it. Leave
    `defaults_reviewed` false here—that flag belongs to the final approval. Organize
    the synthesis so decisions that constrain each other appear together rather than
    in module order, which is the order they were asked rather than the order they
    matter in. Approval locks the design direction at the current setup revision; it
    does not approve unseen prepared files.
20. **Integrated Materialized Preparation Review:** cross-read the prepared files
    before showing the Player anything. Until here every review has reasoned over
    accepted answers; this is the first point where the corpus itself exists, and
    the Player should not be the first reader to notice it does not hold together.
    Run the RPG section of `workflows/audit/WORKFLOW.md` against the prepared
    campaign—that workflow already asks these questions and is otherwise only
    reached when a Designer asks for it—and check what only a cross-read can catch:

    - every module the status block marks resolved has its mapped owner actually
      written, since the revision counter proves how many writes happened and not
      what they touched;
    - the act scope's named places exist as notes and are reachable in the graph;
    - the opening's present cast exists with notes whose routines and availability
      agree with the scene that is about to run;
    - each faction's claimed reach and the places it touches agree;
    - what the knowledge layer marks hidden agrees with what the threads treat as
      hidden;
    - relationship edges resolve to real entities on both sides;
    - `tools/check_player_facing.py` passes on everything about to be shown.

    Correcting here is free because preparation approval has not happened yet, which
    is exactly why the pass belongs before the review rather than after it. A
    correction that changes an accepted design decision is not folded in quietly: it
    returns to module 19 and clears the design approval. This pass removes the errors
    the Player should never have had to catch; it does not replace their review or
    turn into a report shown to them.

    Then, after the approved design
    has been materially prepared while not ready, show the actual player-safe
    character, world, places, relationships, independent movement, intersection,
    active opening, and neutral action space, then ask whether that prepared
    truth is factually accurate, complete at the promised scale, and faithful to
    the approved design. Review prepared campaign truth, not another abstract
    pitch, and never implementation detail or hidden truth. Acceptance records
    the review without granting preparation approval or readiness.
21. **Preparation Approval:** show the unchanged preparation accepted at module
    20 together with the final locked/defaulted/deferred record and readiness
    implications, then ask only for approval to proceed to readiness preflight or
    a not-yet response. Introduce no new campaign truth or first-time
    persistence. Only this current-revision approval authorizes preflight and
    finalization.

# Immediate Persistence Map

| Module | Immediate authoritative persistence |
| --- | --- |
| 1. Promise | `campaign_one_pager.md`, premise/summary in `world.md`, setup/session progress |
| 2. Research | `research_dossier.md`; accepted source constraints in `boundaries.md` before dependent locks |
| 3. Agency/Authorship | `boundaries.md`, `palette.md`, `player.md` authorship limits, relevant knowledge constraints |
| 4. Identity/Desire | `player.md`, appearance guide, current motivation and desired experience |
| 5. Competence/Position | `player.md` permissions/bands/stats, limitation/cost/counterplay, social position and change appetite |
| 6. Play/System | profile mechanics/resolution/performance, `system_fit.md`, `rules.md`; mechanics state only when approved |
| 7. Presentation/Visual | profile narration/dashboard/visual/World Voices policy, `storytelling.md`, visual gallery/style/state; projections wait |
| 8. Canon | dossier, boundaries, canon summary in `world.md` |
| 9. Palette | `palette.md` and resulting hard boundaries |
| 10. World Truths | `world_truths.md` and World Operating Model in `world.md` |
| 11. Scale/Life/Routes | `world.md`, location graph, relevant places/domains, draft starting state and prep |
| 12. Issues/Dynamics | `issues.md`, `world_dynamics.md`, `threads.md`, gated clues |
| 13. Factions | faction notes, ledger, relationships, knowledge and owning domains |
| 14. Faces/Places | character/place notes, index, ledger, relationships, knowledge, cast, routes and appearance guidance |
| 15. Progression | `progression.md`, profile advancement and closure/carry-forward policy |
| 16. Reciprocity | `player_ties.md`, relationship map, threads, world/issue/place/faction revisions and Player/PC knowledge |
| 17. Starting Design | `first_session.md` drafting inputs, pending `opening_brief.md`, draft scene/current state and relevant cast |
| 18. Continuity/Prep | rules/storytelling, authority notes, knowledge/research/progression state, review boundaries and final runtime contract |
| 19. Design Review | player-safe design record and consolidated default/defer record in `session_zero.md`, approval references in ties/prep, current `design_direction_approved_revision`; preparation approval null and `defaults_reviewed` still false |
| 20. Preparation Review | all materialized semantic owners, final current state/cast/routes, `first_session.md: materialized`, `opening_brief.md: active`, and player-safe actual-preparation record; readiness false |
| 21. Preparation Approval | current `preparation_approved_revision`, reviewed defaults/deferrals, status and final approval in `session_zero.md` |

For every ordinary inferred choice, write a stable label to
`setup_profile.yaml.defaulted_decisions` and readable detail to
`session_zero.md`. `defaulted_packs` never stores an ordinary module default.

# Deep Activation And Completion

Activate packs only from accepted answers; append the pack to
`activated_packs` immediately when its trigger is established:

- persistent crew/company/base -> `group`;
- a `long_journey` or `episodic` declared reach, an explicit request for character
  depth, or detailed identity/inner life/change arc -> `character_foundation`.
  A character who carries a long campaign needs the deep layer, so do not wait
  for the Player to ask for it;
- substantially original society/law/economy/culture/metaphysics/history ->
  `world_fabric`;
- exploration/travel/routes/sandbox/survival logistics -> `location_network`;
- politics/intrigue/contested information -> `faction_information`;
- a `long_journey` or `episodic` declared reach, or explicit multi-arc
  promises/setup-payoff/climax/endings -> `campaign_architecture`;
- tactical resources/stats/conditions/clocks/detailed growth ->
  `mechanics_progression`;
- canon/real-world/hard-science source sensitivity -> `source_grounding`.

Do not activate Group for a solo campaign without a persistent collective or
World Fabric merely because all campaigns have a world.

## Pack Owners

| Deep pack | Immediate owners |
| --- | --- |
| `character_foundation` | `character_foundation.md`, player/ties, personal places/relationships and change line |
| `group` | `group.md`, relevant faction/place notes, relationships and player ties |
| `world_fabric` | world, truths, issues and only relevant faction/place notes |
| `location_network` | location graph, places, travel/world domains and cast availability |
| `faction_information` | faction notes, knowledge, relationships, issues/domains |
| `campaign_architecture` | threads, issues, progression and closure/carry-forward promises without fixing a plot |
| `mechanics_progression` | approved profile modules, system/rules/progression and optional mechanics state |
| `source_grounding` | dossier, boundaries, palette and supported world truth |

### `character_foundation` Structure

Create `character_foundation.md` with a fixed structure so depth does not depend
on improvisation. Its sections: inner contradiction—what they want set against
what they would never admit; what they fear losing; relationships that already
exist now; a private routine or place that is theirs; the change line, meaning
what growth would look like and what would break them; and formative pressure
limited to what the Player chooses to reveal. Under fully player-owned
authorship the Player writes the interior sections and the coordinator only
records them; protected facts stay closed until the Player opens them.

### `group` Resolution

Resolve `group` as a companion contract rather than a roster, and do not assume
the company forms in one place or at one time. It is assembled over the course of
play: this decision fixes intent and shape, never a membership list. Say that
plainly, and scale it to the declared reach—on a long or episodic reach the
company may stay incomplete for a long stretch, and an empty seat then is runway
rather than a gap to fill during setup. A single companion at the opening, or
none, is a complete answer.

Ask four things in plain language: what kinds of companions the Player wants
beside them and what kinds they do not want; whether a limit applies,
distinguishing one the setting imposes—berths, party size, a bond that only holds
so many—from one the Player chooses, with open-ended as a real answer; how
companions are expected to arrive, keeping room for one the Player never planned;
and how much control they want over investment in a companion.

Control has a boundary the existing ally policy sets: a companion keeps their own
will. The Player may decide whether to spend a reward on them, what to offer, and
what to ask of them, but not what they want. Offer that control as deciding,
suggesting, or leaving growth to the companion, and say plainly that the last word
on their motives is never the Player's.

Create `group.md` with a fixed structure: the company's purpose and the Player's
intent for it; the limit and whether the setting or the Player set it; roles or
temperaments wanted and unwanted; how members are expected to join; what holds it
together and what would break it; its base or vessel if it has one; its identity
such as a name, mark, or flag; the accepted control policy; current members; and
how departure or loss is handled under the accepted consequence stance.

### `world_fabric` Resolution

A materialized World Operating Model describes how the world produces consequences,
not what the world contains. Restating the premise—its era, its tone, what exists in
it—leaves the section unmaterialized however long it runs, and placeholder text left
in place fails outright. Derive the model from accepted answers and write how power is
held and lost, how law or custom actually reaches a particular person, what money or
obligation buys, how knowledge travels and how fast, and where any metaphysics stops.
Every line should let a scene be adjudicated without further invention. Keep it to
what was accepted rather than what the genre usually assumes.

### `location_network` Resolution

`location_graph.md` asks for per-edge travel cost, access, visibility, ordinary
traffic, conditions, and whether the Player knows the route, so resolving this pack
by inventing all of it silently takes the network away from the Player, while asking
how travel should work in the abstract produces the passing remark module 11 warns
about. Split it instead: the Player owns three decisions and the coordinator fills
the edges.

Before offering options, derive how movement actually behaves in this setting and
period—what carries people, what the terrain or medium costs them, how reliable maps
and directions are, and who watches movement—then phrase the three decisions in that
setting's own terms rather than generic ones.

- Whether distance costs anything: travel is a cut to arrival, or it spends time and
  resources without becoming a scene, or the route is itself a place where things
  happen. This is what gives the travel column teeth.
- Whether the map is known or discovered: the Player starts with a working sense of
  what is reachable, or the network reveals itself through play. This sets the
  player-known column at setup.
- Whether movement can be traced: whether going somewhere leaves something others can
  act on, which drives visibility and conditions and matters most when the character
  is being sought.

Fill individual edges yourself from the accepted answers and existing place notes,
and let the Player name any route they specifically care about. Remove the example
row, keep every endpoint resolvable to a place note or an explicitly incidental
current location, and record at least one asymmetry—one-way, closed, costly, watched,
or unknown—unless the accepted answers deliberately removed all travel friction.
Without one the graph is a list of places rather than a network.

### `faction_information` Resolution

Do not manufacture a faction where the accepted answers established only a person or a
pressure: a single dangerous individual belongs in a character note, and an
uncoordinated condition belongs in `issues.md`. When a faction is real, its note has to
carry what it knows, what it believes wrongly, and what it refuses to share, because
this pack exists for contested information and a faction whose knowledge is unrecorded
is a name rather than a participant. Give its reach the same kind of edges the location
layer uses, so its influence can be reached, avoided, or exceeded instead of hanging
over everything as atmosphere.

### `mechanics_progression` Resolution

This pack translates rather than interviews. Modules 6, 11, and 15 already collected
the Player's answers; the pack's work is turning them into the named module set and
the tracking field each module requires, and doing it before design approval instead
of discovering the coupling at validation. Re-read the accepted answers to derive the
set—never infer it from the world or from what the setting usually does.

- Supplies that are counted rather than assumed -> `strict_consumables`, with
  quantified or encumbrance inventory tracking.
- Injury or loss that persists past the scene -> `wounds`, with conditions wound
  tracking.
- Travel presented as lived passage rather than arrival -> `structured_travel`, with
  route_time travel tracking.
- Any use of dice at all -> `dice_resolution`, with a dice mode other than
  judgment_only.
- Pressure that advances on its own between scenes -> `clocks`.
- A separate pool for abilities the ordinary axes cannot describe ->
  `abilities_costs`.
- A finite pool the Player spends and must replenish -> `bounded_resources`.
- Numeric stat axes -> numeric resolution grounding.

Enable mechanics state whenever any approved module is stateful, meaning anything
beyond `dice_resolution` on its own. Record every promise that maps to no module as a
narrative commitment in the progression record: a wholly verbal system is a legitimate
outcome, but it has to be written down as one or it lapses without anyone noticing.
Where an accepted answer and a module requirement conflict, do not quietly change the
tracking field and do not quietly drop the module—return to the Player with the
conflict stated plainly.

Materialize the accepted advancement cadence as a concrete value in
`play_profile.yaml`. Cadence is a separate decision from how advancement is presented,
and leaving it unset leaves the whole progression layer unenforceable no matter how
carefully the rest was chosen.

### `campaign_architecture` Resolution

This pack deepens an Arc Compass that module 17 already filled for the first act;
it is not what creates one. Its own work is the multi-arc layer—promises that
outlive this act, setups whose payoff belongs to a later one, and how the campaign
could end.

Do not interview the Player through Arc Compass field names, for the same reason
module 14 forbids interviewing through entity schema fields: asked directly, setups
and climax conditions produce either confusion or a pre-written story, and this pack
is bound to shape a campaign without fixing a plot. Ask instead what the Player wants
to find out and what they want the campaign to put to the test, then derive the
compass from what they say.

- Dramatic question: derive it from the character premise and the Player's stated
  interest, and phrase it so both answers stay live. Test it by asking whether the
  opposite answer would still leave a campaign worth playing; if it would not, the
  question is a plot in one sentence and has to be rewritten.
- Active pressures: reference `issues.md` and `world_dynamics.md` rather than
  restating them, since those own systemic problems and offscreen movement.
- Setups awaiting payoff: record what is already planted and available—an unresolved
  capability, a debt, a piece of knowledge someone holds—not what will happen. Leave
  the payoff unscheduled.
- Climax availability conditions: state what must be true for a climax to become
  reachable, never when it occurs, and keep every condition something the Player can
  move toward or away from.
- Closure conditions: align them with the actual arc-close trigger and the accepted
  cadence instead of inventing a parallel rule; consult `arc_closure.md`.
- Player interest signals: record only what the Player has actually expressed, never a
  prediction of what they will enjoy, and update the field from play.

### `source_grounding` Resolution

Resolve the research gate instead of leaving it pending: the dossier's status has to
record a decision consistent with the accepted canon stance and research mode. Keep
verified material separate from what stays uncertain, and name the specific questions
left open so play can reopen them deliberately rather than improvising across a gap.
Where the source is silent, record the silence as silence—filling it quietly converts
an open question into a false certainty that contradicts the source later, which is the
failure this pack exists to prevent.

## Dependency-Safe Schedule

Pack work no longer waits blindly until after the whole core:

- `source_grounding` resolves before dependent Canon, Palette, or World Truths
  are locked;
- `character_foundation` resolves after modules 4–5 and before any dependent
  personal place, relationship, or world design is treated as final;
- `world_fabric`, `location_network`, and `faction_information` resolve after
  their scaffold inputs exist and before the reciprocity design is approved;
- `group` resolves once character/group intent and relevant world handles exist;
- `mechanics_progression` resolves after modules 6 and 15 supply its inputs;
- `campaign_architecture` resolves after issues/progression and before design
  approval.

Normally every activated pack is resolved before module 16. The absolute gate
is module 19: no Deep reciprocity design approval while an activated pack is
unresolved.

Append a pack to `completed_packs` only after all accepted pack decisions are
persisted in their owners and its readable completion summary is shown. Use
`defaulted_packs` only when an already activated pack is resolved through
explicitly displayed and accepted defaults. A design change or pack revision
after module 19 clears both approval fields and returns to the design review.

At each 8–10 decision boundary, run the checkpoint **before** asking the next
content question: show locked choices, open packs, ordinary defaults, and
approximate remainder, then set `last_checkpoint` to the current count. Treat it as
part of the sequence rather than an optional summary, because it is the only place
an overdue pack becomes visible on its own. When the checkpoint shows a pack that is
already due, resolve that pack before continuing the module order, and run a
checkpoint before requesting design approval whenever one is outstanding. Validation
flags a missing checkpoint after eight decisions, and treats it as an error once the
campaign is content-ready. Adjust `question_target` within 30–45 as triggered work becomes known.
Before opening work beyond 45, obtain explicit extension permission and set
`deep_extension_approved: true`; never pre-authorize it.

# Reciprocity Invariants

- Character-originated content is not optional unless the Player explicitly
  approves isolation and its consequences.
- At least one issue/domain/process exists and moves without the character.
- The intersection lets both sides affect one another without revealing or
  predetermining an outcome.
- Competence receives a natural affordance and clean-success space; limitation
  receives causal cost, pressure, or counterplay rather than automatic failure.
- Important NPCs/factions retain independent work, obligations, routines, and
  next moves beyond delivering a hook.
- The opening's routine, arrival, routes, availability, present people, visible
  change, and neutral actions agree with the approved design.
- Backstory, identity, feelings, dialogue, conclusions, decisions, and hidden
  ties follow the accepted authorship boundaries.
- Semantic coverage is judged by the coordinator and Player review; do not add
  a keyword-counting checker.

For the module-18 creation-authority decision, offer two to four contextual
cards in readable language rather than new profile enums:

- **approval-first:** ask before any new persistent or named element beyond
  ordinary scene texture;
- **bounded inference (recommended):** infer low-risk world-side and connective
  detail, and still ask again for protected player-character truth, hard
  boundaries, source or canon scope, stateful mechanics, and any major
  irreversible direction;
- **broad within boundaries:** prepare most world-side detail inside the locked
  boundaries and show it at the normal review points.

No card may waive a non-waivable permission. Persist the accepted authority in
the existing approval-trigger and continuity owners.

Existing authority invariants remain: stable NPC truth in character notes;
temporary whereabouts in `active_cast.md`; current knowledge in
`knowledge_boundaries.md`; world movement in `world_dynamics.md`; systemic
problems in `issues.md`; player-linked questions in `threads.md`; current
relationships in `relationship_map.md`. Numeric grounding alone requires the
numeric stat contract.

# Revision-Bound Approval Contract

Before module 19, keep both approval fields null. Module 19 acceptance persists
the review, increments `setup_revision`, and sets
`design_direction_approved_revision` to that resulting current revision.
`preparation_approved_revision` remains null.

After design approval, materialize the approved preparation while
`ready_for_play: false`. Module 20 acceptance is persisted at a newer revision.
Module 21 acceptance increments the revision again, sets
`preparation_approved_revision` to that current revision, and sets
`defaults_reviewed: true` only when the displayed ordinary defaults/deferrals
were part of the approval.

- Revising modules 1–19 or any Deep pack clears both approvals.
- Revising only materialized preparation without changing approved design
  clears preparation approval and repeats modules 20–21.
- Revising a completed decision never adds another completed decision.
- Stale preparation approval cannot pass preflight or readiness.
- Final fields and derived projections do not advance `setup_revision`.

# Preparation Materialization And Review

Between modules 19 and 20, freeze the approved direction and prepare the actual
opening scale. Standard/Deep may use at most three read-only proposal workers:

1. **world ecology:** truths, independent issues/domains, factions and world
   counterplay;
2. **cast and space:** anchors, NPC/place cards, routines, natural presence,
   relationships, routes and opening affordances;
3. **systems and presentation:** accepted mechanics/progression consequences,
   rules/storytelling nuance and approved projection requirements, only when
   substantial and independent.

The coordinator owns player/profile truth, ids, knowledge classification,
authoritative writes, current state, the final opening, approval fields, and
all player-facing delivery. Merge and leakage-check before module 20. A worker
failure falls back to serial completion.

The module-20 review shows actual player-safe prepared truth: character and
current desire; competence/limitation affordances; starting place, routine,
access and arrival; known relationship positions and independent agendas;
world-independent movement; the intersection; naturally present people;
visible opening situation; neutral action possibilities; and displayed
defaults/deferrals. Exclude hidden motives, maps, secrets, unrevealed names, and
GM-only causal truth.

Ask module 20 as a factual accuracy and completeness question about that
prepared truth. Module 21 then asks a separate readiness go/no-go on the same
unchanged preparation and the complete locked/defaulted/deferred record; it never
displays a default, prepared fact, or persisted answer for the first time.

# Turn Protocol And Performance

Offer Fast, Balanced, Maximum Continuity, or Custom with the established turn
timing/freshness and Dashboard/visual estimates. Fast remains recommended and
never defers current truth, knowledge, mechanics, durable revision events, or
advancement gates. Offer semantic parallelism in the same decision; Standard
and Deep retain a cap of three supporting workers.

The old 30–60 minute Standard setup estimate is not a promise for the 21-module
route. Do not invent a replacement duration until measured. Deep remains an
adaptive 30–45-decision route; its time estimate is likewise planning guidance,
not a guarantee.

# Standard/Deep Finalization

After module 21 records preparation approval at the current setup revision,
load `finalization.md`. Schema-v7 Standard/Deep finalization must not perform
first-time world/cast/opening synthesis. It runs draft preflight, locks final
profiles/readiness without advancing the setup revision, builds approved
projections, takes the starting snapshot, and runs the aggregate check.

A substantive correction returns to modules 20–21, or to module 19 when design
or Deep-pack truth changed. Legacy schema-v1–v6 Standard/Deep campaigns retain
their existing finalization route unless explicitly migrated.
