"""Xiangqi rule helpers: flying general detection.

This module is a backward-compatibility shim. Core logic has moved:
  - get_game_result() -> endgame.py
  - is_in_check(), is_legal_move(), generate_legal_moves(), apply_move() -> legal.py
  - flying_general_violation() -> legal.py
"""
from __future__ import annotations

from .endgame import get_game_result
from .legal import (
    flying_general_violation,
    is_in_check,
    is_legal_move,
    generate_legal_moves,
    apply_move,
    _generals_face_each_other,
)

__all__ = [
    'get_game_result',
    'flying_general_violation',
    '_generals_face_each_other',
    'is_in_check',
    'is_legal_move',
    'generate_legal_moves',
    'apply_move',
]
