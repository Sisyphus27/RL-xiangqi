# Pitfalls Research

**Domain:** Xiangqi (Chinese Chess) rule engine — v0.1 milestone; engine to support RL training and human-AI gameplay
**Researched:** 2026-03-19
**Confidence:** HIGH (Xiangqi-specific rules verified via 2024 WXF academic paper and community implementations; move generation patterns verified via chess programming wiki and xiangqi engine source analysis; RL integration design patterns verified via AlphaZero literature)

---

## Critical Pitfalls

### Pitfall 1: Perpetual Check Is a Loss, Not a Draw

**What goes wrong:**
The engine implements `position repeated 3 times = draw`, mirroring Western chess. In Xiangqi, perpetual check is a **loss for the checking side**. An RL agent trained against this incorrect rule learns to exploit repeated-check sequences as a "draw escape" from losing positions, which corrupts every reward signal. Discovered late, this requires retraining from scratch because all terminal rewards in the training history are wrong.

**Why it happens:**
Developers with Western chess experience carry the mental model that repetition is neutral. Many popular Xiangqi apps have this wrong (Tiantian Xiangqi's repetition handling is documented as "completely broken"). The WXF repetition rules are 16+ conditions involving check loops, chase loops, mutual loops, and idle-draw loops — vastly more complex than the Western 3-fold draw rule.

**How to avoid:**
Implement WXF repetition classification from the start. The minimum correct behavior for v0.1:
1. Track position history using Zobrist hashes (not full board copies)
2. When a position repeats for the third time, classify the repeated moves:
   - All repeated moves are checks → loss for the checking side
   - All repeated moves are chases of an unprotected piece → loss for the chasing side
   - Mixed or non-check/non-chase repetition → draw (or game continues under 60-move rule)
3. "Perpetual idle" (exchanges and blocks with no check or chase) → draw after 4 repetitions
4. Reference: "A Complete Algorithm for Ruling the WXF Repetition Rules" (arXiv:2412.17334, 2024) provides pseudocode for all 16 cases

**Warning signs:**
- Games last 60+ moves between two random agents without terminating
- Agent in a clearly losing endgame never gets a loss signal
- Win/loss statistics show fewer losses than expected for random play

**Phase to address:** v0.1 Rule Engine — must be correct before any RL training begins.

---

### Pitfall 2: Perpetual Chase Detection Requires "Chased Piece" Set Intersection

**What goes wrong:**
The engine detects "chasing" across repeated positions by checking whether *any* piece is being threatened. But if the threatening piece changes between repetitions (Rook chases a Horse on move 1, then Cannon chases a different Horse on move 3), the engine wrongly flags it as perpetual chase. Correct WXF rules require the same piece to be chased continuously.

**Why it happens:**
The obvious implementation tracks "is any piece under attack?" per position without tracking *which specific piece* is targeted. The subtlety is that the repeated positions must share a non-empty intersection of chased pieces — if the intersection is empty, the repeated sequence is classified as "idle", not "chase".

**How to avoid:**
- For each position in the repetition loop, compute the set of pieces being chased (unprotected pieces under attack)
- Compute the intersection across all positions in the loop
- If the intersection is non-empty → perpetual chase (loss for chasing side)
- If the intersection is empty → perpetual idle (draw, or ruled by 60-move limit)
- Also implement the "false protector" guard: a piece that is pinned (would expose the king to check if it moved) does NOT count as protecting the chased piece

**Warning signs:**
- Agent develops a "piece harassment" pattern that never terminates
- Two chasing pieces alternate targeting different enemy pieces and avoid a loss verdict

**Phase to address:** v0.1 Rule Engine — implement together with basic repetition detection, not after.

---

### Pitfall 3: Horse Movement Blocking Rule Implemented Incorrectly

**What goes wrong:**
The Horse (马) is coded like a Western chess knight — it leaps in an L-shape regardless of intervening pieces. In Xiangqi the Horse cannot jump: if the square **orthogonally adjacent** to the Horse in the direction it wants to move is occupied, that entire leg of movement is blocked. This is the "hobbling the horse's leg" rule (蹩马腿). A knight-like Horse generates illegal moves and allows escapes from checks that should be blocked.

**Why it happens:**
Western chess programmers default to the knight L-shape move table. The difference is subtle — the Horse still ends on an L-shape destination, but the occupancy check is on the *orthogonal intermediate square*, not the destination. Many tutorials describe Xiangqi movement without emphasizing this distinction.

**How to avoid:**
For each of the 4 orthogonal directions from the Horse:
1. Check if the adjacent square in that direction is occupied
2. If occupied → skip both diagonal destinations reachable from that direction (both are blocked)
3. If empty → add both diagonal destinations (if on board and not occupied by friendly pieces)

Never use a precomputed "knight attack table" from Western chess for the Horse. The Horse's legal destinations are board-state-dependent.

**Warning signs:**
- Horse can apparently move "through" pieces when a blocking piece is adjacent
- Perft test counts for positions with horses near blocked squares are incorrect
- AI agent learns to use a Horse to deliver check from positions that should be blocked

**Phase to address:** v0.1 Rule Engine — piece movement core. Test with positions specifically designed to trigger every blocking direction.

---

### Pitfall 4: Elephant Cannot Cross the River — But the Block Rule Also Applies

**What goes wrong:**
The Elephant (相/象) move is coded to check only the river boundary but not the "elephant eye" blocking rule. The Elephant moves diagonally exactly 2 squares and is blocked if the diagonal intermediate square ("elephant's eye", the midpoint of its 2-step diagonal path) is occupied. Missing the eye check generates illegal moves, and missing the river check allows the Elephant to be used as an attacking piece (it should be purely defensive and confined to its own half).

**Why it happens:**
Two independent constraints (river boundary + diagonal midpoint blocking) must both be checked. Developers often implement one and forget the other. Unlike the Horse's orthogonal block, the Elephant's block is on a diagonal midpoint — a different coordinate calculation.

**How to avoid:**
For each of the 4 diagonal destinations (±2, ±2):
1. Compute the midpoint: `(row ± 1, col ± 1)`
2. If the midpoint square is occupied → this destination is blocked
3. If the destination is on the opponent's side of the river → this destination is illegal (river constraint)
4. The Elephant has at most 7 reachable squares on the entire board; precomputing these per starting position is a valid optimization

**Warning signs:**
- Elephant can reach the opponent's side in any game position
- Elephant can "jump" over a piece that should block its diagonal
- Unit test counting the Elephant's legal moves from starting position returns more than 2

**Phase to address:** v0.1 Rule Engine — piece movement core.

---

### Pitfall 5: Flying General Rule Missed in Check Detection

**What goes wrong:**
The "Flying General" rule (将帅碰面) states that if the two Kings face each other on the same file (column) with no pieces between them, that position is illegal — as if they were giving each other "check through the empty file". This rule is not a separate game mechanic but an additional check condition in the `is_in_check()` function. If missed, the engine allows moves that interpose a King-vs-King face-off, leading to illegal positions and enabling endgame combinations that should not exist.

**Why it happens:**
The rule is unique to Xiangqi. Check detection in Western chess only considers standard attack patterns. Developers treat it as an "edge case" and defer it, then forget it. It most commonly matters in endgames when one King has moved out of the palace.

**How to avoid:**
In the `is_in_check(color)` function, add a flying general check as the final condition:
1. Find both Kings' positions
2. If they share the same column (file), scan all squares between them
3. If no piece exists between them → the side to move is in check (flying general)

This must run on every move, not just when the Kings are adjacent. Any move that clears a file between the two Kings triggers it.

**Warning signs:**
- Perft counts are incorrect for late-endgame positions with mobile Kings
- AI agent deliberately places Kings on the same file with no intervening pieces to avoid normal check patterns
- Illegal positions appear where both Kings face each other directly

**Phase to address:** v0.1 Rule Engine — check detection. Include dedicated test positions for flying general scenarios.

---

### Pitfall 6: Cannon Capture Logic Conflated with Rook Movement

**What goes wrong:**
The Cannon (炮) moves like a Rook (any number of squares orthogonally) when not capturing. But when capturing, it must jump over **exactly one** intervening piece (the "screen" or "mount"). Engines that copy the Rook's move generation for the Cannon produce: (a) cannons that can capture adjacent pieces without a screen, (b) cannons that can capture through 2+ screens, and (c) cannons that cannot move to empty squares that happen to have pieces behind them.

**Why it happens:**
The movement (non-capture) and capture modes are entirely different. Move generation functions that compute "squares attacked" need two separate code paths for the Cannon: one for empty-square slides (same as Rook) and one for captures (count pieces encountered, capture only on exactly the second piece, stop after the second piece). Conflating these is the single most common Xiangqi engine bug in open-source code.

**How to avoid:**
Implement two distinct functions for Cannon move generation:
- `cannon_slides(board, pos)` → squares the Cannon can move to (empty squares, stop at first occupied square in each direction, do not include the occupied square)
- `cannon_captures(board, pos)` → squares the Cannon can capture on (skip the first occupied piece in each direction, the second occupied piece in each direction is a valid capture target if it's an enemy piece; stop after the second occupied piece)

Never reuse the Rook's attack table for Cannon captures.

**Warning signs:**
- Cannon can capture a piece sitting adjacent to it without a screen
- Cannon cannot capture a piece that has exactly one piece between them
- Cannon can "fire through" two screens
- A Cannon on an otherwise empty rank has the same attack pattern as a Rook (it should attack nothing, only be able to slide)

**Phase to address:** v0.1 Rule Engine — cannon implementation. This deserves its own dedicated unit test suite with at least 8 positions testing all combinations of 0, 1, 2, and 3+ intervening pieces.

---

### Pitfall 7: Stalemate Is a Loss, Not a Draw

**What goes wrong:**
The engine returns a draw when the player to move has no legal moves and is not in check (stalemate). In Xiangqi, stalemate (困毙, *kùn bì*) is a **loss for the stalemated player**. If the engine returns a draw, the RL agent will artificially avoid checkmates when a stalemate is possible (chasing the enemy into a no-moves position), since draws are better than losses for the opponent.

**Why it happens:**
Western chess stalemate = draw is a strong mental default. Xiangqi has the opposite rule. This is one of the most frequently incorrect rules in hobbyist Xiangqi implementations.

**How to avoid:**
- `get_game_result()` logic: if the current player has no legal moves, return a **loss** for the current player regardless of whether they are in check
- Checkmate and stalemate are therefore the same result from the perspective of the losing side — both represent "current player cannot move"
- Add a unit test: construct a position where the player is not in check but has no legal moves; assert the result is a loss for that player

**Warning signs:**
- RL agent learns to "stalemate escape" — herding enemy King to a no-move position instead of delivering checkmate
- Endgame positions that should be decisive are returned as draws
- Win statistics are artificially low (some wins are being recorded as draws)

**Phase to address:** v0.1 Rule Engine — game termination logic.

---

### Pitfall 8: Action Space Not Providing a Legal Move Mask to the RL Agent

**What goes wrong:**
The engine's API returns the board state as an observation tensor but does not provide a corresponding boolean mask of legal moves. The RL agent must then call `get_legal_moves()` separately, producing mismatched state-action pairs during rollout collection. Worse, if illegal moves are sampled by the policy and then rejected by the engine, training data is full of zero-reward, undefined transitions that confuse the value function.

**Why it happens:**
The rule engine is built first as a standalone module with no thought given to RL consumption. The observation and the legal move mask are generated in separate code paths and can desync when state transitions happen asynchronously (e.g., the mask is computed before a move is applied, but the observation is recorded after).

**How to avoid:**
Design the engine API to return a `(observation, legal_mask)` tuple atomically from a single call. Never let observation and mask be independent calls. The mask should be a boolean numpy array over the fixed action space, shaped `(num_possible_moves,)`. The action space size should be fixed and documented before v0.1 is complete — for Xiangqi, a reasonable encoding is to enumerate all possible (from_square, to_square) pairs = 90 × 90 = 8,100, of which only ~40-100 are legal per position.

For the RL policy network:
- Apply the legal mask to policy logits before softmax: `logits[~legal_mask] = -inf`
- Never penalize the agent with a negative reward for illegal moves — instead, prevent sampling illegal moves via the mask

**Warning signs:**
- Policy gradient loss is undefined or NaN (agent sampled an illegal move with undefined reward)
- Agent learns to avoid all moves in certain board regions (overfit to illegal-move penalties)
- `get_legal_moves()` and `env.reset()` produce different legal move counts for the same position

**Phase to address:** v0.1 Rule Engine — API design. Define the action encoding and the legal mask format before implementing the first piece's move generator.

---

### Pitfall 9: Make/Unmake Move Bugs Cause Non-Deterministic Legal Move Generation

**What goes wrong:**
The engine uses a make/unmake (push/pop) move pattern for efficiency. A bug in `unmake_move()` leaves residual state from the applied move — a captured piece is not restored, a King's position is not rolled back, en-passant-like state flags are not cleared. Subsequent calls to `get_legal_moves()` produce different results for the same position depending on the history of moves applied and reversed, causing non-determinism in legal move generation that is nearly impossible to debug without perft testing.

**Why it happens:**
Make/unmake is harder to implement correctly than copy-state. Every piece of mutable state touched during `make_move()` must have a corresponding undo operation in `unmake_move()`: piece positions, captured pieces, check state cache, Zobrist hash, move counters, repetition history. Missing any one of these causes subtle non-determinism.

**How to avoid:**
For v0.1, prefer **copy-state over make/unmake**: before applying a move, deep-copy the board object; after exploring, discard the copy. Python's `copy.deepcopy()` is sufficient and correct. Optimize to make/unmake only if performance profiling shows it is needed (target is <100ms per move generation, which copy-state can achieve in Python for a 90-square board).

If make/unmake is used, maintain an explicit undo stack as a list of `(attribute, old_value)` tuples applied in `make_move()` and reversed in `unmake_move()`. Test by applying and immediately unmaking every legal move from every position in a perft suite and asserting board equality before and after.

**Warning signs:**
- `get_legal_moves()` returns different counts for identical board positions depending on execution path
- Perft counts are non-reproducible between runs
- Check detection returns `True` when the King is not in check (residual check state from previous make)

**Phase to address:** v0.1 Rule Engine — move application core. Validate with perft tests before any higher-level logic is built on top.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Skip Zobrist hashing, use full board string for repetition detection | Simple to implement | O(board_size) per hash vs O(1); 90-character string comparison per position slows repetition detection to unusable speed during deep self-play | Acceptable in v0.1 if game count is low; replace before RL training at scale |
| Use Python list of dicts as board state | Easy to read and modify | Prevents numpy vectorization; incompatible with PyTorch tensor operations; cannot be used as RL observation directly | Acceptable as internal representation if a separate `to_tensor()` export is clean |
| Skip "check after move" validation for performance | Faster pseudo-legal move generation | Engine accepts moves that leave the King in check, leading to illegal game states reaching the RL training buffer | Never — this validation is mandatory |
| Hard-code piece movement tables | Removes per-move occupancy checks for fixed pieces (Advisor, Elephant) | Tables grow stale when board size changes; false confidence that all positions are covered | Acceptable only for fixed-range pieces (Advisor, General) whose destinations are fully enumerable (5 squares each) |
| Implement repetition as "3-fold = draw" | Mirrors familiar Western chess logic | Wrong Xiangqi rules; corrupts all RL rewards derived from terminal game outcomes | Never |
| Implement stalemate as draw | Mirrors Western chess | Wrong Xiangqi rules; leads to draw-escape strategies in RL agent | Never |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Rule engine → RL observation tensor | Returning board state as a 2D array of piece symbols (strings) | Return as `numpy.ndarray` of `uint8` dtype, one integer per square encoding piece type and color; cast to `float32` tensor at the RL boundary |
| Rule engine → RL action space | Defining action space as "list of legal moves" (variable size) | Define a fixed action space (e.g., 8,100 = 90×90 from/to pairs); provide a boolean legal move mask per state; policy logits are always size 8,100 |
| Rule engine → PyQt6 UI | Calling `get_legal_moves()` on every mouse hover for UI highlighting | Cache legal moves at the start of each turn; invalidate cache only on a committed move; do not recompute per-pixel during drag |
| Repetition detection | Storing full board FEN strings in history for comparison | Use Zobrist hash (a single 64-bit integer) per position; store the hash list; only reconstruct position on actual repetition detection for verification |
| Check detection | Running full legal move generation to determine if the King is in check | Implement a direct `is_square_attacked(square, by_color)` function that checks all attacker types; avoid generating all legal moves just to detect check |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Generating all legal moves inside `is_checkmate()` twice | `is_checkmate()` calls `get_legal_moves()` to check for empty; `get_legal_moves()` internally calls `is_in_check()` for each candidate | Cache legal moves per position; `is_checkmate` checks the cached list | Every move, doubling legal-move-generation cost |
| Full board copy for every node in deep search | >100ms per move at depth 3+ | Use copy-state only for the RL environment wrapper; rule engine internals use make/unmake | At search depth > 2 with copy-state in pure Python |
| String comparison for position equality in repetition detection | Repetition check takes 1ms+ per move | Implement Zobrist hashing; hash each position in O(1) using incremental XOR updates | After 30+ moves per game, with any search depth |
| Recomputing check status on every call to `get_legal_moves()` | Move generation is 5-10x slower than needed | Cache `is_in_check` result as a board attribute; invalidate on each `make_move()`/`unmake_move()` | Immediately, for every pseudo-legal candidate move |
| Returning Python lists of move objects from `get_legal_moves()` | Incompatible with numpy vectorization; cannot be used as action masks directly | Return a numpy bool array (the action mask) alongside the list; the mask is the primary RL interface | At RL training time — Python lists cannot be used as PyTorch tensor inputs |

---

## Testing Strategy

These testing approaches are mandatory for a correct Xiangqi rule engine.

### Perft Testing (Move Generation Correctness)

Perft counts the total number of leaf nodes at a given search depth from a starting position. A correct engine produces exact perft values for known reference positions. Any deviation indicates a move generation bug (illegal moves included, or legal moves missing).

**How to use perft for Xiangqi:**
1. Start from the initial position; compute `perft(1)` through `perft(4)`
2. Compare against known correct values from a reference Xiangqi engine (Fairy-Stockfish supports Xiangqi via UCCI protocol)
3. Use the "divide" variant: `perft_divide(depth)` breaks down counts by each legal move at depth 1, allowing binary search to the exact position containing the bug
4. Key test positions to include alongside the initial position:
   - Position with a Cannon behind exactly one screen (tests cannon capture detection)
   - Position with a Horse blocked in multiple directions (tests horse leg blocking)
   - Position with an Elephant near the river and near occupied diagonal midpoints
   - Position with both Kings on the same file with one intervening piece (tests flying general on the boundary)
   - Position about to trigger the 3-fold repetition rule

**Reference:** [Fairy-Stockfish Xiangqi perft thread](https://github.com/ianfab/Fairy-Stockfish/issues/278) has perft values for the starting position and selected test positions.

### Canonical Rule Test Cases

| Rule Area | Test Case | Expected Outcome |
|-----------|-----------|-----------------|
| Perpetual check | Rook gives check on every move for 4 repetitions | Loss for checking side |
| Perpetual chase | Cannon chases unprotected Rook for 4 repetitions | Loss for chasing side |
| Perpetual idle | Two Rooks trade attacks on empty files | Draw (or continue under 60-move rule) |
| Flying general | Move that clears last piece between two Kings on same file | Move is illegal |
| Stalemate | Red moves Advisor leaving Black King surrounded with no moves, not in check | Black loses |
| Cannon capture no screen | Cannon tries to capture adjacent piece with no screen | Move is illegal |
| Cannon capture two screens | Cannon tries to fire through two pieces | Move is illegal |
| Horse blocked leg | Horse tries to move when orthogonal neighbor is occupied | Move is illegal |
| Elephant crosses river | Elephant tries to move to opponent's side | Move is illegal |
| Elephant eye blocked | Elephant tries to move when diagonal midpoint is occupied | Move is illegal |
| Advisor leaves palace | Advisor tries to move outside the 3x3 palace | Move is illegal |
| General leaves palace | General tries to move outside the 3x3 palace | Move is illegal |

---

## "Looks Done But Isn't" Checklist

- [ ] **Perpetual check:** Often coded as "draw" — verify with a position where Red checks Black repeatedly for 4 moves; Red must receive a loss
- [ ] **Stalemate:** Often coded as "draw" — verify with a position where the current player has no legal moves and is not in check; current player must lose
- [ ] **Horse blocking:** Often coded as a jumping knight — verify with a position where the Horse's orthogonal neighbor is occupied; that leg must be completely blocked
- [ ] **Cannon capture:** Often conflated with Rook — verify that a Cannon cannot capture a piece with 0 screens, and cannot capture through 2 screens; exactly 1 screen is the only valid capture condition
- [ ] **Flying general:** Often omitted entirely — verify that a move leaving the two Kings on the same file with no pieces between them is rejected as illegal
- [ ] **Elephant river crossing:** Often only the river check is done but not the diagonal-midpoint block — verify both constraints independently
- [ ] **Legal move mask:** Often `observation` and `legal_mask` are separate calls — verify both are derived from the same immutable board snapshot with no intervening state change
- [ ] **Perft depth 3:** Often passes at depth 1 and 2 but fails at depth 3 due to make/unmake residual state — verify perft(3) from initial position matches the reference value

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Perpetual check/stalemate rule wrong, discovered after RL training | HIGH | Fix engine; discard all trained weights (rewards were wrong); restart training from random init |
| Cannon or Horse move generation bug found after training | HIGH | Fix engine; verify with perft; discard weights; retrain |
| Make/unmake bug causing non-deterministic legal moves | MEDIUM | Switch to copy-state temporarily to unblock; write undo-stack test; fix unmake; re-verify with perft; resume |
| Flying general check missing in check detection | MEDIUM | Add the check to `is_in_check()`; re-run full perft suite; no retraining needed if caught before RL begins |
| Action space mismatch with RL agent (variable vs fixed) | MEDIUM | Define fixed action encoding; add legal mask output to engine API; RL agent code update; no engine logic changes needed |
| Missing legal move mask (agent samples illegal moves) | LOW | Add mask output to engine API; update RL rollout collector; re-run a test episode to verify no illegal moves sampled |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Perpetual check/chase rules wrong | v0.1 Rule Engine | Test suite: 5 canonical perpetual-check positions, 3 perpetual-chase; all must produce loss for violating side |
| Stalemate treated as draw | v0.1 Rule Engine | Unit test: construct stalemate position; assert current-player loss |
| Horse blocking rule missing | v0.1 Rule Engine — Horse piece implementation | Perft test with horse-blocking positions; unit test for each of 4 blocking directions |
| Elephant eye/river constraints | v0.1 Rule Engine — Elephant piece implementation | Unit test: Elephant near river (boundary cases), Elephant with occupied eye squares |
| Flying general check missing | v0.1 Rule Engine — check detection | Test suite: 3 positions that become illegal via flying general after a move |
| Cannon capture logic wrong | v0.1 Rule Engine — Cannon piece implementation | Dedicated unit tests for 0-screen, 1-screen, 2-screen, 3-screen positions; perft comparison with reference engine |
| Action mask missing from API | v0.1 Rule Engine — API design | Integration test: gymnasium.Env wrapper produces (obs, legal_mask) tuple; mask matches manual `get_legal_moves()` |
| Make/unmake residual state | v0.1 Rule Engine — move application | Perft(3) from initial position matches reference; apply-then-unmake test on all starting legal moves |
| Variable action space for RL | v0.1 Rule Engine — API design | RL unit test: policy network receives fixed-size logit vector regardless of position |

---

## Sources

- "A Complete Algorithm for Ruling the WXF Repetition Rules" (arXiv:2412.17334v1, 2024) — authoritative pseudocode for all 16 WXF repetition conditions, including perpetual check, perpetual chase, false protector logic
- NNUE Dataset Study (arXiv:2412.17948, 2024) — confirms perpetual check is a loss in Xiangqi, notes common incorrect implementations
- TalkChess forum: "Perpetual chasing in Xiangqi" (https://talkchess.com/viewtopic.php?t=35403) — detailed discussion of false-protector edge cases and three proposed detection algorithms
- Fairy-Stockfish Xiangqi perft issue #278 (https://github.com/ianfab/Fairy-Stockfish/issues/278) — reference perft values for Xiangqi starting position and test positions
- ChessProgramming Wiki: Perft (https://www.chessprogramming.org/Perft) — methodology for perft divide debugging
- PlayStrategy Xiangqi repetition rule updates, Nov 2024 (https://playstrategy.org/forum/redirect/post/jbJAP4W6) — recent change from 3-fold to 4-fold repetition adjudication in competitive play
- Chess Engine API for RL: AlphaZero paper (Science, 2018) — fixed action space with legal move masking; illegal move handling via softmax masking (probability = 0 before normalization)
- Xiangqi rules (xqinenglish.com) — authoritative English reference for palace constraints, river crossing, elephant eye, horse leg
- Orange Xiangqi engine (GitHub: danieltan1517/orange-xiangqi) — open-source implementation with WXF repetition coverage; reference for Rust-based bitboard Xiangqi engine

---
*Pitfalls research for: Xiangqi v0.1 rule engine — supporting RL training and human-AI gameplay*
*Researched: 2026-03-19*
