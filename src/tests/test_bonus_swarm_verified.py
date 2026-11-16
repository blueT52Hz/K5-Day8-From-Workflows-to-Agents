"""Bonus B3 tests: swarm_verified keeps the swarm but a code verifier checks quote inputs.

Runs in the default gate (`python -m pytest -q`).
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from bonus.swarm_verified import run_claim as swarm_verified
from bonus.swarm_verified import verify_quote_inputs
from lab8.db import connect, init_store, load_jsonl
from lab8.durability import InjectedCrash
from lab8.metrics import trial_pass
from lab8.shapes import SHAPES
from tests.conftest import BY_ID, CLAIMS, WORLD

BONUS_DIR = Path(__file__).resolve().parents[1] / "bonus"
BONUS_WORLD = json.loads((BONUS_DIR / "world.json").read_text(encoding="utf-8"))
BONUS_CLAIMS = load_jsonl(BONUS_DIR / "cases.jsonl")
BONUS_BY_ID = {claim["claim_id"]: claim for claim in BONUS_CLAIMS}

RUNNERS = {"swarm_verified": swarm_verified, "workflow": SHAPES["workflow"], "swarm": SHAPES["swarm"]}


def _grade(tmp_path, runner, claim_id, seed, world, claims, expected):
    store = tmp_path / f"{claim_id}-{seed}.sqlite"
    init_store(store, world, claims).close()
    started_at = time.time()
    result = runner(claim_id, seed=seed, store_path=str(store))
    conn = connect(store)
    try:
        passed, reason = trial_pass(result.as_dict(), expected, conn, started_at=started_at)
    finally:
        conn.close()
    return result, passed, reason


def _events(result) -> list[str]:
    body = json.loads(Path(result.trace_path).read_text(encoding="utf-8"))
    return [event["kind"] for event in body["events"]]


def test_verify_quote_inputs_flags_only_mismatched_fields():
    structured = {"delay_days": 2, "status": "delivered", "damage_verified": False, "shipping_fee_vnd": 20000}
    assert verify_quote_inputs(dict(structured), structured) == []
    assert verify_quote_inputs({**structured, "delay_days": 5}, structured) == ["delay_days"]
    tampered = {**structured, "status": "delivered_late", "damage_verified": True}
    assert verify_quote_inputs(tampered, structured) == ["status", "damage_verified"]


def test_verifier_repairs_swarm_seed55_miss_on_c002(tmp_path):
    expected = BY_ID["C-002"]["expected"]
    _, swarm_passed, _ = _grade(tmp_path / "s", SHAPES["swarm"], "C-002", 55, WORLD, CLAIMS, expected)
    result, passed, reason = _grade(tmp_path / "v", swarm_verified, "C-002", 55, WORLD, CLAIMS, expected)
    assert not swarm_passed, "reference swarm should still miss C-002 at seed 55"
    assert passed, reason
    assert "verifier_override" in _events(result)


def test_verifier_stays_silent_when_facts_agree(tmp_path):
    result, passed, reason = _grade(tmp_path, swarm_verified, "C-001", 11, WORLD, CLAIMS, BY_ID["C-001"]["expected"])
    assert passed, reason
    kinds = _events(result)
    assert "verifier" in kinds and "verifier_override" not in kinds


@pytest.mark.parametrize("shape", ["swarm_verified", "workflow"])
@pytest.mark.parametrize("claim_id", sorted(BONUS_BY_ID))
@pytest.mark.parametrize("seed", [11, 55])
def test_bonus_adversarial_cases_match_hand_labels(tmp_path, shape, claim_id, seed):
    expected = BONUS_BY_ID[claim_id]["expected"]
    _, passed, reason = _grade(tmp_path, RUNNERS[shape], claim_id, seed, BONUS_WORLD, BONUS_CLAIMS, expected)
    assert passed, reason


def test_swarm_verified_crash_keeps_one_refund(tmp_path):
    store = tmp_path / "crash.sqlite"
    init_store(store, WORLD, CLAIMS).close()
    with pytest.raises(InjectedCrash):
        swarm_verified("C-012", seed=11, store_path=str(store), crash_at="after_effect_before_checkpoint")
    result = swarm_verified("C-012", seed=11, store_path=str(store))
    conn = connect(store)
    try:
        count = conn.execute("SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = 'C-012'").fetchone()["n"]
    finally:
        conn.close()
    assert result.status == "resolved"
    assert count == 1
