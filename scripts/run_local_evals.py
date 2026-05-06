#!/usr/bin/env python
"""Run deterministic local evaluation fixtures."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_SRC_DIR = _REPOSITORY_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from agentic_policy_brief_builder.evals import (  # noqa: E402
    DEFAULT_SYNTHETIC_POLICY_QUESTIONS_PATH,
    run_local_evaluation,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic local policy-brief evals.")
    parser.add_argument(
        "--fixture-path",
        default=str(DEFAULT_SYNTHETIC_POLICY_QUESTIONS_PATH),
        help="Path to an evaluation fixture JSON file.",
    )
    args = parser.parse_args()

    result = run_local_evaluation(args.fixture_path)
    status = "PASS" if result.passed else "FAIL"
    print(
        f"Local evals: {status} "
        f"({result.total_cases} case(s), {len(result.failed_cases)} failed)"
    )
    for case_result in result.case_results:
        case_status = "PASS" if case_result.passed else "FAIL"
        print(f"- {case_status} {case_result.fixture.case_id}")
        for gate in case_result.quality_gates:
            gate_status = "PASS" if gate.passed else "FAIL"
            required = "required" if gate.required else "optional"
            print(f"  - {gate_status} {gate.name} ({required}): {gate.message}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
