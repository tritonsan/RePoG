# Relationship Map

Campaign id: `replace_me`

Use this file as a compact edge-list. It is not a vector store and not an
encyclopedia. Keep entries short so the GM can load the relationship web
without spending many tokens.

Format:

`A -> B: relation / status / player-known? / last change`

## Character Links

- `Character A -> Character B: relation / status / player-known? / last change`

## Location Links

- `Location A -> Location B: route, proximity, access, or contrast / status / player-known? / last change`

## Faction Links

- `Faction A -> Faction B: alliance, rivalry, dependency, fear, debt, or manipulation / status / player-known? / last change`

## Cross-Type Links

- `NPC -> Location: presence, ownership, access, captivity, rumor, or habit / status / player-known? / last change`
- `NPC -> Faction: member, enemy, target, patron, debtor, asset, or threat / status / player-known? / last change`
- `Faction -> Location: control, influence, hidden access, resource, or threat / status / player-known? / last change`
