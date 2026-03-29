---
status: complete
phase: 09-xiangqi-env-core
source: 09-01-SUMMARY.md, 09-02-SUMMARY.md, 09-03-SUMMARY.md
started: 2026-03-26T14:01:00Z
updated: 2026-03-27T10:40:00Z
---

## Current Test

[testing complete]

## Tests

### 1. gymnasium.make("Xiangqi-v0") 创建 XiangqiEnv 实例
expected: 运行 `gymnasium.make("Xiangqi-v0")` 成功创建 XiangqiEnv 实例，无报错。
result: pass

### 2. reset() 返回正确形状的观察和 info 字典
expected: `env = gymnasium.make("Xiangqi-v0"); obs, info = env.reset()` 返回 obs 形状 (16,10,9) float32，info 包含 legal_mask 和 piece_masks。
result: pass

### 3. action_space 是 Discrete(8100)，observation_space 是 Box(0.0, 1.0, (16,10,9))
expected: `env.action_space` 为 Discrete(8100)，`env.observation_space` 为 Box(0.0, 1.0, (16,10,9), float32)。
result: pass

### 4. piece_masks 是 dict，keys 0-6，每个形状 (8100,) float32
expected: `info['piece_masks']` 是 dict，包含 keys 0-6，每个 value 是形状 (8100,) 的 float32 ndarray。
result: pass

### 5. step() 接受合法 action 并正常执行
expected: 传入合法 action（如从 chess board 角落移动），step() 返回 (obs, reward, terminated, truncated, info)，reward 数值合理。
result: pass

### 6. 非法 action 返回 reward=-2.0，terminated=False
expected: 传入超出范围或非法的 action（如 action=9999），step() 返回 reward=-2.0, terminated=False，状态不变。
result: pass

### 7. 将死检测：RED_WINS=+1.0，BLACK_WINS=-1.0，DRAW=0.0
expected: 触发将死时，step() 返回 terminated=True，对应方赢 reward=+/-1.0。
result: pass

### 8. 50 步和局规则：halfmove_clock>=100 触发 DRAW
expected: 残局 FEN（halfmove_clock=120）使 step() 返回 terminated=True, reward=0.0。
result: pass
fix_note: "Gap closed by plan 09-05 - WXF FEN halfmove_clock now correctly parsed from parts[3]"

### 9. SyncVectorEnv(n_envs=2) 完成 20 步无崩溃
expected: SyncVectorEnv 运行 20 步 self-play 无死锁、无异常。
result: pass

### 10. 黑方回合时棋盘旋转（canonical board rotation）
expected: 黑方回合时观察从红方视角显示（np.rot90 k=2），即 9x10 板镜像翻转。
result: pass

## Summary

total: 10
passed: 10
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

All gaps closed. Original issue (Test 8) resolved by plan 09-05:

- truth: "FEN with halfmove_clock>=100 triggers DRAW"
  status: closed
  reason: "WXF FEN parser (constants.py from_fen) uses parts[4] unconditionally. WXF 5-field FEN omits en passant field (pieces/side/castling/halfmove/fullmove), so parts[3]=halfmove, parts[4]=fullmove. Parser reads fullmove number (1) as halfmove (1), breaking 50-move rule check (requires >=100)."
  severity: major
  test: 8
  root_cause: "WXF 5-field FEN format not detected: parser assumes 6-field standard FEN format where parts[3]=en_passant and parts[4]=halfmove"
  artifacts:
    - path: "src/xiangqi/engine/constants.py"
      line: 73
      issue: "halfmove = int(parts[4]) if len(parts) > 4 else 0 — wrong index for WXF 5-field"
  missing:
    - "WXF 5-field format detection: if parts[3] is digit or '-', halfmove is at parts[3] not parts[4]"
    - "Regression test for WXF 5-field FEN halfmove parsing"
  debug_session: "S1648-S1649 (root cause found: FEN parser uses wrong index for halfmove)"
  fix_plan: "09-05"
  resolution: "Fixed in plan 09-05 (3 commits: a6f02e4, c7a5542, 859486d). from_fen() now detects WXF 5-field format via parts[3][0].isdigit(). to_fen() includes halfmove_clock parameter. Regression tests added and passing."
  verified: "2026-03-27T10:30:00Z via 09-VERIFICATION.md (16/16 truths verified)"
