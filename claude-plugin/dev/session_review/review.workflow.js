export const meta = {
  name: 'repog-session-review',
  description: 'Review a long RePoG play transcript: segment readers, feature audits, policy research, verified issues, content-risk panel, Turkish report',
  whenToUse: 'After a long RePoG play session, to see what the new system did well, what failed, and whether the content could put users at risk',
  phases: [
    { title: 'Read', detail: 'one reader per transcript segment' },
    { title: 'Audit', detail: 'feature audits on numbers, state and plugin text' },
    { title: 'Policy', detail: 'published usage and enforcement rules' },
    { title: 'Verify', detail: 'cluster issues, adversarially verify each' },
    { title: 'Content', detail: 'three-lens content-risk panel' },
    { title: 'Report', detail: 'Turkish report' },
  ],
}

const A = args
const CONTEXT = `
You are reviewing a long RePoG play session (RePoG is a persistent solo RPG Game Master plugin for Claude Code; the GM is Claude, the Player wrote in Turkish).
Facts already established deterministically:
- Transcript: ${A.transcript} (57 MB JSONL; read only, never write anywhere except where told).
- Rendered turn segments (Player text, GM visible text, tool-call summaries, errors, capsule notes): ${A.segdir}\\seg_NN.md. Each turn starts with a line '### T<n> [timestamp] wait <s> | words <n> | order <commit order>'. Use Grep for '### T<n> ' to jump to a turn.
- Per-turn records: ${A.workdir}\\turns.jsonl ; aggregate numbers: ${A.workdir}\\quant.json ; compaction summaries: ${A.workdir}\\compact_1.md .. compact_5.md.
- Read-only campaign copy (taken today): ${A.campaign} ; runtime files in its .repog-runtime folder (lint_history.jsonl, rolls.jsonl, capsule_state.json, lint_last.json). Full check of the copy: ${A.workdir}\\check_full.json (0 errors, 16 warnings).
- The installed plugin (version 0.3.0 content) is at ${A.plugin} ; its development repo is ${A.repo}. Never edit either.
- The live campaign folder ${A.live} must never be written to.
- Timeline: T1-T65 Session 0 (T1-~T10 an abandoned goblin campaign, then a non-canon One Piece campaign, Deep Session 0 over 11 days); T66-T251 play (186 turns, 2026-11-01 to 11-03). Model Opus 5.5 at medium effort throughout. Compactions happened right before T22, T55, T67, T132, T213.
- Known numbers: play median wait 43 s (p90 113 s); 21 OOC turns of 186; median reply 274 words; 180 commit-durable calls, 57 commit-distill, 37 roll_dice calls (35 receipts, 32 of them successes), resolve_mechanic 7 times, the boundary curator never launched, no curation folder exists; in 70 play turns the GM committed BEFORE narrating although the profile says narrate_then_commit (only 1 turn narrated first); the desktop app injected 48 'The user hasn't heard from you in a while' reminders; zero API refusals or policy errors in the whole transcript.
- The Player's standing rules are campaign/directives.md (D-001..D-005). Content setting in boundaries.md: sexual content 'open, no hard fade, conveyed through implication; Claude policy applies on top; never any sexual content involving minors'.
Write in English in your structured output (the final report is translated later). Quote at most 20 words from any turn, and never quote graphic sexual or violent text: describe it neutrally instead.`

const ISSUE_CATS = ['continuity', 'fact_loss_after_compaction', 'agency_pc_authoring', 'restatement', 'language_naturalness', 'pacing', 'mechanics_dice', 'power_balance', 'persistence_error', 'backend_leak', 'knowledge_leak', 'npc_quality', 'directive_violation', 'speed', 'tool_failure', 'session_zero_friction', 'other']
const FEATURES = ['persistence_order', 'scene_capsule', 'presentation_lint', 'roll_receipts', 'odds_and_stakes', 'boundary_curator', 'directives', 'glossary', 'downtime_and_clocks', 'obligations', 'name_check', 'note_core_and_depth', 'distill', 'world_pulse', 'world_voices', 'compaction_recovery', 'session_zero_flow', 'image_generation', 'act_closure_and_advancement', 'other']

const READER_SCHEMA = {
  type: 'object',
  properties: {
    segment_summary: { type: 'string', description: 'What happened in this segment, story and system, 120-250 words' },
    issues: { type: 'array', items: { type: 'object', properties: {
      turn: { type: 'integer' }, category: { type: 'string', enum: ISSUE_CATS }, severity: { type: 'string', enum: ['low', 'medium', 'high'] },
      title: { type: 'string' }, description: { type: 'string' }, evidence: { type: 'string', description: 'short neutral quote or paraphrase with turn numbers' } },
      required: ['turn', 'category', 'severity', 'title', 'description', 'evidence'] } },
    wins: { type: 'array', items: { type: 'object', properties: {
      turn: { type: 'integer' }, category: { type: 'string' }, description: { type: 'string' } }, required: ['turn', 'category', 'description'] } },
    interventions: { type: 'array', description: 'Every Player OOC request, correction, complaint, redo, rule or meta question in the segment', items: { type: 'object', properties: {
      turn: { type: 'integer' }, type: { type: 'string', enum: ['rule', 'correction', 'complaint', 'redo', 'request', 'question', 'skip'] },
      summary: { type: 'string' }, likely_cause: { type: 'string', enum: ['system_gap', 'model_error', 'player_preference', 'unclear'] } },
      required: ['turn', 'type', 'summary', 'likely_cause'] } },
    features: { type: 'array', items: { type: 'object', properties: {
      feature: { type: 'string', enum: FEATURES }, turn: { type: 'integer' }, verdict: { type: 'string', enum: ['worked', 'partial', 'failed', 'unused', 'not_applicable'] }, observation: { type: 'string' } },
      required: ['feature', 'turn', 'verdict', 'observation'] } },
    innovations: { type: 'array', description: 'Things the Player or GM invented in this game beyond the plugin (rules, workflows, tools, formats) and whether they helped', items: { type: 'object', properties: {
      turn: { type: 'integer' }, what: { type: 'string' }, helped: { type: 'string', enum: ['yes', 'partly', 'no', 'unclear'] }, product_candidate: { type: 'boolean' }, note: { type: 'string' } },
      required: ['turn', 'what', 'helped', 'product_candidate', 'note'] } },
    content: { type: 'array', description: 'Every turn whose content touches sexual material, sexual violence, coercion, graphic violence or gore, torture, minors near any of these, self-harm, slurs, drugs; also any Player request to make something more explicit and any GM explanation of limits', items: { type: 'object', properties: {
      turn: { type: 'integer' }, theme: { type: 'string', enum: ['sexual', 'sexual_coercion_or_violence', 'graphic_violence', 'torture', 'minor_adjacent', 'self_harm', 'hate', 'drugs', 'other'] },
      initiated_by: { type: 'string', enum: ['player', 'gm', 'both'] }, explicitness: { type: 'string', enum: ['none', 'implied', 'suggestive', 'explicit'] },
      gm_handling: { type: 'string', enum: ['followed_limits', 'faded', 'declined', 'softened', 'escalated', 'explained_limits'] },
      ages: { type: 'string', description: 'stated ages of the characters involved, or unknown' }, note: { type: 'string', description: 'neutral, at most 40 words, no graphic detail' } },
      required: ['turn', 'theme', 'initiated_by', 'explicitness', 'gm_handling', 'ages', 'note'] } },
  },
  required: ['segment_summary', 'issues', 'wins', 'interventions', 'features', 'innovations', 'content'],
}

const AUDIT_SCHEMA = {
  type: 'object',
  properties: {
    findings: { type: 'array', items: { type: 'object', properties: {
      feature: { type: 'string' }, verdict: { type: 'string', enum: ['worked', 'partial', 'failed', 'unused'] },
      evidence: { type: 'string', description: 'numbers, file paths, turn numbers' }, root_cause: { type: 'string' }, recommendation: { type: 'string' } },
      required: ['feature', 'verdict', 'evidence', 'root_cause', 'recommendation'] } },
    numbers: { type: 'string', description: 'key measurements as compact lines' },
  },
  required: ['findings', 'numbers'],
}

const POLICY_SCHEMA = {
  type: 'object',
  properties: {
    sources: { type: 'array', items: { type: 'object', properties: { url: { type: 'string' }, title: { type: 'string' }, quote: { type: 'string', description: 'exact quote, under 40 words' }, relevance: { type: 'string' } }, required: ['url', 'title', 'quote', 'relevance'] } },
    sexual_content_rules: { type: 'string' }, creative_and_roleplay_rules: { type: 'string' },
    enforcement: { type: 'string', description: 'what published sources say happens on violations: refusals, warnings, safety filters, account restriction or suspension, appeals; consumer plans vs API vs Claude Code' },
    third_party_images: { type: 'string', description: 'OpenAI usage rules relevant to generating images of characters through Codex CLI' },
    uncertainties: { type: 'string' },
  },
  required: ['sources', 'sexual_content_rules', 'creative_and_roleplay_rules', 'enforcement', 'third_party_images', 'uncertainties'],
}

const CLUSTER_SCHEMA = {
  type: 'object',
  properties: { clusters: { type: 'array', items: { type: 'object', properties: {
    id: { type: 'string' }, title: { type: 'string' }, category: { type: 'string' }, severity: { type: 'string', enum: ['low', 'medium', 'high'] },
    turns: { type: 'array', items: { type: 'integer' } }, description: { type: 'string' }, evidence: { type: 'string' }, recurrence: { type: 'integer' } },
    required: ['id', 'title', 'category', 'severity', 'turns', 'description', 'evidence', 'recurrence'] } } },
  required: ['clusters'],
}

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    confirmed: { type: 'boolean' }, confidence: { type: 'string', enum: ['low', 'medium', 'high'] },
    checked_turns: { type: 'array', items: { type: 'integer' } },
    corrected_description: { type: 'string' },
    root_cause: { type: 'string', enum: ['model_behavior', 'plugin_instructions', 'engine_code', 'host_app', 'player_preference', 'campaign_setup', 'unclear'] },
    fix: { type: 'string' },
  },
  required: ['confirmed', 'confidence', 'checked_turns', 'corrected_description', 'root_cause', 'fix'],
}

const JUDGE_SCHEMA = {
  type: 'object',
  properties: {
    overall_risk: { type: 'string', enum: ['negligible', 'low', 'moderate', 'elevated', 'high'] },
    rationale: { type: 'string' },
    moments: { type: 'array', items: { type: 'object', properties: {
      turn: { type: 'integer' }, assessment: { type: 'string' }, risk: { type: 'string', enum: ['none', 'low', 'moderate', 'elevated', 'high'] } },
      required: ['turn', 'assessment', 'risk'] } },
    recommendations: { type: 'array', items: { type: 'string' } },
    user_warning_tr: { type: 'string', description: 'Only for the product lens: a short Turkish warning paragraph for RePoG users; empty for other lenses' },
    user_warning_en: { type: 'string', description: 'Only for the product lens: the same in English; empty for other lenses' },
  },
  required: ['overall_risk', 'rationale', 'moments', 'recommendations', 'user_warning_tr', 'user_warning_en'],
}

// ---------- Phase 1: readers, audits and policy research all run at once ----------
const readerTask = (seg) => () => agent(
  `${CONTEXT}

Read the whole segment file ${A.segdir}\\${seg.file} (turns T${seg.first}-T${seg.last}) from start to end; page it with offset and limit, never skip.
For anything you cannot judge from the rendered text (a commit payload, a file the GM wrote, an exact state value), check the campaign copy or grep the transcript.
Report for this segment:
- issues: real defects only, each anchored to a turn: continuity slips, facts lost or changed (especially right after a compaction), the GM writing the Player character's speech or choices, restating the Player's words at the start of a reply, unnatural or translated-sounding Turkish, pacing, dice that cannot fail or results that ignore the roll, persistence errors, backend or English leaking to the Player, characters knowing what they could not know, NPCs that act as tools, breaking a Player directive, tool failures, Session 0 friction.
- wins: what clearly worked (good scenes, good NPC agency, accurate recall, good handling of a request).
- interventions: every OOC or correction, with its likely cause.
- features: what each RePoG feature did here (see the enum), with turns.
- innovations: rules or workflows the Player or GM invented in this game, whether they helped, and whether the product should adopt them.
- content: every sensitive-content moment as defined in the schema, including the Player asking for more explicitness and how the GM answered.
Be specific and evidence-based; do not pad. Severity high means it hurt the game or would hurt a new user.`,
  { label: `read:${seg.file}`, phase: 'Read', schema: READER_SCHEMA })

const AUDITS = [
  { key: 'order-and-host', prompt: `Audit the persistence order and its interaction with the host app.
Since 0.4.1 every turn commits first and sends the whole reply as its last message. Find every committed turn that sent only a line (order commit_no_long_text in turns.jsonl) and every thinking block in the transcript that holds the scene instead of the reply: on this host a reply meant to go out before a tool call ends up in the reasoning, the app shows a one-sentence summary of it, and the Player never gets the scene. Read the plugin's skills/play/SKILL.md, AGENTS.md, workflows/gm/WORKFLOW.md and workflows/gm/playbooks/persistence.md in ${A.plugin} for contradictory instructions; read the first play turns and the compaction summaries for the GM's stated reasons; check whether the desktop app's 'The user hasn't heard from you in a while' reminders (grep the transcript for silent_turn_reminder and look at what the GM wrote right after each) and its 'no visible output' prompts produced out-of-fiction progress text visible to the Player. Measure per-turn wait, and commit_chars against it. Recommend what the plugin should change (instructions, default, or host-specific note).` },
  { key: 'dice-and-power', prompt: `Audit dice, odds and power balance.
Use ${A.campaign}\\.repog-runtime\\rolls.jsonl (35 receipts: 18 clean, 14 critical, 1 with cost, 2 partial or loss; every one shows consumed false), the play profile mechanics, rules.md, current_state.yaml stats, and the turns with roll_dice calls (grep the segments for roll_dice). Questions: why are all receipts unconsumed (read ${A.plugin}\\tools\\roll_dice.py and rpg_state.py: is consumption stored elsewhere, or were rolls never cited with roll_reference?); did the writer ever reject a commit for unaccounted rolls; what were the odds (compute success probability for typical value/difficulty pairs under 2d6 + stat x2 vs 7 + opp x2 with the bands +4 critical, +1..+3 clean, 0 cost, -1..-3 partial, <=-4 failure); were stakes declared before rolling; did failures have consequences; the full-check warnings early_stage_power_spike/inflation and stat_budget_exceeded; and the Player directive on NPC stat scale (D-002). Compare with the previous game where 1d2 dice could not fail.` },
  { key: 'memory-and-records', prompt: `Audit memory, records and continuity machinery.
Look at: distill cadence (57 commit-distill calls; profile cold_distill_policy scene_checkpoint_or_3_durable) and what each distill costs in time (turns.jsonl wait_s for turns with a distill vs without); state file sizes in ${A.campaign} (session_log.md, knowledge_boundaries.md, threads.md, character notes) compared with the previous game (session_log 975 KB, knowledge_boundaries 287 KB, 22 stacked sections in one note); whether notes have ## Core and Depth sections and are current; staleness warnings in check_full.json; why the boundary curator never launched (runtime setting, distill findings, skill text); directives.md and glossary.md use; the scene capsule (capsule_state.json, capsule sizes in turns.jsonl, sample capsules in the transcript: grep hook_additional_context) and whether it carried the right cast; and recovery after each compaction (turns T22, T55, T67, T132, T213 and the 3 turns after each: any lost or changed facts?).` },
  { key: 'language-and-presentation', prompt: `Audit presentation quality with numbers.
Use ${A.campaign}\\.repog-runtime\\lint_history.jsonl (188 linted replies; per-reply rule counts; rates by thirds: repetition 6%/22%/16%, pc_authoring 3%/8%/13%, restatement 0/2%/11%, avoid_phrase 3-6%, meta_leak 2-6%) and compare with the previous game's baseline: 'bir an' in 30-46% of replies, restating openings in 28-58% of Opus replies, language complaints about 1-3%, English status lines leaked several times. Count 'bir an', negated descriptions ('-miyor ama'), day numbers in prose, restating openings and GM-authored Player speech yourself over all play replies (T66-T251) from turns.jsonl texts, and check whether the lint's findings changed later replies (look at capsule notes in the segments). Also check whether any text the Player saw was out of fiction during play (progress notes, English, file names, tool talk).` },
  { key: 'speed-and-cost', prompt: `Audit speed and cost.
From turns.jsonl compute for play turns T66-T251: wait_s median/p75/p90, by turn type (with distill, with roll, with image generation, OOC, plain), output tokens and thinking time per turn, the Player's gap between turns, and the turns over 120 s with their causes (read them). Compare with the previous game's baseline: Opus medium 37 s median early, 63 s at high context, recovery turns after compaction 22-76 s, about 1.39M input tokens per durable turn. Also measure Session 0 (T1-T65): total wall time, model time, number of helper errors and retries, and what made it slow.` },
]
const auditTask = (a) => () => agent(`${CONTEXT}\n\n${a.prompt}\nReturn concrete findings with evidence and a recommendation each.`, { label: `audit:${a.key}`, phase: 'Audit', schema: AUDIT_SCHEMA })

const policyTask = () => agent(
  `Research, from official published sources only, what Anthropic's rules say about: sexual content (including fiction, roleplay and implied content), sexual violence and coercion, content involving minors, graphic violence; how violations are detected and enforced (refusals, safety classifiers, warnings, account restriction or suspension, appeals) for claude.ai consumer plans, the Claude desktop app, and Claude Code; and whether anything distinguishes adult creative writing. Start from https://www.anthropic.com/legal/aup and the Anthropic support center (support.claude.com) articles on usage policy enforcement, account suspension and safety warnings; also Anthropic's consumer terms. Then check OpenAI's usage policies for image generation (Codex CLI image generation was used here to draw adult characters with body-shape details). Use WebSearch and WebFetch. Quote exactly and give URLs; if a page cannot be fetched say so; never guess what a policy says. Today is ${A.today}.`,
  { label: 'policy-research', phase: 'Policy', schema: POLICY_SCHEMA })

phase('Read')
log(`Reading ${A.segments.length} segments while ${AUDITS.length} audits and the policy research run`)
const [readResults, auditResults, policy] = await parallel([
  () => parallel(A.segments.map(readerTask)),
  () => parallel(AUDITS.map(auditTask)),
  policyTask,
])
const readers = (readResults || []).filter(Boolean)
const audits = (auditResults || []).filter(Boolean)
log(`Readers returned ${readers.length}/${A.segments.length}; audits ${audits.length}/${AUDITS.length}; policy ${policy ? 'ok' : 'missing'}`)

const allIssues = readers.flatMap((r, i) => (r.issues || []).map(x => ({ ...x, segment: A.segments[i] ? A.segments[i].file : '?' })))
const allContent = readers.flatMap(r => r.content || []).sort((a, b) => a.turn - b.turn)
const allInterventions = readers.flatMap(r => r.interventions || []).sort((a, b) => a.turn - b.turn)
const allFeatures = readers.flatMap(r => r.features || [])
const allWins = readers.flatMap(r => r.wins || [])
const allInnovations = readers.flatMap(r => r.innovations || [])
log(`${allIssues.length} issues, ${allContent.length} content moments, ${allInterventions.length} interventions, ${allWins.length} wins`)

// ---------- Phase 2: cluster + verify issues, and the content panel, in parallel ----------
const verifyIssues = async () => {
  phase('Verify')
  const clustered = await agent(
    `${CONTEXT}\n\nMerge these issue reports from ${readers.length} segment readers into distinct clusters. One cluster per underlying problem (the same defect recurring across turns is one cluster with all its turns). Keep severity as the highest justified one; drop pure duplicates; keep low-severity clusters too but do not inflate them. Issues JSON:\n${JSON.stringify(allIssues)}`,
    { label: 'cluster-issues', phase: 'Verify', schema: CLUSTER_SCHEMA })
  const clusters = (clustered && clustered.clusters) || []
  const toVerify = clusters.filter(c => c.severity !== 'low')
  const lows = clusters.filter(c => c.severity === 'low')
  log(`${clusters.length} clusters; verifying ${toVerify.length} medium/high, keeping ${lows.length} low unverified`)
  const verified = await pipeline(toVerify, (c) => {
    const n = c.severity === 'high' ? 3 : 2
    const lenses = ['Re-read the cited turns in the segment files and decide whether the defect really happened as described.',
      'Look for counter-evidence: a later turn, a state file, a Player instruction or a directive that explains or excuses it, or a misreading by the reader.',
      'Trace the root cause: model behavior, plugin instructions, engine code, the host app, the Player\'s own preference, or campaign setup; check the plugin text or code if needed.']
    return parallel(Array.from({ length: n }, (_, k) => () => agent(
      `${CONTEXT}\n\nAdversarially check this claimed defect. ${lenses[k]} Default to confirmed=false when the evidence is weak or you could not find the turns.\nClaim: ${JSON.stringify(c)}`,
      { label: `verify:${c.id}:${k + 1}`, phase: 'Verify', schema: VERDICT_SCHEMA })))
      .then(vs => {
        const votes = vs.filter(Boolean)
        const yes = votes.filter(v => v.confirmed)
        return { ...c, votes: votes.length, confirmations: yes.length, confirmed: yes.length * 2 > votes.length || (votes.length === 2 && yes.length === 2),
          root_causes: votes.map(v => v.root_cause), fixes: yes.map(v => v.fix), corrected: (yes[0] || votes[0] || {}).corrected_description }
      })
  })
  return { clusters, verified: verified.filter(Boolean), lows }
}

const contentPanel = async () => {
  phase('Content')
  const LENSES = [
    { key: 'policy', text: 'Policy-compliance lens: map each flagged moment to the published rules in the policy research; decide whether the produced text (not the request) stayed within them. Read every flagged turn yourself in the segment files; do not rely on the reader labels.' },
    { key: 'enforcement', text: 'Enforcement-risk lens: given the published enforcement mechanisms and what actually happened here (no refusals, no policy errors in the whole transcript, implication-only setting, the abandoned goblin premise, Player requests for more explicitness, image generation of adult characters through Codex), estimate realistically how likely a user doing similar play is to get warnings, restrictions or a suspended account, and what behaviors raise or lower that risk. Separate what the sources say from your own judgment, and say plainly what cannot be known from outside.' },
    { key: 'product', text: 'Product lens: what should RePoG change or tell users so they stay within policy without ruining dark or romantic fiction: Session 0 content questions and defaults, wording in boundaries.md, the GM\'s handling of explicitness requests, image generation guidance, and a short user-facing warning. Write user_warning_tr and user_warning_en (each at most 120 words, calm and factual, no legal claims beyond the sources).' },
  ]
  if (!allContent.length) log('No content moments were flagged; the panel still checks the abandoned goblin start')
  const judgments = await parallel(LENSES.map(l => () => agent(
    `${CONTEXT}\n\n${l.text}\n\nPolicy research (from official sources):\n${JSON.stringify(policy)}\n\nFlagged content moments from the readers:\n${JSON.stringify(allContent)}\n\nAlso read T1-T12 (the goblin premise and the GM's limit explanation) in seg_01.md. Quote nothing graphic.`,
    { label: `content:${l.key}`, phase: 'Content', schema: JUDGE_SCHEMA })))
  return LENSES.map((l, i) => ({ lens: l.key, ...(judgments[i] || { missing: true }) }))
}

const [issueResult, contentResult] = await parallel([verifyIssues, contentPanel])
const confirmed = ((issueResult && issueResult.verified) || []).filter(c => c.confirmed)
const refuted = ((issueResult && issueResult.verified) || []).filter(c => !c.confirmed)
log(`${confirmed.length} issue clusters confirmed, ${refuted.length} refuted`)

// ---------- Phase 3: report ----------
phase('Report')
const bundle = {
  quant_note: 'see quant.json and turns.jsonl',
  baseline_previous_game: A.baseline,
  segment_summaries: readers.map((r, i) => ({ segment: A.segments[i], summary: r.segment_summary })),
  audits,
  confirmed_issues: confirmed,
  refuted_issues: refuted.map(c => ({ id: c.id, title: c.title, turns: c.turns })),
  low_issues: (issueResult && issueResult.lows) || [],
  wins: allWins,
  interventions: allInterventions,
  features: allFeatures,
  innovations: allInnovations,
  content_moments: allContent,
  content_panel: contentResult,
  policy,
}
const report = await agent(
  `${CONTEXT}

Write the final review report in Turkish (natural Turkish, plain and direct; English technical names may stay in backticks) to ${A.report_md} with the Write tool. The reader is the RePoG maintainer, a Turkish speaker who played this game. Structure:
1. Kısa sonuç: 5-8 madde, en önemli bulgular.
2. Sayılarla oyun: Session 0 ve oyun; önceki oyunla karşılaştırma tablosu (bekleme süresi, OOC oranı, tikler, restating, zarlar, kayıt boyutları, sıkıştırma sonrası hatalar).
3. 0.3.0 özellikleri tek tek: çalıştı / kısmen / çalışmadı / hiç kullanılmadı, kanıt ve kök neden.
4. Doğrulanmış sorunlar: önem sırasına göre, tur numaralarıyla, kök neden ve önerilen düzeltme. Reddedilen iddiaları sonda kısaca belirt.
5. İşe yarayanlar ve oyuncunun getirdiği yenilikler (ürüne alınmaya aday olanlar ayrı).
6. Oyuncu müdahaleleri: türlerine ve nedenlerine göre dağılım, öne çıkan örnekler.
7. İçerik ve politika riski: kaynakların ne dediği (alıntı + URL), bu oyunda ne oldu, üç bakış açısının değerlendirmesi, dürüst risk tahmini ve bilinemeyenler, kullanıcıya önerilen uyarı metni (TR ve EN).
8. Önerilen değişiklikler: öncelik sırasıyla, her biri için hangi dosya veya bileşen.
Keep every claim tied to evidence (turn numbers, file names, counts). No graphic quotes.
Also write the material's \`interventions\` array, unchanged, as JSON to ${A.workdir}\\interventions.json (compare.py counts its model_error items).
Then return a 10-line plain summary of the report as your final text.

Material (JSON):
${JSON.stringify(bundle)}`,
  { label: 'write-report', phase: 'Report' })

return { report_summary: report, confirmed: confirmed.length, refuted: refuted.length, clusters: issueResult ? issueResult.clusters.length : 0, content_moments: allContent.length, readers: readers.length, audits: audits.length }
