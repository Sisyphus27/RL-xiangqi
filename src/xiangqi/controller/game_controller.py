"""GameController - orchestrates engine, AI, and UI signals."""
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
from PyQt6.QtWidgets import QMessageBox

from src.xiangqi.ai.base import AIPlayer, EngineSnapshot
from src.xiangqi.engine.engine import XiangqiEngine
from src.xiangqi.engine.types import decode_move
from .ai_worker import AIWorker


class GameController(QObject):
    """Orchestrates engine, AI player, and UI signals.

    Per RESEARCH.md Pattern 3: Single QObject that owns engine, AI player,
    and wires all signals. Central state machine for game flow.

    Signals
    -------
    turn_changed : int
        Emitted when turn switches. +1 for red, -1 for black.
    game_over : str
        Emitted when game ends. Result string: 'RED_WINS', 'BLACK_WINS', 'DRAW'.
    ai_thinking_started : None
        Emitted when AI thread starts.
    ai_thinking_finished : None
        Emitted when AI move has been applied.
    """

    turn_changed = pyqtSignal(int)
    game_over = pyqtSignal(str)
    ai_thinking_started = pyqtSignal()
    ai_thinking_finished = pyqtSignal()

    def __init__(
        self,
        engine: XiangqiEngine,
        ai_player: AIPlayer,
        board,  # QXiangqiBoard
        main_window,  # QMainWindow
    ):
        super().__init__()
        self._engine = engine
        self._ai_player = ai_player
        self._board = board
        self._window = main_window
        self._ai_thread: QThread | None = None
        self._ai_worker: AIWorker | None = None

        # Wire board signal (D-19)
        self._board.move_applied.connect(self._on_move_applied)

        # Wire internal signals to handlers
        self.turn_changed.connect(self._on_turn_changed)
        self.game_over.connect(self._on_game_over)
        self.ai_thinking_started.connect(self._on_ai_thinking_started)
        self.ai_thinking_finished.connect(self._on_ai_thinking_finished)

        # Initial status bar update
        self._update_status_bar(self._engine.turn, False)

    # ─── Signal handlers ──────────────────────────────────────────────────────

    @pyqtSlot(int, int, int)
    def _on_move_applied(self, from_sq: int, to_sq: int, captured: int) -> None:
        """Handle move_applied signal from board.

        Per D-13: User move -> check result() -> switch turn -> start AI.
        """
        result = self._engine.result()
        if result != "IN_PROGRESS":
            self._handle_game_over(result)
            return

        # Emit turn changed signal
        self.turn_changed.emit(self._engine.turn)

        # Start AI if black's turn
        if self._engine.turn == -1:
            self._start_ai_turn()

    @pyqtSlot(int)
    def _on_turn_changed(self, turn: int) -> None:
        """Update status bar on turn change."""
        self._update_status_bar(turn, False)

    @pyqtSlot()
    def _on_ai_thinking_started(self) -> None:
        """Update status bar when AI starts thinking."""
        self._update_status_bar(-1, True)

    @pyqtSlot()
    def _on_ai_thinking_finished(self) -> None:
        """Update status bar when AI finishes."""
        self._update_status_bar(self._engine.turn, False)

    @pyqtSlot(str)
    def _on_game_over(self, result: str) -> None:
        """Show game over popup. Per D-03."""
        result_text = {
            "RED_WINS": "红胜",
            "BLACK_WINS": "黑胜",
            "DRAW": "和棋",
        }.get(result, result)

        QMessageBox.information(
            self._window,
            "对局结束",
            result_text,
            QMessageBox.StandardButton.Ok,
        )

    @pyqtSlot(int)
    def _on_ai_move_ready(self, move: int) -> None:
        """Handle AI move ready signal.

        Per D-11: Validate with is_legal() before apply.
        """
        # Clean up thread
        if self._ai_thread is not None:
            self._ai_thread.quit()
            self._ai_thread.wait(5000)
            self._ai_thread = None
            self._ai_worker = None

        self.ai_thinking_finished.emit()

        # D-11: is_legal guard
        if not self._engine.is_legal(move):
            raise ValueError(f"AI returned illegal move: {move}")

        # Decode move and apply via board
        from_sq, to_sq, _ = decode_move(move)
        self._board.apply_move(from_sq, to_sq)

        # Re-enable interaction
        self._board.set_interactive(True)

        # Check for game over after AI move
        result = self._engine.result()
        if result != "IN_PROGRESS":
            self._handle_game_over(result)

    @pyqtSlot(str)
    def _on_ai_error(self, message: str) -> None:
        """Handle AI error signal."""
        # Clean up thread
        if self._ai_thread is not None:
            self._ai_thread.quit()
            self._ai_thread.wait(5000)
            self._ai_thread = None
            self._ai_worker = None

        self.ai_thinking_finished.emit()

        # Re-enable interaction
        self._board.set_interactive(True)

        # Print error (don't crash)
        print(f"AI error: {message}")

    # ─── Internal methods ──────────────────────────────────────────────────────

    def _start_ai_turn(self) -> None:
        """Launch AI computation in background thread.

        Per D-04 to D-06: QThread + moveToThread() pattern.
        """
        # D-18: Disable board interaction
        self._board.set_interactive(False)

        self.ai_thinking_started.emit()

        # Create snapshot on main thread (thread-safe)
        snapshot = EngineSnapshot.from_engine(self._engine)

        # Create worker + thread
        self._ai_thread = QThread()
        self._ai_worker = AIWorker(self._ai_player, snapshot)
        self._ai_worker.moveToThread(self._ai_thread)

        # Wire signals
        self._ai_thread.started.connect(self._ai_worker.compute)
        self._ai_worker.move_ready.connect(self._on_ai_move_ready)
        self._ai_worker.error.connect(self._on_ai_error)

        # Cleanup on finish
        self._ai_thread.finished.connect(self._ai_worker.deleteLater)
        self._ai_thread.finished.connect(self._ai_thread.deleteLater)

        # Start
        self._ai_thread.start()

    def _handle_game_over(self, result: str) -> None:
        """Emit game_over signal."""
        self.game_over.emit(result)

    def _update_status_bar(self, turn: int, ai_thinking: bool) -> None:
        """Update status bar with turn indicator.

        Per D-01, D-02: Status bar shows turn and AI thinking state.
        """
        status = self._window.statusBar()
        if ai_thinking:
            status.showMessage("AI 思考中...")
        elif turn == 1:
            status.showMessage("红方回合")
        else:
            status.showMessage("黑方回合")
