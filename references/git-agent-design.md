# Git-Agent Design Notes
**Version:** 1.0.0

This document outlines the theoretical and operational mapping between the
generic PMCR-O cognitive loop and the Git lifecycle.

---

## The Core Mapping Theorem

The Git lifecycle fundamentally mirrors the PMCR-O loop topology. By applying
PMCR-O governance directly to Git operations, the repository itself becomes an
embodied cognitive loop.

| PMCR-O Phase | Git Operation | Notes |
|---|---|---|
| **Cycle Open** | `git checkout -b cycle/<id>` | Isolate the thought process on a branch |
| **Planner** | `git add` (`stage`) | Stage the intent — declare what changes |
| **Maker** | `git commit` | Execute the TYPE 1 state mutation |
| **Checker** | `git diff`, linting, CI/CD | Validate the mutation |
| **Reflector** | `git log --oneline`, branch review | Assess loop success |
| **Cycle Close** | `git tag pmcro/<id>` + `git merge` | Commit to main memory |
| **HIL Escalation** | Open a Pull Request | Require human verification |

---

## TrailFrame Persistence (EC-GIT-002)

Unlike the Orchestrator-Agent which writes separate JSON files to `.pmcro/trails/`,
the Git-Agent uses two persistence channels simultaneously:

1. **JSON TrailFrames** in `.pmcro/trails/<cycle_id>/<loop>.json` — the standard
   PMCR-O self-frame log, written by `run_cycle.py` / `log_frame.py` exactly as
   any other agent. This is the cognitive audit trail.

2. **Commit message embedding** — the `pmcro-trail:` prefix in commit bodies
   ties the reasoning (the "Why") cryptographically to the execution (the "What")
   via the commit SHA. This ensures the repository history itself is a secondary
   trail database.

The JSON TrailFrame is the authoritative record; the commit message is the
portable, distributed copy.

---

## The `git_action` Domain Extension

The git-agent's `route_cycle.py` adds a `git_action` field to every frame. This
field is what the Maker reads to select which git command to run. The frame schema
is otherwise identical to the universal template:

```
routed_to: "planner"  -->  git_action: "stage"
routed_to: "maker"    -->  git_action: "commit"
routed_to: "checker"  -->  git_action: "diff_test"
routed_to: "reflector"-->  git_action: "log_review"
routed_to: "hil"      -->  git_action: "open_pr"
routed_to: "closed"   -->  git_action: "tag_and_merge"
```

This maintains 100% schema parity with the Master Template while adding
domain-specific actionability.

---

## MaxLoops and PR Promotion (GIT-007)

A standard feature branch runs in `ITERATIVE` O-Mode. If the agent fails to
pass the Checker/Reflector gates within `max_loops` commits, it is no longer
allowed to blindly retry. The Git-Agent automatically escalates to `hil` with
`git_action: "open_pr"`, acting as a mandatory Human-in-the-Loop gate.

This mirrors the universal ORC-007 / EC-009 guardrail but expresses it in
git-native terms: loop budget exhausted = PR required.

---

## Protected Branch Authorization (GIT-018)

Any operation on a protected branch (main, release/*) requires a valid HIL
token before the Maker is dispatched. This maps to MAAI-001 in the universal
framework. Without a token, the agent routes to `hil` and opens a PR,
requiring a human to review and approve before merge.

---

## Routing Precedence Order

`route_cycle.py` evaluates conditions in this fixed sequence:

1. **GIT-010** — Governance BLOCK/ESCALATE → open PR immediately
2. **GIT-018** — Protected branch without HIL token → open PR
3. **GIT-007** — MaxLoops ceiling reached + RETRY → open PR
4. **GIT-022** — Reflector ACCEPT → tag and merge; RETRY → re-stage on next loop
5. **GIT-001/004** — Sequential phase progression (init→stage, plan→commit, make→diff, check→review)

---

## Eval Coverage

See `evals/eval_cases.json` for the 8 canonical test cases covering:
- All 4 standard phase progressions (init, planner, maker, checker)
- Governance BLOCK escalation (GIT-010)
- Protected branch authorization (GIT-018)
- MaxLoops PR promotion (GIT-007)
- ACCEPT cycle close (GIT-022)
- RETRY with O-Mode suggestion (GIT-022)
