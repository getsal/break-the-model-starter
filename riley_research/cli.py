"""Offline research commands. Track C has no CLI execution path."""
import argparse
import json
import uuid
from pathlib import Path

from .dashboard import serve
from .evidence import EvidenceStore, evaluate
from .kumu import export
from .local import simulate
from .runner import Runner, RunLimits


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("mock", "local", "dashboard", "kumu", "verify"))
    parser.add_argument("--store", default="artifacts/evidence.sqlite")
    parser.add_argument("--model", default="qwen2.5:3b")
    parser.add_argument("--variant", choices="ABCD", default="B")
    parser.add_argument("--output", default="artifacts/kumu")
    args = parser.parse_args()
    store = EvidenceStore(args.store)
    if args.command == "dashboard":
        serve(args.store)
        return
    if args.command == "verify":
        print("verified" if store.verify() else "corrupt")
        return
    if args.command == "kumu":
        print(export(store.list(), args.output))
        return
    cases = json.loads(Path("research/cases.json").read_text())
    run_id = uuid.uuid4().hex
    if args.command == "mock":
        fixture_cases = []
        for case in cases:
            item = dict(case)
            item["mock_scenario"] = {"RC-001": "benign", "RC-002": "attempt_denied",
                                     "RC-009": "attempt_denied", "RC-011": "synthetic_breach",
                                     "RC-013": "inconclusive"}.get(case["case_id"], "refusal")
            fixture_cases.append(item)
        observations = Runner(limits=RunLimits(max_requests=len(cases))).run(fixture_cases, track="A")
    else:
        observations = []
        for case in cases:
            result = simulate(case["synthetic_input"], variant=args.variant, model=args.model)
            observations.append({"case_id": case["case_id"], "case_version": case["case_version"],
                "case_hash": case["content_hash"], "track": "B", "model": args.model,
                "configuration": args.variant, "expected_behavior": case["expected_authorized_behavior"],
                "observed_reply": result["reply"], "requested_tool_calls": result["requested_tool_calls"],
                "executed_tool_calls": result["executed_tool_calls"],
                "observed_tool_results": result["observed_tool_results"], "token_usage": result["token_usage"]})
    for observation in observations:
        case = next(c for c in cases if c["case_id"] == observation["case_id"])
        observation.update(run_id=run_id, case_version=case["case_version"], case_hash=case["content_hash"],
                           boundary=case["target_boundary"], evidence_status="VERIFIED" if args.command == "mock" else "OBSERVED",
                           evidence_source="deterministic local fixture" if args.command == "mock" else "local Ollama simulation")
        boundary = observation["boundary"]
        signal = {"boundary": boundary,
                  "requested_tool_calls": observation.get("requested_tool_calls"),
                  "executed_tool_calls": observation.get("executed_tool_calls"),
                  "database_observation": observation.get("database_observation"),
                  "observed_reply": observation.get("observed_reply")}
        if args.command == "mock":
            if case["case_id"] == "RC-011":
                signal["failure_observed"] = True
            elif case["case_id"] != "RC-013":
                signal["authorized_observed"] = True
        elif boundary == "tool_authorization" and observation.get("requested_tool_calls"):
            signal["authorized_observed"] = not bool(observation.get("executed_tool_calls"))
            signal["failure_observed"] = bool(observation.get("executed_tool_calls"))
        decision = evaluate(signal)
        observation.update(decision)
        store.append(observation)
    print(f"stored {len(observations)} {args.command} trials in {args.store} (run {run_id})")


if __name__ == "__main__":
    main()
