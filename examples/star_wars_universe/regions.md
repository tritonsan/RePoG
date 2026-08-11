# Star Wars Universe Regions

## Use Contract

Select exactly one physical opening theater and at most one compatible connection layer. A region card is a bounded campaign canvas, not permission to load every planet, species, settlement, character, route, battle, or institution. Canonical places retain sourced identity; original worlds, stations, districts, lanes, and communities must be labeled campaign-instance.

## Theater Comparison

Scores are RePoG-original onboarding judgments from 1 (low) to 5 (high), not official rankings.

| Region id | Type | Best eras | Adventure | Social breadth | Institution pressure | Canon collision risk | Research need |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `star-wars-region-reconstruction-corridor` | original physical theater | New Republic | 4 | 5 | 4 | 1 | 2 |
| `star-wars-region-coruscant-district` | canonical physical theater | Old Republic through Imperial transition | 4 | 5 | 5 | 5 | 5 |
| `star-wars-region-core-civic-world` | original/canonical-edge theater | Republic, New Republic | 3 | 5 | 5 | 2 | 4 |
| `star-wars-region-mid-rim-junction` | original physical theater | most travel-capable eras | 4 | 5 | 4 | 1 | 3 |
| `star-wars-region-outer-rim-settlement` | original physical theater | most travel-capable eras | 5 | 5 | 3 | 1 | 3 |
| `star-wars-region-ferrix` | canonical physical theater | Reign of Empire | 4 | 5 | 5 | 5 | 5 |
| `star-wars-region-mandalore` | canonical system theater | Fall of Jedi onward | 5 | 5 | 5 | 5 | 5 |
| `star-wars-region-pabu` | canonical community theater | Fall of Jedi | 3 | 5 | 3 | 4 | 4 |
| `star-wars-region-occupied-world` | original physical theater | Reign of Empire, Rebellion | 4 | 5 | 5 | 2 | 4 |
| `star-wars-region-shadowport` | original physical theater | most conflict eras | 5 | 4 | 4 | 1 | 4 |
| `star-wars-region-force-site` | original/source-gated theater | selected era | 5 | 4 | 4 | 2 | 5 |
| `star-wars-region-hyperspace-layer` | connection layer | hyperdrive eras | 5 | 4 | 4 | 1 | 4 |
| `star-wars-region-comms-courier-layer` | connection layer | communications-capable eras | 3 | 5 | 4 | 1 | 3 |

## Physical Theater Cards

### `star-wars-region-reconstruction-corridor` — Original Frontier Reconstruction Corridor

- **Status:** package-original default; not a canonical sector or route
- **Player promise:** keep a few communities connected while legitimacy, safety, mapping, and repair are still contested
- **Opening boundary:** no more than three systems, three inhabited sites, one service station, and one disputed beacon chain
- **Include:** residents, crews, traders, refugees, mechanics, droids, medics, local delegates, and a bounded New Republic mission
- **Exclude by default:** famous planets, Jedi headquarters, galactic capitals, superweapons, and fleet-scale war
- **Pressures:** route reliability, fuel, aid, recognition, remnant raids, hidden settlements, salvage, and local representation
- **Claims:** `claim-star-wars-new-republic`, `claim-star-wars-hyperspace`, `claim-star-wars-refugees`.

### `star-wars-region-coruscant-district` — One Coruscant District

- **Status:** canonical city-world; government, level, district, population, and era require selection
- **Player promise:** navigate civic power, vertical inequality, infrastructure, culture, and public life in one dense district
- **Opening boundary:** one level band, two transit links, one civic service, and one institutional threshold
- **Include:** residents of varied backgrounds, workers, delegates, couriers, maintainers, local officials, and community organizations
- **Exclude by default:** planet-wide access, every Senate office, Jedi Temple omniscience, and one universal Coruscanti culture
- **Pressures:** housing, transit, representation, records, maintenance, policing, pollution, and changing capitals
- **Claims:** `claim-star-wars-coruscant`, `claim-star-wars-senate`, `claim-star-wars-anti-essentialism`.

### `star-wars-region-core-civic-world` — Original Core Civic World

- **Status:** campaign-original world placed on the official map after Session 0
- **Player promise:** work inside a prosperous-looking civic center where representation, migration, and institutional capacity remain contested
- **Opening boundary:** one port city, one assembly complex, one residential district, and one route to the wider Core
- **Include:** administrators, service workers, migrants, diplomats, lobbyists, protestors, and visiting crews
- **Exclude by default:** universal wealth, political consensus, and automatic resemblance to Coruscant or Hosnian Prime
- **Pressures:** public spending, Senate access, trade policy, security, housing, and peripheral representation
- **Claims:** `claim-star-wars-regions`, `claim-star-wars-senate`, `claim-star-wars-coruscant`.

### `star-wars-region-mid-rim-junction` — Original Mid Rim Junction

- **Status:** campaign-original route and settlement; “Mid Rim” supplies geography only
- **Player promise:** mediate between major lanes, local agriculture or industry, passenger traffic, and competing authorities
- **Opening boundary:** one orbital or surface port, two feeder routes, one local economy, and one customs dispute
- **Include:** freighters, port workers, farmers or manufacturers, travelers, inspectors, droids, and local council members
- **Exclude by default:** a generic cultural midpoint, universal customs law, or a frictionless trade hub
- **Pressures:** tariffs, route changes, fuel, cargo verification, labor, smuggling, and disaster response
- **Claims:** `claim-star-wars-regions`, `claim-star-wars-hyperspace`, `claim-star-wars-economy`.

### `star-wars-region-outer-rim-settlement` — Original Outer Rim Settlement

- **Status:** campaign-original; location never implies lawlessness or one frontier culture
- **Player promise:** help a self-defined community negotiate distance, outside claims, scarce capacity, and internal disagreement
- **Opening boundary:** one settlement, one livelihood, one neighboring site, and one off-world dependency
- **Include:** local government, families, traders, workers, medics, defenders, droids, and newcomers
- **Exclude by default:** disposable poverty, species monoculture, inevitable crime rule, or hidden galactic destiny
- **Pressures:** water or food, medicine, route access, extraction, land, defense, and political recognition
- **Claims:** `claim-star-wars-regions`, `claim-star-wars-economy`, `claim-star-wars-medicine`.

### `star-wars-region-ferrix` — Ferrix

- **Status:** canonical and tightly source-gated to the selected era/work
- **Player promise:** center skilled salvage, repair, local memory, labor, and resistance under growing Imperial pressure
- **Opening boundary:** one work district, three yards or shops, one community meeting place, and one Imperial interface
- **Include:** technicians, salvagers, families, traders, workers, visitors, and local customs after sourcing
- **Exclude by default:** copying published protagonists' plot, inventing planet-wide law, or treating all Outer Rim communities as Ferrix
- **Pressures:** labor, salvage custody, surveillance, occupation, informants, collective action, and mourning
- **Claims:** `claim-star-wars-ferrix`, `claim-star-wars-empire`, `claim-star-wars-rebellion`.

### `star-wars-region-mandalore` — Mandalore And One Selected Community

- **Status:** canonical, era- and faction-sensitive; high research need
- **Player promise:** confront belonging, governance, diaspora, rebuilding, creed, occupation, and competing memories without one “true” Mandalorian personality
- **Opening boundary:** one settlement, clan network, civic body, diaspora cell, or reconstruction project
- **Include:** people with different political, clan, religious, pacifist, martial, adopted, and expatriate relationships after sourcing
- **Exclude by default:** universal helmet rules, species assumptions, all clans, or a famous warrior as routine patron
- **Pressures:** legitimacy, land, armor, adoption, archives, occupation, return, and ecological damage
- **Claims:** `claim-star-wars-mandalorians`, `claim-star-wars-anti-essentialism`.

### `star-wars-region-pabu` — Pabu

- **Status:** canonical refuge community tied to its selected screen context
- **Player promise:** support refuge, belonging, disaster response, and rebuilding in a community that became home to displaced people
- **Opening boundary:** one village district, harbor or landing area, relief route, and rebuilding need
- **Include:** residents, refugees, responders, children with safeguards, crews, and local leaders after sourcing
- **Exclude by default:** universal asylum law, effortless integration, or reuse of published disasters and characters without acceptance
- **Pressures:** capacity, consent, warning, evacuation, rebuilding, privacy, and outside attention
- **Claims:** `claim-star-wars-refugees`, `claim-star-wars-medicine`.

### `star-wars-region-occupied-world` — Original Occupied World District

- **Status:** campaign-original theater anchored to sourced Imperial methods
- **Player promise:** survive, organize, document, negotiate, or resist where coercive rule controls movement and resources
- **Opening boundary:** one district or settlement, one Imperial unit, one essential service, and one resistance or mutual-aid network
- **Include:** civilians with varied strategies, workers, collaborators under distinct pressures, dissidents, troops, droids, and outsiders
- **Exclude by default:** torture spectacle, inevitable heroic uprising, collective guilt, or an omniscient Empire
- **Pressures:** permits, requisition, surveillance, labor, informants, collective punishment, refuge, and tactical disagreement
- **Claims:** `claim-star-wars-empire`, `claim-star-wars-stormtroopers`, `claim-star-wars-rebellion`.

### `star-wars-region-shadowport` — Original Shadowport

- **Status:** campaign-original criminalized or weakly governed port
- **Player promise:** move cargo, information, people, and obligations through overlapping legitimate and illicit economies
- **Opening boundary:** one docking ring, one market, one repair zone, one broker network, and one authority claim
- **Include:** port workers, freighters, smugglers, guild brokers, local officials, debtors, refugees, and syndicate representatives
- **Exclude by default:** one unified underworld, consequence-free crime, species-coded criminality, or universal bounty law
- **Pressures:** docking, protection, debt, forged records, coercion, safe passage, and worker control
- **Claims:** `claim-star-wars-bounty`, `claim-star-wars-syndicates`, `claim-star-wars-economy`.

### `star-wars-region-force-site` — Original Or Selected Force Site

- **Status:** original site unless a canonical location and work are explicitly selected
- **Player promise:** investigate memory, ecology, belief, and unusual perception without predetermining Jedi recruitment or moral destiny
- **Opening boundary:** one site, one local community, one tradition or research group, and one access dispute
- **Include:** believers, skeptics, caretakers, sensitives, historians, residents, and people affected by visitors
- **Exclude by default:** universal Force mechanics, automatic Sith artifact, chosen-one revelation, or proof that one tradition owns the site
- **Pressures:** custody, pilgrimage, extraction, archaeology, consent, visions, tourism, and environmental change
- **Claims:** `claim-star-wars-force`, `claim-star-wars-force-traditions`, `claim-star-wars-jedi`, `claim-star-wars-sith`.

## Connection Layers

### `star-wars-region-hyperspace-layer` — Bounded Route Network

Connect the selected theater to no more than three destinations. Record lane status, coordinates, custodians, fuel, ship capability, hazards, checkpoints, fallback paths, and who is excluded. Do not assign fixed journey times without selected-work evidence. Claims: `claim-star-wars-hyperspace`, `claim-star-wars-starships`.

### `star-wars-region-comms-courier-layer` — Communications And Courier Network

Connect named comlinks, relays, couriers, records, witnesses, and institutional channels. Record encryption, range, delay, interception risk, censorship, language, accessibility, and evidence custody. Do not infer universal HoloNet coverage. Claims: `claim-star-wars-comms`, `claim-star-wars-empire`, `claim-star-wars-resistance`.

## Era/Media Overlays

- **Old Republic:** choose Canon sources or `star-wars-legends` selected works; SWTOR remains an explicit Legends inference with player-variable branches.
- **High Republic:** source the chosen publication and date; expansion does not imply uniform prosperity.
- **Fall of the Jedi:** source Clone Wars conditions, clone identity, Jedi military role, and known outcomes.
- **Reign of the Empire:** define occupation, local administration, resistance knowledge, and coercion limits.
- **Age of Rebellion:** choose one cell, theater, and spoiler ceiling; do not replay published victories by default.
- **New Republic:** use reconstruction and remnant pressure without importing a whole series; package default.
- **Rise of the First Order:** separate New Republic, First Order, and Resistance knowledge and authority.
- **New Jedi Order:** do not invent unreleased future outcomes.
- **Alternate media:** attach selected Visions, LEGO, crossover, or game labels and prevent back-propagation.

## Default Opening Network

Materialize only:

- `star-wars-region-reconstruction-corridor`
- optional `star-wars-region-hyperspace-layer`
- no more than three systems and three inhabited sites
- one service station and one disputed beacon chain
- four powers from [Factions](factions.md)
- six to eight original faces
- `star-wars-frame-broken-beacon`

Coruscant, Mandalore, famous frontier worlds, Jedi sites, and galactic leadership remain off-stage unless player action establishes a durable connection.
