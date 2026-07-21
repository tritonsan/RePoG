# Selective Structural Parallelism

RePoG can use supporting agents to reduce the wall-clock wait at a few large
semantic boundaries. This is optional orchestration inside the active agentic
tool, not a background service, API integration, or second narrative engine.

The coordinating agent remains the only campaign writer, revision owner,
knowledge/disclosure authority, and player-facing voice. Supporting agents
read a frozen evidence packet and return proposals for the coordinator to
review. When sub-agents are unavailable, the same lanes run serially.

Workers never write files, send external messages, publish, submit, or mutate
campaign/external state. An explicitly authorized research packet may permit
read-only web or supplied-source retrieval within its named scope; the
coordinator still decides what becomes campaign truth.

## Policies

The active RPG or Companion profile stores:

```yaml
performance:
  semantic_parallelism: selective_structural
  max_parallel_workers: 3
```

- `off`: lowest model usage; all work is serial.
- `selective_structural`: recommended for new workspaces; delegates only at
  measured heavy boundaries.
- `aggressive_structural`: uses lower workload thresholds and may consume more
  model allowance.

Quick materialization is always capped at two supporting agents. All other
boundaries are capped at three, even if the host tool permits more. Existing
profiles without these fields remain `off` for compatibility.

## Eligible Boundaries

- Session 0 materialization after final approval;
- research with at least two independent source domains;
- full distill with at least four cold targets across two authority families;
- scenario, arc, or campaign closure;
- World Voices batches containing at least three independent artifacts;
- exceptional travel/downtime with at least three genuinely due world domains;
- explicit Companion full review with at least four cold targets across two
  independent families.

Ordinary RPG turns, ordinary Companion exchanges, scene checkpoints, tools,
checks, snapshots, Dashboard/Atlas/View updates, and visual transactions stay
single-agent.

## Planning Ranges

These are hypotheses for planning and must not be presented as guarantees:

| Boundary | Possible wall-clock reduction | Possible usage increase |
| --- | ---: | ---: |
| Quick materialization | 20–35% | 15–40% |
| Standard/Deep materialization | 30–55% | 30–80% |
| Multi-domain research | 30–60% | 20–60% |
| Heavy full distill | 20–40% | 30–80% |
| Major closure | 25–45% | 40–100% |
| Three-document World Voices batch | 15–35% | 40–100% |

Sub-agents generally consume more tokens than a comparable single-agent run;
their benefit is parallel wall-clock progress on independent work. OpenAI's
current Codex guidance likewise recommends parallel agents for read-heavy
tasks and warns against overlapping write-heavy work:
[Codex sub-agents](https://learn.chatgpt.com/docs/agent-configuration/subagents.md).

## Benchmark Protocol

Compare serial `off` and `selective_structural` with the same model, reasoning
level, accepted Session 0 answers, starting revision, and fresh workspace copy.
Run each eligible scenario at least twice:

1. Quick RPG materialization;
2. Standard or Deep mixed-lens materialization;
3. Quick Companion materialization;
4. two-domain research;
5. heavy full distill;
6. arc closure, reward, and next-act preparation;
7. a three-artifact World Voices batch;
8. an ordinary RPG and Companion exchange as negative controls.

Record wall-clock time, surfaced model usage, worker count, tool calls, files
touched, final revision, validator findings, and the existing semantic quality
rubric. Keep a boundary enabled in `selective_structural` only when median
wall-clock time improves by at least 20%, validation does not regress, semantic
quality is not lower, and ordinary-turn time changes by no more than 5%.
