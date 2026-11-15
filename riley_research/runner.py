"""Bounded common execution controller for explicitly selected tracks."""

import hashlib
import json
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from .mock import DeterministicMock, _field


@dataclass(frozen=True)
class RunLimits:
    max_requests: int = 10
    max_iterations_per_case: int = 1
    min_interval_seconds: float = 0.0
    max_estimated_cost: float = 0.0

    def __post_init__(self):
        if self.max_requests < 1 or self.max_iterations_per_case < 1:
            raise ValueError("Request and iteration limits must be positive")
        if self.min_interval_seconds < 0 or self.max_estimated_cost < 0:
            raise ValueError("Rate and cost limits cannot be negative")


class Runner:
    def __init__(self, adapters=None, limits=None, *, external_approved=False):
        self.adapters = {"A": DeterministicMock(), **(adapters or {})}
        self.limits = limits or RunLimits()
        self.external_approved = external_approved
        self.requests = 0
        self.last_request_at = None

    def estimate(self, cases, *, iterations=1, estimated_cost_per_request=0.0):
        count = len(cases) * iterations
        return {"requests": count, "estimated_cost": count * estimated_cost_per_request}

    def run(self, cases, *, track, iterations=1, seed=None, configuration=None,
            cancel=None, estimated_cost_per_request=0.0):
        if track not in self.adapters:
            raise ValueError(f"Track {track!r} has no configured adapter")
        if track == "C" and not self.external_approved:
            raise PermissionError("Track C requires explicit external approval")
        if not 1 <= iterations <= self.limits.max_iterations_per_case:
            raise ValueError("Case iteration limit exceeded")
        budget = self.estimate(cases, iterations=iterations,
                               estimated_cost_per_request=estimated_cost_per_request)
        if self.requests + budget["requests"] > self.limits.max_requests:
            raise ValueError("Global request limit exceeded")
        if budget["estimated_cost"] > self.limits.max_estimated_cost:
            raise ValueError("Estimated cost limit exceeded")
        run_id = uuid.uuid4().hex
        records = []
        for case in cases:
            for step in range(1, iterations + 1):
                if cancel is not None and cancel():
                    return records
                now = time.monotonic()
                if self.last_request_at is not None:
                    delay = self.limits.min_interval_seconds - (now - self.last_request_at)
                    if delay > 0:
                        time.sleep(delay)
                start = time.monotonic()
                self.requests += 1
                self.last_request_at = start
                response = self.adapters[track].execute(
                    case, seed=seed, configuration=configuration)
                body = _case_body(case)
                case_hash = hashlib.sha256(json.dumps(body, sort_keys=True,
                    ensure_ascii=False).encode()).hexdigest()
                records.append({
                    "run_id": run_id,
                    "case_id": _field(case, "case_id"),
                    "case_version": _field(case, "case_version", 1),
                    "case_hash": case_hash,
                    "track": track,
                    "model": getattr(self.adapters[track], "model", None),
                    "configuration": configuration,
                    "seed": seed,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "step_number": step,
                    "expected_behavior": _field(case, "expected_authorized_behavior"),
                    "observed_reply": response.reply,
                    "requested_tool_calls": list(response.requested_tool_calls),
                    "executed_tool_calls": list(response.executed_tool_calls),
                    "observed_tool_results": list(response.observed_tool_results),
                    "database_observation": response.database_observation,
                    "turn_id": response.turn_id,
                    "duration_ms": round((time.monotonic() - start) * 1000, 3),
                    "estimated_cost": estimated_cost_per_request,
                })
        return records


def _case_body(case):
    if isinstance(case, dict):
        return case
    if hasattr(case, "__dict__"):
        return vars(case)
    raise TypeError("Case must be a mapping or data object")
