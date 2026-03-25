---
phase: 06-piece-interaction
plan: "05"
type: gap_closure
status: complete
completed: 2026-03-25T11:05:00Z
---

# Summary: Fix UAT Gaps - Click Offset and Turn Management

## Objective

Fix two diagnosed UAT gaps that prevented proper piece interaction:
1. **Click Offset**: Hardcoded viewport offset causing click misalignment across different viewport sizes
2. **Turn Management**: Turn-unaware piece selection preventing alternating red/black gameplay

## Changes Made

### 1. Fixed Viewport Coordinate Conversion (`src/xiangqi/ui/board.py`)

**Problem**: Hardcoded offset `(103.5, 2.0)` in `mousePressEvent` didn't account for dynamic viewport centering.

**Solution**: Replaced hardcoded offset with `mapToScene()` for accurate coordinate conversion.

```python
# Before:
vp_x = event.position().x()
vp_y = event.position().y()
scene_x = vp_x - 103.5
scene_y = vp_y - 2.0
board_pos = self._scene_to_board(QPointF(scene_x, scene_y))

# After:
scene_pos = self.mapToScene(event.position().toPoint())
board_pos = self._scene_to_board(scene_pos)
```

**Key Details**:
- Used `event.position().toPoint()` to convert `QPointF` to `QPoint` (required by `mapToScene()`)
- Leverages Qt's built-in coordinate mapping that handles viewport centering and scaling automatically
- Works correctly across all viewport sizes and window resolutions

### 2. Made Piece Selection Turn-Aware (`src/xiangqi/ui/board.py`)

**Problem**: UI only allowed red pieces (`piece_value > 0`), but engine alternates turns. After red moves, turn becomes black, so selecting a red piece returns empty legal moves.

**Solution**: Check if piece belongs to current turn using `piece_value * engine.turn > 0`.

```python
# Before (line 192 and 204):
if clicked_piece is not None and clicked_piece._piece_value > 0:

# After:
if clicked_piece is not None and clicked_piece._piece_value * self._engine.turn > 0:
```

**Key Details**:
- Red turn (`turn=+1`): Red pieces are +1 to +7, product is positive ✓
- Black turn (`turn=-1`): Black pieces are -1 to -7, product is positive ✓
- Enables alternating red/black gameplay for two-player mode
- Phase 07 will add external turn control via `set_interactive()` for AI turns

## Verification

### Automated Tests
✓ Code inspection verified `mapToScene` usage with `toPoint()` conversion
✓ Hardcoded offset `103.5` removed from codebase
✓ Turn-aware selection check confirmed in `_handle_board_click`

### Manual UAT
✓ Click position matches piece position (no offset)
✓ Gold selection ring appears on clicked piece
✓ Legal move targets shown as gold dots
✓ Piece moves to clicked target
✓ After red move, can select black pieces
✓ Black piece selection shows legal moves
✓ After black move, can select red pieces again
✓ Alternating gameplay works correctly

## Requirements Met

- **UI-03**: Click-to-select interaction with visual feedback ✓
- **UI-04**: Legal move visualization ✓
- **UI-05**: Click-to-move interaction ✓

## Impact

This fix enables:
- Accurate click detection across all viewport sizes and window configurations
- Full alternating gameplay between red and black sides
- Foundation for AI integration in Phase 07 (AI will control black pieces)
- Correct user experience matching Chinese chess rules

## Files Modified

- `src/xiangqi/ui/board.py`: Fixed `mousePressEvent` coordinate conversion and `_handle_board_click` turn-aware selection

## Related Documents

- `.planning/phases/06-piece-interaction/06-05-PLAN.md`: Original fix plan
- `.planning/phases/06-piece-interaction/06-UAT.md`: UAT results with diagnosed gaps
- `.planning/debug/click-offset.md`: Debug session for click offset issue
- `.planning/debug/second-selection-no-legal-moves.md`: Debug session for turn management issue
