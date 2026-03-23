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


class MainWindow(QMainWindow):
    """
    Top-level application window for RL-Xiangqi.

    Contains a single QXiangqiBoard as the central widget and sets
    the fixed window title and size constraints.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("RL-Xiangqi v0.2")
        self.setCentralWidget(QXiangqiBoard())
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
