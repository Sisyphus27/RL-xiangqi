"""GameController - orchestrates engine, AI, and UI signals."""
import random

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
    undo_available = pyqtSignal(bool)

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
        self._human_side: int = random.choice([1, -1])  # D-07: random side assignment

        # Wire board signal (D-19)
        self._board.move_applied.connect(self._on_move_applied)

        # Wire internal signals to handlers
        self.turn_changed.connect(self._on_turn_changed)
        self.game_over.connect(self._on_game_over)
        self.ai_thinking_started.connect(self._on_ai_thinking_started)
        self.ai_thinking_finished.connect(self._on_ai_thinking_finished)

        # Initial status bar update with side indicator
        self._update_status_bar(self._engine.turn, False)

        # If human plays Black, trigger AI move immediately (D-09)
        if self._human_side == -1:
            self._start_ai_turn()

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

        # Start AI if it's AI's turn (not human's side)
        if self._engine.turn != self._human_side:
            self._start_ai_turn()

    @pyqtSlot(int)
    def _on_turn_changed(self, turn: int) -> None:
        """Update status bar and interaction on turn change."""
        self._update_status_bar(turn, False)
        # Enable interaction only on human's turn (D-09)
        self._board.set_interactive(turn == self._human_side)

    @pyqtSlot()
    def _on_ai_thinking_started(self) -> None:
        """Update status bar when AI starts thinking."""
        self._update_status_bar(-1, True)
        # Disable undo during AI thinking (D-04)
        self.undo_available.emit(False)

    @pyqtSlot()
    def _on_ai_thinking_finished(self) -> None:
        """Update status bar and undo button when AI finishes."""
        self._update_status_bar(self._engine.turn, False)
        # Check if undo is possible (D-05)
        can_undo = len(self._engine.move_history) > 0
        self.undo_available.emit(can_undo)

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
        """Update status bar with side indicator and turn state.

        Per D-01, D-02: Status bar shows side, turn, and AI thinking state.
        Format: "你执红方 | 红方回合" or "你执黑方 | AI 思考中..."
        """
        side_text = "你执红方" if self._human_side == 1 else "你执黑方"

        if ai_thinking:
            turn_text = "AI 思考中..."
        elif turn == 1:
            turn_text = "红方回合"
        else:
            turn_text = "黑方回合"

        status = self._window.statusBar()
        status.showMessage(f"{side_text} | {turn_text}")

    # ─── Public API ───────────────────────────────────────────────────────────

    def new_game(self) -> None:
        """Start a new game.

        Per D-06: Reset engine to starting position, clear board state,
        and optionally reassign human side randomly.
        """
        # Stop any ongoing AI computation
        if self._ai_thread is not None:
            self._ai_thread.quit()
            self._ai_thread.wait(1000)
            self._ai_thread = None
            self._ai_worker = None

        # Reset engine to starting position
        self._engine.reset()

        # Reset board to match engine state
        self._board.sync_state(self._engine.state)

        # Re-randomize human side for variety
        self._human_side = random.choice([1, -1])

        # Update status bar with new side assignment
        self._update_status_bar(self._engine.turn, False)

        # Reset undo button state (no moves yet)
        self.undo_available.emit(False)

        # If human plays Black, trigger AI move immediately (D-09)
        if self._human_side == -1:
            self._start_ai_turn()
        else:
            # Enable interaction for human's turn
            self._board.set_interactive(True)

    def undo(self) -> None:
        """Undo the last move (and AI's response if applicable).

        Per D-05: Undo is only available when there are moves in history
        and AI is not thinking.
        """
        # Cannot undo during AI thinking (D-04)
        if self._ai_thread is not None and self._ai_thread.isRunning():
            return

        # Need at least one move to undo
        if len(self._engine.move_history) == 0:
            return

        # Undo the last move (could be AI's move or human's move)
        self._engine.undo()

        # If it was AI's turn before undo, we need to undo human's move too
        # to get back to the state before human's action
        if self._engine.turn != self._human_side and len(self._engine.move_history) > 0:
            self._engine.undo()

        # Update board to reflect new state
        self._board.sync_state(self._engine.state)

        # Emit turn changed signal
        self.turn_changed.emit(self._engine.turn)

        # Update undo button state
        can_undo = len(self._engine.move_history) > 0
        self.undo_available.emit(can_undo)
