# Current State

## Active Task
Hand off the staged official Riley campaign at the completed wave-01 boundary.

## Current Status
The 30-POST pilot and 50-POST wave-01 completed with no API errors. Campaign ledger: 80/300 additional POSTs, configured estimate $1.575/$30, actual charges unknown. Campaign evidence: 12 PASS, 0 FAIL, 68 INCONCLUSIVE, all 80 unique turn IDs and verified hashes. Historical workspace requests before this campaign: 12 POSTs. The combined Dashboard store has 13 A, 59 B, 91 C records; Kumu has 149 elements and 252 connections. No later wave was started.

## Next Action
Finish handoff validation, commit and publish the report/state, then stop API work. A later session should inspect the ledger and report before deciding whether to run prepared wave-02.

## Blockers
The user requested a Codex handoff; no further API batch should be started in this turn. Current event time window and rate terms remain unstated; actual provider charges and Riley executor/DB results are unavailable. Stop on API errors, connection refusal, or a discovered restriction.

## Relevant Files
- docs/Orca Implementation Plan v2.md
- orca/ORCA-0-architecture.md
- btm.py
- riley_research/
- research/
- docs/reproduction-report.md
- docs/track-c-campaign-report.md
- docs/track-c-campaign-handoff.md
- GitHub Issues #1–#9 in getsal/break-the-model-starter

## Handover Note
The campaign is at a clean batch boundary. Read `docs/track-c-campaign-handoff.md` before resuming. Track C PASS results are limited to observable model or tool-invocation behavior; TC-001 tool reports do not establish execution or DB access.
