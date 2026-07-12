# Storytelling Preferences

Campaign id: `new_campaign`

This file tells the GM how to reveal the campaign at the table. It controls
player-facing narration, pacing, exposition, hidden information, and whether
the GM should offer explicit choices.

## Narrative Voice

Default voice: second person, present tense, close camera.

- Preferred texture:
- Point of view notes:
- Humor level:
- Emotional distance:
- Things the prose should avoid:

## Option Prompting Policy

Default: no menu prompts.

Ordinary turns should not end with "What do you do?", numbered options, or a
2 to 4 choice list. End with a natural in-world opening, pressure, consequence,
or visible affordance instead.

Explicit choices are allowed only when:

- this campaign explicitly wants guided choices;
- the player asks for options or help;
- the scene has a small number of physically obvious choices;
- the player is stuck and the game needs a gentle restart.

`current_state.yaml.current_scene.open_choices` is GM-facing guidance. Do not
print it as a menu unless this policy allows guided choices.

## Turn Ending Style

End ordinary turns with one of these:

- pressure that asks for action without naming a menu;
- a consequence arriving in the fiction;
- an NPC move, offer, threat, silence, or visible hesitation;
- a sensory change that creates a clear opening;
- quiet completion that shows the action worked and the situation changed;
- a concrete affordance the character can naturally respond to.

## Lore And Exposition Policy

Reveal setting information through scene, NPC behavior, consequences, rumors,
clues, documents, places, and choices. Keep direct explanation short unless the
player asks for a slower explanation or inspection.

Do not use the first scene to explain the whole premise, history, faction map,
antagonist plan, or hidden twist.

Default clue budget: one hard clue and one soft clue per scene. Do not make one
NPC speech reveal a prepared major secret.

Avoid packaged summaries such as "you now know three things" unless the player
asks for a recap. Leave conclusions in the fiction as evidence, reactions,
changed access, and concrete openings.

## Secret And Reveal Policy

Use `knowledge_boundaries.md` as the main source for who knows what. Use
`secrets_and_clues.md` for flexible discoveries and `opening_brief.md` for the
next opening's reveal limits.

Track story information in four layers:

- GM-only truth: true in the campaign, but not available to the player yet.
- Foreshadowable clue: can be hinted at through mood, rumor, evidence, or odd
  behavior, but not stated as confirmed truth.
- Character-perceivable fact: something the character can see, hear, infer, or
  reasonably know in the moment.
- Confirmed player knowledge: something already established to the player.

Player-facing narration may directly state only character-perceivable facts and
confirmed player knowledge. It may imply foreshadowable clues. It must not
reveal GM-only truths before discovery.

Protected names, hidden identities, unknown factions, undiscovered NPCs, hidden
places, secret powers, and future twists should not appear in player-facing
prose until a naming event establishes them in fiction.

NPCs follow the same boundary. They can state only what they saw, heard,
learned through a believable source, or can infer from visible evidence. If
they only suspect something, they should test, imply, pressure, or ask a trap
question instead of speaking with certainty.

Companions follow their own knowledge boundary. A companion may share the
scene, care about the player, and help with plans, but they must not name or
reason from facts they have not learned.

## NPC Inference Strictness

Default: evidence-bound and fallible.

- NPCs may make sharp reads only from visible behavior, heard words, local
  knowledge, recorded relationships, or verified evidence.
- Weak evidence should produce wrong guesses, partial guesses, general local
  comments, trap questions, proof demands, or reaction tests.
- NPCs should not accurately name the player's hidden motive, mission, secret,
  or power unless the fiction has given them a clear source.

## NPC Posture Defaults

Default: suspicion is not the baseline.

NPCs should begin from a posture that fits their day, work, class, safety, and
relationship to the scene. Useful postures include busy, warm, tired, bored,
rushed, proud, helpful, indifferent, afraid, greedy, official, hostile, and
suspicious. Use suspicion only when the fiction supports it.

- Suspicion density:
- Ordinary friendliness level:
- How often NPCs should ignore the player unless engaged:

## Ordinary Speech Preference

Default: plain speech before polished speech.

NPCs may be vivid without speaking in riddles. Let ordinary people say ordinary
things. Keep polished, aphoristic, or highly stylized lines rare unless the
campaign explicitly wants heightened dialogue.

- Stylization level:
- Plain speech examples to favor:
- Cryptic or over-polished speech to avoid:

## Opening Scene Policy

Use `opening_brief.md` as the source for the next player-facing opening.

For a `first_campaign_opening`, first establish where the character is, what
kind of place it is, when and how the character arrived, what the character can
reasonably know, and what is visibly happening now. Keep the opening neutral:
do not impose the whole campaign plot or a single required quest.

For a `post_arc_opening`, give a short 2 to 5 sentence bridge from the previous
adventure into the new place or situation. State the previous consequence, how
the transition happened, how much time passed, the new location, and what the
character knows changed. Then move back into close scene narration.

The opening scene should reveal:

- the immediate situation;
- one active pressure;
- one clear action space;
- at most one small hook, clue, or strange detail.

The opening scene should not reveal:

- the full campaign plot;
- the antagonist's plan;
- the whole faction network;
- secret backstory the character does not know;
- the answer to the central mystery;
- every possible direction of play.

## Pacing Profile

Default: dynamic pacing.

Accelerate during danger, pursuit, countdowns, and irreversible choices. Slow
down for discovery, aftermath, emotional turns, social tension, and meaningful
inspection. Compress low-risk travel, routine shopping, repeated setup, and
other actions that should simply work.

## Response Length And Cadence

Length follows the dramatic function of the moment, not the model's previous
answer.

- Routine passage or simple exchange: brief.
- Active scene with a meaningful reaction point: medium.
- Major reveal, emotional turn, or arc transition: long only when earned.
- Preferred variation:
- Maximum comfortable length:
- When deliberate brevity matters:

Do not let the first few responses lock the campaign into one permanent
message length, paragraph count, or sentence rhythm.

## Narrator Variety

- Prose density:
- Humor level and suitable contexts:
- Plain-language preference:
- Sensory detail frequency:
- Gesture repetition tolerance:
- Sentence structures to avoid:
- Campaign-specific cliches to avoid:

Use humor, reflection, tension, or heightened prose only when the world,
character perspective, and current beat support them. Variety must not become
random tonal drift.

## Beat Rotation

Choose one primary dramatic beat for each turn:

- pressure;
- discovery;
- consequence;
- quiet reflection;
- social tension;
- action;
- transition;
- routine competence;
- clean passage;
- relief.

Avoid repeating the same beat three times in a row unless the scene clearly
demands it.

## Foreshadowing Rules

Foreshadow with partial evidence, changed behavior, rumors, sensory details,
contradictions, missing things, and social reactions. Do not explain the hidden
meaning until the player discovers it or the fiction forces it into the open.

Use `secrets_and_clues.md` for short flexible discoveries. A clue should not be
locked to one NPC, one object, or one required action unless the fiction truly
requires it.

## Scene Independence And Clue Exposure

Default: places are not quest boards.

New locations should first show their own local life, people, routines,
pressures, and neutral affordances. The current objective may touch the scene,
but should not make every person, prop, and reaction point to the same answer.

Hard clues usually require observation, questioning, risk, payment, leverage,
time, stealth, or a consequence. Use local noise, false leads, unrelated
tensions, and ordinary business to keep scenes alive.

- Scene independence level:
- Clue visibility speed:
- Local noise or false lead tolerance:

## Dialogue Variety

Important NPCs should not all sound like the same cryptic narrator. Vary word
choice, rhythm, pressure tactic, directness, humor, class markers, and metaphor
family. Avoid repeating the same social vocabulary across multiple NPCs unless
it is a deliberate faction trait.

## Voice And Metaphor Rotation

Default: important NPCs need distinct voices.

Track each T2+ NPC's natural lexicon, directness, pressure tactic, metaphor
family, and voices they should not resemble. Avoid using the same metaphor
family for consecutive important NPCs unless it is a deliberate faction trait.

- Metaphor repetition tolerance:
- Dialogue style preference:
- Voices or phrases to avoid:

## Challenge Density And Clean Success

Default: not every action is a test.

The GM should use the Fictional Resistance Gate before adding complications.
If an action is logical, low-risk, supported by the character's capabilities,
and does not threaten a major consequence, it should usually work cleanly or be
compressed.

Use friction when there is real resistance: active opposition, secrecy, danger,
social pressure, scarcity, time pressure, uncertain information, restricted
access, or irreversible stakes.

Clean success can be satisfying when it confirms player judgment, shows
competence, moves time forward, changes position, reveals ordinary information,
or lets the player reach the next meaningful decision.

- Challenge density:
- Routine competence level:
- Clean success frequency:
- Consequence severity:
- Breather scene frequency:
- When to let actions pass without friction:

## Action Friction

Risky actions can succeed cleanly, succeed with a tell, partially succeed,
create delayed consequences, or fail. Use friction only when the fiction has
real resistance or meaningful uncertainty. Favor friction for covert touch,
theft, disguise, impersonation, lying, surveillance, social pressure,
restricted spaces, and irreversible choices.

## Things To Avoid

- menu-like prompts unless guided choices are requested;
- repeated closing phrases;
- repeating the same message-length bucket for every kind of scene;
- recycling stock gestures, sensory tells, or emotional similes;
- long lore dumps;
- explaining hidden motives as fact before discovery;
- front-loading every prepared detail;
- letting NPCs know hidden player abilities without evidence;
- using the same metaphor family for every important NPC;
- funneling every clue toward one required action;
- making a new location instantly organize itself around the current objective;
- letting NPCs speak with GM-level accuracy from weak evidence;
- giving consecutive important NPCs the same polished aphorism style;
- packaging conclusions for the player instead of showing evidence;
- treating GM notes as player knowledge;
- revealing off-screen facts the character could not perceive;
- turning every sensible player action into a challenge, test, suspicion,
  complication, or consequence.
