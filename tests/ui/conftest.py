"""
Pytest fixtures for UI tests.

Provides:
  - starting_state: XiangqiState in standard starting position
  - board: QXiangqiBoard widget with qtbot lifecycle management
  - board_with_engine: QXiangqiBoard with engine reference for legal_moves() access
"""

import pytest
from src.xiangqi.engine.state import XiangqiState


@pytest.fixture
def starting_state() -> XiangqiState:
    """Standard starting XiangqiState (red to move, 32 pieces)."""
    return XiangqiState.starting()


@pytest.fixture
def board(qtbot):
    """QXiangqiBoard widget with starting position; managed by qtbot."""
    from src.xiangqi.ui.board import QXiangqiBoard

    b = QXiangqiBoard()
    qtbot.addWidget(b)
    return b


@pytest.fixture
def board_with_engine(qtbot):
    """QXiangqiBoard with engine reference for legal_moves() access.

    Note: QXiangqiBoard.__init__ will be updated in 06-01 to accept the
    engine parameter. This fixture establishes the contract for that API.
    """
    from src.xiangqi.engine.engine import XiangqiEngine
    from src.xiangqi.ui.board import QXiangqiBoard

    engine = XiangqiEngine()  # owns state
    b = QXiangqiBoard(state=engine.state, engine=engine)
    qtbot.addWidget(b)
    return b
