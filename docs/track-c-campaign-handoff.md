# Track C Campaign Handoff

## Current checkpoint

The user requested a handoff while `wave-01` was running. The wave finished cleanly; no later wave was started. The root agent was the only process authorized to send official Riley requests. The current campaign is paused at a batch boundary by user request, with no running API process.

- Branch: `getsal/feat-riley-research-platform`.
- Campaign manifests: `research/track_c_campaign_pilot-30.json`, `research/track_c_campaign_wave-01.json`; `wave-02`–`wave-06` are prepared but unexecuted.
- Persistent request ledger: `artifacts/campaign-ledger.sqlite` (ignored local file).
- Authoritative campaign evidence: `artifacts/campaign-evidence.sqlite` (ignored local file).
- Dashboard's combined evidence: `artifacts/evidence.sqlite` (ignored local file; contains earlier A/B/C records plus campaign records).
- Report: `docs/track-c-campaign-report.md`.

## Exact budget and evidence state

The ledger has **80 attempted and successful POST requests**, estimated **$1.575**. This campaign has a hard ceiling of 300 additional POST requests and a currently configured $30 estimated-cost ceiling, with a two-second minimum interval for subsequent batches. The pilot used an eight-second interval; wave-01 used two seconds. Historical work before this campaign used 12 POST requests. The user increased the cost allowance and approved one-to-two-second spacing after the pilot. Actual provider charges are unknown.

`pilot-30` has 30 records: 8 PASS, 0 FAIL, 22 INCONCLUSIVE. `wave-01` has 50 records: 4 PASS, 0 FAIL, 46 INCONCLUSIVE. All 80 records have unique turn IDs and passed evidence hash verification. No API error occurred. TC-001 reported at least one client-visible tool call in all 12 campaign trials; raw arguments and executor results were not retained. Wave-01 stores only argument shape, hash, and coarse topic flags, with no result field in the observed tool-call objects. Do not equate these reports with execution or database access.

The local combined store has 13 Track A, 59 Track B, and 91 Track C records. The latest Kumu export has 149 elements and 252 connections. The older Track C records and one historical benign connectivity request are explained in the report.

## Resume procedure

1. Read `state/current.md`, this handoff, `docs/track-c-campaign-report.md`, and `research/track_c_campaign_design.md`.
2. Check `git status`, ensure no other agent or process is sending Riley requests, and inspect the ledger and evidence without printing secrets or raw personal data.
3. Run `python3 -m unittest discover -s tests -q` and `python3 -m riley_research.cli verify`.
4. Recheck the approved host and model availability through `/models`. Stop if the endpoint, authorization, or organizer rules have changed.
5. Decide whether additional evidence is needed. If resuming, start only the next prepared batch with the same ledger and evidence paths: `python3 -m riley_research.campaign_runner --execute research/track_c_campaign_wave-02.json`. No additional approval is required under the user's current authorization, but do not exceed the global POST or configured estimated-cost ceiling. Any API error stops the batch automatically; inspect and reconcile the ledger before another attempt.
6. After a batch, verify evidence hashes, compare ledger request count to stored records, review redaction and outcomes, append a batch report, merge into the Dashboard store, regenerate Kumu, update the relevant GitHub Issues, run tests, and commit. Do not mark a model statement or tool-call display as an executor/DB failure.

The current organizer time window and rate terms are still unstated, and actual API costs are not exposed by the observed client response. Do not infer those terms from successful requests. Stop on an explicit restriction, access failure, unexpected real personal data, evidence corruption, or unresolved budget discrepancy.
