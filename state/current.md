# Current State

## Active Task
Maintain Riley Research Platform v2 and track ORCA-0–8 work in GitHub Issues.

## Current Status
Implemented and integrated ORCA-0/1/2/4 plus local simulation, gated remote adapter, dashboard, and expanded Kumu export. Track A produced 13 revised fixture records; Track B ran 13 cases per A/B/C/D configuration. Sixteen unit tests pass; evidence integrity verifies. Revised classifications are 10 PASS, 1 deliberately weak synthetic FAIL, and 2 INCONCLUSIVE for Track A; 2 local authorization PASS and 11 INCONCLUSIVE for Track B variant B. Track C made three bounded POST requests, with two metadata-only inconclusive probe records.

## Next Action
Address the open tasks in Issues #1–#9, starting with independent case-specific scoring and a clean-environment reproduction. Keep additional Track C execution on hold until current organizer terms are confirmed.

## Blockers
The user authorized Track C and provided the host; connectivity and three bounded POST requests succeeded. Continuing organizer time-window and rate terms remain unverified, and actual provider charges are unavailable. GitHub Issues are enabled; ORCA-0–8 are Issues #1–#9 with dependency and deliverable links. The implementation branch is published to origin. Riley internals and Supabase private schema permissions remain unknown.

## Relevant Files
- docs/Orca Implementation Plan v2.md
- orca/ORCA-0-architecture.md
- btm.py
- riley_research/
- research/
- docs/reproduction-report.md
- GitHub Issues #1–#9 in getsal/break-the-model-starter

## Handover Note
Track C metadata observations are inconclusive and do not establish a Riley vulnerability. Do not broaden live tests without current organizer scope.
