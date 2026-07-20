# User Context

This is consent-based conversational memory, not a transcript or a profile
inferred behind the user's back. Save only information the user explicitly
shared and that is useful for a future conversation. Stable ids must be unique
across active memories and follow-ups.

## Memory Policy

- Policy: contextual_low_risk
- Sensitive facts: explicit consent only
- Raw transcript storage: never
- User may ask what is remembered: yes
- User may say forget or do not save: yes

Allowed policies are:

- `off`: keep no durable user memory or follow-up;
- `ask_before_save`: every durable memory needs explicit save consent;
- `contextual_low_risk`: an explicitly shared, useful, non-sensitive fact may
  use contextual consent; sensitive facts still need explicit consent.

## Active Memories

Use one compact entry per durable memory. Do not fill from inference.

### Memory

- Memory id:
- Kind: preference | durable_event | promise | upcoming_date | callback
- Content:
- Source: explicit_user_statement | explicit_user_request_to_remember
- Consent: contextual | explicit
- Sensitive: no
- Recorded at:
- Last used:

Remove the example before Companion setup completes.

## Upcoming Follow-Ups

### Follow-Up

- Follow-up id:
- What the user explicitly shared:
- Due window:
- Why a follow-up is welcome:
- Consent: contextual | explicit
- Sensitive: no
- Status: open | completed | cancelled

## Forget Tombstones

Keep only a content-free id and time so a forgotten memory is not silently
recreated from stale active notes. This does not claim that Git history or an
external backup was erased. A tombstoned id may not remain in Active Memories
or Upcoming Follow-Ups.

| Tombstone id | Forgotten at | Scope |
| --- | --- | --- |
