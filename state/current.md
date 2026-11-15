# Current State

## Active Task
Run bounded Track C experiments against the user-authorized official Riley challenge environment and integrate evidence.

## Current Status
Implemented and integrated the Track A/B base plus a bounded Track C batch. Track A has 13 fixture records. Track B has 59 local records, including seven same-prompt comparisons. Track C has 11 stored trial records: nine from eight new cases (4 PASS, 0 FAIL, 5 INCONCLUSIVE) plus two earlier inconclusive probes. The cumulative workspace POST count is 12, including one earlier benign request without a trial record. Evidence integrity verifies.

## Next Action
Investigate TC-001 reported tool-call arguments/execution and the TC-007 tool-schema claim only if an authorized observation path becomes available. Continue ORCA-0–8 open work without treating model claims as verified internals.

## Blockers
The user confirmed organizer permission and prioritized Track C at the specified official host. The nine-request batch used at least eight-second spacing and a configured $0.045 estimate under a $0.06 ceiling. Current event time window and rate terms remain unstated; actual provider charges and Riley executor/DB results are unavailable. Track C code and related Issues are published.

## Relevant Files
- docs/Orca Implementation Plan v2.md
- orca/ORCA-0-architecture.md
- btm.py
- riley_research/
- research/
- docs/reproduction-report.md
- GitHub Issues #1–#9 in getsal/break-the-model-starter

## Handover Note
Track C PASS results are limited to observable model or tool-invocation behavior for exact synthetic prompts. The TC-001 reported tool call does not establish execution or DB access. Do not infer a Riley vulnerability from current evidence.
