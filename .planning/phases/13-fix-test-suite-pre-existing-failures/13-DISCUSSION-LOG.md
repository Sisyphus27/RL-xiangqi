# Phase 13: Fix Test Suite Pre-Existing Failures - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-28
**Phase:** 13-fix-test-suite-pre-existing-failures
**Areas discussed:** (none — mechanical fixes, no ambiguity)

---

## Phase Analysis

6 failing tests with 2 diagnosed root causes. Both fixes are mechanical with no meaningful design choices.

### Root Cause 1: from_fen 3-tuple (5 tests)

| Option | Description | Selected |
|--------|-------------|----------|
| Unpack 3 values | `board, turn, _ = from_fen(...)` | ✓ |
| Unpack with named var | `board, turn, halfmove_clock = from_fen(...)` | |

**User's choice:** Mechanical fix — no discussion needed
**Notes:** User confirmed no discussion needed for either root cause

### Root Cause 2: Async AI thread race (1 test)

| Option | Description | Selected |
|--------|-------------|----------|
| Mock AI worker | Prevent real thread spawning | ✓ |
| Add thread cleanup | Wait for thread in conftest teardown | |
| Use qtbot.waitSignal | Proper async test pattern | |

**User's choice:** Mock approach — Claude's discretion on exact strategy

---

## Claude's Discretion

- Exact mock strategy for AI worker thread prevention
- Whether to add explicit thread cleanup in conftest.py

## Deferred Ideas

- UI bugs in `.planning/debug/` — v0.2 scope, not test failures
- Phase 11-02 (R4/R5 test coverage) — unexecuted plan, separate phase
