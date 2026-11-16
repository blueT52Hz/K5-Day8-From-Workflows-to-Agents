"""Shape B - one ReAct agent.

Use `lab8.runtime.run_react` with max_steps=8. `decide` may pick a read tool.
It must not call `issue_refund`. After the loop, the host validates the quote
and is the only writer.

A decide() that trusts ticket text over the order row will fail hidden claims
where the customer overstates the delay or cites a superseded clause.

Per-order cap: an order may already have been refunded by an earlier claim.
The host enforces the cap, so pass the full quote to `durability.issue_refund`,
not a net amount.

Caps: stop at 8 steps. Count model calls in the Budget so cost stays comparable.

Trace contract v1 (docs/contracts.md): every return path writes `traces/<run_id>.json`
with {"run_id", "events"}. The trace holds actions, visibility and the quote,
never the ticket, the claim row or the order row.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.mock_llm import complete
from lab8.runtime import run_react
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.tools import get_claim_view, tool_cost
from lab8.trace import Trace

SHAPE = "single"
MAX_STEPS = 8


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
    except InjectedCrash:
        # Fault-lab crash: flush the trace, then let it propagate (T12 checks it fired).
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise
    except Exception as exc:  # run_claim must never raise: report a failed trial instead.
        return done("failed", 0, f"exception:{type(exc).__name__}")


def _make_decide(claim: dict[str, Any], *, seed: int, budget: Budget, trace: Trace, memory: dict[str, Any]):
    """Build the agent policy (function factory).

    run_react only shows the agent the last tool result, so anything needed
    after that step (step count, quote) is kept in the `memory` closure.
    """
    claim_id = claim["claim_id"]
    order_id = claim["order_id"]
    principal_id = claim["principal_id"]

    def act(tool: str, args: dict[str, Any]) -> dict[str, Any]:
        trace.add("react", {"step": memory["steps"], "action": tool})
        return {"tool": tool, "args": args}

    def final(payload: dict[str, Any]) -> dict[str, Any]:
        trace.add("react", {"step": memory["steps"], "action": "final", "status": payload["status"]})
        return {"final": payload}

    def decide(seen: dict[str, Any]) -> dict[str, Any]:
        last_tool = seen.get("last_tool")
        result = seen.get("last_result") or {}
        memory["steps"] += 1
        # One simulated model call per step. The prompt carries no ticket text or PII.
        complete(
            budget,
            seed=seed,
            purpose="react",
            prompt=f"{claim_id}|step={memory['steps']}|last={last_tool or 'start'}",
        )

        if last_tool is None:
            if not order_id:
                return final({"status": "needs_info", "reason": "missing_order_id"})
            # Ids come from the claim columns, never from ticket text (injection / IDOR).
            return act("lookup_order", {"order_id": order_id, "principal_id": principal_id})

        if last_tool == "lookup_order":
            trace.add("lookup_order", {"order_id": order_id, "visible": result.get("visible"), "reason": result.get("reason")})
            if not result.get("visible"):
                return final({"status": "escalated", "reason": result.get("reason")})
            return act("compute_compensation", {"order": result["order"]})

        if last_tool == "compute_compensation":
            memory["quote"] = int(result["amount_vnd"])
            trace.add("quote", {"amount_vnd": memory["quote"], "reason": result.get("reason"), "clause_ids": result.get("clause_ids")})
            return final({"status": "propose", "amount": memory["quote"], "reason": result.get("reason")})

        return final({"status": "failed", "reason": f"unexpected_tool:{last_tool}"})

    return decide


def _steps(conn, claim_id, *, seed: int, budget: Budget, trace: Trace, crash_at, done) -> RunResult:
    # Host reads the claim once: it needs found / principal before any agent step.
    budget.add_tool(tool_cost())
    claim = get_claim_view(conn, claim_id)
    if not claim["found"]:
        return done("failed", 0, "unknown_claim")

    memory: dict[str, Any] = {"steps": 0, "quote": None}
    decide = _make_decide(claim, seed=seed, budget=budget, trace=trace, memory=memory)
    # The agent sees ids only, no ticket text (untrusted, may carry PII).
    observation = {"claim": {"claim_id": claim_id, "order_id": claim["order_id"]}}
    loop = run_react(conn, budget, observation=observation, decide=decide, max_steps=MAX_STEPS)
    trace.add("react_stop", {"stopped": loop["stopped"], "steps": memory["steps"]})
    if loop["stopped"] != "final":
        return done("failed", 0, "step_cap")

    final = loop["final"]
    status = final.get("status")
    if status == "needs_info":
        return done("needs_info", 0, final.get("reason"))
    if status == "escalated":
        return done("escalated", 0, final.get("reason"))
    if status != "propose" or memory["quote"] is None:
        return done("failed", 0, final.get("reason") or "no_quote")

    # Host validation: trust the recorded tool result, not the agent's final text.
    amount = memory["quote"]
    if final.get("amount") != amount:
        return done("failed", 0, "proposal_mismatch")
    if amount <= 0:
        return done("denied", 0, final.get("reason"))

    # Host is the only writer. Pass the FULL quote and crash_at through.
    outcome = issue_refund(conn, claim_id, amount, crash_at=crash_at)
    trace.add("issue_refund", {"ok": outcome["ok"], "reason": outcome["reason"], "conflict": outcome["conflict"]})
    if outcome["ok"]:
        return done("resolved", amount, None)
    if outcome["conflict"]:
        return done("failed", amount, outcome["reason"])
    return done("denied", amount, outcome["reason"])
