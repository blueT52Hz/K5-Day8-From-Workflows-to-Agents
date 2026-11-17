"""Count verifier interventions of swarm_verified from its traces.

Run after the bonus benchmarks (they write traces/R-swarm_verified-*.json):

    python -m bonus.report_interventions --out reports/bonus_verifier.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def collect(trace_dir: Path) -> dict:
    runs = []
    for path in sorted(trace_dir.glob("R-swarm_verified-*.json")):
        body = json.loads(path.read_text(encoding="utf-8"))
        overrides = [event["payload"] for event in body["events"] if event["kind"] == "verifier_override"]
        decision = next((event["payload"] for event in reversed(body["events"]) if event["kind"] == "decision"), {})
        runs.append({
            "run_id": body["run_id"],
            "verifier_checked": any(event["kind"] == "verifier" for event in body["events"]),
            "override": bool(overrides),
            "fields": overrides[0]["fields"] if overrides else [],
            "before_vnd": overrides[0]["before_vnd"] if overrides else None,
            "after_vnd": overrides[0]["after_vnd"] if overrides else None,
            "amount_changed": bool(overrides) and overrides[0]["before_vnd"] != overrides[0]["after_vnd"],
            "status": decision.get("status"),
        })
    checked = [run for run in runs if run["verifier_checked"]]
    return {
        "trace_dir": str(trace_dir),
        "runs_total": len(runs),
        "runs_verifier_checked": len(checked),
        "interventions": sum(run["override"] for run in runs),
        "interventions_amount_changed": sum(run["amount_changed"] for run in runs),
        "override_runs": [run for run in runs if run["override"]],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--traces", default="traces")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    report = collect(Path(args.traces))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"interventions {report['interventions']} / {report['runs_verifier_checked']} checked runs -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
