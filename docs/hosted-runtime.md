# Hosted Agent Seat Runtime

The hosted runtime lets a juror open a real RePoG campaign without leaving a
developer computer or Codex process running. OpenAI GPT-5.6 Luna runs through
Amazon Bedrock in `us-east-1`; Sites remains the same-origin WebMCP surface and
safe projection mirror, while S3 plus DynamoDB own the hosted campaign.

## Runtime contract

- A session lasts at most 20 turns or 90 minutes and is retained for 7 days.
- The first human or Agent Seat intent opens one 15-second Step Functions
  coordination window. Both intents are resolved in one causal beat.
- A missing intent remains `null`. The runtime never invents an Agent Seat move.
- The Agent Seat intent is a proposal. The character may cooperate, refuse,
  negotiate, or choose a character-consistent third action.
- Luna is the only configured model. There is no silent provider or model
  fallback. Atomic reservations cap model spend at $1 per session and $10 per
  UTC day.
- Only `tools/rpg_state.py commit-durable` and `commit-checkpoint` may mutate
  campaign truth. A failed durable commit suppresses narration and leaves the
  session in `resolution_failed`.
- Sites-to-runtime requests are timestamped and HMAC signed. Nonces are stored
  conditionally in DynamoDB so a signed request cannot be replayed.

## Golden campaign gate

Prepared mode requires two reviewed artifacts:

1. `workspace.zip`: a complete public RePoG workspace containing a campaign
   that passes `python tools/verify_workspace.py . --scope full --json` and has
   a ready Tier 3 Agent Seat.
2. `bootstrap.json`: the matching validated Agent Session Pack and initial
   Agent Turn Brief. It has exactly `{ "manifest": ..., "initial_turn": ... }`.

The deploy script requires both paths and uploads them to the versioned,
private S3 `golden/` prefix. This prevents a fixture or unfinished template from
silently becoming the jury campaign. Generate the reviewed pair from the
canonical Git commit with:

```powershell
python tools/build_jury_bundle.py --json
```

The generated `workspace.zip` is intentionally rootless for Lambda extraction.
The ordinary downloadable RePoG distribution remains a separate package.

## Deploy

From the repository root, create a 32-byte or longer random shared secret and
run:

```powershell
.\infra\aws\deploy.ps1 `
  -SharedSecret $secret `
  -GoldenWorkspaceZip C:\path\to\workspace.zip `
  -GoldenBootstrap C:\path\to\bootstrap.json
```

The script builds and scans the Lambda image in ECR, deploys CloudFormation,
uploads the approved golden artifacts, and prints `RuntimeUrl`. Configure the
Sites deployment with `REPOG_RUNTIME_URL` and the same
`REPOG_RUNTIME_SHARED_SECRET`, apply the generated D1 migration, then publish.

When a local Docker engine is unavailable, `infra/aws/image-builder.yaml`
provides the equivalent credit-backed CodeBuild path. It consumes a source ZIP
from a private S3 build prefix and pushes the same Dockerfile to the immutable
ECR repository; no developer computer must remain online after the build.

Quick Forge starts from the same validated workspace shell, accepts a maximum
2,000-character premise, writes only under `campaign/`, configures exactly one
Tier 3 Agent Seat after explicit WebMCP opt-in, and must pass the full campaign
validator within the 180-second state-machine ceiling.
