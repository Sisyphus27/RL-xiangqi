"""Self-play E2E validation test (Phase 12, R7).

Runs 100 random vs random games through XiangqiEnv to validate the full
RL environment pipeline (reset/step/reward/terminal/masking) works correctly
in a complete game loop. Collects and prints statistics for human review.
"""
import time
from collections import Counter

import numpy as np
import pytest

from xiangqi.rl import XiangqiEnv


def _get_termination_reason(env: XiangqiEnv, result: str) -> str:
    """Determine WHY a game ended by inspecting engine internals.

    This is test-only code -- no production code modifications needed.
    Priority order mirrors get_game_result() in endgame.py.
    """
    if result in ("RED_WINS", "BLACK_WINS"):
        legal = env._engine.legal_moves()
        if len(legal) == 0:
            if env._engine.is_check():
                return "checkmate"
            else:
                return "stalemate"
        # Has legal moves but game ended -> long chase (chaser loses)
        return "long_chase"
    else:  # DRAW
        state = env._engine.state
        # Priority: repetition > 50-move > long_check > long_chase
        hash_counts = Counter(state.zobrist_hash_history)
        if max(hash_counts.values()) >= 3:
            return "repetition_3fold"
        if state.halfmove_clock >= 100:
            return "50_move_rule"
        if env._engine._rep_state.consecutive_check_count >= 4:
            return "long_check"
        return "unknown_draw"


def test_selfplay_100_games():
    """R7: Run 100 random vs random self-play games and validate pipeline integrity.

    Validates:
    - All 100 games complete without crash
    - Legal move mask matches engine.legal_moves() at every step
    - Game length statistics are reasonable for random play
    - All three outcomes (RED_WINS, BLACK_WINS, DRAW) appear
    - Termination reasons are extracted and reported
    - Reward statistics are collected and printed
    - Timing information is reported (total, games/sec, avg per step)
    """
    np.random.seed(42)

    stats = {
        "game_lengths": [],
        "results": [],
        "total_rewards": [],
        "termination_reasons": [],
        "per_step_rewards": [],
    }

    t_start = time.time()

    for game_idx in range(100):
        env = XiangqiEnv()
        obs, info = env.reset(seed=game_idx)
        steps = 0
        total_reward = 0.0

        while True:
            # R7: legal move verification at every step
            engine_legal_count = len(env._engine.legal_moves())
            mask_legal_count = int(info["legal_mask"].sum())
            assert engine_legal_count == mask_legal_count, (
                f"Game {game_idx} step {steps}: engine has {engine_legal_count} "
                f"legal moves but mask has {mask_legal_count}"
            )

            # Sample only from legal moves
            mask = info["legal_mask"]
            legal_indices = np.where(mask == 1.0)[0]
            if len(legal_indices) == 0:
                break  # should not happen if terminated correctly
            action = int(np.random.choice(legal_indices))
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += reward
            stats["per_step_rewards"].append(reward)
            steps += 1
            if terminated:
                break

        result = env._engine.result()
        reason = _get_termination_reason(env, result)
        stats["game_lengths"].append(steps)
        stats["results"].append(result)
        stats["total_rewards"].append(total_reward)
        stats["termination_reasons"].append(reason)

    elapsed = time.time() - t_start
    total_steps = sum(stats["game_lengths"])

    # Print statistics
    game_lengths = stats["game_lengths"]
    results = stats["results"]
    reasons = stats["termination_reasons"]
    per_step = stats["per_step_rewards"]

    print()
    print("=" * 60)
    print(f"  Self-Play E2E Validation (100 games)")
    print("=" * 60)
    print(f"Timing: {elapsed:.1f}s total ({100 / elapsed:.1f} games/sec)")
    print(f"Avg step time: {elapsed / total_steps:.4f}s")
    print()
    print("Game Length:")
    print(f"  Mean: {np.mean(game_lengths):.1f}, Median: {np.median(game_lengths):.1f}, "
          f"Min: {np.min(game_lengths)}, Max: {np.max(game_lengths)}, "
          f"Std: {np.std(game_lengths):.1f}")
    print()
    print("Results:")
    for outcome in ("RED_WINS", "BLACK_WINS", "DRAW"):
        count = results.count(outcome)
        pct = count / len(results) * 100
        print(f"  {outcome}: {count} ({pct:.1f}%)")
    print()
    print("Termination Reasons:")
    for reason in ("checkmate", "stalemate", "repetition_3fold",
                   "50_move_rule", "long_check", "long_chase", "unknown_draw"):
        count = reasons.count(reason)
        if count > 0:
            print(f"  {reason}: {count}")
    print()
    print("Reward Statistics:")
    print(f"  Mean: {np.mean(per_step):.4f}, Std: {np.std(per_step):.4f}, "
          f"Min: {np.min(per_step):.4f}, Max: {np.max(per_step):.4f}")
    print("=" * 60)

    # Assertions (R7 core requirements)
    assert len(game_lengths) == 100, f"Only {len(game_lengths)} games completed"
    assert all(l > 0 for l in game_lengths), "Game with 0 steps detected"
    assert 20 < np.mean(game_lengths) < 2000, (
        f"Unexpected avg game length: {np.mean(game_lengths):.0f}"
    )
    assert "RED_WINS" in results, "No RED_WINS in 100 games"
    assert "BLACK_WINS" in results, "No BLACK_WINS in 100 games"
    assert "DRAW" in results, "No DRAW in 100 games"
    assert results.count("RED_WINS") + results.count("BLACK_WINS") > 0, (
        "All 100 games were draws"
    )
    assert "unknown_draw" not in reasons, (
        f"Unknown draw reasons: {[i for i, r in enumerate(reasons) if r == 'unknown_draw']}"
    )
