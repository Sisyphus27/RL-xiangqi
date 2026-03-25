# Phase 07: AI Interface + Game State - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-25
**Phase:** 07-ai-interface
**Areas discussed:** Turn Display, AI Thinking, Game Over, AI Timing, Thread Model, Snapshot, AI Error, Move Flow, New Game, AI API, Random Seed, AI Module

---

## Turn Display

| Option | Description | Selected |
|--------|-------------|----------|
| 状态栏文本 | 使用 QMainWindow.statusBar() 显示回合信息，位于窗口底部，简洁不占棋盘空间 | ✓ |
| 棋盘顶部标签 | 在棋盘上方添加 QLabel 显示回合，与棋盘视觉关联更紧密 | |
| 窗口标题栏 | 更新 window title 包含回合信息，无需额外 UI 空间 | |

**User's choice:** 状态栏文本
**Notes:** 简洁、Qt 原生支持、不干扰棋盘区域

---

## AI Thinking

| Option | Description | Selected |
|--------|-------------|----------|
| 状态栏文本 | 与回合指示器同一位置，黑方回合时显示 "AI 思考中..."，红方回合时显示 "红方回合" | ✓ |
| 棋盘中央悬浮框 | 棋盘上方半透明覆盖层，显示 "AI 思考中..." + 动画转圈，更醒目但实现复杂 | |
| 静默模式 | 仅改变回合指示器颜色/样式，最简单但不直观 | |

**User's choice:** 状态栏文本
**Notes:** 与回合指示器共用，同一位置不同文本

---

## Game Over

| Option | Description | Selected |
|--------|-------------|----------|
| 模态弹窗 | QMessageBox.information() 显示结果，用户点击"确定"关闭，标准做法 | ✓ |
| 非模态横幅 | 棋盘上方或底部显示结果横幅，不阻塞交互 | |
| 静默状态栏 | 状态栏显示结果 + 棋盘禁用交互，无弹窗打扰 | |

**User's choice:** 模态弹窗
**Notes:** 清晰、直接、标准 UX

---

## AI Timing

| Option | Description | Selected |
|--------|-------------|----------|
| 立即执行 | AI 返回走法后立即执行，无延迟，最快响应 | ✓ |
| 人工延迟 | AI 返回后等待 500-1000ms 再执行，让用户感知 "AI 思考过程" | |

**User's choice:** 立即执行
**Notes:** RandomAI 很快，延迟无意义；未来复杂 AI 可考虑

---

## Thread Model

| Option | Description | Selected |
|--------|-------------|----------|
| QThread + moveToThread | AI worker 对象调用 moveToThread(QThread)，线程运行事件循环，信号槽跨线程通信，Qt 官方推荐模式 | ✓ |
| 主线程同步调用 | 主线程直接调用 AI.suggest_move()，简单但会阻塞 UI | |
| Python Thread | Python threading.Thread 运行 AI，队列传递结果，纯 Python 方案 | |

**User's choice:** QThread + moveToThread
**Notes:** 与架构研究一致，Qt 官方推荐

---

## Snapshot

| Option | Description | Selected |
|--------|-------------|----------|
| 完整副本 | EngineSnapshot 包含 board 数组副本、turn、legal_moves 列表、game result，AI 只读访问，线程安全 | ✓ |
| 引用 + 锁 | EngineSnapshot 持有 engine 引用，通过属性访问，不复制数据但需要锁 | |

**User's choice:** 完整副本
**Notes:** 简单、无锁、线程安全

---

## AI Error

| Option | Description | Selected |
|--------|-------------|----------|
| 抛出异常 | is_legal() 校验失败时抛出 ValueError，游戏终止，黑方判负 | ✓ |
| 回溯重试 | is_legal() 失败时记录警告，RandomAI 重新随机选择其他合法走法 | |

**User's choice:** 抛出异常
**Notes:** 开发阶段早发现 bug

---

## Move Flow

| Option | Description | Selected |
|--------|-------------|----------|
| 用户走棋 → 检查结束 → AI走棋 | 用户落子后立即检查 result()，未结束则切换回合并启动 AI | ✓ |
| 用户走棋 → 回合显示 → 延迟 → AI | 用户落子后先显示回合切换，500ms 延迟后启动 AI | |

**User's choice:** 用户走棋 → 检查结束 → AI走棋
**Notes:** 简单直接，无多余延迟

---

## New Game

| Option | Description | Selected |
|--------|-------------|----------|
| 等待用户手动重置 | 弹窗关闭后棋盘保持终局状态，用户点击 "新对局" 按钮重置（Phase 08 实现） | ✓ |
| 弹窗内提供重置按钮 | 弹窗增加 "再来一局" 按钮，点击后立即重置 | |

**User's choice:** 等待用户手动重置
**Notes:** Phase 08 会实现 "新对局" 按钮

---

## AI API

| Option | Description | Selected |
|--------|-------------|----------|
| 单一参数：EngineSnapshot | suggest_move(snapshot: EngineSnapshot) -> int | ✓ |
| 多参数展开 | suggest_move(board, turn, legal_moves) -> int | |

**User's choice:** 单一参数：EngineSnapshot
**Notes:** 简洁，Snapshot 封装所有数据

---

## Random Seed

| Option | Description | Selected |
|--------|-------------|----------|
| 支持可配置种子 | RandomAI.__init__() 接受 seed 参数，方便测试复现 | ✓ |
| 纯随机 | 不提供种子参数，总是使用系统随机 | |

**User's choice:** 支持可配置种子
**Notes:** 测试可复现性

---

## AI Module

| Option | Description | Selected |
|--------|-------------|----------|
| src/xiangqi/ai/ | 与 engine/ 和 ui/ 平级，清晰的三层分离 | ✓ |
| src/xiangqi/ui/ai/ | AI 视为 UI 层的一部分 | |

**User's choice:** src/xiangqi/ai/
**Notes:** 与架构研究一致，三层分离清晰

---

## AI 核心澄清

用户确认：**目前阶段 AI 决策就是随机选择**，关键在于构建接口。RandomAI 的决策逻辑是从 `snapshot.legal_moves` 中随机选择一个走法。

---

## Claude's Discretion

以下决定由 Claude 处理（用户授权"你决定"）：
- EngineSnapshot dataclass 的具体字段名称
- 状态栏文本的具体措辞
- AI 思考中文本的样式
- GameController 类的具体实现细节
- 信号命名风格

---

## Deferred Ideas

- AlphaBetaAI / MCTSAI — Phase 09+ 考虑
- 将军视觉高亮 — Phase 08 UI 增强
- AI 思考动画 — v0.3 考虑
- AI 思考超时处理 — v0.3 考虑
