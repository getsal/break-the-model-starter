"""Single-host Riley campaign runner with a persistent, cross-process budget ledger."""
import argparse
import hashlib
import json
import os
import re
import sqlite3
import time
import uuid
import errno
import socket
import ssl
import urllib.error
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv

from .evidence import EvidenceStore
from .remote import RileyAdapter, HTTP_TIMEOUT_SECONDS
from .track_c_run import HOST, safe_reply
from .track_c_review import decision


MAX_POST = 300
MAX_ESTIMATED_COST = 30.0
MIN_INTERVAL_SECONDS = 2.0
MODEL_ESTIMATES = {
    "Qwen/Qwen3-30B-A3B-Instruct-2507": 0.015,
    "openai/gpt-oss-120b": 0.03,
}

def error_details(error):
    """Keep only recognized, non-sensitive system reason text; never persist URLs or payloads."""
    reason = getattr(error, "reason", error)
    code = getattr(error, "code", None) if isinstance(error, urllib.error.HTTPError) else None
    number = getattr(reason, "errno", None)
    if isinstance(error, urllib.error.HTTPError):
        category = "HTTP_ERROR"
    elif isinstance(reason, (TimeoutError, socket.timeout)) or number == errno.ETIMEDOUT:
        category = "TIMEOUT"
    elif isinstance(reason, socket.gaierror):
        category = "DNS_ERROR"
    elif isinstance(reason, ssl.SSLError):
        category = "TLS_ERROR"
    elif isinstance(reason, (ConnectionError, ConnectionRefusedError, ConnectionResetError, BrokenPipeError)) or number in {errno.ECONNREFUSED, errno.ECONNRESET, errno.ECONNABORTED, errno.ENETUNREACH, errno.EHOSTUNREACH}:
        category = "CONNECTION_ERROR"
    else:
        category = "UNKNOWN_ERROR"
    # Arbitrary exception strings may contain secrets, URLs, or response bodies.
    safe_messages = {"timed out", "The read operation timed out", "Connection refused", "Connection reset by peer", "Temporary failure in name resolution", "Name or service not known", "nodename nor servname provided, or not known"}
    message = str(reason)
    safe_reason = message if message in safe_messages else {"TIMEOUT": "Timed out [details redacted]", "DNS_ERROR": "Name resolution error [details redacted]", "TLS_ERROR": "TLS error [details redacted]", "CONNECTION_ERROR": "Connection error [details redacted]", "HTTP_ERROR": "HTTP error [details redacted]"}.get(category, "[REDACTED: unrecognized reason]")
    if isinstance(number, int):
        safe_reason += f" (errno {number})"
    return {"exception_type": type(error).__name__, "reason_type": type(reason).__name__,
            "reason": safe_reason, "classification": category, "http_status": code,
            "timeout_seconds": HTTP_TIMEOUT_SECONDS}


def summarize_tool_call(call):
    """Record argument shape and topic without retaining raw argument values."""
    args = call.get("args")
    encoded = json.dumps(args, sort_keys=True, ensure_ascii=False, default=str)
    return {"name": call.get("name"), "fields": sorted(call.keys()),
            "args_type": type(args).__name__,
            "arg_keys": sorted(str(key) for key in args) if isinstance(args, dict) else None,
            "args_hash": hashlib.sha256(encoded.encode()).hexdigest() if args is not None else None,
            "mentions_restricted_data": bool(re.search(r"patient|staff|private|confidential|protected", encoded, re.I)),
            "mentions_public_data": bool(re.search(r"public|hours|clinic|facilit|location", encoded, re.I)),
            "result_field_present": any(key in call for key in ("result", "output", "response"))}


class BudgetLedger:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS requests (
                trial_id TEXT PRIMARY KEY, batch_id TEXT NOT NULL, model TEXT NOT NULL,
                estimated_cost REAL NOT NULL, reserved_at REAL NOT NULL,
                completed_at REAL, status TEXT NOT NULL, evidence_hash TEXT)""")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        try:
            yield db
            db.commit()
        finally:
            db.close()

    def reserve(self, trial):
        cost = MODEL_ESTIMATES.get(trial["model"])
        if cost is None:
            raise ValueError("Model is not in the approved campaign allowlist")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            count, spent, last = db.execute("SELECT COUNT(*), COALESCE(SUM(estimated_cost),0), COALESCE(MAX(reserved_at),0) FROM requests").fetchone()
            if count >= MAX_POST or spent + cost > MAX_ESTIMATED_COST + 1e-9:
                raise RuntimeError("Global request or estimated-cost budget exhausted")
            next_at = max(time.time(), last + MIN_INTERVAL_SECONDS)
            db.execute("INSERT INTO requests VALUES (?, ?, ?, ?, ?, NULL, 'reserved', NULL)",
                (trial["trial_id"], trial["batch_id"], trial["model"], cost, next_at))
        return next_at, cost

    def complete(self, trial_id, status, evidence_hash=None):
        with self.connect() as db:
            db.execute("UPDATE requests SET completed_at=?, status=?, evidence_hash=? WHERE trial_id=?",
                (time.time(), status, evidence_hash, trial_id))

    def summary(self):
        with self.connect() as db:
            count, cost = db.execute("SELECT COUNT(*), COALESCE(SUM(estimated_cost),0) FROM requests").fetchone()
            statuses = dict(db.execute("SELECT status, COUNT(*) FROM requests GROUP BY status"))
        return {"post_requests": count, "estimated_cost": round(cost, 4), "statuses": statuses}

    def trailing_errors(self):
        with self.connect() as db:
            rows = db.execute("SELECT status FROM requests ORDER BY rowid DESC LIMIT 2").fetchall()
        count = 0
        for (status,) in rows:
            if not status.startswith("error:"):
                break
            count += 1
        return count


def validate_manifest(trials):
    if not trials or len(trials) > 50:
        raise ValueError("Batch must contain 1–50 POST requests")
    ids = [trial["trial_id"] for trial in trials]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate trial_id")
    required = {"trial_id", "batch_id", "case_id", "case_hash", "prompt", "model",
                "conversation_group", "step_number", "repetition", "variant",
                "target_boundary", "expected_authorized_behavior"}
    for trial in trials:
        if required - set(trial):
            raise ValueError("Missing campaign trial fields")
        if trial["model"] not in MODEL_ESTIMATES or not isinstance(trial["prompt"], str) or len(trial["prompt"]) > 2000:
            raise ValueError("Unapproved model or prompt")
        if trial["target_boundary"] not in {"model_instruction", "tool_invocation", "tool_authorization", "database_authorization", "response_disclosure"}:
            raise ValueError("Unknown target boundary")


def run_batch(manifest_path, ledger_path, store_path):
    trials = json.loads(Path(manifest_path).read_text())
    validate_manifest(trials)
    load_dotenv()
    endpoint = os.environ.get("API_URL", "").rstrip("/")
    if endpoint != "https://" + HOST:
        raise ValueError("Configured host is outside the approved challenge")
    key = os.environ.get("API_KEY") or os.environ.get("NEBIUS_API_KEY") or ""
    if not key:
        raise ValueError("Provider key is unavailable")
    ledger = BudgetLedger(ledger_path)
    store = EvidenceStore(store_path)
    conversations = {}
    adapters = {}
    completed = 0
    consecutive_errors = ledger.trailing_errors()
    if consecutive_errors >= 2:
        raise RuntimeError("Two consecutive ledger errors require investigation")
    failed_groups = set()
    for trial in trials:
        if trial["conversation_group"] in failed_groups:
            continue
        model = trial["model"]
        if model not in adapters:
            adapters[model] = RileyAdapter(endpoint=endpoint, approved=True, allowed_host=HOST,
                max_requests=len(trials), min_interval_seconds=1,
                max_estimated_cost=MAX_ESTIMATED_COST,
                estimated_cost_per_request=MODEL_ESTIMATES[model],
                participant=os.environ.get("YOUR_NAME", "synthetic-research"),
                team_token=os.environ.get("TEAM_CODE", ""), api_key=key, model=model)
        reserved_at, cost = ledger.reserve(trial)
        time.sleep(max(0, reserved_at - time.time()))
        group = trial["conversation_group"]
        conversation = conversations.setdefault(group, "conv_" + uuid.uuid4().hex[:12])
        start = time.monotonic()
        try:
            response = adapters[model].chat(trial["prompt"], conversation)
            status = "ok"
            details = None
            consecutive_errors = 0
        except Exception as error:
            response = {}
            status = "error:" + type(error).__name__
            details = error_details(error)
            consecutive_errors += 1
            failed_groups.add(group)
        calls = response.get("tool_calls") or []
        names = [summarize_tool_call(call) for call in calls if isinstance(call, dict)]
        record = {"run_id": trial["batch_id"], "case_id": trial["case_id"],
            "case_version": 1, "case_hash": trial["case_hash"], "track": "C",
            "model": model, "configuration": f"batch:{trial['batch_id']}; variant:{trial['variant']}; repetition:{trial['repetition']}",
            "conversation_id_hash": hashlib.sha256(conversation.encode()).hexdigest(),
            "turn_id": response.get("turn_id"), "step_number": trial["step_number"],
            "expected_behavior": trial["expected_authorized_behavior"],
            "observed_reply": safe_reply(response.get("reply")),
            "requested_tool_calls": names, "executed_tool_calls": None,
            "observed_tool_results": None, "database_observation": None,
            "evaluation_result": "ERROR" if status != "ok" else "INCONCLUSIVE",
            "evaluation_reason": status if status != "ok" else "Client-visible observation awaiting case oracle",
            "confidence": 0.0, "evidence_status": "OBSERVED",
            "evidence_source": "official Riley API /chat campaign; trial " + trial["trial_id"],
            "boundary": trial["target_boundary"],
            "duration_ms": round((time.monotonic() - start) * 1000, 2),
            "estimated_cost": cost, "actual_cost": None}
        if details is not None:
            details["duration_ms"] = record["duration_ms"]
            record["error_details"] = details
        if status == "ok" and trial.get("variant") == "base":
            result, reason = decision(record)
            record.update(evaluation_result=result, evaluation_reason=reason,
                          confidence=0.8 if result == "PASS" else 0.0)
        saved = store.append(record)
        ledger.complete(trial["trial_id"], status, saved["evidence_hash"])
        completed += 1
        print(json.dumps({"trial_id": trial["trial_id"], "case_id": trial["case_id"],
            "status": status, "outcome": saved["evaluation_result"],
            "tool_calls": len(names), "evidence_id": saved["evidence_hash"][:16]}), flush=True)
        if details is not None and (consecutive_errors >= 2 or details["classification"] not in {"TIMEOUT", "DNS_ERROR", "TLS_ERROR", "CONNECTION_ERROR"}):
            break  # never retry; stop on consecutive errors or non-transport errors
    return {"completed": completed, **ledger.summary()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("manifest")
    parser.add_argument("--ledger", default="artifacts/campaign-ledger.sqlite")
    parser.add_argument("--store", default="artifacts/campaign-evidence.sqlite")
    args = parser.parse_args()
    if not args.execute:
        parser.error("External execution requires --execute")
    print(json.dumps(run_batch(args.manifest, args.ledger, args.store)), flush=True)


if __name__ == "__main__":
    main()
