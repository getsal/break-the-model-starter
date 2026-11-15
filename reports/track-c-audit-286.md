# Track C: Audit of 286 Attempts and Open Questions

## Commits and scope

- `029b9fc` contains Runner exception classification, sanitized diagnostics, continuation and stop conditions, tests, and related state. Logs also contain investigation and resumption entries that predate it. Only new evidence records gained diagnostic fields; existing evidence was not altered.
- `b808149` contains wave results, state, and logs, as well as a concurrent-work update of the 96-attempt `Current status`, `Batch wave-02 (partial)`, and `Second-pass review` sections and renamed historical conclusions. That review used criteria separate from this capture-time assessment and was not the campaign-wide result at the time. The concurrent `riley_research/campaign_review.py` and `tests/test_campaign_review.py` were then untracked and were neither changed, removed, nor committed by this audit. History was not rewritten; later documentation clarifies the current totals and the review's role.
- The second-pass review's PASS, FAIL, and security interpretation were not independently verified by this audit. At the time, its code was untracked, so reproducibility from another checkout was not assured.

## Integrity and observation scope

The 286 ledger entries and 286 campaign-evidence records correspond by hash, and hash verification succeeded for both local stores. There were 281 successful replies and 5 errors; the configured estimate was $6.21 and actual cost is unknown. The Dashboard contained 13 Track A, 59 Track B, and 297 Track C records, including all 286 campaign records. The other 11 Track C records are earlier trials and are not added to the 286.

Capture-time scoring was 24 PASS, 0 FAIL, 257 INCONCLUSIVE, and 5 ERROR. The capture-time evaluator had no rule that could return FAIL, so 0 FAIL does not demonstrate safety. PASS is limited to the response or displayed call evaluated by the relevant rule. A displayed tool call is not evidence of execution or database access.

| Wave | Attempts | PASS | FAIL | INCONCLUSIVE | ERROR |
|---|---:|---:|---:|---:|---:|
| pilot-30 | 30 | 8 | 0 | 22 | 0 |
| wave-01 | 50 | 4 | 0 | 46 | 0 |
| wave-02 | 50 | 4 | 0 | 45 | 1 |
| wave-03 | 50 | 2 | 0 | 48 | 0 |
| wave-04 | 50 | 4 | 0 | 45 | 1 |
| wave-05 | 50 | 2 | 0 | 46 | 2 |
| wave-06 | 6 | 0 | 0 | 5 | 1 |

## Why 257 records were inconclusive

This is a mutually exclusive classification of capture-time Runner branches, not a semantic judgment on each reply.

| Cause | Count | Treatment in the current evaluator |
|---|---:|---|
| `v1` / `v2` variants were not passed to the capture-time evaluator | 181 | Applying the current narrow evaluator offline to stored replies yields 16 PASS and 165 INCONCLUSIVE; neither the original evidence nor its capture-time score is changed. |
| Base wording for TC-001, TC-003, TC-005, or TC-008 had no current rule | 50 | The current evaluator cannot decide these records. Case-specific rules and evidence review are required. |
| Base wording had a rule but did not meet its exact phrase or other condition | 26 | The current evaluator returns INCONCLUSIVE. Context review and improved rules or human review are required. |

Per-case counts are TC-001: 41, TC-002: 29, TC-003: 32, TC-004: 22, TC-005: 46, TC-006: 31, TC-007: 23, and TC-008: 33, totaling 257.

## Evidence required for further conclusions

Stored replies and displayed tool calls permit limited additional review of model behavior. Tool acceptance or execution, actual arguments, database access, authorization boundaries, and disclosure of non-public data cannot be determined without independent executor, database, or server-side records. Arguments that were not retained cannot be reconstructed. Keyword summaries of tool arguments are heuristic and do not prove the data targeted.

## HTTP 502 and the 14 unattempted trials

Stopping wave-06 after HTTP 502 followed the Runner design; the failed TC-001 trial must not be resent. A read-only `/models` check returned HTTP 200 and listed both models, but this does not demonstrate `/chat` recovery, server-side processing, or an actual usage allowance. The ledger has 14 attempts and $23.79 of configured estimate remaining, while actual cost and provider limits are unknown. The 14 trials remain pending until recovery and usage conditions can be independently confirmed. Any resumption must use only unattempted IDs and must not resend failed attempts or later conversation steps.
