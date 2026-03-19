# Chinese Chess (Xiangqi) Rules — Engine Implementation Reference

This document is the authoritative rule specification for implementing a xiangqi engine. Where
official rules permit variation (e.g. specific repetition-count thresholds), the standard
Chinese XOBA / WXO rules are stated as the default.

---

## 1. Board Layout

### 1.1 Grid

- **9 columns** (files), numbered 0–8 left-to-right from Red's perspective.
- **10 rows** (ranks), numbered 0–9 top-to-bottom (Red's back rank = row 0, Black's back rank = row 9).
- Intersections are called **points** or **positions**. Pieces occupy points, not squares.

### 1.2 Visual Markers

| Marker | Location | Significance |
|---|---|---|
| River | Between rows 4 and 5 (horizontal gap) | Divides Red (rows 0–4) from Black (rows 5–9) |
| Red Palace | Rows 0–2, cols 3–5 | Confines Red General and Red Advisors |
| Black Palace | Rows 7–9, cols 3–5 | Confines Black General and Black Advisors |
| River + Palace diagonals | Internal diagonal lines | Visual only; no gameplay function |

### 1.3 Starting Position

```
Row 0 (Red back rank):
  0: Chariot(R)   1: Horse(R)   2: Elephant(R)  3: Advisor(R)  4: General(R)
  5: Advisor(R)   6: Elephant(R) 7: Horse(R)    8: Chariot(R)

Row 2: Cannons at cols 1 and 7

Row 3: Soldiers at cols 0, 2, 4, 6, 8

Rows 5–9: Symmetrically Black (same piece types, mirrored)
```

---

## 2. Pieces — All Legal Moves

### 2.1 General (帅 Red / 将 Black) — 1 piece each

- **Move**: exactly 1 point orthogonally (up/down/left/right).
- **Constraint**: must stay inside its own palace (rows 0–2 for Red, rows 7–9 for Black).
- **Capture**: may capture any enemy piece on an adjacent orthogonal point inside the palace.
- **Face-to-face rule**: If the Red General and Black General occupy the same file (column) with **no pieces of any color between them**, neither General may move to a point that would leave them facing each other with no intervenor. (Effectively: they cannot occupy the same file unless something blocks between them.)

```
Red General range:  rows ∈ {0,1,2}, cols ∈ {3,4,5}
Black General range: rows ∈ {7,8,9}, cols ∈ {3,4,5}
```

### 2.2 Chariot (车) — 1 piece each

- **Move**: any non-zero number of points orthogonally (horizontal or vertical), as far as desired, until blocked by any piece.
- **Capture**: stops on the enemy piece's point and removes it; may not jump over any piece.
- **Constraint**: none (no river or palace restriction).

### 2.3 Horse (马) — 1 piece each

- **Move**: the "leg" pattern — 2 steps orthogonally then 1 step at a 90° turn, forming an L-shape of total radius 2 (i.e. offsets: (±1, ±2) or (±2, ±1)) **from the destination**.
- **Blocking rule**: the point **one step orthogonally** from the starting position (the "leg") must be **empty**. If occupied by any piece (own or enemy), the horse is blocked and may not move to that destination.
- **Capture**: destination must contain an enemy piece (or be empty for a non-capture move).
- **Corner squares**: a horse at col 0 or col 8 cannot move left/right outward; at row 0 or row 9 cannot move up/down outward; these are naturally handled by board-boundary checks.

### 2.4 Cannon (炮/砲) — 1 piece each

- **Move**: any non-zero number of points orthogonally, as far as desired.
- **Capture rule**: requires exactly **one intervening piece** (the **screen**) between the cannon and the target. The screen may be any color. The cannon jumps to the target point and removes the enemy piece there. Without a screen, a cannon may not capture.
- **Non-capture move**: moves like a chariot (orthogonal sliding) with no restriction except board edges and own pieces.
- **Constraint**: none (no river or palace restriction).

### 2.5 Advisor (士) — 1 piece each

- **Move**: exactly 1 point diagonally (i.e. offsets (±1, ±1)).
- **Constraint**: must stay inside its own palace.
- **Capture**: may capture any enemy piece on the adjacent diagonal point inside the palace.

```
Red Advisor range:  rows ∈ {0,1,2}, cols ∈ {3,4,5}, diagonal moves only
Black Advisor range: rows ∈ {7,8,9}, cols ∈ {3,4,5}, diagonal moves only
```

- **Palace diagonal points** for Red: (0,4)↔(1,3), (0,4)↔(1,5), (1,3)↔(2,4), (1,5)↔(2,4).
  For Black: (7,4)↔(8,3), (7,4)↔(8,5), (8,3)↔(9,4), (8,5)↔(9,4).

### 2.6 Elephant (象/相) — 1 piece each

- **Move**: exactly 2 points diagonally (i.e. offsets (±2, ±2)) — effectively two diagonal steps.
- **Diagonal mid-point (eye) rule**: the **intermediate point** (the "eye", at offset (±1, ±1) from start) must be **empty**. If any piece occupies it, the elephant is blocked and cannot move to that destination.
- **River constraint**: an elephant may **not** cross the river. All destination points must be on the same half of the board as the starting point (Red elephants: rows 0–4; Black elephants: rows 5–9).
- **Capture**: may capture an enemy elephant (or any enemy piece) on the destination point; the "eye" must still be empty (even though the destination's piece is captured, the eye check is performed on the pre-move board state).

```
Red Elephant range: rows ∈ {0,1,2,3,4}, cols ∈ {0..8}, moves diagonal only
Black Elephant range: rows ∈ {5,6,7,8,9}, cols ∈ {0..8}, moves diagonal only
```

### 2.7 Soldier (兵 Red / 卒 Black) — 5 pieces each

- **Move before crossing the river**: exactly 1 point **forward** (Red: row+1; Black: row-1). No sideways movement.
- **Move after crossing the river**: exactly 1 point forward OR 1 point sideways (left/right). (Diagonal movement is **never** allowed.)
- **Capture**: may capture any enemy piece directly in front, or sideways after crossing.
- **No retreat restriction**: once across the river, soldiers may move backward? **No.** Soldiers always move forward only. Sideways is permitted only after crossing the river.

```
Red Soldier forward direction: row increases (+1)
Black Soldier forward direction: row decreases (-1)
```

---

## 3. Board Constraints Summary

| Piece | Horizontal bounds | Vertical bounds | Special |
|---|---|---|---|
| Red General | cols 3–5 | rows 0–2 | palace only |
| Black General | cols 3–5 | rows 7–9 | palace only |
| Red Advisor | cols 3–5 | rows 0–2 | palace only, diagonal only |
| Black Advisor | cols 3–5 | rows 7–9 | palace only, diagonal only |
| Red Elephant | any col | rows 0–4 | cannot cross river (row 5+) |
| Black Elephant | any col | rows 5–9 | cannot cross river (row 4 or below) |
| Chariot | any | any | none |
| Horse | any | any | none |
| Cannon | any | any | none |
| Red Soldier | any (after river) | row 5+ = across | forward only; +sideways after river |
| Black Soldier | any (after river) | row 4- = across | forward only; +sideways after river |

---

## 4. Special Rules

### 4.1 Generals Meeting (Face-to-Face, 将帅对面)

- If the Red General and Black General occupy the **same column** (file) with **no pieces of any color on any intermediate point** between them, the position is illegal.
- The game state must be validated so that **no move** leaves a position where the two generals face each other unobstructed.
- This rule makes the file between the generals effectively a "forbidden file" for the General's vertical movement when no intervenor exists.
- **Implementation note**: Before applying any move, compute whether the resulting position has the two generals on the same file with an empty interval. If so, the move is illegal.

### 4.2 Advisor Diagonal Palace Movement

- Advisors move only diagonally, exactly 1 point, constrained to the 3×3 palace.
- The 5 valid diagonal points within each palace form an X pattern. From the corner positions (rows 0/2, cols 3/5), the advisor can move only to the center of the palace (row 1/8, col 4). From the palace center, the advisor can move to any of the 4 corner positions.

### 4.3 Elephant River Block

- Elephants cannot cross the river under any circumstances. This is an absolute constraint independent of the "eye" rule.
- An elephant on row 4 cannot move to row 6 even if the intermediate eye point is empty. An elephant on row 5 cannot move to row 3.

---

## 5. Illegal Moves

A move is illegal if **any** of the following conditions hold:

1. **Leaving own General in check**: After the move is applied, if the player's own General is under attack by at least one enemy piece, the move is illegal.
2. **Moving the General into check**: The destination of a General or Advisor move must not be a point attacked by any enemy piece.
3. **Violating the face-to-face rule**: The resulting position must not have both generals on the same file with an empty interval between them.
4. **Piece-specific constraints violated**: e.g. Elephant crossing river, Advisor leaving palace, General leaving palace.
5. **Obstruction**: A chariot, cannon (non-capture), or elephant path is blocked by a piece (own or enemy) before reaching the destination.
6. **Horse leg blocked**: The intermediate orthogonal "leg" point for a horse is occupied.
7. **Cannon missing screen on capture**: A cannon attempting to capture with zero or more than one intervening screen.
8. **Cannon capture with screen being own piece**: The screen must be a piece of any color; a cannon may capture an enemy piece even if its own piece serves as the screen (the screen can be either color).
9. **Elephant eye blocked**: The diagonal intermediate point is occupied.
10. **Soldier sideways before crossing**: Soldier attempts a sideways move while still on its home half.

---

## 6. Check (将军) Detection

### 6.1 Definition

A side is **in check** if the opponent has at least one piece that could capture the General on the opponent's next move (i.e. the General's point is in the attack set of at least one enemy piece).

### 6.2 Attack Set Computation

For each enemy piece, compute the set of points it could capture on this move (same as legal-move generation but without the self-check constraint). If the General's point is in this set, the side is in check.

**Special attention for Cannons**: A cannon attacks a point if there is exactly 1 piece (of any color) between them on the same orthogonal line, and the destination is empty or enemy-occupied. Note: when computing the enemy's attack set, a cannon attacks a point if it could **capture** there — i.e. exactly 1 screen between them, destination empty or enemy-occupied.

### 6.3 Sources of Check

| Piece | Mechanism of Check |
|---|---|
| Chariot | Same row or column with no pieces between |
| Horse | L-shape destination being the General's point, with leg empty |
| Cannon | Same row or column with exactly 1 screen between, General is destination |
| Advisor | Adjacent diagonal point within palace |
| Elephant | Adjacent diagonal point on own side (eye must be empty for attack) |
| Soldier | One point forward (or forward/sideways after crossing river) |
| General | Adjacent orthogonal point (face-to-face) — only if no screen between |

### 6.4 Implementation

```
is_in_check(color):
  general_pos = find_general(color)
  opponent_pieces = all pieces of opposite color
  for each piece in opponent_pieces:
    if can_capture(piece, general_pos):  # normal capture logic, no self-check filter
      return True
  return False
```

The `can_capture` function is identical to the normal legal-move generator for the piece type, checking board boundaries and obstruction.

---

## 7. Checkmate (将死) vs Stalemate (困毙) Detection

### 7.1 Checkmate (将死)

A position is **checkmate** if:
1. The player whose turn it is is **in check**.
2. The player has **no legal moves** that would resolve the check.

### 7.2 Stalemate / "No Legal Moves" (困毙)

A position is **stalemate** (formally: "no legal moves" / 困毙) if:
1. The player whose turn it is is **not in check**.
2. The player has **no legal moves** at all.

In xiangqi, stalemate is treated as a **loss for the player who cannot move** (same as checkmate — the opponent wins). There is no draw from stalemate as in Western chess.

### 7.3 Detection Algorithm

```
generate_all_legal_moves(color):
  moves = []
  for each piece of color:
    for each destination in piece_type_destinations(piece):
      if move_is_legal(piece, destination):
        moves.append((piece, destination))
  return moves

is_checkmate(color):
  return is_in_check(color) AND len(generate_all_legal_moves(color)) == 0

is_stalemate(color):
  return not is_in_check(color) AND len(generate_all_legal_moves(color)) == 0
```

**Note**: `generate_all_legal_moves` must include the General's moves. If the General has no legal moves, no other piece's moves can resolve the check, so the position is checkmate.

### 7.4 Bare General (将/帅) — Special Edge Case

- A player wins immediately if they capture the opponent's General. There is no checkmate sequence required.
- If a move results in the opponent having **zero pieces** besides the General (i.e. a "bare general"), the remaining pieces must not give check to the opponent's General, or the side with only a General must have no legal moves. This is covered by the normal checkmate/stalemate logic.

---

## 8. Win / Loss / Draw Rules

### 8.1 Win Conditions (in priority order)

| Condition | Description |
|---|---|
| Capture opponent's General | Immediate win; the game ends before checkmate evaluation |
| Checkmate | Opponent's General is in check with no legal moves |
| Stalemate (困毙) | Opponent has no legal moves and is not in check |

### 8.2 Draw Conditions

| Condition | WXO Rule | Notes |
|---|---|---|
| Mutual agreement | Both sides agree to draw | Not detectable by engine without UI prompt |
| Triple repetition (三次循环) | Same position occurs 3 times (including same side to move) | Requires a **position** (not move) hash table with occurrence count |
| Perpetual check (长将) | A player gives perpetual check and the other player is not in check | The checking side must stop; otherwise draw |
| Perpetual chase (长捉) | A player chases the same piece for ≥ 4 moves without making a "useful" move (e.g. giving check, moving a piece to a new square, capturing) | WXO rule: perpetual chase without meaningful progress → draw |
| No pieces capable of delivering checkmate | Both sides have insufficient material (e.g. both bare generals, or one side has only a General and the other only a General + Advisor cannot force checkmate) | Conservative engine rule; tournament rules vary |

### 8.3 The "Long" Repetition Rules (长将 / 长捉)

**Long Check (长将, cháng jiàng)**:
- If one side **repeatedly checks** the opponent's General for 4 or more consecutive moves, and the opponent is not in check, the checking side must find a non-checking move. If the checking side has no non-checking move and continues to give check, the position is a draw.
- WXO Rule 22.2: A position with a side giving continuous check for 4+ moves is draw.

**Long Chase (长捉, cháng zhuō)**:
- If one side chases the same enemy piece for 4 or more consecutive moves without making meaningful progress (no check given, no piece captured, no piece moved to a new square), the position is a draw.
- WXO Rule 22.3: Continuous chase without progress for 4+ moves.

**Implementation of repetition tracking**:
```
State:
  position_history: list of board hash (FEN-like or zobrist) → occurrence count
  current_side_to_move: Red | Black
  consecutive_check_count: int  (reset when non-check position)
  chase_sequence: list of (chasing_piece_id, chased_piece_id)  (reset on any non-chase move)

On each move:
  1. Compute new board hash
  2. Increment position_history[hash] (game is draw if count reaches 3)
  3. Evaluate if the move gives check → update consecutive_check_count
  4. Evaluate if the move is a chase (attacks enemy piece of same type as previous chase) → update chase_sequence
  5. If consecutive_check_count >= 4 and opponent not in check → draw
  6. If chase_sequence length >= 4 and no meaningful progress → draw
```

**"Meaningful progress"** in a chase: the chasing side captures a piece, gives check, or moves a piece to a square it has never occupied in the chase sequence.

### 8.4 Perpetual Siege (长围)

A generalization of long-check and long-chase: if one side has an overwhelming positional advantage and the opponent cannot make progress, some rules treat this as a draw. This is rarely implemented in engines.

---

## 9. Edge Cases and Corner Cases

### 9.1 Elephant Eye and Capture

When an elephant captures an enemy piece at its destination, the "eye" check is performed on the **pre-capture** board. The destination piece does not affect the eye check.

### 9.2 Cannon Screen During Capture

The screen piece is **not** removed when a cannon captures. The screen remains on the board. The cannon jumps over the screen to the destination and removes the enemy piece there.

**Example**: Cannon at (5,3), screen at (4,3), enemy General at (2,3). After capture: Cannon at (2,3), screen still at (4,3).

### 9.3 Horse Leg and Cannon Screen Are Not the Same

The horse's blocking point is called the "leg" (蹩马腿). The cannon's screen is the intervening piece (任意颜色). A cannon requires **exactly one** screen. Zero screens = no capture. More than one screen = no capture.

### 9.4 Elephant Cannot See Past River

An elephant's vision is limited to its own half. It cannot "see" across the river for any purpose. This is a hard constraint even if the eye point is empty.

### 9.5 Soldier Movement Direction

- Red soldiers move toward **increasing row number** (down the board toward Black's side).
- Black soldiers move toward **decreasing row number** (up the board toward Red's side).
- A soldier at the exact river boundary (row 4 for Red, row 5 for Black) may not move sideways — it must move forward to cross.

### 9.6 Soldiers at the Palace Edge

A soldier on the palace boundary (cols 3 or 5, rows 0–4 for Red) can move sideways to cols 2 or 4 only after crossing the river (rows 5+). Before crossing, only forward.

### 9.7 Bare General and Forced Loss

If a player has only a General remaining and the opponent has any piece that can checkmate, the game continues until checkmate or stalemate. There is no automatic loss for having few pieces.

### 9.8 Elephant Eye Point Is Always Empty After Any Move

The eye point is not affected by the move itself. For a move from A to B, the eye point (midpoint between A and B) is checked on the board **before** the move is applied.

### 9.9 Discovered Attack After Own Move

When generating legal moves, the engine must evaluate the position **after** the hypothetical move is applied. If a piece moves out of the line between an enemy cannon/chariot and the own General, and the resulting position has the General in check from a now-unblocked attacker, that move is illegal.

### 9.10 Castling

**There is no castling in xiangqi.**

### 9.11 En Passant

**There is no en passant in xiangqi.**

### 9.12 Pawn Promotion

**There is no pawn promotion in xiangqi.** Soldiers do not upgrade when reaching the back rank.

### 9.13 Elephant and River Crossing with Screen

An elephant cannot cross the river even if the eye point on its own side is empty. The river constraint is independent of the eye constraint. The move is illegal regardless of whether the eye is empty.

### 9.14 Check from Elephant Across River

An elephant on its home side attacks only points on its home side. An elephant on row 4 cannot attack a point on row 6. This limits the elephant's check-giving capability.

### 9.15 Face-to-Face as a Source of Check

If both generals are on the same file with no pieces between, each general is **already giving check** to the other. Any move by the blocking side that clears the file is illegal (it would expose the general to immediate capture). The side not on that file can capture the blocking piece or move their general.

**This is NOT a "double check" in the Western chess sense** — both generals threaten each other simultaneously. The player not under direct capture threat must resolve the situation by clearing the file or blocking.

### 9.16 Horse at Board Corners

A horse at (0,0), (0,8), (9,0), or (9,8) has fewer than 8 destinations. Boundary checks must handle these naturally. Offsets that go off the board simply have no valid destination.

### 9.17 Symmetry of Red/Black

All rules are symmetric between Red and Black. Red moves first in standard play (though some variants alternate). The only asymmetry is the starting position orientation and the soldier forward direction.

---

## 10. Turn Order and Game State Management

### 10.1 Standard Turn Order

- **Red moves first.**
- Players alternate, one move at a time.
- A "move" consists of selecting one own piece and moving it to a valid destination.

### 10.2 Game State Structure

```python
@dataclass
class XiangqiState:
    board: List[List[Optional[Piece]]]]          # 10×9, board[row][col]
    side_to_move: Color                          # RED or BLACK
    move_history: List[Move]                     # ordered list of all moves
    position_history: Dict[int, int]            # zobrist_hash → occurrence count
    consecutive_check_count: int                 # consecutive moves in check
    chase_sequence: List[Tuple[int, int]]        # (chasing_piece_id, chased_piece_id)
    game_status: GameStatus                      # IN_PROGRESS | RED_WINS | BLACK_WINS | DRAW
```

### 10.3 Move Application

```
apply_move(state, move):
  1. Validate move is in generate_all_legal_moves(state.side_to_move)
  2. Save state snapshot for potential undo
  3. Remove piece from source point (handle capture)
  4. Place piece at destination point
  5. Swap side_to_move
  6. Update move_history
  7. Compute new position hash, increment position_history
  8. Evaluate game-ending conditions (capture General → win; checkmate; stalemate; repetition)
  9. Return new state
```

### 10.4 Undo Move

```
undo_move(state, saved_snapshot):
  restore board, side_to_move, move_history, position_history from snapshot
```

### 10.5 Position Equality (for repetition detection)

Two positions are equal if and only if:
- The board configuration is identical (all 32 piece positions).
- The side to move is the same.

Use **Zobrist hashing** for efficient position comparison and history tracking.

### 10.6 Game Start

- Initialize board to standard starting position.
- side_to_move = RED.
- All counters = 0.
- game_status = IN_PROGRESS.

### 10.7 Game End Triggers

| Trigger | Priority | Action |
|---|---|---|
| Capture of General | 1 (highest) | Opponent wins immediately |
| Checkmate | 2 | Opponent wins |
| Stalemate | 2 | Opponent wins |
| Triple repetition | 3 | Draw |
| Perpetual check ≥ 4 moves | 3 | Draw |
| Perpetual chase ≥ 4 moves | 3 | Draw |

---

## 11. Quick Reference: Move Offsets by Piece

```
General:   (±1, 0), (0, ±1)
Advisor:   (±1, ±1)   [must stay in palace]
Elephant:  (±2, ±2)   [eye at (±1,±1) must be empty; cannot cross river]
Horse:     offsets to 8 destination squares:
             leg step (0,+1) → dest (+1,+2) or (-1,+2)
             leg step (0,-1) → dest (+1,-2) or (-1,-2)
             leg step (+1,0) → dest (+2,+1) or (+2,-1)
             leg step (-1,0) → dest (-2,+1) or (-2,-1)
Chariot:   any (r, c) where r=same or c=same, path clear
Cannon:    non-capture: same as chariot
           capture: same as chariot but exactly 1 screen between
Soldier:   forward (±1,0) always valid
           sideways (0,±1) only if row >= 5 (Red) or row <= 4 (Black)
```

---

## 12. Implementation Hints

### 12.1 Piece Representation

```python
class PieceType(Enum):
    GENERAL = 0    # 帅/将
    ADVISOR = 1    # 士
    ELEPHANT = 2   # 象/相
    HORSE = 3      # 马
    CHARIOT = 4    # 车
    CANNON = 5     # 炮
    SOLDIER = 6   # 兵/卒

class Color(Enum):
    RED = 0
    BLACK = 1
```

### 12.2 Move Representation

```python
@dataclass
class Move:
    from_row: int
    from_col: int
    to_row: int
    to_col: int
    piece_type: PieceType
    color: Color
    captured_piece: Optional[PieceType] = None
```

### 12.3 Board Coordinate Convention

This document uses **row-major** coordinates: `board[row][col]` where:
- row 0 = Red's back rank (top)
- row 9 = Black's back rank (bottom)
- col 0 = left file from Red's perspective
- col 4 = center file

Palace bounds: Red: rows [0,1,2], cols [3,4,5]; Black: rows [7,8,9], cols [3,4,5].
River: rows 4–5.

### 12.4 FEN-like Notation (Optional)

A compact board notation for debugging/serialization uses the standard xiangqi coordinate system. The WXF FEN standard is commonly used:
- Pieces in algebraic notation (e.g. R=Red chariot, r=black chariot, G=red general, g=black general)
- Ranks separated by `/`
- Numbers for empty points within a rank

### 12.5 Zobrist Hashing

For repetition detection and transposition tables, use Zobrist hashing:
- Pre-compute random 64-bit integers for each `(piece_type, color, row, col)` combination.
- XOR all piece positions into a running hash.
- Include side-to-move bit (XOR with a dedicated constant when side_to_move is Red, 0 when Black).

### 12.6 Legal Move Generation Order

For move ordering in search:
1. Captures (prioritized by MVV-LVA: largest victim, smallest attacker)
2. Checks (moves that give check)
3. Non-capture forward moves
4. Other non-captures

This ordering improves alpha-beta pruning efficiency.

---

*Document version: 1.0*
*Coverage: All WXO standard rules. Variant rules (e.g. blindfold, faster time controls with different repetition thresholds) are out of scope.*
