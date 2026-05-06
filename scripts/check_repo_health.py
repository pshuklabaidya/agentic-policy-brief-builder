"""CLI entrypoint for deterministic repository health checks."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agentic_policy_brief_builder.health import check_repository_health, format_health_check_result  # noqa: E402, I001


def main() -> int:
    result = check_repository_health(ROOT)
    print(format_health_check_result("Repository health", result))
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
