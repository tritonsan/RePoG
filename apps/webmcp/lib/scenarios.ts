export type Resolution = { outcome: 'accepted' | 'altered' | 'rejected'; summary: string; visibleConsequences: string[] };
export type Capability = 'self.speak' | 'self.move' | 'self.use_owned_resource' | 'self.personal_commitment' | 'self.observe' | 'self.recall';
export type KnowledgeFact = { factId: string; text: string; status: 'observed' | 'heard' | 'inferred' | 'suspected' | 'disproven' | 'misremembered'; source: string; confidence: number; learnedAtRevision: number; lastConfirmedRevision: number };
export type PreparedTurn = {
  sceneId: string; sourceRevision: number; title: string; summary: string; pressure: string;
  perceivableFacts: string[]; selfKnowledge: string[]; knowledgeIndex: KnowledgeFact[]; partyPublicFacts: string[]; affordances: string[];
  entityRefs: string[]; ownedResourceRefs: string[];
  resolutions: Array<Resolution & { terms: string[] }>; fallback: Resolution;
};
export type ScenarioPack = {
  schemaVersion: '1.0'; scenarioId: string; title: string; genre: string; tone: string; realityRules: string[]; tableBoundaries: string[];
  character: { id: string; name: string; role: string; identity: string; prioritizedValues: string; shortTermGoal: string; longTermGoal: string; contradictions: string; decisionRules: string[]; voiceExamples: string[]; capabilities: Capability[]; authority: string[]; forbiddenAuthority: string[] };
  turns: PreparedTurn[];
};

export const blackGullScenario: ScenarioPack = {
  schemaVersion: '1.0', scenarioId: 'black-gull', title: 'The Black Gull Cellar', genre: 'Rain-soaked fantasy intrigue', tone: 'Tense, grounded, and consequence-led.',
  realityRules: ['Consequences follow visible positioning.', 'Secret knowledge remains character-bounded.', 'No character may author another person’s choice.'],
  tableBoundaries: ['The agent authors only the active character.', 'RePoG remains the sole outcome authority.'],
  character: {
    id: 'mira', name: 'Mira', role: 'Scout', identity: 'A wary dockside scout who tests people before trusting them.',
    prioritizedValues: 'Protect the party first; preserve initiative second; satisfy curiosity third.',
    shortTermGoal: 'Open a safe route through the cellar.', longTermGoal: 'Learn why the Black Gull is moving contraband through the docks.',
    contradictions: 'Patient when observing, impatient when someone threatens the vulnerable.',
    decisionRules: ['Test before confronting.', 'Prefer leverage over spectacle.', 'Do not abandon a party member for a cleaner victory.'],
    voiceExamples: ['Long night. Low tide.', 'I trust doors more than the people guarding them.', 'Quiet first. Running later.'],
    capabilities: ['self.speak', 'self.move', 'self.use_owned_resource', 'self.personal_commitment', 'self.observe', 'self.recall'],
    authority: ['Speak as Mira.', 'Move Mira.', 'Use Mira’s knowledge and owned gear.', 'Make Mira’s personal commitments.'],
    forbiddenAuthority: ['Do not decide another character’s action or thoughts.', 'Do not assert a world outcome.', 'Do not access GM truth.'],
  },
  turns: [
    {
      sceneId: 'dock-arrival', sourceRevision: 12, title: 'The guarded stair',
      summary: 'A nervous guard blocks the cellar stairs while the innkeeper watches from behind an untouched glass.', pressure: 'The guard can reach a brass warning bell before Arden crosses the room.',
      perceivableFacts: ['The guard keeps his left hand close to his coat.', 'A brass warning bell hangs within reach.', 'The rear service exit remains open.'], selfKnowledge: ['You can see both exits.', 'You prefer indirect tests before open confrontation.'],
      knowledgeIndex: [
        { factId: 'black-gull-ring', text: 'The guard’s ring resembles the Black Gull mark.', status: 'observed', source: 'Mira', confidence: 0.94, learnedAtRevision: 12, lastConfirmedRevision: 12 },
        { factId: 'black-gull-low-tide', text: 'Black Gull members react to “low tide” when checking allegiance.', status: 'heard', source: 'dockside informant', confidence: 0.76, learnedAtRevision: 9, lastConfirmedRevision: 12 },
      ], partyPublicFacts: ['The party needs cellar access.', 'Arden is ready to distract the innkeeper.'], affordances: ['Observe', 'Question', 'Signal Arden', 'Test the guard', 'Withdraw'], entityRefs: ['guard', 'arden', 'innkeeper'], ownedResourceRefs: ['black-gull-ring'],
      resolutions: [{ terms: ['black gull', 'low tide', 'ring', 'yüzük', 'gelgit'], outcome: 'accepted', summary: 'Mira’s indirect test lands. The guard recognizes the phrase before he can hide it.', visibleConsequences: ['The guard’s gaze snaps to Mira.', 'His hand leaves the warning bell.', 'Arden gains a clean opening to move.'] }],
      fallback: { outcome: 'altered', summary: 'Mira draws the guard’s attention, but not cleanly enough to conceal Arden’s movement.', visibleConsequences: ['The guard turns from the cellar.', 'The innkeeper begins watching Arden.'] },
    },
    {
      sceneId: 'cellar-ledger', sourceRevision: 13, title: 'The salt ledger',
      summary: 'Below the inn, a wet ledger lies open beside three sealed crates and a narrow drainage tunnel.', pressure: 'Bootsteps gather above; Mira has time to secure one advantage before the cellar is searched.',
      perceivableFacts: ['One ledger page has been freshly torn out.', 'Blue salt leaks from the smallest crate.', 'The drainage tunnel carries a cold outward draft.'], selfKnowledge: ['You notice handling patterns other people dismiss.', 'Arden is still covering the stair.'],
      knowledgeIndex: [
        { factId: 'courier-double-stroke', text: 'Black Gull couriers mark false cargo weights with a doubled stroke.', status: 'heard', source: 'dock records', confidence: 0.81, learnedAtRevision: 10, lastConfirmedRevision: 13 },
        { factId: 'blue-salt-prints', text: 'Blue salt can reveal recent fingerprints in damp air.', status: 'observed', source: 'Mira', confidence: 0.97, learnedAtRevision: 8, lastConfirmedRevision: 13 },
      ], partyPublicFacts: ['The guard was diverted without ringing the bell.', 'The party still needs a route out.'], affordances: ['Inspect the ledger', 'Use blue salt', 'Secure a crate', 'Take the drainage route', 'Support Arden'], entityRefs: ['arden'], ownedResourceRefs: ['blue-salt'],
      resolutions: [{ terms: ['salt', 'finger', 'iz', 'ledger', 'defter'], outcome: 'accepted', summary: 'Mira uses the cargo and ledger together instead of treating either as the whole answer.', visibleConsequences: ['A fresh courier mark appears on the torn-page edge.', 'The mark points toward the drainage route.', 'Mira keeps enough time to warn Arden.'] }],
      fallback: { outcome: 'altered', summary: 'Mira secures a useful lead but spends the last quiet seconds doing it.', visibleConsequences: ['The route forward becomes clearer.', 'The cellar door starts to open above.'] },
    },
    {
      sceneId: 'tide-gate', sourceRevision: 14, title: 'The courier at the tide gate',
      summary: 'The drainage tunnel opens onto a tide gate where a frightened courier struggles with a jammed skiff.', pressure: 'The rising water will trap the courier, but taking the skiff immediately would preserve the party’s pursuit.',
      perceivableFacts: ['The courier is injured and unarmed.', 'A sealed message case is tied to the skiff.', 'The tide chain can be released from Mira’s side.'], selfKnowledge: ['You refuse to trade a helpless person for a cleaner lead.', 'You can release the chain or seize the case, not both before the surge.'],
      knowledgeIndex: [
        { factId: 'courier-ledger-match', text: 'The courier mark matches the torn ledger page.', status: 'observed', source: 'Mira', confidence: 1, learnedAtRevision: 14, lastConfirmedRevision: 14 },
        { factId: 'courier-may-know-order', text: 'A living courier may know who ordered the shipment.', status: 'inferred', source: 'Mira', confidence: 0.68, learnedAtRevision: 14, lastConfirmedRevision: 14 },
      ], partyPublicFacts: ['Arden is seconds behind.', 'The Black Gull now knows someone entered the cellar.'], affordances: ['Release the tide chain', 'Take the message case', 'Question the courier', 'Prepare an escape', 'Call to Arden'], entityRefs: ['courier', 'arden'], ownedResourceRefs: ['tide-chain'],
      resolutions: [{ terms: ['chain', 'courier', 'save', 'release', 'zincir', 'kurtar'], outcome: 'accepted', summary: 'Mira chooses the living witness over the cleanest piece of evidence.', visibleConsequences: ['The released chain swings the skiff into reach.', 'The courier survives and keeps hold of the message case.', 'Arden arrives to find Mira with a frightened witness and an unfinished pursuit.'] }],
      fallback: { outcome: 'altered', summary: 'Mira preserves the lead but cannot control every cost of the rising tide.', visibleConsequences: ['The message case stays in play.', 'The courier’s trust becomes harder to win.', 'The three-turn session reaches a consequential stopping point.'] },
    },
  ],
};

export const orisonFixture: ScenarioPack = {
  schemaVersion: '1.0', scenarioId: 'orison-signal', title: 'Signal at Orison', genre: 'Low-orbit science-fiction negotiation', tone: 'Procedural tension under a hard deadline.', realityRules: ['No faster-than-light communication.', 'Sensor claims require recorded evidence.'], tableBoundaries: ['The agent cannot command station weapons.', 'RePoG resolves institutional reactions.'],
  character: { id: 'iko', name: 'Iko', role: 'Systems Envoy', identity: 'A meticulous envoy who distrusts elegant explanations.', prioritizedValues: 'Crew safety, verifiable evidence, institutional legitimacy.', shortTermGoal: 'Keep the station from firing on an unknown signal.', longTermGoal: 'Expose falsified sensor governance.', contradictions: 'Procedural in public, willing to improvise when evidence is buried.', decisionRules: ['Verify the channel before the claim.', 'Make reversible commitments first.'], voiceExamples: ['Show me the timestamp, not the confidence.'], capabilities: ['self.speak', 'self.observe', 'self.recall', 'self.personal_commitment'], authority: ['Speak and negotiate as Iko.'], forbiddenAuthority: ['Do not command station weapons.', 'Do not invent sensor results.'] },
  turns: [{ sceneId: 'orison-array', sourceRevision: 3, title: 'The disputed signal', summary: 'A station officer wants to classify an unverified signal as hostile.', pressure: 'The firing window closes in ninety seconds.', perceivableFacts: ['Two sensor clocks disagree.'], selfKnowledge: ['You audit timestamps before conclusions.'], knowledgeIndex: [{ factId: 'outer-array-service', text: 'The outer array was serviced yesterday.', status: 'heard', source: 'maintenance log', confidence: 0.88, learnedAtRevision: 2, lastConfirmedRevision: 3 }], partyPublicFacts: ['No weapon has fired yet.'], affordances: ['Request raw timestamps', 'Delay classification'], entityRefs: ['station-officer'], ownedResourceRefs: [], resolutions: [{ terms: ['timestamp', 'clock', 'zaman'], outcome: 'accepted', summary: 'Iko forces the disagreement into the open.', visibleConsequences: ['The firing order pauses for an audit.'] }], fallback: { outcome: 'altered', summary: 'Iko wins a brief delay without resolving the evidence conflict.', visibleConsequences: ['The station waits, but suspicion rises.'] } }],
};

export const scenarios: Record<string, ScenarioPack> = { [blackGullScenario.scenarioId]: blackGullScenario, [orisonFixture.scenarioId]: orisonFixture };
export function resolvePreparedTurn(turn: PreparedTurn, action: string, speech = ''): Resolution { const normalized = `${action} ${speech}`.toLocaleLowerCase(); return turn.resolutions.find((candidate) => candidate.terms.some((term) => normalized.includes(term))) || turn.fallback; }
