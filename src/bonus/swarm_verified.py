"""Bonus B3 - swarm_verified: the reference swarm plus a code verifier before the write.

Signature (same as every shape):

    run_claim(claim_id, *, seed, store_path, crash_at=None) -> RunResult

The swarm part is kept as in `lab8/shapes/swarm_reference.py`, including its
REFERENCE_WEAKNESS (on seed % 5 == 0 it trusts the delay written in the ticket).
The only addition is `verify_quote_inputs`, run right before the draft and the write:

- It compares every fact the quote used (`delay_days`, `status`, `damage_verified`)
  with the structured order returned by the read-only investigator.
- On a mismatch it re-quotes from the structured order (at most 1 repair round)
  and writes a `verifier_override` trace event.
- If the facts still disagree after the repair, the claim is `failed` and no write happens.

Run next to the four shapes:

    python -m lab8.benchmark --shapes workflow,swarm,swarm_verified \
        --extra-shape swarm_verified=bonus.swarm_verified:run_claim \
        --seeds 11,22,33,44,55 --out reports/bonus_benchmark.json
"""

from __future__ import annotations

import sqlite3
from typing import Any

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.handoff import make_handoff
from lab8.mock_llm import complete, parse_delay_days
from lab8.runtime import run_readonly_investigators
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish, safe_dump
from lab8.tools import compute_compensation, tool_cost
from lab8.trace import Trace

SHAPE = "swarm_verified"
VERIFIED_FIELDS = ("delay_days", "status", "damage_verified")
MAX_REPAIRS = 1


def verify_quote_inputs(used: dict[str, Any], structured: dict[str, Any]) -> list[str]:
    """Return the quote facts that differ from the structured order (empty list = agree)."""
    return [field for field in VERIFIED_FIELDS if used.get(field) != structured.get(field)]


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    try:
        return _run(conn, claim_id, seed=seed, crash_at=crash_at)
    finally:
        conn.close()


def _run(conn: sqlite3.Connection, claim_id: str, *, seed: int, crash_at: str | None) -> RunResult:
    budget = Budget()
    trace = Trace(make_run_id(SHAPE, claim_id, seed))

    def done(status: str, proposal: int, reason: str | None) -> RunResult:
        trace.add("decision", {"status": status, "proposal_amount": int(proposal), "reason": reason})
        return finish(
            conn,
            shape=SHAPE,
            claim_id=claim_id,
            seed=seed,
            status=status,
            proposal_amount=proposal,
            budget=budget,
            trace=trace,
            error_reason=reason,
        )

    try:
        return _steps(conn, claim_id, seed=seed, budget=budget, trace=trace, crash_at=crash_at, done=done)
    except InjectedCrash:
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise
    except Exception as exc:  # run_claim must never raise.
        return done("failed", 0, f"exception:{type(exc).__name__}")


def _steps(conn, claim_id, *, seed: int, budget: Budget, trace: Trace, crash_at, done) -> RunResult:
    # --- swarm part (same calls and costs as swarm_reference) ---
    budget.add_tool(tool_cost())
    claim_row = conn.execute(
        "SELECT claim_id, principal_id, order_id, ticket FROM claims WHERE claim_id = ?",
        (claim_id,),
    ).fetchone()
    if claim_row is None:
        return done("failed", 0, "unknown_claim")

    ticket = claim_row["ticket"]
    complete(budget, seed=seed, purpose="peer", prompt=ticket)
    parsed_delay = parse_delay_days(ticket)
    complete(budget, seed=seed, purpose="parse", prompt=ticket)

    if not claim_row["order_id"]:
        complete(budget, seed=seed, purpose="draft", prompt="needs_info")
        return done("needs_info", 0, "missing_order_id")

    handoff = make_handoff(
        request_id=f"REQ-{claim_id}",
        claim_id=claim_id,
        task="check_applicable_policy",
        facts={},
        allowed_tools=["lookup_order", "lookup_policy", "compute_compensation"],
    )
    trace.add("handoff", safe_dump(handoff))
    investigated = run_readonly_investigators(conn, budget, handoff, principal_id=claim_row["principal_id"])
    order_view = investigated["tools"].get("lookup_order", {})
    trace.add("investigator", {"order_id": claim_row["order_id"], "visible": order_view.get("visible"), "reason": order_view.get("reason")})
    if not order_view.get("visible"):
        complete(budget, seed=seed, purpose="draft", prompt="escalated")
        return done("escalated", 0, order_view.get("reason"))

    structured = dict(order_view["order"])
    order = dict(structured)
    # REFERENCE_WEAKNESS kept on purpose: one seed in five trusts the ticket delay.
    if parsed_delay is not None and parsed_delay != int(order["delay_days"]) and seed % 5 == 0:
        order["delay_days"] = parsed_delay
        trace.add("model_override", {"delay_days": parsed_delay})

    quote = investigated["tools"]["compute_compensation"]
    if order["delay_days"] != structured["delay_days"]:
        budget.add_tool(tool_cost())
        quote = compute_compensation(conn, order)

    # --- verifier (the B3 addition): code checks the quote inputs before any write ---
    order, quote = _verify(conn, order, structured, quote, budget=budget, trace=trace)
    if order is None:
        return done("failed", 0, "verifier_unresolved")

    proposal = int(quote["amount_vnd"])
    trace.add("quote", {"amount_vnd": proposal, "reason": quote["reason"], "clause_ids": quote["clause_ids"]})
    complete(budget, seed=seed, purpose="draft", prompt=f"proposal={proposal}")
    if proposal <= 0:
        return done("denied", 0, quote.get("reason"))

    outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
    if outcome["ok"]:
        return done("resolved", proposal, None)
    return done("failed" if outcome["conflict"] else "denied", proposal, outcome["reason"])


def _verify(conn, order, structured, quote, *, budget: Budget, trace: Trace):
    """Repair at most MAX_REPAIRS times. Returns (order, quote), or (None, None) if unresolved."""
    for _ in range(MAX_REPAIRS):
        mismatched = verify_quote_inputs(order, structured)
        trace.add("verifier", {"checked": list(VERIFIED_FIELDS), "mismatched": mismatched})
        if not mismatched:
            return order, quote
        before = int(quote["amount_vnd"])
        order = dict(structured)
        budget.add_tool(tool_cost())
        quote = compute_compensation(conn, order)
        trace.add("verifier_override", {"fields": mismatched, "before_vnd": before, "after_vnd": int(quote["amount_vnd"])})
    if verify_quote_inputs(order, structured):
        return None, None
    return order, quote
