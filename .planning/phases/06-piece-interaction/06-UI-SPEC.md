---
gsd_state_version: 1.0
phase: 06
phase_name: piece-interaction
status: draft
milestone: v0.2
created: "2026-03-25"
---

# UI-SPEC: Phase 06 - Piece Interaction

**Phase Goal:** User clicks own piece (red) to select, legal move targets highlight, click legal target to execute move.

**Design System:** PyQt6 (native desktop, not web framework)

---

## Design Tokens

### Spacing

Using cell-based proportional system (not fixed pixels). Base unit: `cell = min(vw, vh) / 11.2`

| Token | Value | Usage |
|-------|-------|-------|
| `CELL_UNIT` | `1.0 * cell` | Grid cell unit |
| `PIECE_DIAMETER` | `0.80 * cell` | Piece circle size |
| `PIECE_OFFSET` | `0.20 * cell` | Piece rect offset from grid intersection |
| `PIECE_CENTER` | `0.60 * cell` | Piece center offset from cell origin |
| `DOT_DIAMETER` | `0.50 * cell` | Legal move dot size (D-08) |
| `DOT_OFFSET` | `0.35 * cell` | Legal move dot centering offset |
| `RING_DIAMETER` | `0.85 * cell` | Selection ring size (slightly larger than piece) |
| `RING_OFFSET` | `0.15 * cell` | Selection ring centering offset |

### Typography

Already defined in Phase 05 constants.py:

| Token | Ratio | Min | Usage |
|-------|-------|-----|-------|
| `PIECE_FONT_RATIO` | 0.56 | 8px | Piece Chinese character |
| `RIVER_FONT_RATIO` | 0.28 | 10px | "楚河"/"漢界" text |
| `COORD_FONT_RATIO` | 0.22 | 8px | Column/row labels |

Font family: `"SimSun, Microsoft YaHei, Arial"` (Chinese-compatible)

### Color

| Token | Hex | Usage | Allocation |
|-------|-----|-------|------------|
| `BOARD_BG` | #7BA05B | Board background | Dominant (60%) |
| `GRID_COLOR` | #2D5A1B | Grid lines, river text, coord labels | Secondary (30%) |
| `HIGHLIGHT_COLOR` | #FFD700 | Selection ring, legal move dots | Accent (10%) |
| `RED_FILL` | #CC2200 | Red piece fill | Semantic |
| `BLACK_FILL` | #1A1A1A | Black piece fill | Semantic |
| `PIECE_TEXT_COLOR` | #FFFFFF | Piece character text | Supporting |
| `PIECE_STROKE_COLOR` | #FFFFFF | Piece border stroke | Supporting |

**Accent reserved for:**
- Selection ring highlight (D-01)
- Legal move target dots (D-05)

### Opacity

| Token | Value | Usage |
|-------|-------|-------|
| `SELECTION_RING_OPACITY` | 0.70 | Selection ring (70% - Claude's discretion) |
| `LEGAL_DOT_OPACITY` | 0.50 | Legal move dots (D-07) |

### Z-Values (Layer Order)

| Layer | Z-Value | Contents |
|-------|---------|----------|
| Background | 0.0 (implicit) | Board felt, grid, text (drawBackground) |
| Highlights | 0.5 | Legal move dots (Claude's discretion) |
| Pieces | 1.0 | PieceItem instances |
| Selection | 1.1 | Selection ring highlight (D-03) |

### Stroke Widths

| Token | Value | Usage |
|-------|-------|-------|
| `GRID_STROKE` | 1.0px | Grid lines |
| `PIECE_STROKE` | 2.0px | Piece border |
| `RING_STROKE` | 3.0px | Selection ring (Claude's discretion) |

---

## Component Inventory

### Existing Components (Phase 05)

| Component | Location | Description |
|-----------|----------|-------------|
| `QXiangqiBoard` | `src/xiangqi/ui/board.py` | Main board view, QGraphicsView subclass |
| `PieceItem` | `src/xiangqi/ui/board_items.py` | Piece rendering, QGraphicsEllipseItem subclass |
| `constants.py` | `src/xiangqi/ui/constants.py` | Color and ratio constants |

### New Components (Phase 06)

| Component | Parent | Purpose | Implementation |
|-----------|--------|---------|----------------|
| Selection Ring | QGraphicsEllipseItem | Gold outline around selected piece | Dynamic create/delete (D-02) |
| Legal Move Dot | QGraphicsEllipseItem | Gold dot at legal move targets | Dynamic create/delete (D-06) |
| `_piece_index` | dict[tuple[int,int], PieceItem] | O(1) piece lookup by position | Built in _load_pieces (D-15) |
| `move_applied` | pyqtSignal(int, int, int) | Move notification signal | Emitted after successful move (D-20) |

### Component API Extensions

**QXiangqiBoard new instance variables:**

```python
_selected: tuple[int, int] | None        # (row, col) of selected piece
_highlight_items: list[QGraphicsEllipseItem]  # legal move dots
_selection_ring: QGraphicsEllipseItem | None  # selection highlight
_piece_index: dict[tuple[int, int], PieceItem]  # O(1) lookup
_interactive: bool  # interaction enabled flag (default True)
```

**QXiangqiBoard new methods:**

| Method | Signature | Purpose |
|--------|-----------|---------|
| `mousePressEvent` | `(event: QMouseEvent \| None) -> None` | Click handling |
| `_scene_to_board` | `(pos: QPointF) -> tuple[int, int] \| None` | Coordinate conversion |
| `_select_piece` | `(row: int, col: int) -> None` | Select piece, show highlights |
| `_deselect_piece` | `() -> None` | Clear selection and highlights |
| `_show_legal_moves` | `(row: int, col: int) -> None` | Create legal move dots |
| `_clear_highlights` | `() -> None` | Remove all highlight items |
| `_is_legal_target` | `(from_r, from_c, to_r, to_c) -> bool` | Check if target is legal |
| `_execute_move` | `(from_r, from_c, to_r, to_c) -> None` | Apply move to engine |
| `set_interactive` | `(enabled: bool) -> None` | External control of interaction |

**QXiangqiBoard new signal:**

```python
move_applied = pyqtSignal(int, int, int)  # from_sq, to_sq, captured_piece_value
```

---

## Interaction States

### Piece Selection States

| State | Visual | Trigger |
|-------|--------|---------|
| Unselected | Normal piece (white 2px border) | Default |
| Selected | Gold ring highlight (3px, 70% opacity) | Click red piece |
| Legal Target | Gold dot (0.5*cell, 50% opacity) | Derived from selected piece's legal moves |

### Selection Ring Visual Specification

```
Position: (col + 0.15) * cell, (row + 0.15) * cell
Diameter: 0.85 * cell (slightly larger than piece's 0.80)
Pen: QPen(QColor("#FFD700"), 3.0)
Brush: NoBrush (outline only)
Opacity: 0.70
Z-Value: 1.1
```

### Legal Move Dot Visual Specification

```
Position: (col + 0.35) * cell, (row + 0.35) * cell
Diameter: 0.50 * cell
Pen: NoPen
Brush: QBrush(QColor("#FFD700"))
Opacity: 0.50
Z-Value: 0.5
```

### Interaction Flow

```
User clicks board:
  1. If !_interactive: return (silent ignore)
  2. Convert click to (row, col) via mapToScene + rounding
  3. If no current selection:
     - If clicked red piece: select it, show legal moves
     - Else: ignore
  4. If has current selection:
     - If clicked same piece: deselect
     - If clicked another red piece: switch selection
     - If clicked legal target: execute move
     - If clicked illegal target: deselect
```

### Disabled Interaction State

| Condition | Behavior |
|-----------|----------|
| Black turn (AI thinking) | `_interactive = False`, all clicks silently ignored (D-25) |
| Move execution in progress | Temporarily disable to prevent double-click (D-21) |

---

## Copywriting Contract

### User Feedback

| State | Text/Visual | Context |
|-------|-------------|---------|
| Piece selected | Gold ring highlight | Visual only, no text |
| Legal moves shown | Gold dots at targets | Visual only, no text |
| Invalid click | Selection cleared | Visual only, no text |
| Black turn | No response to clicks | Silent, no visual feedback |

### Phase 06 has NO text copy requirements

All feedback is visual (highlights). Text elements (turn indicator, game over) are Phase 07 scope.

---

## Registry

**Tool:** None (PyQt6 desktop application, not shadcn/web)

**Third-party components:** None

**Safety Gate:** Not applicable (no third-party registry)

---

## Responsive Behavior

### Window Resize Handling

When window resizes (resizeEvent):

1. Recalculate `cell = min(vw, vh) / 11.2`
2. Clear all PieceItem instances from scene
3. Re-add pieces at new scale via `_load_pieces()`
4. Rebuild `_piece_index` dictionary
5. If piece is selected:
   - Clear existing highlights
   - Recreate selection ring at new scale
   - Recreate legal move dots at new scale

### Coordinate System Reference

```
Scene bounds: (0, 0) to (10.2*cell, 11.2*cell)
Grid bounds: (0.6*cell, 0.6*cell) to (9.6*cell, 9.6*cell)
Piece center: (col + 0.6) * cell, (row + 0.6) * cell
Board coordinate: row 0 = top (black home), row 9 = bottom (red home)
```

### Scene-to-Board Conversion

```python
def _scene_to_board(pos: QPointF) -> tuple[int, int] | None:
    col = round(pos.x() / cell - 0.6)
    row = round(pos.y() / cell - 0.6)
    if 0 <= row < 10 and 0 <= col < 9:
        return (row, col)
    return None
```

---

## Accessibility

### Keyboard Support

Not in Phase 06 scope (MVP is mouse-only interaction).

### Visual Accessibility

- Gold highlight (#FFD700) provides 4.5:1 contrast against green board (#7BA05B)
- Semi-transparency ensures board grid remains visible
- Selection ring is 3px thick for visibility

---

## Animation

**Phase 06: No animations** (D-09)

- Move execution is immediate (no sliding animation)
- Selection highlight appears/disappears immediately
- Animation deferred to v0.3

---

## Testing Requirements

### Visual Test Cases

| Test ID | Behavior | Expected Visual |
|---------|----------|-----------------|
| V-01 | Click red piece | Gold ring appears around piece |
| V-02 | Select piece with legal moves | Gold dots appear at legal targets |
| V-03 | Click legal target | Piece moves, highlights cleared |
| V-04 | Click illegal target | Selection cleared, dots removed |
| V-05 | Click another red piece | Selection switches, new dots shown |
| V-06 | Black turn interaction | No response to clicks |
| V-07 | Window resize with selection | Highlights repositioned correctly |

### Signal Test Cases

| Test ID | Behavior | Signal Args |
|---------|----------|-------------|
| S-01 | Move without capture | (from_sq, to_sq, 0) |
| S-02 | Move with capture | (from_sq, to_sq, captured_value) |

---

## Implementation Notes

### Incremental Update Pattern (D-10 to D-17)

After move execution:
1. Get piece item from `_piece_index[(from_row, from_col)]`
2. If target has piece (capture): remove from scene, delete from index
3. Update piece item's `_row`, `_col`, and `setPos()`
4. Update `_piece_index`: delete old key, add new key
5. Call `engine.apply(move)` to update game state
6. Clear highlights
7. Emit `move_applied` signal

### State Update Order (D-11)

```
1. engine.apply(move)
2. self._state = engine.state (or equivalent)
3. Update visual items
```

---

## Pre-Populated From

| Source | Decisions Used |
|--------|---------------|
| CONTEXT.md | 27 decisions (D-01 to D-27) |
| RESEARCH.md | Architecture patterns, pitfall avoidance |
| constants.py | 6 color tokens, 4 size ratios |
| board.py | Coordinate system, existing QXiangqiBoard API |
| board_items.py | PieceItem structure, _row/_col/_piece_value |
| Claude's discretion | 5 choices (ring opacity, ring thickness, dot z-value, index timing, signal naming) |

---

## Quality Checklist

- [x] Spacing scale: cell-based proportional system
- [x] Typography: ratios already defined in Phase 05
- [x] Color contract: 60/30/10 split with accent reserved for highlights
- [x] Copywriting: N/A (visual-only feedback in this phase)
- [x] Registry: N/A (desktop app, not web)
- [x] Interaction states: selection, deselection, move execution, disabled
- [x] Responsive behavior: resize recreates highlights
- [x] Animation: explicitly none for MVP

---

*UI-SPEC created: 2026-03-25*
*Phase: 06-piece-interaction*
*Milestone: v0.2*
