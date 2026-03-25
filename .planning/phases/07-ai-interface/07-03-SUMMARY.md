---
phase: 07-ai-interface
plan: "03"
subsystem: controller

# Dependency graph
requires:
  - phase: 07-ai-interface
    plan: "01"
    provides: AIPlayer ABC, EngineSnapshot
  - phase: 07-ai-interface
    plan: "02"
    provides: RandomAI implementation
provides:
  - GameController orchestration layer connecting engine, AI, and UI
  - AIWorker QThread-based background AI computation
  - Status bar turn indicator (红方回合 / AI 思考中...)
  - Game over popup (QMessageBox with 红胜/黑胜/和棋)
affects:
  - phase 08-game-control (new game button, undo)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - QThread + moveToThread() worker pattern for AI computation
    - EngineSnapshot for thread-safe state capture
    - is_legal() guard before every AI move apply (D-11)
    - Signal-based orchestration (turn_changed, game_over, ai_thinking_started/finished)

key-files:
  created:
    - src/xiangqi/controller/__init__.py
    - src/xiangqi/controller/ai_worker.py
    - src/xiangqi/controller/game_controller.py
    - tests/controller/__init__.py
    - tests/controller/conftest.py
    - tests/controller/test_ai_worker.py
    - tests/controller/test_game_controller.py
  modified:
    - src/xiangqi/ui/main.py

key-decisions:
  - "GameController is single orchestrator - owns engine, AI, board refs"
  - "Board never calls engine directly for moves - only through controller"
  - "is_legal() guard mandatory before every AI move apply (D-11)"
  - "Thread cleanup with deleteLater prevents memory leaks"

patterns-established:
  - "Pattern 1: QThread + moveToThread() for AI computation off main thread"
  - "Pattern 2: EngineSnapshot deep copy for thread safety"
  - "Pattern 3: Signal-based game flow (move_applied -> turn_changed -> ai_thinking)"

requirements-completed:
  - AI-04
  - UI-06
  - UI-07

# Metrics
duration: 8min
completed: 2026-03-25
---
# Phase 07 Plan 03: GameController Summary

**GameController orchestration layer with QThread-based AI worker, status bar turn indicator, and game over popup for human-vs-AI gameplay**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-25T14:24:36Z
- **Completed:** 2026-03-25T14:32:22Z
- **Tasks:** 4 (3 code + 1 manual verification)
- **Files modified:** 9

## Accomplishments
- GameController orchestrates engine, AI, and UI signals in single class
- AIWorker runs AI computation in background QThread using moveToThread pattern
- Status bar shows "红方回合" on red's turn, "AI 思考中..." during AI thinking
- Game over shows QMessageBox with Chinese result text (红胜/黑胜/和棋)
- Board interaction disabled during AI thinking via set_interactive(False)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create AIWorker for QThread-based AI computation** - `dbf8531` (feat)
2. **Task 2: Create GameController orchestration layer** - `3f37f1e` (feat)
3. **Task 3: Wire MainWindow with GameController** - `ef3c255` (feat)
4. **Task 4: Manual UAT verification** - (no commit - manual verification only)

_Note: TDD tasks may have multiple commits (test -> feat -> refactor)_

## Files Created/Modified
- `src/xiangqi/controller/__init__.py` - Package init exporting GameController, AIWorker
- `src/xiangqi/controller/ai_worker.py` - QThread worker for AI computation
- `src/xiangqi/controller/game_controller.py` - Orchestration layer for engine + AI + UI
- `tests/controller/__init__.py` - Test package init
- `tests/controller/conftest.py` - pytest-qt fixtures for controller tests
- `tests/controller/test_ai_worker.py` - 4 tests for AIWorker
- `tests/controller/test_game_controller.py` - 5 tests for GameController
- `src/xiangqi/ui/main.py` - Updated to create GameController with engine, AI, board

## Decisions Made
- Used QThread + moveToThread() pattern per Qt official recommendation (D-04 to D-06)
- GameController receives board and window references (not owning them)
- is_legal() guard raises ValueError on illegal AI move (D-11, D-12)
- Status bar updates via internal signal connections

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Mock QMessageBox in test**
- **Found during:** Task 2 (GameController test)
- **Issue:** QMessageBox.information() requires real QWidget parent, Mock fails
- **Fix:** Patched QMessageBox.information in test to avoid Qt widget requirement
- **Files modified:** tests/controller/test_game_controller.py
- **Verification:** All 5 GameController tests pass
- **Committed in:** 3f37f1e (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Test infrastructure fix only. No scope creep.

## Issues Encountered
None - implementation followed plan as specified

## User Setup Required
None - no external service configuration required.

## Manual UAT Required

Task 4 requires manual verification. To test:

1. Launch: `conda activate xqrl && python -m src.xiangqi.ui.main`
2. Verify initial status bar shows "红方回合"
3. Click a red piece and move it to a legal target
4. Verify status shows "AI 思考中..." then returns to "红方回合" after AI moves
5. Play a few moves to verify alternating gameplay

## Next Phase Readiness
- GameController ready for Phase 08 (new game button, undo)
- AI worker thread pattern established for future AI implementations

---
*Phase: 07-ai-interface*
*Completed: 2026-03-25*

## Self-Check: PASSED

All created files and commits verified:
- src/xiangqi/controller/__init__.py - FOUND
- src/xiangqi/controller/ai_worker.py - FOUND
- src/xiangqi/controller/game_controller.py - FOUND
- tests/controller/test_ai_worker.py - FOUND
- tests/controller/test_game_controller.py - FOUND
- Commit dbf8531 (Task 1) - FOUND
- Commit 3f37f1e (Task 2) - FOUND
- Commit ef3c255 (Task 3) - FOUND
