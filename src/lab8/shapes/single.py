"""Shape B — one ReAct agent. Student work.

Use `lab8.runtime.run_react` with max_steps=8. `decide` may pick a read tool.
It must not call `issue_refund`. After the loop, the host validates the quote
and is the only writer.

A decide() that trusts ticket text over the order row will fail hidden claims
where the customer overstates the delay or cites a superseded clause.

Per-order cap: an order may already have been refunded by an earlier claim.
The read tool `lookup_refund_history` shows how much. The host still enforces
the cap, so pass the full quote to `durability.issue_refund`, not a net amount.

Caps: stop at 8 steps. Count model calls in the Budget so cost stays comparable.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.mock_llm import complete
from lab8.runtime import run_react
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish, safe_dump
from lab8.trace import Trace


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


def _run(
    conn: sqlite3.Connection,
    claim_id: str,
    *,
    seed: int,
    crash_at: str | None,
) -> RunResult:
    budget = Budget()
    run_id = make_run_id("single", claim_id, seed)
    trace = Trace(run_id)

    state: dict[str, Any] = {
        "step": 0,
        "claim": None,
        "order": None,
        "refund_history": None,
        "quote": None,
    }

    def decide(observation: dict[str, Any]) -> dict[str, Any]:
        step = state["step"]
        state["step"] = step + 1

        # Step 0: Read claim via allowlisted read tool (never exposes parent_secret)
        if step == 0:
            trace.add("react_step", {"step": 1, "action": "get_claim_view", "claim_id": claim_id})
            return {"tool": "get_claim_view", "args": {"claim_id": claim_id}}

        last_tool = observation.get("last_tool")
        last_result = observation.get("last_result") or {}

        # Step 1: Validate claim existence & order_id; parse ticket with LLM (untrusted data)
        if last_tool == "get_claim_view":
            if not last_result.get("found"):
                trace.add("error", {"reason": "unknown_claim"})
                return {"final": {"status": "failed", "proposal_amount": 0, "error_reason": "unknown_claim"}}

            state["claim"] = last_result
            ticket = str(last_result.get("ticket") or "")
            # Count model call in Budget; treat ticket text strictly as untrusted data
            complete(budget, seed=seed, purpose="parse", prompt=ticket)

            order_id = last_result.get("order_id")
            if not order_id:
                trace.add("decision", {"status": "needs_info", "reason": "missing_order_id"})
                return {"final": {"status": "needs_info", "proposal_amount": 0, "error_reason": "missing_order_id"}}

            trace.add("react_step", {"step": 2, "action": "lookup_order", "order_id": order_id})
            return {
                "tool": "lookup_order",
                "args": {
                    "order_id": order_id,
                    "principal_id": last_result["principal_id"],
                },
            }

        # Step 2: Check order visibility/ownership, then inspect prior refund history
        if last_tool == "lookup_order":
            trace.add(
                "observation",
                {
                    "tool": "lookup_order",
                    "visible": bool(last_result.get("visible")),
                    "reason": last_result.get("reason"),
                },
            )
            if not last_result.get("visible"):
                reason = last_result.get("reason") or "not_found"
                return {"final": {"status": "escalated", "proposal_amount": 0, "error_reason": reason}}

            state["order"] = last_result["order"]
            claim_info = state["claim"]
            trace.add("react_step", {"step": 3, "action": "lookup_refund_history", "order_id": claim_info["order_id"]})
            return {
                "tool": "lookup_refund_history",
                "args": {
                    "order_id": claim_info["order_id"],
                    "principal_id": claim_info["principal_id"],
                },
            }

        # Step 3: Record refund history, then compute deterministic compensation from DB truth
        if last_tool == "lookup_refund_history":
            state["refund_history"] = last_result
            trace.add(
                "observation",
                {
                    "tool": "lookup_refund_history",
                    "refund_count": last_result.get("refund_count", 0),
                    "refunded_vnd": last_result.get("refunded_vnd", 0),
                },
            )
            trace.add("react_step", {"step": 4, "action": "compute_compensation"})
            return {
                "tool": "compute_compensation",
                "args": {"order": state["order"]},
            }

        # Step 4: Finalize quote and exit ReAct loop
        if last_tool == "compute_compensation":
            state["quote"] = last_result
            proposal = int(last_result.get("amount_vnd", 0))
            trace.add("quote", safe_dump(last_result))
            if proposal <= 0:
                return {
                    "final": {
                        "status": "denied",
                        "proposal_amount": 0,
                        "error_reason": last_result.get("reason"),
                    }
                }
            return {
                "final": {
                    "status": "ready_to_issue",
                    "proposal_amount": proposal,
                    "error_reason": None,
                }
            }

        return {"final": {"status": "failed", "proposal_amount": 0, "error_reason": "unexpected_react_state"}}

    react_out = run_react(
        conn,
        budget,
        observation={"claim_id": claim_id},
        decide=decide,
        max_steps=8,
        worker=True,
    )
    final = react_out.get("final") or {}
    status = final.get("status", "failed")
    proposal = int(final.get("proposal_amount") or 0)
    error_reason = final.get("error_reason")

    # Early termination states (unknown_claim, needs_info, escalated, denied with quote=0, step_cap)
    if status != "ready_to_issue":
        if status in {"needs_info", "escalated", "denied"}:
            complete(budget, seed=seed, purpose="draft", prompt=status)
        return finish(
            conn,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status=status,
            proposal_amount=proposal,
            budget=budget,
            trace=trace,
            error_reason=error_reason,
        )

    # Draft response and pass full quote to host durability gate
    complete(budget, seed=seed, purpose="draft", prompt=f"proposal={proposal}")

    try:
        outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
    except InjectedCrash:
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise

    if not outcome["ok"]:
        out_status = "failed" if outcome.get("conflict") else "denied"
        return finish(
            conn,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status=out_status,
            proposal_amount=proposal,
            budget=budget,
            trace=trace,
            error_reason=outcome.get("reason"),
        )

    return finish(
        conn,
        shape="single",
        claim_id=claim_id,
        seed=seed,
        status="resolved",
        proposal_amount=proposal,
        budget=budget,
        trace=trace,
        error_reason=None,
    )