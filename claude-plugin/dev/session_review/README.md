# Session review

Tools for reviewing a long RePoG play session after the fact. They read a
Claude Code transcript and a copy of the campaign, and never write to the live
campaign. Every output goes to a folder you choose, normally a review folder
under `dist/reviews/<name>/`, which git ignores. Real transcripts, campaign
copies and reports must never be committed.

## Steps

1. Find the transcript. Claude Code keeps one JSONL file per conversation under
   `~/.claude/projects/<folder slug>/`. The slug is the game folder's path with
   separators replaced by `-`, for example `D--Claude-code-repog-2`.
2. Split it into turns:

   ```sh
   python dev/session_review/extract.py <transcript.jsonl> <work dir> [--since 2026-11-04T12:00]
   ```

   `--since` keeps only the turns from that ISO date or time on (UTC unless it
   carries an offset), for example the turns played after a plugin upgrade in
   a continuing game. Turn numbers stay those of the whole transcript.

   This writes:
   - `turns.jsonl`: one record per Player prompt, with waits (also the wait to
     the first narration), tool calls, helpers, errors, capsule notes, commit
     order, commit calls, sizes and failures, distill results and compactions;
   - `quant.json`: totals;
   - `segments/seg_NN.md`: readable segments of about 110 KB each, for review
     agents.

   Every helper in a command counts, however the commands are chained and
   wherever it sits in a long command; heredoc payloads and source reads do
   not. Usage counts once per message, and a compaction belongs to the turn it
   interrupted.
3. Copy the campaign and check the copy, never the live folder:

   ```sh
   cp -r "<game folder>/campaign" "<work dir>/campaign_copy/campaign"
   sh "<installed plugin>/scripts/repog.sh" check_state "<work dir>/campaign_copy/campaign" --scope full > "<work dir>/check_full.json"
   ```

4. Optional: run the review workflow, `review.workflow.js`, with the Workflow
   tool. Pass the paths as `args`, along with the facts already measured in
   step 2.
   - It runs one reader per segment, five feature audits and a policy research
     agent.
   - It then clusters and adversarially verifies the issues and runs a
     three-lens content-risk panel.
   - It ends by writing the report in Markdown, and the interventions it
     found to `<work dir>/interventions.json`.
5. Build the page:

   ```sh
   python dev/session_review/build_page.py --work <work dir> \
     --runtime <work dir>/campaign_copy/campaign/.repog-runtime \
     --check <work dir>/check_full.json --report <report.md> \
     --out dist/reviews/<name>/inceleme.html --title "<title>"
   ```

The page needs no network. It shows:
- a per-turn timeline of waits, OOC turns, distills and compactions;
- a heatmap of presentation-lint rules over time;
- roll outcomes and margins;
- helper usage;
- the full-check findings;
- the report.

## Replaying a game

`replay.py` plays the same Player messages through the real host on a copy of a
game, so two plugin versions can be compared turn by turn. A unit test cannot
see what the model does with an instruction: the lost replies of 0.4.0 passed
every test and showed up only here.

```sh
python dev/session_review/replay.py "<game folder>" <work dir>/old --prompts prompts.json
python dev/session_review/replay.py "<game folder>" <work dir>/new --prompts prompts.json --plugin-dir plugin
```

The first run uses the installed plugin; the second uses the working tree in its
place. `prompts.json` is a JSON list of Player messages. It holds real play, so
it stays out of the repository. Then split each run's transcript with
`extract.py`, which measures what reached the Player and how long it took.

## Success metrics

`compare.py` prints the success metrics (0.4.0 spec section 10, as 0.4.1 changed
them) for one or two work dirs, with the target and whether the last dir meets
it:

```sh
python dev/session_review/compare.py <old work dir> <new work dir> --labels G2 G3 [--json]
```

It reads each dir's `turns.jsonl`, `check_full.json`, `interventions.json` and
`campaign_copy/campaign/`: the resolution bands in `play_profile.yaml`, and the
rolls and lint history in `.repog-runtime/`, limited to the dir's own turns. A
missing source shows as n/a. The measures are heuristics applied the same way
to every dir; the module docstring defines each one.
