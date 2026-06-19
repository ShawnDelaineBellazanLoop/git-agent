"""
route_cycle.py — Git-Agent Routing Engine (v1.1.0)
==================================================
PMCR-O v1.5.0 logic mapped to the Git Lifecycle.
Maintains 100% schema parity with pmcro-agent-template v4.4.2.
Domain extension: adds `git_action` field for Maker git command selection.

o_mode       — cognitive technique (OUTPUT/OPTIMIZE/ORCHESTRATE/COT/TOT/GOT/REACT/THOUGHTLOCK)
cycle_policy — loop execution behavior (DIRECT/ITERATIVE/REFLECTIVE/ESCALATION/AUDIT)
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional


def route(payload: Dict[str, Any], governor_verdicts: List[str]) -> Dict[str, Any]:
    """
    Standard PMCR-O routing logic mapped to Git lifecycle actions.
    Frame schema is identical to the universal template; `git_action` is a
    domain extension field the Maker reads to select the git command.
    """
    frame = {
        "cycle_id": payload.get("cycle_id", f"CycleQ-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"),
        "loop": int(payload.get("loop", 1)),
        "o_mode": payload.get("o_mode", "OUTPUT"),
        "cycle_policy": payload.get("cycle_policy", "ITERATIVE"),
        "routed_to": None,
        "domain_action": None,
        "reason": None,
        "hil_required": False,
        "trail_written": False,
        "earned_constraints": payload.get("constraints_active", []),
        "notes": [],
        "cycle_id_self": f"CycleQ-GIT-{uuid.uuid4().hex[:8].upper()}",
        # Domain extension: Maker uses this to select the git command
        "git_action": None
    }

    # 1. GIT-010: Governance Pre-Check (BLOCK/ESCALATE wins immediately)
    if "BLOCK" in governor_verdicts or "ESCALATE" in governor_verdicts:
        frame.update({
            "routed_to": "hil",
            "git_action": "open_pr",
            "hil_required": True,
            "reason": "GIT-010: Governance block; escalating to Pull Request review."
        })
        return frame

    # 2. GIT-018: Authorization (Protected Branch check)
    if payload.get("branch_protected", False) and not _valid_hil_token(payload.get("hil_token")):
        frame.update({
            "routed_to": "hil",
            "git_action": "open_pr",
            "hil_required": True,
            "reason": "GIT-018: HIL token required for protected branch operations."
        })
        return frame

    # 3. GIT-007: MaxLoops (EC-009)
    if frame["loop"] >= payload.get("max_loops", 3) and payload.get("reflector_verdict") == "RETRY":
        frame.update({
            "routed_to": "hil",
            "git_action": "open_pr",
            "hil_required": True,
            "reason": "GIT-007: MaxLoops reached; promoting local cycle to PR review."
        })
        return frame

    # 4. GIT-022: Reflector Verdicts
    verdict = payload.get("reflector_verdict")
    if verdict == "ACCEPT":
        frame.update({
            "routed_to": "closed",
            "git_action": "tag_and_merge",
            "reason": "GIT-022: Reflector ACCEPT; sealing cycle with tag and merge to main."
        })
        return frame

    if verdict == "RETRY":
        frame["loop"] += 1
        frame["routed_to"] = "planner"
        frame["git_action"] = "stage"
        # suggest_o_mode governs loop behavior → applied to cycle_policy
        frame["cycle_policy"] = payload.get("suggest_o_mode", payload.get("suggest_cycle_policy", "ITERATIVE"))
        frame["reason"] = f"GIT-022: RETRY issued; re-entering loop {frame['loop']}."
        return frame

    # 5. GIT-001 / GIT-004: Sequential Phase Routing
    phase_map = {
        "init":    ("planner",   "stage"),
        "planner": ("maker",     "commit"),
        "maker":   ("checker",   "diff_test"),
        "checker": ("reflector", "log_review"),
    }

    current_phase = payload.get("current_phase", "init")
    if current_phase in phase_map:
        frame["routed_to"], frame["git_action"] = phase_map[current_phase]
        frame["reason"] = f"GIT-004: Phase progression: {current_phase} -> {frame['routed_to']}."
    else:
        frame.update({
            "routed_to": "hil",
            "git_action": "open_pr",
            "hil_required": True,
            "reason": f"GIT-999: Unknown phase '{current_phase}'; escalating for review."
        })

    # Domain projection
    domain_map = payload.get("domain_map")
    if domain_map and frame["routed_to"]:
        frame["domain_action"] = domain_map.get(frame["routed_to"], frame["git_action"])
    else:
        frame["domain_action"] = frame["git_action"]

    return frame


def _valid_hil_token(token: Optional[str]) -> bool:
    """Stub for HIL token verification (MAAI-001). Replace with real verifier in production."""
    return token is not None and len(str(token)) > 8
