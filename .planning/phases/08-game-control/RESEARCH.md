# Phase 08: Game Control - Research

**Researched:** 2026-03-26
**Focus:** PyQt6 QToolBar, QAction, and button state management patterns

---

## Qt Widgets API Reference

### QToolBar

Qt6 工具栏标准用法：

```python
from PyQt6.QtWidgets import QMainWindow, QToolBar, QPushButton

toolbar = QToolBar("Game Control")
self.addToolBar(toolbar)  # QMainWindow method

# Add buttons
new_game_btn = QPushButton("新对局")
undo_btn = QPushButton("悔棋")
toolbar.addWidget(new_game_btn)
toolbar.addWidget(undo_btn)

# Or use QAction for menu + toolbar integration
from PyQt6.QtGui import QAction
new_game_action = QAction("新对局", self)
new_game_action.setShortcut("Ctrl+N")
new_game_action.triggered.connect(self.new_game)
toolbar.addAction(new_game_action)
```

### QAction vs QPushButton

| Aspect | QAction | QPushButton |
|--------|---------|-------------|
| Toolbar integration | Native | Via addWidget() |
| Menu integration | Native | N/A |
| Shortcuts | Built-in | setShortcut() |
| Icons | setIcon() | setIcon() |
| Disable/Enable | setEnabled(bool) | setEnabled(bool) |

**Decision:** Use QPushButton in toolbar for direct visual control and simpler state management.

### Button State Management

```python
# Disable button
button.setEnabled(False)

# Enable button
button.setEnabled(True)

# Check if enabled
if button.isEnabled():
    ...
```

---

## Existing Code Patterns

### GameController Signal Pattern

From `src/xiangqi/controller/game_controller.py`:

```python
# Signal definition
ai_thinking_started = pyqtSignal()
ai_thinking_finished = pyqtSignal()

# Emit signals for state changes
self.ai_thinking_started.emit()
self.ai_thinking_finished.emit()
```

**Pattern:** Controller emits signals → UI updates button states in response.

### Status Bar Update Pattern

```python
def _update_status_bar(self, turn: int, ai_thinking: bool) -> None:
    status = self._window.statusBar()
    if ai_thinking:
        status.showMessage("AI 思考中...")
    elif turn == 1:
        status.showMessage("红方回合")
    else:
        status.showMessage("黑方回合")
```

**Extension:** Add side indicator: "你执红方 | 红方回合"

### Board Interactive Control

From `src/xiangqi/ui/board.py`:

```python
def set_interactive(self, enabled: bool) -> None:
    self._interactive = enabled
```

Used by GameController to disable interaction during AI turn.

---

## Implementation Patterns

### Toolbar Integration in MainWindow

```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # ... existing init ...
        self._setup_toolbar()

    def _setup_toolbar(self):
        toolbar = QToolBar("Game Control")
        self.addToolBar(toolbar)

        self._new_game_btn = QPushButton("新对局")
        self._undo_btn = QPushButton("悔棋")

        toolbar.addWidget(self._new_game_btn)
        toolbar.addWidget(self._undo_btn)
```

### Button State Controller Extension

```python
class GameController(QObject):
    # New signals
    undo_available = pyqtSignal(bool)  # True when undo is possible

    def _on_ai_thinking_started(self):
        self._update_status_bar(-1, True)
        self.undo_available.emit(False)  # Disable undo during AI turn

    def _on_ai_thinking_finished(self):
        self._update_status_bar(self._engine.turn, False)
        self.undo_available.emit(True)   # Enable undo after AI move
```

### Random Side Assignment

```python
import random

def new_game(self):
    self._human_side = random.choice([1, -1])  # +1=Red, -1=Black
    self._engine.reset()
    # ... update UI ...
    if self._human_side == -1:
        # Human plays Black, AI (Red) moves first
        self._start_ai_turn()
```

---

## XiangqiEngine API Reference

### reset()
```python
def reset(self) -> None:
    """Reset board to starting position, clear undo stack."""
```

### undo()
```python
def undo(self) -> bool:
    """Undo last move. Returns True if successful, False if stack empty."""
```

### turn property
```python
@property
def turn(self) -> int:
    """Current turn: +1 for Red, -1 for Black."""
```

---

## Keyboard Shortcuts

| Action | Shortcut | Qt Code |
|--------|----------|---------|
| New Game | Ctrl+N | `QKeySequence("Ctrl+N")` |
| Undo | Ctrl+Z | `QKeySequence("Ctrl+Z")` |

```python
from PyQt6.QtGui import QKeySequence
from PyQt6.QtWidgets import QShortcut

shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
shortcut.activated.connect(self.new_game)
```

---

## Success Criteria Mapping

| Success Criterion | Implementation Approach |
|-------------------|------------------------|
| 新对局按钮清空棋盘 | `engine.reset()` + `board.refresh_pieces()` |
| 悔棋恢复上一局面 | `engine.undo()` x2 + `board.refresh_pieces()` |
| 开局随机分配执方 | `random.choice([1, -1])` in `new_game()` |
| 状态栏显示执方 | Update `_update_status_bar()` format |
| 按钮状态动态更新 | Connect signals to `setEnabled(bool)` |

---

## References

- Qt6 QToolBar: https://doc.qt.io/qt-6/qtoolbar.html
- Qt6 QAction: https://doc.qt.io/qt-6/qaction.html
- Existing: `src/xiangqi/controller/game_controller.py`
- Existing: `src/xiangqi/ui/main.py`
- Existing: `src/xiangqi/engine/engine.py`
