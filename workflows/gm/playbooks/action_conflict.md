# Action And Conflict Playbook

Use this playbook for danger, contests, chases, infiltration under pressure,
violence, and other actions with meaningful resistance.

## Fictional Resistance Gate

Before any test or consequence, classify the action:

- **Trivial/color:** no meaningful resistance or durable consequence; allow it.
- **Routine competence:** within established capability under ordinary
  conditions; allow clean success.
- **Uncertain:** outcome is genuinely in doubt and failure changes something;
  resolve with the selected basis.
- **Contested/high stakes:** active opposition or substantial danger; make
  position, likely cost, and important risk legible before commitment.

Do not add friction merely to create drama. Locked access, limited time,
hostile intent, physical danger, scarce resources, or incompatible goals are
real sources of resistance; mood is not.

## Resolution Grounding

Follow `play_profile.yaml.mechanics.resolution_grounding`:

- `fictional`: decide from position, capability, method, leverage, and
  established world logic.
- `bands`: compare compact capability/difficulty bands and translate the result
  back into fiction.
- `numeric`: use the configured stats and approved mechanic modules.

Use dice only when the approved dice policy calls for them. Follow the Player
roll/GM roll visibility policy, use a unique operation id for durable mechanic
mutations, and expose no internal math in Player Mode beyond the receipt's
`display` line where the dice mode shows rolls. A tool may resolve bounded
uncertainty; it may not invent motives, events, or consequences.

## When Not To Roll

Roll only when a bad result is a real possibility. When the chance of landing
below the lowest success band is under about 15%, or nil, do not roll: narrate
the success and hand the scene back to the world. Read that chance from the
odds table (`python tools/odds.py campaign`) for the value, factors, and
difficulty you would declare. A roll call that returns `certain`, with the
warning `roll_certain`, was recorded at its floor band without a roll: narrate
that band as an unrolled success and show no dice for it. This threshold
decides what is uncertain; it never makes a likely failure disappear.

## Declare Before Rolling

When `dice_mode` is not `judgment_only`, an uncertain or contested action is
rolled, never judged around. Before any die is read, fix the `actor`, the
`axis` or capability and its `value`, the `difficulty` with a one-line
`reason` read from the opposition, each factor as a labelled whole-number
modifier, and the `stakes`: what each reachable band below success costs.

Factors cut both ways. What favors the opposition (numbers, ground, a wound,
bad light, no time) enters as a negative modifier as readily as an advantage
enters as a positive one, and a list of bonuses alone is a call being steered.
Size each factor 2 to 6, for a small, clear, or decisive edge, unless
`rules.md` sizes factors for a narrower scale. The stakes describe every band
the call can reach below success and no band it cannot reach; the receipt warns
`stakes_unreachable_band` or `stakes_missing_band` when they do not.

Roll the call once through
`python tools/roll_dice.py --campaign campaign --input-file -` with a new
`roll_id` and a `call` of those fields (`factors` as `label` and `modifier`).
A Player who rolls under the dice mode reports against the same declaration.
Never change a declaration after the roll; a new attempt needs a fictional
reason and a new roll id. A value or difficulty outside the declared scale is
refused: change the scale through the OOC adjustment playbook, never with a
hidden "counts as". When the odds table (`python tools/odds.py campaign`) shows
the actor cannot miss on this scale, offer that OOC scale change once, at a
natural pause; until the Player decides, roll as declared. Cite the roll in the
durable change (persistence playbook).

Where the dice mode shows rolls (`open_gm_rolls`, or a GM roll under
`hybrid`), show the receipt's `display` line as it stands, in the play language,
then narrate the band; under `hidden_gm_rolls` show nothing of it.

## Crowds And Named Enemies

A crowd is not one opponent. Against many, use one of these, whichever the
fiction supports: a negative small-edge factor (-2 at the default sizes) for
each doubling of the opponents (two, four, eight), several exchanges rolled in
turn, or an alarm clock that fills as the fight goes on and brings what the
noise draws. A named enemy rolls separately from the extras around them: a
roll against the crowd never decides a named enemy's fate, and beating the
crowd leaves the named enemy standing until their own roll or the fiction
settles them.

## Let Competence Stand

Respect established strengths, equipment, preparation, authority, and prior
success. Do not negate a strong capability through an unestablished counter.
When opposition lacks the position or power to resist, let the action work.

Weakness matters only where the declared action actually relies on it. Avoid
requiring an eight-stat NPC block unless `numeric` resolution is selected;
fictional and band-based NPCs can be grounded by capabilities, limits, and
power band.

## Consequences

Consequences follow the stated risk and causal situation. Prefer changes to
position, time, exposure, resources, relationships, access, conditions, or
threat behavior. Do not attach an unrelated twist. If a cost was not visible
and would materially change consent, surface it before the Player commits.

Use failure to move the situation, not to deny the attempt happened. Keep
severity proportional to stakes, preparation, and opposition. A clean success
is valid when the fiction supports one.

Narrate the band rolled. A success delivers what the action sought and is never
narrated with an added setback; a cost comes only from a lower band's declared
stakes or from a real outside actor with its own cause. A failed roll is not
quietly reversed by an easier route, and no NPC hands over the solution unless
their own motive causes it.

## Actor Reactions

Only witnesses or actors reached by a credible channel may react. Their moves
follow their knowledge, objective, capacity, and current position. Do not grant
instant coordination to distant NPCs or factions.

## Narrate The Beat

Resolve the Player's method first. Show the nearest physical/social result,
then the relevant reaction, then the changed situation. Preserve unavoidable
bodily sensation but never decide the player character's fear, resolve,
pleasure, trust, or next action. End at the first meaningful reaction point.

After major pressure breaks, consider `breather/aftermath` rather than
immediately replacing the conflict with another threat.
