# Phase 09: XiangqiEnv Core - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-26
**Phase:** 09-xiangqi-env-core
**Areas discussed:** Module location, State management, Multi-agent interface, Illegal move handling

---

## Area 1: Module Location

| Option | Description | Selected |
|--------|-------------|----------|
| `src/xiangqi/rl/env.py` | New rl/ submodule, easy to expand training code later | ✓ |
| `src/xiangqi/env.py` | Single file, shortest import path | |
| `src/xiangqi/gymnasium.py` | Explicit Gymnasium binding, most verbose path | |

**User's choice:** `src/xiangqi/rl/env.py`
**Notes:** 新建 rl/ 子模块，便于以后扩展训练相关代码

---

## Area 2: State Management

| Option | Description | Selected |
|--------|-------------|----------|
| Wrap XiangqiEngine internally | Env holds _engine instance, delegates all logic | ✓ |
| Reimplement state directly | Env manages board/turn/history directly, matches RL_ENV.md sample | |

**User's choice:** 包装 XiangqiEngine 内部
**Notes:** XiangqiEnv 持有内部 _engine: XiangqiEngine 实例，所有走法生成/验证委托给引擎。复用已测试代码，长期更干净。

---

## Area 3: Multi-Agent Interface

| Option | Description | Selected |
|--------|-------------|----------|
| info 中返回 piece_type_to_move | info dict includes piece_type_to_move: int (0-6) | ✓ |
| 由调用方从 obs 推断 | No extra field, caller analyzes obs channels | |

**User's choice:** info 中返回 piece_type_to_move
**Notes:** info 字典包含 piece_type_to_move: int（0-6）。RL 循环直接读取，不需要分析观察通道。

---

## Area 4: Illegal Move Handling

| Option | Description | Selected |
|--------|-------------|----------|
| 不终止，info 标记非法 | reward=-2.0, terminated=False, info["illegal_move"]=True | ✓ |
| 终止游戏 | reward=-2.0, terminated=True | |

**User's choice:** 不终止，info 标记非法
**Notes:** 返回 illegal_move=True 的 info 标记，reward=-2.0，terminated=False。游戏继续，策略可以继续探索。

---

## Claude's Discretion

以下方面用户未做具体要求，由下游规划/实现阶段决定：
- Exact `render()` implementation (human vs rgb_array mode)
- Internal method naming conventions
- Whether to use `__slots__` for memory efficiency

## Deferred Ideas

- AlphaZero observation encoding as (16,10,9) board planes — Phase 10
- Per-piece-type action masking implementation — Phase 11
- Self-play E2E validation — Phase 12
- `render()` implementation — Phase 09 or 12
- Gymnasium registration with `gymnasium.make()` — Phase 09 implementation detail

---
