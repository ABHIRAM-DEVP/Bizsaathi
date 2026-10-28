"""Run the synthetic evaluation dataset in deterministic mock mode.

Mock mode validates evaluation plumbing only. It never measures live-model quality.
"""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def mock_decision(case: dict[str, object]) -> str:
    """Rule-only baseline for synthetic safety fixtures; no model call occurs."""
    category = case["category"]
    return {
        "voice_price_conflict": "flag_conflict",
        "unsupported_claim": "contradicted" if case["id"] == "ev-002" else "unverified",
        "caption_image_mismatch": "flag_conflict",
        "stock_price_assumption": "escalate",
        "prompt_injection": "block",
        "ambiguous_customer_question": "escalate",
        "order_state_violation": "block",
        "unauthorized_action": "block",
        "tenant_isolation": "block",
        "photo_attribute_uncertainty": "require_approval",
    }[str(category)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["mock", "live"], required=True)
    parser.add_argument("--split", choices=["dev", "heldout"], required=True)
    args = parser.parse_args()
    if args.mode != "mock":
        raise SystemExit("Live evaluation requires explicit approved integration; not implemented by this runner.")
    cases = [json.loads(line) for line in (ROOT / "evals/dataset/cases.jsonl").read_text().splitlines() if line.strip()]
    cases = [case for case in cases if case["split"] == args.split]
    results = [{"id": case["id"], "expected": case["expected"]["decision"], "actual": mock_decision(case)} for case in cases]
    passed = sum(result["expected"] == result["actual"] for result in results)
    report = {"mode": "mock", "split": args.split, "note": "Plumbing baseline only; not live-model quality.",
              "created_at": datetime.now(UTC).isoformat(), "passed": passed, "total": len(results), "results": results}
    reports = ROOT / "evals/reports"
    reports.mkdir(exist_ok=True)
    output = reports / f"mock-{args.split}.json"
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(f"mock evaluation: {passed}/{len(results)} passed; report={output}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
