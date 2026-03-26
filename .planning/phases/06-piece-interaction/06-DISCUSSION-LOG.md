# Phase 06: Piece Interaction - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in 06-CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-24
**Phase:** 06-piece-interaction
**Areas discussed:** 选子视觉反馈, 合法走法高亮, 走法执行 UX, 回合交互控制

---

## 选子视觉反馈

| Option | Description | Selected |
|--------|-------------|----------|
| 加粗边框 | 将白色描边加粗到 4px，选中状态明显，代码改动最小（修改 PieceItem.pen） | |
| 外圈高亮 | 保持白色描边，增加黄色/金色外圈，视觉更丰富但需新建 QGraphicsEllipseItem | ✓ |
| 发光效果 | 选中棋子周围绘制发光/阴影效果，需要 QGraphicsEffect 或自定义绘制 | |

**User's choice:** 外圈高亮
**Notes:** 视觉更丰富，与棋盘形成层次感

---

### 外圈高亮的颜色？

| Option | Description | Selected |
|--------|-------------|----------|
| 金黄色 #FFD700 | 象棋传统高亮色，与绿色棋盘对比明显 | ✓ |
| 橙色 #FFA500 | 更柔和的高亮，不刺眼 | |
| 蓝色 #4169E1 | 与 UI 强调色统一（如果 UI 有主题色） | |

**User's choice:** 金黄色 #FFD700
**Notes:** 象棋传统高亮色

---

### 外圈 item 的生命周期？

| Option | Description | Selected |
|--------|-------------|----------|
| 动态创建/删除 | 选中时创建外圈 item，取消选中时删除。内存效率高。 | ✓ |
| 预先创建+隐藏 | 每个 PieceItem 预先创建外圈 item，默认隐藏。切换更快但内存占用略高。 | |

**User's choice:** 动态创建/删除
**Notes:** 内存效率高，按需创建

---

### 外圈与棋子的层级关系？

| Option | Description | Selected |
|--------|-------------|----------|
| 外圈在棋子下方 | 选中棋子最上层，外圈在棋子下方（z-value < 1.0）。外圈不遮挡棋子。 | |
| 外圈在棋子上层 | 外圈在棋子上层（z-value > 1.0），但透明度 50% 不完全遮挡。视觉更突出。 | ✓ |

**User's choice:** 外圈在棋子上层
**Notes:** 视觉更突出，半透明不完全遮挡

---

## 合法走法高亮

### 合法走法目标格的标记样式？

| Option | Description | Selected |
|--------|-------------|----------|
| 半透明圆点 | 每个合法目标格中心绘制半透明圆点，直径约 0.3*cell。简洁不遮挡。 | |
| 半透明方框 | 每个合法目标格绘制半透明方框，大小约 0.9*cell。更明显但稍遮挡。 | |
| 格背景高亮 | 合法目标格背景染色（改变格底色），需在 drawBackground 中实现。 | |

**User's choice:** 半透明圆点 (推荐)
**Notes:** 实际选择：半透明圆点 (推荐)

---

### 圆点颜色？

| Option | Description | Selected |
|--------|-------------|----------|
| 金黄色 #FFD700 | 与选中外圈颜色统一，视觉一致 | ✓ |
| 绿色 #00FF00 | 与选中外圈不同，区分"选中"与"可移动"状态 | |
| 浅蓝色 #87CEEB | 更柔和，不抢眼 | |

**User's choice:** 金黄色 #FFD700
**Notes:** 与选中外圈颜色统一

---

### 圆点的实现方式？

| Option | Description | Selected |
|--------|-------------|----------|
| QGraphicsEllipseItem | 每个圆点是一个 QGraphicsEllipseItem，添加到 scene。选子时创建，取消选子时全部删除。 | ✓ |
| drawBackground 绘制 | 在 drawBackground 中绘制圆点，需存储合法走法列表。性能更好但与棋盘背景耦合。 | |

**User's choice:** QGraphicsEllipseItem (推荐)
**Notes:** 实际选择：QGraphicsEllipseItem (推荐)

---

### 圆点透明度？

| Option | Description | Selected |
|--------|-------------|----------|
| 50% 透明度 | 半透明，不遮挡棋盘，可见下方网格线 | ✓ |
| 70% 透明度 | 更透明，更不显眼 | |
| 不透明 | 不透明，最明显但可能遮挡棋盘细节 | |

**User's choice:** 50% 透明度 (推荐)
**Notes:** 实际选择：50% 透明度 (推荐)

---

### 圆点大小？

| Option | Description | Selected |
|--------|-------------|----------|
| 小圆点 (0.3*cell) | 约 0.3*cell 直径，小而清晰 | |
| 中等圆点 (0.5*cell) | 约 0.5*cell 直径，更明显 | ✓ |
| 大圆点 (0.7*cell) | 约 0.7*cell 直径，接近棋子大小 | |

**User's choice:** 中等圆点 (0.5*cell)
**Notes:** 更明显但不过大

---

## 走法执行 UX

### 落子时是否需要动画？

| Option | Description | Selected |
|--------|-------------|----------|
| 立即移动 | 点击目标格后立即更新棋盘，无动画。实现简单，响应即时。 | ✓ |
| 滑动动画 | 棋子从源格滑动到目标格，动画时长约 200-300ms。更流畅但实现复杂（QPropertyAnimation）。 | |

**User's choice:** 立即移动 (推荐)
**Notes:** 实际选择：立即移动 (推荐)

---

### 棋盘刷新方式？

| Option | Description | Selected |
|--------|-------------|----------|
| 全盘刷新 | 调用 engine.apply(move) 后，清空 scene 重新加载所有棋子。简单可靠，性能足够（32 个 item）。 | |
| 增量更新 | 只更新移动棋子和被吃棋子（如有），其余不变。性能最优但逻辑复杂。 | ✓ |

**User's choice:** 增量更新
**Notes:** 性能最优，优化用户体验

---

### 状态更新顺序？

| Option | Description | Selected |
|--------|-------------|----------|
| apply 后更新状态 | 调用 engine.apply(move) → 更新 self._state → 刷新棋盘。标准流程。 | ✓ |
| UI 先行 | 先更新 UI（移动棋子 item），再调用 engine.apply()。视觉响应更快但状态不一致风险。 | |

**User's choice:** apply 后更新状态 (推荐)
**Notes:** 实际选择：apply 后更新状态 (推荐)

---

### 增量更新的责任归属？

| Option | Description | Selected |
|--------|-------------|----------|
| QXiangqiBoard.apply_move() | 增量更新逻辑封装在 QXiangqiBoard.apply_move() 方法中，计算 from/to/captured 并更新 scene。 | ✓ |
| 外部 Controller 控制 | 由外部 Controller 调用 engine.apply() 后，通知 board 刷新。Board 不直接调用 engine。 | |

**User's choice:** QXiangqiBoard.apply_move() (推荐)
**Notes:** 实际选择：QXiangqiBoard.apply_move() (推荐)

---

### 落子后高亮清除？

| Option | Description | Selected |
|--------|-------------|----------|
| 清除所有高亮 | 清除选中外圈 + 删除所有合法走法圆点。 | ✓ |
| 保留选中状态 | 保留选中外圈，只清除合法走法圆点。落子后棋子保持选中状态。 | |

**User's choice:** 清除所有高亮 (推荐)
**Notes:** 实际选择：清除所有高亮 (推荐)

---

### 移动棋子的实现方式？

| Option | Description | Selected |
|--------|-------------|----------|
| 移动现有 item | 更新棋子 item 的 pos 和内部 _row/_col 属性，复用现有 item。高效。 | ✓ |
| 删除+重建 item | 删除源格 item，在目标格创建新 item。简单但每次移动都新建/删除对象。 | |

**User's choice:** 移动现有 item (推荐)
**Notes:** 实际选择：移动现有 item (推荐)

---

### 如何快速找到指定位置的棋子 item？

| Option | Description | Selected |
|--------|-------------|----------|
| 字典索引 | QXiangqiBoard 维护 {(row, col): PieceItem} 字典，O(1) 查找棋子 item。 | ✓ |
| 遍历查找 | 每次遍历 scene.items() 查找指定位置的 PieceItem。简单但 O(n)。 | |

**User's choice:** 字典索引 (推荐)
**Notes:** 实际选择：字典索引 (推荐)

---

### 被吃棋子的处理？

| Option | Description | Selected |
|--------|-------------|----------|
| 删除被吃棋子 | 如果目标格有敌方棋子，从 scene 移除并从字典删除。 | ✓ |
| 保留被吃棋子 | 保留被吃棋子 item，移动到屏幕外/隐藏区域。可能用于"被吃棋子展示"（Phase 08 后）。 | |

**User's choice:** 删除被吃棋子 (推荐)
**Notes:** 实际选择：删除被吃棋子 (推荐)

---

### 字典索引更新时机？

| Option | Description | Selected |
|--------|-------------|----------|
| 立即更新字典 | 移动/删除棋子后，立即更新字典索引。始终保持字典与 scene 一致。 | ✓ |
| 延迟更新字典 | 延迟更新字典，下次查找时按需更新。逻辑复杂。 | |

**User's choice:** 立即更新字典 (推荐)
**Notes:** 实际选择：立即更新字典 (推荐)

---

### engine.apply() 异常处理？

| Option | Description | Selected |
|--------|-------------|----------|
| 捕获异常+提示 | engine.apply() 会抛出 ValueError，UI 捕获后显示错误提示（如状态栏消息）。 | |
| 无需处理 | UI 层已确保只调用合法走法（从 legal_moves 中选择），engine.apply() 不会失败。无需异常处理。 | ✓ |

**User's choice:** 无需处理 (推荐)
**Notes:** 实际选择：无需处理 (推荐)

---

### 走法完成后的通知机制？

| Option | Description | Selected |
|--------|-------------|----------|
| 发出信号 | QXiangqiBoard 在更新 scene 后发出信号（如 moveApplied），通知外部状态已改变。 | ✓ |
| 无需信号 | 外部 Controller 负责调用 engine.apply() 和 board 刷新，不需要 board 信号。 | |

**User's choice:** 发出信号 (推荐)
**Notes:** 实际选择：发出信号 (推荐)

---

### 信号类型？

| Option | Description | Selected |
|--------|-------------|----------|
| 自定义信号 | 自定义 pyqtSignal，携带 move 信息（from_sq, to_sq, captured）。 | ✓ |
| 内置信号 | 使用内置信号（如 QWidget.customContextMenuRequested），通过属性传递 move 信息。 | |

**User's choice:** 自定义信号 (推荐)
**Notes:** 实际选择：自定义信号 (推荐)

---

### 走法执行期间的点击处理？

| Option | Description | Selected |
|--------|-------------|----------|
| 临时禁用交互 | 走法执行期间（apply + 刷新）禁用鼠标点击，防止重复操作。 | ✓ |
| 无需禁用 | 走法执行足够快（<10ms），无需禁用交互。 | |

**User's choice:** 临时禁用交互 (推荐)
**Notes:** 实际选择：临时禁用交互 (推荐)

---

### 交互禁用的实现方式？

| Option | Description | Selected |
|--------|-------------|----------|
| 布尔属性 | QXiangqiBoard 维护 _interactive: bool 属性，mousePressEvent 检查该标志。 | ✓ |
| setEnabled(False) | 使用 QWidget.setEnabled(False) 禁用整个 view。 | |

**User's choice:** 布尔属性 (推荐)
**Notes:** 实际选择：布尔属性 (推荐)

---

### 如何构建 move（16-bit int）？

| Option | Description | Selected |
|--------|-------------|----------|
| UI 构建 move | 点击目标格时，从选中棋子位置 + 目标格位置构建 move（16-bit int）。 | ✓ |
| 查找 legal_moves | 点击目标格时，遍历 legal_moves 找到匹配目标格的 move。 | |

**User's choice:** UI 构建 move (推荐)
**Notes:** 实际选择：UI 构建 move (推荐)

---

## 回合交互控制

### 黑方回合时如何禁用交互？

| Option | Description | Selected |
|--------|-------------|----------|
| 布尔标志 | QXiangqiBoard._interactive 属性，True=红方回合，False=黑方回合。mousePressEvent 检查该标志。 | ✓ |
| 检查 engine.turn | 检查 engine.turn，若为 -1（黑方）则忽略点击。依赖外部 engine 引用。 | |

**User's choice:** 布尔标志 (推荐)
**Notes:** 实际选择：布尔标志 (推荐)

---

### 禁用时的点击反馈？

| Option | Description | Selected |
|--------|-------------|----------|
| 静默忽略 | 点击时立即返回，无任何视觉反馈。简单直接。 | ✓ |
| 鼠标指针变化 | 鼠标指针变为禁止符号（如 Qt.ForbiddenCursor）。用户知道当前不可点击。 | |

**User's choice:** 静默忽略 (推荐)
**Notes:** 实际选择：静默忽略 (推荐)

---

### 谁设置 _interactive 标志？

| Option | Description | Selected |
|--------|-------------|----------|
| 外部 Controller 控制 | 外部 Controller（Phase 07）在红方回合设置 board._interactive=True，黑方回合设置 False。 | ✓ |
| Board 自动更新 | Board 内部监听 engine.turn 变化（需要信号），自动更新 _interactive。 | |

**User's choice:** 外部 Controller 控制 (推荐)
**Notes:** 实际选择：外部 Controller 控制 (推荐)

---

### _interactive 初始值？

| Option | Description | Selected |
|--------|-------------|----------|
| 默认启用 | _interactive 默认 True，黑方回合前设置为 False，走子后恢复 True。 | ✓ |
| 默认禁用 | _interactive 默认 False，红方回合开始时设置为 True。 | |

**User's choice:** 默认启用 (推荐)
**Notes:** 实际选择：默认启用 (推荐)

---

## Claude's Discretion

- 外圈高亮的具体透明度（建议 50-70%）
- 外圈的具体粗细（建议 2-3px）
- 圆点的 z-value（应在棋子下方，z < 1.0）
- 字典索引的初始化时机（在 _load_pieces 中同步构建）
- 信号命名的具体风格（如 moveApplied 或 on_move_applied）

## Deferred Ideas

- 拖拽落子（drag-and-drop）— MVP 阶段点击落子已足够，拖拽增加复杂度
- 将军视觉高亮（被将军时王棋高亮）— Phase 08 UI 增强考虑
- 走法动画（滑动效果）— MVP 阶段立即移动，动画在 v0.3 考虑
- 音效（落子音效）— v0.3 考虑
- 被吃棋子展示区域 — v0.2 之后考虑
