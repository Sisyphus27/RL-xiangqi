---
plan: 07-02
phase: 07-ai-interface
status: complete
completed: 2026-03-25T22:30:00+08:00
requirements:
  - AI-03
key-files:
  created:
    - path: src/xiangqi/ai/random_ai.py
      desc: RandomAI implementation with seed support
    - path: tests/ai/test_random_ai.py
      desc: 5 tests for RandomAI behavior
  modified:
    - path: src/xiangqi/ai/__init__.py
      desc: Added RandomAI export
---

# Summary: RandomAI Implementation

## What was built

Implemented `RandomAI` class - the baseline AI player that selects random legal moves.

### Key Components

1. **`src/xiangqi/ai/random_ai.py`**
   - `RandomAI(AIPlayer)` class with optional seed parameter
   - Uses `random.Random(seed)` for independent RNG (not global)
   - `suggest_move()` returns random choice from `snapshot.legal_moves`
   - Returns `None` when no legal moves available

2. **`tests/ai/test_random_ai.py`**
   - 5 tests covering:
     - AIPlayer interface compliance
     - Returns legal moves only
     - Returns None on empty legal_moves
     - Seed reproducibility
     - Different seeds produce different sequences

## Verification

All 13 AI tests pass:
- 4 test_base.py (ABC contract)
- 4 test_snapshot.py (immutability)
- 5 test_random_ai.py (RandomAI behavior)

## Requirements Traceability

- **AI-03**: RandomAI returns random legal move ✓

## Decisions

1. **Independent RNG** - Used `random.Random(seed)` instead of global `random` module to avoid test interference
2. **Seed=None default** - Non-deterministic by default, reproducible when seed provided

## Self-Check

- [x] All tasks completed
- [x] Tests pass (13/13)
- [x] Commits created
- [x] No regressions in existing tests
