"""Aggregate bounded Track C campaigns without inferring hidden server behavior."""

from collections import Counter, defaultdict
from decimal import Decimal
from typing import Any, Iterable, Mapping


OUTCOMES = ("PASS", "FAIL", "INCONCLUSIVE", "ERROR", "NOT_RUN")


def _batch_id(record: Mapping[str, Any]) -> str:
    config = record.get("configuration")
    if isinstance(config, dict) and config.get("batch_id"):
        return str(config["batch_id"])
    return str(record.get("run_id") or "unknown")


def _money_total(records: list[Mapping[str, Any]], field: str) -> tuple[str | None, int]:
    values = [record.get(field) for record in records]
    known = [value for value in values if isinstance(value, (int, float, str)) and value != ""]
    if not known:
        return None, 0
    try:
        amount = sum((Decimal(str(value)) for value in known), Decimal("0"))
    except Exception:
        return None, 0
    # A partial sum is never represented as the total for the batch.
    return (str(amount) if len(known) == len(values) else None), len(known)


def batch_summaries(records: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Return one row per explicit batch ID, or run ID when absent.

    A row represents evidence records, not necessarily billable API requests.
    The caller must report sent requests separately when some failed before
    evidence capture. Tool-call display never implies execution or DB access.
    """
    groups = defaultdict(list)
    for record in records:
        if record.get("track") == "C":
            groups[_batch_id(record)].append(record)
    summaries = []
    for batch_id, batch in sorted(groups.items()):
        outcomes = Counter(record.get("evaluation_result") for record in batch)
        reported = sum(bool(record.get("requested_tool_calls")) for record in batch)
        executor = sum(record.get("executed_tool_calls") is not None and
                       record.get("observed_tool_results") is not None for record in batch)
        database = sum(record.get("database_observation") is not None for record in batch)
        estimated, estimated_known = _money_total(batch, "estimated_cost")
        actual, actual_known = _money_total(batch, "actual_cost")
        summaries.append({
            "batch_id": batch_id,
            "run_ids": sorted({str(record.get("run_id")) for record in batch}),
            "trial_count": len(batch),
            "case_count": len({record.get("case_id") for record in batch}),
            "models": dict(sorted(Counter(str(record.get("model") or "unknown") for record in batch).items())),
            "outcomes": {name: outcomes[name] for name in OUTCOMES},
            "tool_call_reported_trials": reported,
            "tool_call_report_rate": f"{reported}/{len(batch)}",
            "executor_result_trials": executor,
            "database_result_trials": database,
            "estimated_cost_total": estimated,
            "estimated_cost_known_trials": estimated_known,
            "actual_cost_total": actual,
            "actual_cost_known_trials": actual_known,
            "evidence_ids": [record.get("evidence_hash") for record in batch],
            "turn_ids": [record.get("turn_id") for record in batch],
        })
    return summaries


def variability_rows(records: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Compare repeated prompts by case hash and model with explicit denominators."""
    groups = defaultdict(list)
    for record in records:
        if record.get("track") == "C":
            key = (record.get("case_id"), record.get("case_hash"), record.get("model"))
            groups[key].append(record)
    result = []
    for (case_id, case_hash, model), rows in sorted(groups.items(), key=lambda item: str(item[0])):
        outcomes = Counter(row.get("evaluation_result") for row in rows)
        tool_reported = sum(bool(row.get("requested_tool_calls")) for row in rows)
        result.append({
            "case_id": case_id,
            "case_hash": case_hash,
            "model": model,
            "trials": len(rows),
            "pass": outcomes["PASS"],
            "fail": outcomes["FAIL"],
            "inconclusive": outcomes["INCONCLUSIVE"],
            "error": outcomes["ERROR"],
            "tool_call_reported": tool_reported,
            "tool_call_report_rate": f"{tool_reported}/{len(rows)}",
            "outcomes_vary": len({row.get("evaluation_result") for row in rows}) > 1,
            "tool_reports_vary": len({bool(row.get("requested_tool_calls")) for row in rows}) > 1,
        })
    return result


def batch_markdown(summary: Mapping[str, Any]) -> str:
    """Create a compact, source-linked batch report section."""
    outcomes = summary["outcomes"]
    evidence = ", ".join(str(value)[:12] for value in summary["evidence_ids"] if value)
    actual = summary["actual_cost_total"] if summary["actual_cost_total"] is not None else "unknown"
    estimated = summary["estimated_cost_total"] if summary["estimated_cost_total"] is not None else "unknown"
    return (
        f"### Batch {summary['batch_id']}\n\n"
        f"- Stored trials: {summary['trial_count']}; distinct cases: {summary['case_count']}. "
        "Sent API requests may exceed stored trials if an error occurred before collection.\n"
        f"- PASS / FAIL / INCONCLUSIVE / ERROR / NOT_RUN: "
        f"{outcomes['PASS']} / {outcomes['FAIL']} / {outcomes['INCONCLUSIVE']} / "
        f"{outcomes['ERROR']} / {outcomes['NOT_RUN']}.\n"
        f"- Reported tool calls: {summary['tool_call_report_rate']}; independently observed "
        f"executor results: {summary['executor_result_trials']}; database results: {summary['database_result_trials']}.\n"
        f"- Estimated cost: {estimated}; actual cost: {actual}.\n"
        f"- Evidence ID prefixes: {evidence}. Full hashes and turn IDs are in the local evidence store.\n"
    )
