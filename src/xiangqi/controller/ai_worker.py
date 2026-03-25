"""AIWorker - QThread worker object for AI computation."""
from PyQt6.QtCore import QObject, pyqtSignal

from src.xiangqi.ai.base import AIPlayer, EngineSnapshot


class AIWorker(QObject):
    """Worker object for AI computation in a background thread.

    Per D-04 to D-06: Uses QThread + moveToThread() pattern.
    The worker is created on main thread, then moved to AI thread.
    compute() slot runs in worker thread; signals cross to main thread.

    Signals
    -------
    move_ready : int
        Emitted with 16-bit move integer when AI selects a move.
    error : str
        Emitted with error message if AI computation fails.
    """

    move_ready = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self, ai_player: AIPlayer, snapshot: EngineSnapshot):
        super().__init__()
        self._ai = ai_player
        self._snapshot = snapshot

    def compute(self) -> None:
        """Slot called when thread starts. Runs in worker thread.

        Calls AI suggest_move and emits result via signal.
        """
        try:
            move = self._ai.suggest_move(self._snapshot)
            if move is not None:
                self.move_ready.emit(move)
        except Exception as e:
            self.error.emit(str(e))
