# Riley Research Architecture and Trust Boundaries

**Status:** Repository-visible architecture register and evidence boundary.  
**Scope:** Checked-in client and harness behavior, plus explicitly labelled client-visible observations. It does not describe Riley server internals.

## Evidence labels

- **VERIFIED**: independently confirmed in accessible source, configuration, or local evidence.
- **OBSERVED**: directly visible in an authorized interaction; internal behavior remains unknown.
- **CLAIMED**: stated by documentation or a participant without independent confirmation.
- **HYPOTHESIS**: plausible design interpretation that requires evidence.

## Architecture register

| Component | Evidence | Current understanding | What remains unknown |
|---|---|---|---|
| Client application | VERIFIED | `btm.py` loads local dotenv configuration, selects a provider from credential prefixes, and calls the API. | Whether all challenge clients use the same implementation. |
| API gateway | VERIFIED (interface only) | The checked-in client targets configured `API_URL` and issues `GET /models` and `POST /chat`. | Hosting, routing, request validation, network controls, and service topology. |
| Authentication/session | VERIFIED (client request shape) | A POST includes `participant` and `team_token`; `X-API-Key` is sent when a key is present. A generated or reused `conversation_id` identifies the conversation. | Which field authenticates, authorization semantics, token lifecycle, session isolation, and server-side checks. |
| Model selection | VERIFIED (client behavior) | `GET /models` returns a `models` collection; the client filters by provider and sorts by tier. POST includes the selected `model`. | Current server-side model versions, routing, system/developer instructions, and inference settings. |
| Prompt assembly | HYPOTHESIS | A Riley-like assistant may combine trusted instructions, user messages, and conversation history. | Exact prompts, ordering, isolation, untrusted-input handling, and prompt construction. |
| Tool-call output | VERIFIED (response contract) | The client reads optional `tool_calls` and displays each call name. The research harness stores only sanitized tool-call summaries for campaign evidence. | Tool schemas, whether displayed calls execute, argument validation, executor identity, and error behavior. |
| Local executor and database | VERIFIED (Track A/B only) | The local harness separately records requested calls, executor decisions, observed local results, and replies. Track B uses a synthetic in-memory SQLite database. | Whether Riley has comparable components or policies. |
| Riley executor and database | HYPOTHESIS / CLAIMED | Challenge documentation describes a fictional hospital database; campaign responses can display tool calls. | Executor existence and permissions, query validation, database roles, row policies, tool results, and whether tools can mutate data. No server database access was attempted. |
| Final response processing | VERIFIED (client contract) | The client expects `reply` and `turn_id`; it returns reply text and retains the turn ID in process state. | Server-side output filtering, redaction, provenance, and whether final text reflects actual tool results. |
| Local logging and evidence | VERIFIED | `btm.py` appends full request and response JSON to `logs/my_attempts.jsonl`. The research harness instead writes sanitized, hashed records to ignored local SQLite stores. | Server-side retention, access, redaction, and telemetry controls. |

## Client-visible request and response flow

```text
Local client configuration
  ├─ API_URL ───────────────────────────────────────────────┐
  ├─ API_KEY ── X-API-Key header (when present)              │
  ├─ TEAM_CODE ── team_token field                           │
  └─ YOUR_NAME ── participant field                          │
                                                            ▼
                                                   Riley API (internals unknown)
GET /models ── models[] ── provider/tier filtering ── selected model
POST /chat {participant, team_token, model, conversation_id, message}
                                                            │
              response {reply, tool_calls?, turn_id} ◀───────┘
                     │
                     ├─ tool-call names displayed by client
                     ├─ reply returned to caller
                     └─ full request/response appended by btm.py
```

This flow establishes only checked-in client behavior. It does not establish tool execution, database access, or information disclosure.

## Research trust-boundary map

```text
[Research operator]
       │ synthetic test case
       ▼
[Local runner / client] ── external network boundary ──> [Riley API / gateway]
       │                                                   │
       │ sanitized local evidence                           ├─ authentication/session boundary
       ▼                                                   ├─ prompt assembly boundary
[Ignored SQLite evidence]                                  ├─ LLM boundary
                                                           ├─ tool request boundary
                                                           ├─ tool executor boundary
                                                           ├─ query validation boundary
                                                           ├─ database authorization boundary
                                                           └─ response filtering boundary
```

Gateway-to-model and model-to-tool/database topology are not verified. Track A and Track B implement explicit synthetic boundaries; their results are simulations. Track C is externally gated: its entry points require an explicit `--execute` flag and must only be used under separately verified authorization.

## Independently enforceable and model-dependent controls

| Boundary or control | Independent enforcement | Evidence |
|---|---|---|
| Network-free Track A | Yes, in the deterministic mock | VERIFIED: `riley_research.mock` never contacts a network. |
| Synthetic fixtures | Yes, in repository case definitions | VERIFIED: `research/` cases use fictional records. |
| Request count, rate, stop conditions, and estimated budget | Yes, in the campaign runner and persistent ledger | VERIFIED locally; actual provider charges and server outcomes remain unknown. |
| Sanitized, hashed local evidence | Yes, in the evidence store | VERIFIED: the evidence layer sanitizes records before append and verifies hashes. |
| API authentication and participant scope | Must be server-enforced | Client request fields are verified; enforcement is unverified. |
| Instruction hierarchy and refusal | Not independent if only expressed in prompts | Server prompts are unavailable; treat as model-dependent. |
| Tool and query validation | Yes, if enforced by the executor | Remote executor rules are unverified. |
| Database least privilege and row filtering | Yes, in database policy | Remote database configuration was not inspected. |
| Final response redaction | Potentially, in server middleware | Remote middleware is unverified. |

## Evidence limits

Campaign Runner records are sanitized and summarized: they do not retain complete authenticated requests or responses, credential values, raw tool-call arguments, tool results, or database results. A displayed tool call or model prose is therefore not evidence of executor acceptance, database access, or protected-data disclosure. The [campaign report](../reports/track-c-campaign-report.md), [286-attempt audit](../reports/track-c-audit-286.md), and [offline review](../reports/track-c-oracle-review.md) record the observed results and their limits.
