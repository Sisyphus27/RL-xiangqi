"""
Main entry point for RL-Xiangqi desktop UI.

Creates a QApplication with a MainWindow containing the QXiangqiBoard.

Usage
-----
    python -m src.xiangqi.ui.main
    # or
    python -c "from src.xiangqi.ui.main import main; main()"
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QToolBar, QPushButton
from PyQt6.QtGui import QKeySequence, QShortcut

from .board import QXiangqiBoard
from .constants import DEFAULT_SIZE, MIN_SIZE, MAX_SIZE
from src.xiangqi.ai import RandomAI
from src.xiangqi.controller import GameController
from src.xiangqi.engine.engine import XiangqiEngine


class MainWindow(QMainWindow):
    """
    Top-level application window for RL-Xiangqi.

    Contains a single QXiangqiBoard as the central widget and sets
    the fixed window title and size constraints.

    Attributes
    ----------
    _engine : XiangqiEngine
        Game engine instance.
    _board : QXiangqiBoard
        Board widget instance.
    _ai : RandomAI
        AI player for black.
    _controller : GameController
        Game orchestrator connecting engine, AI, and UI.
    _new_game_btn : QPushButton
        New Game button in toolbar.
    _undo_btn : QPushButton
        Undo button in toolbar.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("RL-Xiangqi v0.2")

        # Create engine and board
        self._engine = XiangqiEngine.starting()
        self._board = QXiangqiBoard(state=self._engine.state, engine=self._engine)
        self.setCentralWidget(self._board)

        # Create AI player (black)
        self._ai = RandomAI()

        # Create controller (wires engine, AI, board, and window)
        self._controller = GameController(
            engine=self._engine,
            ai_player=self._ai,
            board=self._board,
            main_window=self,
        )

        # Setup toolbar with New Game and Undo buttons
        self._setup_toolbar()

        self.resize(*DEFAULT_SIZE)
        self.setMinimumSize(*MIN_SIZE)
        self.setMaximumSize(*MAX_SIZE)

    def _setup_toolbar(self) -> None:
        """Setup toolbar with New Game and Undo buttons.

        Creates a QToolBar with "新对局" and "悔棋" buttons,
        keyboard shortcuts (Ctrl+N, Ctrl+Z), and connects
        button signals to controller methods.
        """
        toolbar = QToolBar("游戏控制", self)
        self.addToolBar(toolbar)

        # New Game button
        self._new_game_btn = QPushButton("新对局", self)
        self._new_game_btn.setToolTip("开始新对局 (Ctrl+N)")
        self._new_game_btn.clicked.connect(self._on_new_game)
        toolbar.addWidget(self._new_game_btn)

        # Undo button
        self._undo_btn = QPushButton("悔棋", self)
        self._undo_btn.setToolTip("悔棋 (Ctrl+Z)")
        self._undo_btn.setEnabled(False)  # Disabled until moves exist
        self._undo_btn.clicked.connect(self._on_undo)
        toolbar.addWidget(self._undo_btn)

        # Keyboard shortcuts
        shortcut_new = QShortcut(QKeySequence("Ctrl+N"), self)
        shortcut_new.activated.connect(self._on_new_game)

        shortcut_undo = QShortcut(QKeySequence("Ctrl+Z"), self)
        shortcut_undo.activated.connect(self._on_undo)

        # Connect controller signals for button state management
        self._connect_controller_signals()

    def _connect_controller_signals(self) -> None:
        """Connect controller signals to UI slots.

        Per D-04, D-05: Undo button disabled during AI thinking
        or when undo stack empty.
        """
        # Connect undo_available signal to button state
        self._controller.undo_available.connect(self._undo_btn.setEnabled)

    def _on_new_game(self) -> None:
        """Handle New Game button click or Ctrl+N shortcut.

        Per D-06: New Game button always enabled.
        Delegates to controller's new_game method.
        """
        self._controller.new_game()

    def _on_undo(self) -> None:
        """Handle Undo button click or Ctrl+Z shortcut.

        Per D-04, D-05: Only enabled when undo is available.
        Delegates to controller's undo method.
        """
        self._controller.undo()


def main() -> None:
    """Run the RL-Xiangqi application."""
    app = QApplication(sys.argv)
    app.setApplicationName("RL-Xiangqi")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
