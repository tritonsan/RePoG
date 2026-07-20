# World Dynamics

Use this file for on-demand changes outside the immediate scene. It is not a
background simulation and should not attempt to model the whole world.

Only add a domain when it can produce meaningful fictional consequences for
the current campaign scale.

This file owns current offscreen movement for its domains, including a
faction's current move when that move matters beyond the immediate scene.
Faction notes own stable desire, method, and capability and reference the
relevant domain instead of copying its current trajectory.

In AI Companion mode, use domains for only the character's currently relevant
life lines: work/education, family or social obligations, housing/economics,
health/recovery when explicitly established, or a personal project. Elapsed
real time alone never forces a result. Evaluate a domain only on the next user
message when its recorded trigger is due, and keep developments within the
ceiling returned by `tools/companion_state.py begin-exchange`.

This file owns the domain trajectory, not the immediate conversational mood.
`companion_state.json.current_condition` owns the current energy, social
bandwidth, emotional weather, and active preoccupation. Its bounded
`attention_queue` may reference due domains but must not copy their truth.

## Update Policy

- The GM detects refresh needs from fiction; the Player does not request system
  updates.
- Refresh only relevant domains.
- Use elapsed fictional time, prior events, active pressures, and involved
  actors as context.
- Establish the causal result from those inputs before applying any optional
  bounded uncertainty. Uncertainty may select among plausible causal outcomes;
  it may not replace cause and effect.
- Give each due evaluation a stable id. Reusing the same id with the same
  inputs must not generate a different persisted result.
- Surface only consequences the character can perceive or learn from a
  believable source.
- Record notable changes, not routine noise.

## Active Domains

### Domain Name

- Domain id:
- Scope:
- Status: dormant | stable | shifting | volatile
- Volatility: 0-3
- Current pressure: 0-4
- Relevant actors:
- Current trajectory:
- Desired outcome (Companion only):
- Pending evaluation id:
- Last evaluation id:
- Last evaluation inputs:
  - Trigger:
  - Fictional time or elapsed index:
  - Relevant prior events:
  - Involved actors and available resources:
  - Active pressure:
- Causal result before uncertainty:
- Bounded uncertainty result, if used:
- Last evaluated fictional time:
- Last evaluated real time (Companion only):
- Last evaluated time index:
- Last evaluated revision:
- Due: no
- Refresh triggers:
- Player-visible channels:
- Next move if ignored:
- Hidden considerations:

## Due Checks

Domains that may need evaluation when their trigger occurs:

- None yet.

## Notable World Events

Append compact durable changes here.

### Event Title

- Evaluation id:
- Fictional time:
- Real timestamp (Companion only):
- Place (Companion only):
- Involved people (Companion only):
- Domain:
- Direction: advance | setback | opportunity | complication | stasis
- Intensity: 1-3
- What changed:
- Why it changed:
- Related elements:
- Player visibility: hidden | foreshadowable | perceivable | confirmed
- Consequence or next pressure:
