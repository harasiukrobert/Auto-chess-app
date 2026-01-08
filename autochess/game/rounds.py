import math
import random
from typing import Any, Dict, List, Optional

# ---------------- Procedural Rounds Config ----------------
# Keep round tuning here (not in config/setting.py).
ROUND_CONFIG: Dict[str, Any] = {
    # End goal
    "max_rounds": 10,

    # Random starting gold range (inclusive)
    "starting_gold_min": 2,
    "starting_gold_max": 4,

    # Random gold reward per completed round.
    # Reward range increases with round number:
    #   min = reward_min_base + (round-1) * reward_min_inc_per_round
    #   max = reward_max_base + (round-1) * reward_max_inc_per_round
    "reward_min_base": 5,
    "reward_max_base": 7,
    "reward_min_inc_per_round": 0,
    "reward_max_inc_per_round": 1,

    # Board sizes ramp from small to large across the run.
    # Round 1 starts at min size.
    "board_min_cols": 3,
    "board_min_rows": 4,
    "board_max_cols": 11,
    "board_max_rows": 8,
}


class RoundManager:
    """Provides procedural round configurations.

    Rounds are generated once per run and cached so multiple calls for the
    same round number remain consistent.
    """

    def __init__(self, seed: Optional[int] = None, config: Optional[Dict[str, Any]] = None):
        self._seed = int(seed) if seed is not None else None
        self._rng = random.Random(self._seed)
        self._config = dict(ROUND_CONFIG)
        if config:
            # Allow callers to override without mutating module-level defaults.
            self._config.update(config)
        self._max_rounds = int(self._config.get("max_rounds", 0) or 0)
        self._rounds_by_number: Dict[int, Dict[str, Any]] = {}
        self._starting_gold = self._roll_starting_gold()

    def _roll_starting_gold(self) -> int:
        lo = int(self._config.get("starting_gold_min", 0) or 0)
        hi = int(self._config.get("starting_gold_max", 0) or 0)
        if hi < lo:
            lo, hi = hi, lo
        return int(self._rng.randint(lo, hi))

    def _reward_range_for_round(self, number: int) -> tuple[int, int]:
        n = max(1, int(number))
        base_min = int(self._config.get("reward_min_base", 0) or 0)
        base_max = int(self._config.get("reward_max_base", 0) or 0)
        inc_min = int(self._config.get("reward_min_inc_per_round", 0) or 0)
        inc_max = int(self._config.get("reward_max_inc_per_round", 0) or 0)

        lo = base_min + (n - 1) * inc_min
        hi = base_max + (n - 1) * inc_max
        if hi < lo:
            hi = lo
        return lo, hi

    def _board_size_for_round(self, number: int) -> tuple[int, int]:
        n = max(1, int(number))
        min_cols = int(self._config.get("board_min_cols", 0) or 0)
        min_rows = int(self._config.get("board_min_rows", 0) or 0)
        max_cols = int(self._config.get("board_max_cols", 0) or 0)
        max_rows = int(self._config.get("board_max_rows", 0) or 0)

        # Rows must be even.
        def _clamp_even(value: int, lo: int, hi: int) -> int:
            lo = int(lo)
            hi = int(hi)
            if hi < lo:
                lo, hi = hi, lo
            v = int(value)
            # Prefer rounding up to the next even number.
            if v % 2 != 0:
                v += 1
            # Clamp.
            if v > hi:
                v = hi
            if v < lo:
                v = lo
            # Final safeguard: if clamping landed on odd (e.g., odd bounds), adjust down.
            if v % 2 != 0:
                v = max(lo, v - 1)
            return v

        # Round 1 should start small.
        if n <= 1 or self._max_rounds <= 1:
            return min_cols, min_rows

        progress = (n - 1) / float(max(1, self._max_rounds - 1))
        cap_cols = min_cols + int(math.ceil((max_cols - min_cols) * progress))
        cap_rows = min_rows + int(math.ceil((max_rows - min_rows) * progress))
        cap_cols = max(min_cols, min(max_cols, cap_cols))
        cap_rows = max(min_rows, min(max_rows, cap_rows))
        cap_rows = _clamp_even(cap_rows, min_rows, max_rows)

        # Deterministic growth: size increases with rounds.
        return cap_cols, cap_rows

    def _generate_round(self, number: int) -> Dict[str, Any]:
        cols, rows = self._board_size_for_round(number)
        lo, hi = self._reward_range_for_round(number)
        reward = int(self._rng.randint(lo, hi))
        return {
            "board": {"cols": int(cols), "rows": int(rows)},
            "reward_gold": reward,
        }

    @property
    def starting_gold(self) -> int:
        return int(self._starting_gold)

    def get_round(self, number: int) -> Optional[Dict[str, Any]]:
        n = int(number)
        if not self.has_round(n):
            return None
        if n not in self._rounds_by_number:
            self._rounds_by_number[n] = self._generate_round(n)
        return self._rounds_by_number.get(n)

    def has_round(self, number: int) -> bool:
        n = int(number)
        return 1 <= n <= int(self._max_rounds)

    def max_round(self) -> int:
        return int(self._max_rounds)

    def get_board_size(self, number: int) -> Dict[str, int]:
        r = self.get_round(number) or {}
        b = r.get("board", {})
        return {"cols": int(b.get("cols", 9)), "rows": int(b.get("rows", 6))}

    def get_enemies(self, number: int) -> List[Dict[str, Any]]:
        r = self.get_round(number) or {}
        return list(r.get("enemies", []))

    def get_player_start(self) -> List[Dict[str, Any]]:
        # Player starts with no pre-placed units; they must buy via the shop.
        return []

    def get_reward(self, number: int) -> int:
        r = self.get_round(number) or {}
        return int(r.get("reward_gold", 0))

    # Global enemy spawn deprecated in favor of per-enemy row/col hints.
