"""Track B adapter for the bounded common runner.

The role and boundary variant are trusted execution settings. Case text never
selects either value, even if it contains role claims or configuration text.
"""

from dataclasses import dataclass

from .mock import _field


@dataclass(frozen=True)
class LocalResponse:
    reply: str | None
    requested_tool_calls: tuple
    executed_tool_calls: tuple
    observed_tool_results: tuple
    database_observation: dict | None
    turn_id: str | None = None


class LocalOllamaAdapter:
    track = "B"

    def __init__(self, model="qwen2.5:3b", *, trusted_role="visitor"):
        if model not in {
            "qwen2.5-coder:7b",
            "richardyoung/llama-3.2-3b-instruct-abliterated:latest",
            "llama3.2:3b",
            "qwen2.5:3b",
        }:
            raise ValueError("Model is not in the installed-model allowlist")
        if trusted_role not in {"visitor", "staff"}:
            raise ValueError("Unknown trusted role")
        self.model = model
        self.trusted_role = trusted_role

    def execute(self, case, *, seed=None, configuration=None):
        # Import here so offline Track A does not import or initialize Ollama.
        from .local import VARIANTS, simulate

        variant = configuration or "B"
        if isinstance(variant, dict):
            if set(variant) != {"variant"}:
                raise ValueError("Only variant is accepted in run configuration")
            variant = variant["variant"]
        if variant not in VARIANTS:
            raise ValueError("Unknown boundary variant")
        prompt = _field(case, "synthetic_input")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Case requires nonempty synthetic_input")
        result = simulate(prompt, variant=variant, model=self.model,
                          seed=7 if seed is None else seed,
                          trusted_role=self.trusted_role)
        tool_results = tuple(result.get("observed_tool_results") or ())
        db_observation = {
            "synthetic": True,
            "tool_result_statuses": [r.get("status") for r in tool_results if isinstance(r, dict)],
            "returned_record_ids": [
                row.get("id") for r in tool_results if isinstance(r, dict)
                for row in r.get("rows", ()) if isinstance(row, dict)
            ],
        }
        return LocalResponse(
            result.get("reply"),
            tuple(result.get("requested_tool_calls") or ()),
            tuple(result.get("executed_tool_calls") or ()),
            tool_results, db_observation,
        )
