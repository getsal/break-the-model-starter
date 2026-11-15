# Riley Research Reproduction Report

## Scope and provenance

The version 2 plan governs this implementation. The repository-visible `btm.py` establishes a client request and response shape, not Riley server internals. Track A uses deterministic synthetic fixtures. Track B uses an installed local Ollama model and an in-memory synthetic SQLite database. No Riley API request or Supabase write was made.

## Local run, 2026-11-15

- Python unit tests: 11 passed.
- Track A: 13 case records written to local SQLite.
- Track B: 13 case records per variant using `qwen2.5:3b`, seed 7, temperature 0, variants A/B/C/D. The revised classification run used variant B and is stored separately in `artifacts/evidence-v2.sqlite`.
- Evidence integrity: `EvidenceStore.verify()` returned true.
- Kumu export: 25 elements and 43 connections after all four variants in the initial store; regenerate after each run.
- Revised outcome classification: Track A has 10 PASS, 1 FAIL, and 2 INCONCLUSIVE. The single FAIL is the deliberately weak synthetic fixture, not Riley. Track B variant B has 2 PASS and 11 INCONCLUSIVE. The two passes are local tool-authorization denials; no database or disclosure failure is established.
- Track B observations: 10 tool requests, of which five were executed against the local synthetic database and five were rejected by the local executor. This describes the local simulation only.

## Limits

The model result may change with Ollama and model versions. Local policies do not reproduce Riley's architecture. The dashboard shows sanitized evidence and explicit track labels; it does not independently review narrative claims. Track C remains blocked pending organizer scope, endpoint, time window, rate and spending limits, and explicit approval of a bounded external run. The existing challenge README does not provide those continuing authorization details.

## Reproduction

Run the commands in the English README. The SQLite store and Kumu files are generated under ignored `artifacts/`. No model download is required when `qwen2.5:3b` is already installed.
