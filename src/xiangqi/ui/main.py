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
from PyQt6.QtWidgets import QApplication, QMainWindow

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

        self.resize(*DEFAULT_SIZE)
        self.setMinimumSize(*MIN_SIZE)
        self.setMaximumSize(*MAX_SIZE)


def main() -> None:
    """Run the RL-Xiangqi application."""
    app = QApplication(sys.argv)
    app.setApplicationName("RL-Xiangqi")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
