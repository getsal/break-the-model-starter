"""Validate and hash bounded synthetic Track C cases."""
import hashlib
import json
from pathlib import Path


PATH = Path(__file__).with_name("track_c_cases.json")


def content_hash(case):
    body = {key: value for key, value in case.items() if key != "case_hash"}
    canonical = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def main():
    cases = json.loads(PATH.read_text(encoding="utf-8"))
    ids = [case["case_id"] for case in cases]
    if len(cases) != 8 or len(set(ids)) != len(ids):
        raise ValueError("Expected eight unique cases")
    for case in cases:
        if not case["steps"] or any(not isinstance(step, str) or not step for step in case["steps"]):
            raise ValueError(f"Invalid steps for {case['case_id']}")
        if any(term in " ".join(case["steps"]).lower() for term in ("real patient", "api key", "team token")):
            raise ValueError(f"Potential sensitive-data request in {case['case_id']}")
        case["case_hash"] = content_hash(case)
    PATH.write_text(json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"validated {len(cases)} synthetic cases and {sum(len(case['steps']) for case in cases)} planned POST requests")


if __name__ == "__main__":
    main()
