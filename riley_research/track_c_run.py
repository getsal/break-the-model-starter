"""Bounded, synthetic-only Riley challenge experiment runner.

This entry point requires an explicit --execute flag and never prints replies or
credentials. All API calls are made by one process under a shared request cap.
"""
import argparse
import hashlib
import json
import os
import re
import time
import uuid
from pathlib import Path

from dotenv import load_dotenv

from .evidence import EvidenceStore, sanitize
from .remote import RileyAdapter


HOST = "2-31-186-181.sslip.io"
MODEL = "Qwen/Qwen3-30B-A3B-Instruct-2507"
MAX_POST = 12
MIN_INTERVAL_SECONDS = 8
ESTIMATED_COST_PER_POST = 0.005
MAX_ESTIMATED_COST = 0.06


def safe_reply(value):
    """Keep an observed response while suppressing likely personal identifiers."""
    if not isinstance(value, str):
        return None
    cleaned = sanitize(value)
    cleaned = re.sub(r"\b(?:\+?\d[\d ()-]{7,}\d)\b", "[REDACTED_NUMBER]", cleaned)
    cleaned = re.sub(r"\b(?:TEST|P|SYN)-\d{3,}\b", "[REDACTED_RECORD_ID]", cleaned, flags=re.I)
    if re.search(r"(?:patient|staff)\s+(?:name|address|phone|email|record)\b", cleaned, re.I):
        return "[REDACTED_POTENTIAL_RECORD_RESPONSE]"
    return cleaned[:1200]


def run(cases_path, store_path):
    cases = json.loads(Path(cases_path).read_text())
    total = sum(len(case["steps"]) for case in cases)
    if total > MAX_POST or total == 0:
        raise ValueError("Case batch exceeds fixed request cap")
    load_dotenv()
    endpoint = os.environ.get("API_URL", "")
    if endpoint.rstrip("/") != "https://" + HOST:
        raise ValueError("Configured endpoint differs from approved challenge host")
    key = os.environ.get("API_KEY") or os.environ.get("NEBIUS_API_KEY") or ""
    if not key:
        raise ValueError("No configured provider key")
    adapter = RileyAdapter(endpoint=endpoint, approved=True, allowed_host=HOST,
        max_requests=total, min_interval_seconds=MIN_INTERVAL_SECONDS,
        max_estimated_cost=MAX_ESTIMATED_COST,
        estimated_cost_per_request=ESTIMATED_COST_PER_POST,
        participant=os.environ.get("YOUR_NAME", "synthetic-research"),
        team_token=os.environ.get("TEAM_CODE", ""), api_key=key, model=MODEL)
    store = EvidenceStore(store_path)
    run_id = uuid.uuid4().hex
    count = 0
    for case in cases:
        conversation = "conv_" + uuid.uuid4().hex[:12]
        for step, prompt in enumerate(case["steps"], 1):
            start = time.monotonic()
            try:
                response = adapter.chat(prompt, conversation)
            except Exception as error:
                # Never include exception bodies; they may echo authenticated data.
                print(json.dumps({"case_id": case["case_id"], "step": step,
                    "error_type": type(error).__name__, "sent_so_far": count + 1}))
                return run_id, count + 1
            count += 1
            calls = response.get("tool_calls") or []
            names = [{"name": call.get("name")} for call in calls if isinstance(call, dict)]
            reply = safe_reply(response.get("reply"))
            store.append({"run_id": run_id, "case_id": case["case_id"],
                "case_version": case["case_version"], "case_hash": case["case_hash"],
                "track": "C", "model": MODEL, "configuration": "user-authorized synthetic challenge; 8s interval",
                "conversation_id_hash": hashlib.sha256(conversation.encode()).hexdigest(),
                "turn_id": response.get("turn_id"), "step_number": step,
                "expected_behavior": case["expected_authorized_behavior"],
                "observed_reply": reply, "requested_tool_calls": names,
                "executed_tool_calls": None, "observed_tool_results": None,
                "database_observation": None, "evaluation_result": "INCONCLUSIVE",
                "evaluation_reason": "Awaiting case-specific review; API tool execution and DB result unverified",
                "confidence": 0.0, "evidence_status": "OBSERVED",
                "evidence_source": "official Riley API /chat, client-observed response",
                "boundary": case["target_boundary"],
                "duration_ms": round((time.monotonic() - start) * 1000, 2),
                "estimated_cost": ESTIMATED_COST_PER_POST, "actual_cost": None})
            print(json.dumps({"case_id": case["case_id"], "step": step,
                "turn_id": response.get("turn_id"), "reply_recorded": reply is not None,
                "reported_tool_calls": len(names)}))
    return run_id, count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--cases", default="research/track_c_cases.json")
    parser.add_argument("--store", default="artifacts/track-c-expanded.sqlite")
    args = parser.parse_args()
    if not args.execute:
        parser.error("External execution requires --execute")
    run_id, count = run(args.cases, args.store)
    print(json.dumps({"run_id": run_id, "post_requests": count}))


if __name__ == "__main__":
    main()
