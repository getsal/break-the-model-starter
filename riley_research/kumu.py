"""Sanitized, deterministic Kumu CSV export of local evidence."""

from __future__ import annotations

import csv
import hashlib
import re
from pathlib import Path


SAFE = re.compile(r"^[A-Za-z0-9_.:-]{1,64}$")
KNOWN_MODELS = {"deterministic-mock", "mock", "qwen2.5-coder:7b", "richardyoung/llama-3.2-3b-instruct-abliterated:latest", "llama3.2:3b", "qwen2.5:3b"}


def _id(kind, value):
    return f"{kind}:{hashlib.sha256(str(value).encode('utf-8')).hexdigest()[:20]}"


def _label(value, fallback):
    value = str(value or "")
    return value if SAFE.fullmatch(value) else fallback


def _tool_names(calls):
    if not isinstance(calls, list):
        return set()
    return {call.get("name") for call in calls if isinstance(call, dict) and isinstance(call.get("name"), str) and SAFE.fullmatch(call["name"])}


def export(records, directory, cases=(), controls=()):
    """Export only controlled identifiers and labels; never raw prompts or replies.

    `cases` is the versioned synthetic case inventory. `controls` may contain
    dictionaries with `id` and `boundary`; no free-text control description is exported.
    """
    destination = Path(directory)
    destination.mkdir(parents=True, exist_ok=True)
    inventory = {case["case_id"]: case for case in cases}
    elements = {}
    edges = set()

    def element(kind, value, label=None):
        identifier = _id(kind, value)
        elements[identifier] = (identifier, _label(label if label is not None else value, kind), kind)
        return identifier

    for record in records:
        case_key = str(record["case_id"])
        run_key = str(record["run_id"])
        case_data = inventory.get(case_key, {})
        case = element("Test case", case_key)
        run = element("Experiment", run_key)
        track = element("Track", record.get("track"), _label(record.get("track"), "unknown"))
        model_value = record.get("model")
        model = element("Model", model_value, model_value if model_value in KNOWN_MODELS else "redacted model")
        boundary_value = record.get("boundary") or case_data.get("target_boundary") or "unknown"
        boundary = element("Trust boundary", boundary_value)
        edges.update({(run, case, "tests"), (run, track, "uses track"),
                      (run, model, "uses model"), (case, boundary, "targets")})

        category_value = case_data.get("category")
        if category_value:
            category = element("Attack category", category_value)
            edges.add((case, category, "classified as"))

        for tool_name in _tool_names(record.get("requested_tool_calls")) | _tool_names(record.get("executed_tool_calls")):
            tool = element("Tool", tool_name)
            edges.add((run, tool, "invokes"))

        outcome = record.get("evaluation_result")
        if outcome in {"PASS", "FAIL", "INCONCLUSIVE", "ERROR"}:
            finding = element("Finding", f"{run_key}:{case_key}:{record.get('step_number')}", outcome)
            edges.add((finding, run, "originates from"))

    for control in controls:
        if not isinstance(control, dict) or not SAFE.fullmatch(str(control.get("id", ""))):
            continue
        control_id = element("Control", control["id"])
        boundary_value = control.get("boundary")
        if isinstance(boundary_value, str) and SAFE.fullmatch(boundary_value):
            boundary = element("Trust boundary", boundary_value)
            edges.add((control_id, boundary, "protects"))

    with (destination / "elements.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(("id", "label", "type"))
        writer.writerows(sorted(elements.values()))
    with (destination / "connections.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(("from", "to", "label"))
        writer.writerows(sorted(edges))
    return len(elements), len(edges)
