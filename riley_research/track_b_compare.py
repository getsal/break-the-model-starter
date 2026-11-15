"""Run the single-turn Track C prompts against a local synthetic model."""
import argparse
import json
import uuid
from pathlib import Path

from .evidence import EvidenceStore
from .local import simulate


def run(cases_path, store_path, model="qwen2.5:3b", variant="B"):
    cases = json.loads(Path(cases_path).read_text())
    store = EvidenceStore(store_path)
    run_id = uuid.uuid4().hex
    count = 0
    for case in cases:
        if len(case["steps"]) != 1:
            continue  # local simulation does not retain conversational context
        result = simulate(case["steps"][0], variant=variant, model=model, seed=7)
        store.append({"run_id": run_id, "case_id": case["case_id"],
            "case_version": case["case_version"], "case_hash": case["case_hash"],
            "track": "B", "model": model, "configuration": variant,
            "seed": 7, "step_number": 1,
            "expected_behavior": case["expected_authorized_behavior"],
            "observed_reply": result.get("reply"),
            "requested_tool_calls": result.get("requested_tool_calls"),
            "executed_tool_calls": result.get("executed_tool_calls"),
            "observed_tool_results": result.get("observed_tool_results"),
            "database_observation": None,
            "evaluation_result": "INCONCLUSIVE",
            "evaluation_reason": "Comparison-only local simulation; no matching case-specific oracle",
            "confidence": 0.0, "evidence_status": "OBSERVED",
            "evidence_source": "local Ollama synthetic simulation",
            "boundary": case["target_boundary"], "token_usage": result.get("token_usage")})
        count += 1
    return count, store.verify()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", default="research/track_c_cases.json")
    parser.add_argument("--store", default="artifacts/track-b-c-comparison.sqlite")
    args = parser.parse_args()
    print(run(args.cases, args.store))


if __name__ == "__main__":
    main()
