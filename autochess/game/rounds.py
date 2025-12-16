import json
import os
from typing import Any, Dict, List, Optional

DEFAULT_CONFIG = {
    "starting_gold": 10,
    "rounds": [
        {
            "number": 1,
            "board": {"cols": 7, "rows": 5},
            "player_start": [
                {"name": "warrior", "count": 1},
                {"name": "archer", "count": 1}
            ],
            "enemies": [
                {"name": "warrior", "count": 2}
            ],
            "reward_gold": 5
        },
        {
            "number": 2,
            "board": {"cols": 8, "rows": 6},
            "enemies": [
                {"name": "warrior", "count": 2},
                {"name": "archer", "count": 1}
            ],
            "reward_gold": 6
        },
        {
            "number": 3,
            "board": {"cols": 9, "rows": 6},
            "enemies": [
                {"name": "warrior", "count": 2},
                {"name": "archer", "count": 1},
                {"name": "lancer", "count": 1}
            ],
            "reward_gold": 7
        }
    ]
}


class RoundManager:
    """Loads and provides round configurations.

    Expected JSON format (config/rounds.json):
    {
      "starting_gold": 10,
      "rounds": [
        {"number": 1,
         "board": {"cols": 7, "rows": 5},
         "player_start": [{"name": "warrior", "count": 1}],
         "enemies": [{"name": "warrior", "count": 2}],
         "reward_gold": 5}
      ]
    }
    """

    def __init__(self, config_path: str):
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self._rounds_by_number: Dict[int, Dict[str, Any]] = {}
        self._load()

    def _load(self):
        cfg = None
        try:
            with open(self.config_path, 'r') as f:
                cfg = json.load(f)
        except Exception:
            # Fallback to defaults if file missing or invalid
            cfg = DEFAULT_CONFIG
        self._config = cfg or DEFAULT_CONFIG
        rounds: List[Dict[str, Any]] = self._config.get("rounds", [])
        self._rounds_by_number = {int(r.get("number", i + 1)): r for i, r in enumerate(rounds)}

    @property
    def starting_gold(self) -> int:
        return int(self._config.get("starting_gold", 10))

    def get_round(self, number: int) -> Optional[Dict[str, Any]]:
        return self._rounds_by_number.get(int(number))

    def has_round(self, number: int) -> bool:
        return int(number) in self._rounds_by_number

    def max_round(self) -> int:
        return max(self._rounds_by_number.keys()) if self._rounds_by_number else 0

    def get_board_size(self, number: int) -> Dict[str, int]:
        r = self.get_round(number) or {}
        b = r.get("board", {})
        return {"cols": int(b.get("cols", 9)), "rows": int(b.get("rows", 6))}

    def get_enemies(self, number: int) -> List[Dict[str, Any]]:
        r = self.get_round(number) or {}
        return list(r.get("enemies", []))

    def get_player_start(self) -> List[Dict[str, Any]]:
        r1 = self.get_round(1) or {}
        return list(r1.get("player_start", []))

    def get_reward(self, number: int) -> int:
        r = self.get_round(number) or {}
        return int(r.get("reward_gold", 0))

    # Global enemy spawn deprecated in favor of per-enemy row/col hints.
