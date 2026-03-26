"""xiangqi UI package.

Re-exports the public API for convenient top-level imports:

    from src.xiangqi.ui import QXiangqiBoard, PieceItem, MainWindow

Module contents:

    QXiangqiBoard : QGraphicsView subclass — full board rendering
    PieceItem     : QGraphicsEllipseItem — single piece rendering
    MainWindow    : QMainWindow — top-level application window
"""

from .board import QXiangqiBoard
from .board_items import PieceItem
from .main import MainWindow

__all__ = ["QXiangqiBoard", "PieceItem", "MainWindow"]
