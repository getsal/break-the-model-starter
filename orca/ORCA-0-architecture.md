# ORCA-0: Riley Architecture and Trust Boundaries

**Status:** Initial architecture register; client-side findings only  
**Specification:** `docs/Orca Implementation Plan v2.md`  
**Scope:** Repository-visible contract and safe research design. No live Riley requests, Supabase access, or credential inspection were performed.

## Evidence labels

- **VERIFIED**: independently confirmed in accessible source/configuration or direct evidence.
- **OBSERVED**: directly visible in an authorized interaction; internal behavior remains unknown.
- **CLAIMED**: stated by documentation or a participant without independent confirmation.
- **HYPOTHESIS**: plausible design interpretation requiring evidence.
- **CONTRADICTED**: inconsistent with another supported observation.

## Architecture register

| Component | Evidence | Current understanding | What remains unknown |
|---|---|---|---|
| Client application | VERIFIED | `btm.py` loads local dotenv configuration, selects a provider from credential prefixes, and calls the API. | Whether all challenge clients use the same implementation. |
| API gateway | VERIFIED (interface only) | Client targets configured `API_URL`; it issues `GET /models` and `POST /chat`. This confirms the client contract, not gateway internals. | Hosting, routing, request validation, network controls, and service topology. |
| Authentication/session | VERIFIED (client request shape) | POST body includes `participant` and `team_token`; `X-API-Key` is sent when a key is present. A generated/reused `conversation_id` identifies the conversation. | Which field authenticates, authorization semantics, token lifecycle, session isolation, and server-side checks. |
| Model selection | VERIFIED (client behavior) | `GET /models` returns a `models` collection; client filters by provider and sorts by tier. POST includes selected `model`. | Available server-side models, model versions, routing, system/developer instructions, and inference settings. |
| Instructions and prompt assembly | HYPOTHESIS | A Riley-like assistant likely combines trusted instructions with user messages and possibly conversation history. | Exact prompts, ordering, isolation, untrusted-input handling, and prompt construction. |
| Tool definitions and tool-call output | VERIFIED (response contract) | Client reads optional `tool_calls` and prints each call's `name`. | Tool schemas, whether displayed calls were executed, argument validation, executor identity, and error behavior. |
| Tool executor | HYPOTHESIS | A server component may execute model-requested tools. | Whether it exists, its permissions, validation, network access, and separation from the model runtime. |
| Query validation | HYPOTHESIS | Any query validation must be enforced outside model text generation to constitute an independent boundary. | Query language, validation rules, parameterization, authorization checks, and bypass behavior. |
| Database connection and permissions | CLAIMED | Challenge documentation describes Riley as able to read a fictional hospital database. This is a documentation claim, not proof of schema or access policy. | Database type, records, roles, grants, row-level policies, and whether tools can mutate data. No DB access was attempted. |
| Final response processing | VERIFIED (client contract) | Client expects `reply` and `turn_id`; it returns reply text and stores the turn ID in process state. | Server-side output filtering, redaction, provenance, and whether final text reflects actual tool results. |
| Logging/telemetry | VERIFIED (client behavior) | Existing `btm.py` appends timestamp, full request body, and response JSON to `logs/my_attempts.jsonl`. | Server-side retention, access, redaction, and telemetry controls. The existing format can contain participant/team values; the research harness must not reuse it. |

## Client-visible request/response flow

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
                     ├─ tool_calls names displayed by client
                     ├─ reply returned to caller
                     └─ request + response appended to local attempt log
```

This flow describes only behavior visible in the checked-in client. It does not establish that tool calls execute, that database access occurs, or that any information is disclosed.

## Trust-boundary map

```text
[Research operator]
       │ synthetic test case only
       ▼
[Local runner / client] ── external network boundary ──> [Riley API / gateway]
       │                                                   │
       │ local evidence store                              ├─ authentication/session boundary
       │                                                   ├─ prompt assembly boundary
       │                                                   ├─ LLM boundary
       │                                                   ├─ tool request boundary
       │                                                   ├─ tool executor boundary
       │                                                   ├─ query validation boundary
       │                                                   ├─ database authorization boundary
       │                                                   └─ response filtering boundary
       ▼
[Sanitized local evidence]
```

The gateway-to-model and model-to-tool/database boundaries are design questions, not verified internal topology. Track A and Track B must implement these boundaries explicitly and label their results as simulations. Track C remains disabled until its authorization and bounded-execution prerequisites are met.

## Independently enforceable versus model-dependent controls

| Boundary/control | Independent enforcement possible? | Current evidence |
|---|---|---|
| Runner blocks network by default | Yes, in our harness | Required design; implementation not yet present. |
| Synthetic-only test fixtures | Yes, in our repository | Required design; verify fixtures during implementation. |
| Request count, rate, cancellation, budget | Yes, in our runner | Required design; no live execution authorized here. |
| API authentication and participant scope | Must be server enforced | Client fields observed; enforcement unverified. |
| Instruction hierarchy and refusal | No, if only expressed in prompts | Internal prompts unavailable; treat as model-dependent until tested. |
| Tool name/argument validation | Yes, in executor | Executor and its rules unverified. |
| Database least privilege / row filtering | Yes, in database policy | No database configuration inspected; status unknown. |
| Final response redaction | Potentially, in server middleware | No evidence of such middleware. |
| Evidence-log secret exclusion | Yes, in our harness | Existing client logger stores full request/response; do not reuse. |

## ORCA-0 interface decisions for implementation

1. Define a transport interface that accepts the client-shaped operation but defaults to an in-process deterministic Mock. No network-capable adapter is constructed by default.
2. Keep the Riley HTTP adapter isolated; prohibit live calls until the Track C gate is explicitly satisfied. This work does not enable Track C.
3. Represent model/tool-call intent, executor acceptance, database outcome, and final disclosure as separate events and evaluation dimensions.
4. Store expected and observed outputs separately. Keep assistant reply, tool-call display, and actual tool response distinct; a displayed call is not evidence of execution.
5. Store only synthetic, sanitized evidence. Never persist API keys, team tokens, environment dumps, or full authenticated request bodies.
6. Treat database permissions and internal Riley architecture as unknown until independently verified; do not infer them from assistant responses.

## Open questions and blockers

- The client contract does not reveal authentication or authorization enforcement.
- Riley's model, prompt assembly, tool schema/executor, query validation, database grants/RLS, output filters, and server logging are not accessible from the checked-in client.
- Supabase private experiment schema and permissions were not inspected; no Supabase operation is part of this deliverable.
- Post-hackathon Track C authorization, endpoint scope, time window, rate limits, and spending limits remain unconfirmed. Live testing is blocked.
- No attempt was made to connect to Riley or inspect credentials.

## Review checklist

- [ ] Confirm common transport, case, event, and evidence interfaces before parallel ORCA work.
- [ ] Ensure network is unreachable from the default Track A runner.
- [ ] Ensure positive, negative, and inconclusive outcomes are independently reproducible.
- [ ] Ensure tool-call intent is never scored as execution or disclosure by itself.
- [ ] Ensure logs contain no credentials or real personal data.
- [ ] Keep Track C disabled until all authorization and execution gates are satisfied.
