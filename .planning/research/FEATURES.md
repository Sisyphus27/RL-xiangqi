# Feature Research

**Domain:** Chinese Chess (Xiangqi) Rule Engine v0.1
**Researched:** 2026-03-19
**Confidence:** HIGH (based on WXF official rules, academic research, and established engine implementations)

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist in any Xiangqi rule engine. Missing these = engine is unusable.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Board Representation** | Core data structure for all operations | LOW | 9x10 grid (90 intersections), FEN-like notation support |
| **Piece Movement Generation** | Each piece has unique movement rules | MEDIUM | 7 piece types with distinct patterns |
| **General (King) Movement** | Wazir (1-step orthogonal), palace-confined | LOW | Must include "Flying General" rule |
| **Advisor Movement** | Ferz (1-step diagonal), palace-confined | LOW | Only 5 valid squares per side |
| **Elephant Movement** | Alfil (2-step diagonal), river-bound | LOW | Blockable at "eye" position |
| **Horse Movement** | Narrow knight (1 ortho + 1 diag outward) | MEDIUM | Blockable at "leg" position |
| **Chariot Movement** | Rook (sliding orthogonal) | LOW | Standard sliding piece |
| **Cannon Movement** | Hopper: slides non-capture, jumps to capture | MEDIUM | Must count exactly one screen for capture |
| **Soldier Movement** | Forward 1; after river: +sideways | LOW | No backward movement ever |
| **Move Validation** | Filter pseudo-legal to legal moves | MEDIUM | Must verify king safety after move |
| **Check Detection** | Determine if General is under attack | MEDIUM | Required for legal move filtering |
| **Checkmate Detection** | No legal moves to escape check | MEDIUM | Similar to Western chess |
| **Stalemate Detection** | No legal moves, not in check | LOW | **Critical:** Stalemate = LOSS in Xiangqi |
| **Flying General Rule** | Kings cannot face on same file | LOW | Immediate win/illegal position check |
| **Game Over Detection** | Terminal position identification | MEDIUM | Checkmate, stalemate, or draw conditions |

### Differentiators (Competitive Advantage)

Features that distinguish a high-quality engine from a basic one.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Perpetual Check Detection** | WXF rules: 4 repetitions = loss | HIGH | Requires position history + move classification |
| **Perpetual Chase Detection** | WXF rules: chasing unprotected piece = loss | HIGH | Most complex rule; many edge cases |
| **Repetition Draw Detection** | Legal repetition = draw | MEDIUM | Position hashing with occurrence counting |
| **50/60-Move Rule** | No capture/pawn advance = draw | LOW | Counter-based; 50 moves (WXF) or 60 plies (CXA) |
| **Insufficient Material Detection** | Neither side can force checkmate | MEDIUM | Static evaluation of material combinations |
| **Zobrist Hashing** | Fast position hashing for repetition | MEDIUM | Essential for performance at scale |
| **Incremental Attack Updates** | Update attacked squares after each move | HIGH | Major performance optimization |
| **Staged Move Generation** | Generate checks/captures first | MEDIUM | Alpha-beta search optimization |
| **UCCI Protocol Support** | Standard engine communication | MEDIUM | Required for GUI integration |
| **Move Annotation** | SAN-like notation for moves | LOW | Human-readable move recording |
| **Game History / PGN** | Record and replay games | MEDIUM | WXF notation format |
| **Position FEN Import/Export** | Standard position serialization | LOW | Essential for testing and debugging |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem useful but create problems or violate Xiangqi rules.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Stalemate as Draw** | Western chess convention | Violates Xiangqi rules; stalemate is LOSS | Implement correct Xiangqi stalemate = loss |
| **Simplified Repetition (3-fold draw)** | Western chess convention | Xiangqi has complex repetition rules with win/loss/draw outcomes | Implement full WXF repetition classification |
| **Allow Illegal Moves** | "Training mode" idea | Corrupts game state, breaks RL training | Strict validation always; use "analysis mode" for exploration |
| **Custom Piece Values** | "Balance the game" | Xiangqi has established balance; changes break standard play | Use standard piece values for RL rewards |
| **Time Control in Engine** | "Complete game management" | Engine should be stateless; time belongs to UI/arbitrator | Keep engine focused on rules; UI handles time |
| **Opening Book Integration** | "Better play from start" | Project goal is pure RL learning from zero | Defer to post-training; engine should be rule-only |

---

## Feature Dependencies

```
Board Representation
    |--requires--> Piece Definitions
    |                  |--requires--> Movement Patterns
    |
    |--requires--> Position Validation
    |                  |--requires--> Flying General Check
    |
    |--requires--> Move Generation
    |                   |--requires--> Pseudo-legal Generation
    |                   |                  |--requires--> General Movement
    |                   |                  |--requires--> Advisor Movement
    |                   |                  |--requires--> Elephant Movement
    |                   |                  |--requires--> Horse Movement
    |                   |                  |--requires--> Chariot Movement
    |                   |                  |--requires--> Cannon Movement
    |                   |                  |--requires--> Soldier Movement
    |                   |
    |                   |--requires--> Legal Move Filtering
    |                                  |--requires--> Check Detection
    |                                                 |--requires--> Attack Detection

Check Detection
    |--requires--> Sliding Piece Attacks (Chariot, Cannon)
    |--requires--> Leaper Attacks (Horse, Elephant)
    |--requires--> Hopper Attacks (Cannon capture)

Checkmate Detection
    |--requires--> Legal Move Generation
                       |--requires--> Check Detection

Stalemate Detection
    |--requires--> Legal Move Generation

Repetition Detection
    |--requires--> Zobrist Hashing
    |                  |--requires--> Board Representation
    |--requires--> Position History

Perpetual Check/Chase Detection
    |--requires--> Repetition Detection
                       |--requires--> Move Nature Classification
                                          |--requires--> Check Detection
                                          |--requires--> Chase Detection

Game Over Detection
    |--requires--> Checkmate Detection
    |--requires--> Stalemate Detection
    |--requires--> Repetition Detection
    |--requires--> Insufficient Material Detection
```

### Dependency Notes

- **Legal Move Filtering requires Check Detection:** After making a pseudo-legal move, must verify own king is not in check
- **Check Detection requires Attack Detection:** Must determine all squares attacked by opponent
- **Perpetual Check/Chase requires Move Nature Classification:** Each move must be classified as check/chase/idle
- **Cannon is unique:** Requires both sliding (non-capture) and hopper (capture) attack detection

---

## MVP Definition

### Launch With (v0.1)

Minimum viable rule engine for RL training to begin.

- [x] **Board Representation** — Foundation for all operations; 9x10 grid with piece placement
- [x] **All 7 Piece Movement Rules** — Complete pseudo-legal move generation
- [x] **Flying General Rule** — Critical Xiangqi-specific rule
- [x] **Legal Move Validation** — Filter pseudo-legal to legal (king safety check)
- [x] **Check Detection** — Determine if General is under attack
- [x] **Checkmate Detection** — Terminal condition for game end
- [x] **Stalemate Detection** — Terminal condition (LOSS for stalemated side)
- [ ] **Basic Repetition Detection** — Detect 4-fold repetition (as draw for MVP)
- [ ] **50-Move Rule** — Draw by no capture/pawn advance

### Add After Validation (v0.2)

Features to add once core engine is stable and RL training is working.

- [ ] **Perpetual Check Detection (WXF)** — Loss for 4 consecutive checks
- [ ] **Perpetual Chase Detection (WXF)** — Loss for 4 consecutive chases
- [ ] **Zobrist Hashing** — Performance optimization for repetition detection
- [ ] **Insufficient Material Detection** — Automatic draw for unwinnable positions
- [ ] **UCCI Protocol Support** — Interface with standard Xiangqi GUIs

### Future Consideration (v1.0+)

Features to defer until core RL system is proven.

- [ ] **Full WXF Notation Support** — Complete game recording format
- [ ] **Opening/Endgame Tablebase Detection** — For perfect play in known positions
- [ ] **Transposition Table Integration** — For engine search (not needed for RL)

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Board Representation | HIGH | LOW | P1 |
| Piece Movement (7 types) | HIGH | MEDIUM | P1 |
| Flying General Rule | HIGH | LOW | P1 |
| Legal Move Validation | HIGH | MEDIUM | P1 |
| Check/Checkmate Detection | HIGH | MEDIUM | P1 |
| Stalemate Detection | HIGH | LOW | P1 |
| Basic Repetition (4-fold draw) | MEDIUM | MEDIUM | P1 |
| 50-Move Rule | MEDIUM | LOW | P1 |
| Perpetual Check (WXF) | HIGH | HIGH | P2 |
| Perpetual Chase (WXF) | HIGH | HIGH | P2 |
| Zobrist Hashing | MEDIUM | MEDIUM | P2 |
| Insufficient Material | MEDIUM | MEDIUM | P2 |
| UCCI Protocol | LOW | MEDIUM | P2 |
| WXF Notation | LOW | MEDIUM | P3 |

**Priority Key:**
- P1: Must have for v0.1 launch
- P2: Should have for v0.2 (full rule compliance)
- P3: Nice to have, future consideration

---

## Competitor Feature Analysis

| Feature | xiangqi.js | Orange-Xiangqi | Fairy-Stockfish | Our Approach |
|---------|------------|----------------|-----------------|--------------|
| Move Generation | Complete | Complete | Complete | Complete (P1) |
| Check/Checkmate | Complete | Complete | Complete | Complete (P1) |
| Stalemate | Complete | Complete | Complete | Complete (P1) |
| Flying General | Complete | Complete | Complete | Complete (P1) |
| Perpetual Check | Partial | Complete | Partial | P2 (v0.2) |
| Perpetual Chase | No | Complete | No | P2 (v0.2) |
| Repetition Draw | Complete | Complete | Complete | P1 (basic) |
| 50-Move Rule | Complete | Complete | Complete | P1 |
| Zobrist Hashing | Yes | Yes | Yes | P2 |
| UCCI Protocol | No | Yes | Yes | P2 |
| NNUE Evaluation | No | Yes | Yes | N/A (RL project) |

---

## Piece Movement Reference

### Movement Patterns by Piece Type

| Piece | Betza Notation | Movement | Constraints |
|-------|----------------|----------|-------------|
| **General (将/帅)** | `W` | 1 step orthogonal | Palace only; Flying General rule |
| **Advisor (士/仕)** | `F` | 1 step diagonal | Palace only |
| **Elephant (象/相)** | `nA` | 2 steps diagonal | Cannot cross river; blocked at eye |
| **Horse (马/傌)** | `n[WF]` | 1 ortho + 1 diag outward | Blocked at leg position |
| **Chariot (车/俥)** | `R` | Sliding orthogonal | Cannot jump |
| **Cannon (炮/砲)** | `pR` | Sliding orthogonal; hopper capture | Capture needs exactly 1 screen |
| **Soldier (卒/兵)** | `fW` / `fWsW` | Forward 1; +sideways after river | Never backward |

### Special Rule Details

**Flying General (对将):**
- If two Generals face each other on same file with no intervening pieces
- Either General can capture the other
- Position is illegal if active player leaves kings facing after move
- Some rules treat this as immediate win for player who exposes the facing

**Cannon Capture Algorithm:**
```
For each orthogonal direction:
    screen_found = false
    for each square along ray:
        if not screen_found:
            if square has piece:
                screen_found = true  # Found the screen
        else:
            if square has enemy piece:
                add to capture list
            break  # Blocked after first piece past screen
```

**Horse Blocking (拐马脚):**
- Horse moves 1 orthogonal then 1 diagonal outward
- If the orthogonal "leg" square is occupied, horse cannot move in that direction
- 8 potential destinations, each with unique leg position

**Elephant Blocking (塞象眼):**
- Elephant moves exactly 2 diagonal squares
- The intermediate "eye" square must be empty
- Cannot cross river (stays on own side)

---

## Rule Engine Complexity Analysis

### Implementation Difficulty by Component

| Component | Lines of Code (est.) | Algorithm Complexity | Testing Complexity |
|-----------|---------------------|---------------------|-------------------|
| Board Representation | 50-100 | LOW | LOW |
| Piece Movement | 200-300 | MEDIUM | MEDIUM |
| Attack Detection | 150-200 | MEDIUM | HIGH |
| Legal Move Filter | 50-100 | LOW | MEDIUM |
| Check/Checkmate | 100-150 | MEDIUM | HIGH |
| Stalemate | 30-50 | LOW | MEDIUM |
| Flying General | 30-50 | LOW | MEDIUM |
| Repetition (basic) | 100-150 | MEDIUM | HIGH |
| 50-Move Rule | 20-30 | LOW | LOW |
| Perpetual Check (WXF) | 200-300 | HIGH | VERY HIGH |
| Perpetual Chase (WXF) | 300-500 | VERY HIGH | VERY HIGH |
| Zobrist Hashing | 50-100 | MEDIUM | MEDIUM |

### Critical Testing Scenarios

1. **Pin Detection:** Piece pinned to king cannot move (would expose king)
2. **Discovered Check:** Moving a piece reveals check on opponent king
3. **Double Check:** King attacked by two pieces simultaneously
4. **Cannon Screen Changes:** Moving piece affects cannon's capture ability
5. **River Crossing:** Soldier gains sideways movement exactly on river crossing
6. **Palace Corners:** Advisor and General corner cases
7. **Flying General:** All scenarios of king facing detection

---

## Draw Rules Summary

| Rule | Trigger | Result | Complexity |
|------|---------|--------|------------|
| **Repetition Draw** | Same position occurs 4 times with same player to move | Draw | MEDIUM |
| **Perpetual Check** | One player checks 4+ times consecutively | Loss for checking player | HIGH |
| **Perpetual Chase** | One player chases same unprotected piece 4+ times | Loss for chasing player | HIGH |
| **50-Move Rule** | 50 moves without pawn advance or capture | Draw | LOW |
| **Insufficient Material** | Neither side can force checkmate | Draw | MEDIUM |
| **Mutual Check/Chase** | Both players violate rules equally | Draw | HIGH |

**Key Insight:** Xiangqi repetition rules are asymmetric — the same position repeating can result in win, loss, or draw depending on the *nature* of the moves being repeated.

---

## Sources

- [Complete Implementation of WXF Chinese Chess Rules](https://arxiv.org/html/2412.17334v1) (arXiv:2412.17334, December 2024) — HIGH confidence
- [The Rules of Xiangqi (Chinese Chess)](https://www.xqinenglish.com/index.php?option=com_content&view=article&id=923:the-rules-of-xiangqi-chinese-chess&catid=119&Itemid=569&lang=en) — HIGH confidence
- [xiangqi.js GitHub Repository](https://github.com/lengyanyu258/xiangqi.js/) — MEDIUM confidence
- [Orange-Xiangqi GitHub Repository](https://github.com/danieltan1517/orange-xiangqi) — MEDIUM confidence
- [Xiangqi (Chinese Chess) — GNU XBoard Rules](https://www.gnu.org/software/xboard/whats_new/rules/Xiangqi.html) — HIGH confidence
- [Xiangqi — PlayStrategy](https://playstrategy.org/variant/xiangqi) — MEDIUM confidence
- [How to Play Chinese Chess (Xiangqi)](https://www.ymimports.com/pages/how-to-play-xiangqi-chinese-chess) — MEDIUM confidence
- [Wikipedia — Xiangqi](https://en.wikipedia.org/wiki/Xiangqi) — MEDIUM confidence

---

*Feature research for: RL-Xiangqi v0.1 Rule Engine*
*Researched: 2026-03-19*
