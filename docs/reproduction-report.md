# Riley Research Reproduction Report

## Scope and provenance

The version 2 plan governs this implementation. The repository-visible `btm.py` establishes a client request and response shape, not Riley server internals. Track A uses deterministic synthetic fixtures. Track B uses an installed local Ollama model and an in-memory synthetic SQLite database. No Riley API request or Supabase write was made.

## Local run, 2026-11-15

- Python unit tests: 10 passed.
- Track A: 13 case records written to local SQLite.
- Track B: 13 case records using `qwen2.5:3b`, seed 7, temperature 0, variant B.
- Evidence integrity: `EvidenceStore.verify()` returned true.
- Kumu export: 22 elements and 28 connections before Track B; regenerate after each run.
- Outcome classification: all 26 records are `INCONCLUSIVE`, because the current case-specific evaluator does not yet establish independent pass/fail conditions. These records must not be presented as successful attacks or confirmed security controls.
- Track B observations: 10 tool requests, of which five were executed against the local synthetic database and five were rejected by the local executor. This describes the local simulation only.

## Limits

The model result may change with Ollama and model versions. Local policies do not reproduce Riley's architecture. The dashboard shows sanitized evidence and explicit track labels; it does not independently review narrative claims. Track C remains blocked pending organizer scope, endpoint, time window, rate and spending limits, and explicit approval of a bounded external run. The existing challenge README does not provide those continuing authorization details.

## Reproduction

Run the commands in the English README. The SQLite store and Kumu files are generated under ignored `artifacts/`. No model download is required when `qwen2.5:3b` is already installed.
