from __future__ import annotations

import json
from pathlib import Path

from app.evaluator import PolicyEvaluator
from app.schemas import PolicyDocument


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    policy_data = json.loads((root / "examples" / "restricted-zone-policy.json").read_text())
    event = json.loads((root / "examples" / "matching-event.json").read_text())
    result = PolicyEvaluator().simulate(PolicyDocument(**policy_data), event)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()

