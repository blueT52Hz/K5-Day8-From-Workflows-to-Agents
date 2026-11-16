"""Shape C - orchestrator plus read-only investigators.

Signature (do not change):

    run_claim(claim_id, *, seed, store_path, crash_at=None) -> RunResult

1. Orchestrator reads the claim view. Unknown -> `failed`, missing order_id -> `needs_info`.
2. One simulated planner call, then a typed handoff from `make_handoff`:
   no facts (the only source before investigation is the untrusted ticket),
   read-only tools only. No parent_secret, headers or claim row.
3. `run_readonly_investigators` runs `lookup_order` under the claim's principal.
   Not visible -> `escalated`.
4. Orchestrator quotes itself from the investigator's structured order view,
   then calls `durability.issue_refund(conn, claim_id, <full quote>)`.
   Investigators have no write registry. Host maps ok -> resolved,
   conflict -> failed, other refusal -> denied.

An LLM summary of the parent context is not a sanitizer. Use the allowlist.

Trace contract v1 (docs/contracts.md): every return path writes `traces/<run_id>.json`.
The trace holds the sanitized handoff (`safe_dump`), visibility and the quote,
never the parent context, the ticket or raw rows.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from lab8.db import connect
from lab8.durability import issue_refund
from lab8.handoff import make_handoff
from lab8.mock_llm import complete
from lab8.runtime import run_readonly_investigators
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish, safe_dump
from lab8.tools import compute_compensation, get_claim_view, tool_cost
from lab8.trace import Trace

SHAPE = "orchestrator"
TASK = "verify_order_for_shipping_refund"
INVESTIGATOR_TOOLS = ["lookup_order"]


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
        # Always close: an open handle locks the .sqlite file on Windows.
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
    except Exception as exc:  # run_claim must never raise (HandoffError included).
        return done("failed", 0, f"exception:{type(exc).__name__}")


def _investigate(conn, claim: dict[str, Any], *, seed: int, budget: Budget, trace: Trace) -> dict[str, Any]:
    """Plan, delegate through an allowlisted handoff, return the investigator's order view."""
    claim_id = claim["claim_id"]
    # Simulated planner call. The prompt holds ids only, never ticket text.
    complete(budget, seed=seed, purpose="plan", prompt=f"{claim_id}|task={TASK}")

    # facts stays empty: before investigation the only source for delay / status
    # is the ticket, which is untrusted. make_handoff also drops non-FACT_KEYS
    # and refuses canary secrets or write tools.
    handoff = make_handoff(
        request_id=f"REQ-{claim_id}",
        claim_id=claim_id,
        task=TASK,
        facts={},
        allowed_tools=INVESTIGATOR_TOOLS,
    )
    trace.add("handoff", safe_dump(handoff))

    investigated = run_readonly_investigators(conn, budget, handoff, principal_id=claim["principal_id"])
    order_view = investigated["tools"].get("lookup_order") or {}
    # Trace visibility only, not the order row.
    trace.add("investigator", {"order_id": claim["order_id"], "visible": order_view.get("visible"), "reason": order_view.get("reason")})
    return order_view


def _steps(conn, claim_id, *, seed: int, budget: Budget, trace: Trace, crash_at, done) -> RunResult:
    # Step 1: claim view (allowlisted columns).
    budget.add_tool(tool_cost())
    claim = get_claim_view(conn, claim_id)
    if not claim["found"]:
        return done("failed", 0, "unknown_claim")
    if not claim["order_id"]:
        return done("needs_info", 0, "missing_order_id")

    # Steps 2-3: delegate the order lookup to a read-only investigator.
    order_view = _investigate(conn, claim, seed=seed, budget=budget, trace=trace)
    if not order_view.get("visible"):
        return done("escalated", 0, order_view.get("reason"))

    # Step 4: the orchestrator quotes from the structured order view itself.
    budget.add_tool(tool_cost())
    quote = compute_compensation(conn, order_view["order"])
    amount = int(quote["amount_vnd"])
    trace.add("quote", {"amount_vnd": amount, "reason": quote["reason"], "clause_ids": quote["clause_ids"]})
    complete(budget, seed=seed, purpose="synthesize", prompt=f"{claim_id}|quote={amount}")
    if amount <= 0:
        return done("denied", 0, quote["reason"])

    # Host is the only writer. Pass the FULL quote.
    # TODO CP3 (student): truyền crash_at vào durability.issue_refund, không bắt InjectedCrash.
    outcome = issue_refund(conn, claim_id, amount)
    trace.add("issue_refund", {"ok": outcome["ok"], "reason": outcome["reason"], "conflict": outcome["conflict"]})
    if outcome["ok"]:
        return done("resolved", amount, None)
    if outcome["conflict"]:
        return done("failed", amount, outcome["reason"])
    return done("denied", amount, outcome["reason"])
