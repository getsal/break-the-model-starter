
## 2026-11-15 — ORCA-0 architecture register
- Task: Create ORCA-0 Riley architecture and trust-boundary Markdown from the approved v2 plan.
- Result: Added a client-visible architecture register, request/response flow, trust-boundary map, enforcement comparison, interface decisions, and open questions. Evidence labels distinguish verified behavior, documentation claims, hypotheses, and unknowns.
- Files changed: `orca/ORCA-0-architecture.md`, `state/current.md`, `logs/worklog.md`.
- Next action: Review and commit this scoped deliverable.
- Blockers: Track C authorization and internal Riley/Supabase configuration remain unverified; no external access was attempted.

## 2026-11-15 — V2 integration and local experiments
- Task: Integrate ORCA worktrees and implement Track B, gated Track C adapter, dashboard, Kumu export, and reproduction documentation.
- Result: Integrated ORCA-1/2/4 commits; ran 13 Track A and 13 Track B synthetic cases, verified SQLite evidence hash chain, and passed 10 unit tests. The 26 recorded outcomes remain inconclusive rather than inferred pass/fail findings.
- Files changed: `riley_research/`, `research/`, `tests/`, `.gitignore`, `README.md`, `docs/reproduction-report.md`, `state/current.md`, `logs/worklog.md`.
- Next action: Review and commit integration; obtain continuing organizer scope before any Track C call, then add case-specific independent evaluation criteria.
- Blockers: Track C authorization details unavailable; Supabase schema not verified. No Riley or Supabase access occurred.

## 2026-11-15 — Bounded Track C check
- Task: Verify the user-approved Riley host using the existing client contract without exposing credentials.
- Result: `/models` returned 200; one benign POST and two synthetic instruction probes returned replies. The probes reported no tool calls and did not exactly match the override marker. Metadata-only records were stored in ignored local SQLite and verified; results remain INCONCLUSIVE.
- Files changed: `riley_research/remote.py`, `docs/reproduction-report.md`, `state/current.md`, `logs/worklog.md`.
- Next action: Confirm current organizer time-window and rate terms before further live testing; continue offline refinement.
- Blockers: Actual provider charges unavailable; organizer's current continuing terms not independently confirmed. GitHub Issues are disabled for this repository.

## 2026-11-15 — Final offline integration checks
- Task: Integrate bounded Track B Runner adapter, expanded Kumu graph, and evaluator boundary tests.
- Result: Sixteen unit tests pass, evidence integrity verifies, and Kumu export produces 94 elements and 157 connections from the initial four-variant store. Fixed SQLite connection cleanup.
- Files changed: `riley_research/local_adapter.py`, `riley_research/kumu.py`, `riley_research/evidence.py`, `tests/`, `docs/reproduction-report.md`, `state/current.md`, `logs/worklog.md`.
- Next action: Review limitations and continue case-specific scoring and current Track C terms when available.
- Blockers: GitHub Issues disabled; actual Riley provider charges and current organizer time-window/rate terms unavailable.

## 2026-11-15 — ORCA issue tracking restored
- Task: Recheck GitHub Issues, authentication, and repository permission; create V2 work-package Issues.
- Result: `getsal/break-the-model-starter` reports Issues enabled and ADMIN permission. Created ORCA-0–8 as Issues #1–#9, each with completed items, remaining work, dependency links, and local deliverable commits.
- Files changed: `state/current.md`, `logs/worklog.md`; GitHub Issues #1–#9.
- Next action: Re-run all tests, review the branch for secret exposure, and publish the current branch so commit references resolve on GitHub.
- Blockers: Current organizer Track C terms and actual provider costs remain unverified; no additional Track C requests were sent.

## 2026-11-15 — Post-Issue validation
- Task: Re-run integrated validation before publishing the branch.
- Result: All 16 Python unit tests passed; compileall and diff checks passed; both local evidence stores verified; Kumu export produced 94 elements and 157 connections. No Track C request was made.
- Files changed: `logs/worklog.md`.
- Next action: Commit state and publish the branch, then verify Issue commit references.
- Blockers: Track C continuing terms remain unverified.
