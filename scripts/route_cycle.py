"""
route_cycle.py — Orchestrator Routing Engine (Pure)
==================================================
Deterministic routing logic for the PMCR-O cognitive loop.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

def route(payload: Dict[str, Any], governor_verdicts: List[str]) -> Dict[str, Any]:
    """
    Determines the next phase of the PMCR-O loop based on input state
    and governance verdicts.
    """
    # Initialize the OrchestratorFrame
    frame = {
        "cycle_id": payload.get("cycle_id", f"CycleQ-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"),
        "loop": int(payload.get("loop", 1)),
        "o_mode": payload.get("o_mode", "DIRECT"),
        "routed_to": None,
        "reason": None,
        "hil_required": False,
        "trail_written": False,
        "earned_constraints": payload.get("constraints_active", []),
        "notes": [],
        "cycle_id_self": f"CycleQ-ORCHSTR-{uuid.uuid4().hex[:8].upper()}"
    }

    # 1. ORC-010: Governance Pre-Check
    if "BLOCK" in governor_verdicts or "ESCALATE" in governor_verdicts:
        frame.update({
            "routed_to": "hil",
            "hil_required": True,
            "reason": "ORC-010: C-suite governance verdict (BLOCK/ESCALATE) detected."
        })
        return frame

    # 2. ORC-018: TYPE 1 Authorization
    if payload.get("type1_action_requested", False):
        if not _valid_hil_token(payload.get("hil_token")):
            frame.update({
                "routed_to": "hil",
                "hil_required": True,
                "reason": "ORC-018: TYPE 1 action requested without valid HIL token."
            })
            return frame

    # 3. ORC-007: MaxLoops Guardrail (EC-009)
    if frame["loop"] >= payload.get("max_loops", 3) and payload.get("reflector_verdict") == "RETRY":
        frame.update({
            "routed_to": "hil",
            "hil_required": True,
            "reason": "ORC-007: MaxLoops ceiling reached (EC-009); escalating to HIL."
        })
        return frame

    # 4. ORC-022: Reflector Verdicts
    verdict = payload.get("reflector_verdict")
    if verdict == "ACCEPT":
        frame.update({
            "routed_to": "closed",
            "reason": "ORC-022: Reflector issued ACCEPT verdict."
        })
        return frame
    
    if verdict == "ESCALATE":
        frame.update({
            "routed_to": "hil",
            "hil_required": True,
            "reason": "ORC-022: Reflector issued ESCALATE verdict."
        })
        return frame

    if verdict == "RETRY":
        frame["loop"] += 1
        frame["routed_to"] = "planner"
        frame["o_mode"] = payload.get("suggest_o_mode", "ITERATIVE")
        frame["reason"] = f"ORC-022: Reflector issued RETRY; entering loop {frame['loop']}."
        return frame

    # 5. ORC-001 / ORC-004: Sequential Phase Routing
    phase_map = {
        "init": "planner",
        "planner": "maker",
        "maker": "checker",
        "checker": "reflector"
    }
    
    current_phase = payload.get("current_phase", "init")
    if current_phase in phase_map:
        frame["routed_to"] = phase_map[current_phase]
        frame["reason"] = f"ORC-004: Sequential phase progression: {current_phase} -> {frame['routed_to']}."
    else:
        frame.update({
            "routed_to": "hil",
            "hil_required": True,
            "reason": f"ORC-999: Unknown or invalid current_phase: {current_phase}."
        })

    return frame

def _valid_hil_token(token: Optional[str]) -> bool:
    return token is not None and len(str(token)) > 8