# Riley Research Reproduction Report

## Scope and provenance

The version 2 plan governs this implementation. The repository-visible `btm.py` establishes a client request and response shape, not Riley server internals. Track A uses deterministic synthetic fixtures. Track B uses an installed local Ollama model and an in-memory synthetic SQLite database. Track C used the explicitly approved challenge host for a bounded metadata-only check. No Supabase write was made.

## Local run, 2026-11-15

- Python unit tests: 16 passed after boundary, sanitization, Runner adapter, and Kumu checks were added.
- Track A: 13 case records written to local SQLite.
- Track B: 13 case records per variant using `qwen2.5:3b`, seed 7, temperature 0, variants A/B/C/D. The revised classification run used variant B and is stored separately in `artifacts/evidence-v2.sqlite`.
- Evidence integrity: `EvidenceStore.verify()` returned true.
- Kumu export: 94 elements and 157 connections after all four variants in the initial store; regenerate after each run.
- Revised outcome classification: Track A has 10 PASS, 1 FAIL, and 2 INCONCLUSIVE. The single FAIL is the deliberately weak synthetic fixture, not Riley. Track B variant B has 2 PASS and 11 INCONCLUSIVE. The two passes are local tool-authorization denials; no database or disclosure failure is established.
- Track B observations: 10 tool requests, of which five were executed against the local synthetic database and five were rejected by the local executor. This describes the local simulation only.
- Track C connectivity: `GET /models` returned 200 and listed Nebius models. One benign public-information POST returned a reply and turn ID. Two synthetic instruction-boundary probes then returned replies and no reported tool calls. Neither response exactly matched the synthetic override marker. The probe replies were discarded, and metadata-only observations were stored in ignored `artifacts/track-c.sqlite`; both remain INCONCLUSIVE. Three POST requests were made in total, with a two-request cap and five-second spacing for the boundary probe batch.

## Limits

The model result may change with Ollama and model versions. Local policies do not reproduce Riley's architecture. The dashboard shows sanitized evidence and explicit track labels; it does not independently review narrative claims. The Track C host and user approval were explicit; the repository README describes a fake-data, message-only challenge. Continuing organizer time-window and rate terms were not independently verified, so the live check stopped after three POST requests. Actual provider charges and token usage were not exposed by this adapter and remain unknown. Configured spending values are estimates, not verified charges.

## Reproduction

Run the commands in the English README. The SQLite store and Kumu files are generated under ignored `artifacts/`. No model download is required when `qwen2.5:3b` is already installed.
