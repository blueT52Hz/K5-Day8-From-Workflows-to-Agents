"""Shape A - deterministic workflow.

Signature (do not change):

    run_claim(claim_id, *, seed, store_path, crash_at=None) -> RunResult

Fixed Python steps, no model decides anything:

1. Read the claim through `get_claim_view` (allowlisted columns, not SELECT *).
2. Missing order_id -> `needs_info`. No ledger write.
3. `lookup_order` with the claim's principal. Not visible -> `escalated`.
4. Quote from the structured order row via `compute_compensation`.
   Delay numbers written in the ticket are user data and are ignored.
5. Quote 0 -> `denied`. `issue_refund` is not called.
6. Quote > 0 -> `durability.issue_refund(conn, claim_id, <full quote>)`.
   The host checks the approval, subtracts earlier refunds on the same order
   and writes `policy_denied` when it refuses. `proposal_amount` stays the full quote.
7. Host ok -> `resolved`; conflict -> `failed`; other refusal -> `denied`.

Trace contract v1 (docs/contracts.md): every return path writes `traces/<run_id>.json`.
The trace only carries decisions, the order id and the quote. It never carries
the ticket, the claim row or the order row (secret / PII boundary).
"""

from __future__ import annotations

import sqlite3

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.tools import compute_compensation, get_claim_view, lookup_order, tool_cost
from lab8.trace import Trace

SHAPE = "workflow"


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
        return _steps(conn, claim_id, budget=budget, trace=trace, crash_at=crash_at, done=done)
    except InjectedCrash:
        # Fault-lab crash: flush the trace, then let it propagate (T12 checks it fired).
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise
    except Exception as exc:  # run_claim must never raise: report a failed trial instead.
        return done("failed", 0, f"exception:{type(exc).__name__}")


def _steps(conn, claim_id, *, budget: Budget, trace: Trace, crash_at, done) -> RunResult:
    # Step 1: claim view (only claim_id, principal_id, order_id, ticket).
    budget.add_tool(tool_cost())
    claim = get_claim_view(conn, claim_id)
    if not claim["found"]:
        return done("failed", 0, "unknown_claim")

    # Step 2: order id must come from the claim column, never from ticket text.
    order_id = claim["order_id"]
    if not order_id:
        return done("needs_info", 0, "missing_order_id")

    # Step 3: ownership check is done by lookup_order (principal scope).
    budget.add_tool(tool_cost())
    view = lookup_order(conn, order_id, claim["principal_id"])
    trace.add("lookup_order", {"order_id": order_id, "visible": view["visible"], "reason": view["reason"]})
    if not view["visible"]:
        return done("escalated", 0, view["reason"])

    # Step 4: money is computed by code from the structured order row.
    budget.add_tool(tool_cost())
    quote = compute_compensation(conn, view["order"])
    amount = int(quote["amount_vnd"])
    trace.add("quote", {"amount_vnd": amount, "reason": quote["reason"], "clause_ids": quote["clause_ids"]})

    # Step 5: nothing to pay -> deny without touching the host.
    if amount <= 0:
        return done("denied", 0, quote["reason"])

    # Step 6: host is the only writer. Pass the FULL quote and crash_at through.
    # Retry safety comes from the ledger key refund:{claim_id}, not from a checkpoint.
    outcome = issue_refund(conn, claim_id, amount, crash_at=crash_at)
    trace.add("issue_refund", {"ok": outcome["ok"], "reason": outcome["reason"], "conflict": outcome["conflict"]})

    # Step 7: map the host outcome to the output contract.
    if outcome["ok"]:
        return done("resolved", amount, None)
    if outcome["conflict"]:
        return done("failed", amount, outcome["reason"])
    return done("denied", amount, outcome["reason"])
