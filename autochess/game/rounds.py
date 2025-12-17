from typing import Any, Dict, List, Optional

# Embedded rounds configuration (formerly config/rounds.json)
DEFAULT_CONFIG: Dict[str, Any] = {
    "starting_gold": 2,
    "rounds": [
        {
            "board": {"cols": 3, "rows": 3},
            "player_start": [
                {"name": "warrior", "r": 2, "c": 1}
            ],
            "enemies": [
                {"name": "archer", "r": 0, "c": 1}
            ],
            "reward_gold": 5
        },
        {
            "board": {"cols": 3, "rows": 3},
            "player_start": [
                {"name": "warrior", "r": 2, "c": 1}
            ],
            "enemies": [
                {"name": "archer", "r": 0, "c": 1, "lvl": 2}
            ],
            "reward_gold": 5
        },
        {
            "board": {"cols": 3, "rows": 3},
            "enemies": [
                {"name": "warrior", "r": 0, "c": 0},
                {"name": "warrior", "r": 0, "c": 2}
            ],
            "reward_gold": 6
        },
        {
            "board": {"cols": 5, "rows": 5},
            "enemies": [
                {"name": "warrior", "r": 0, "c": 1},
                {"name": "warrior", "r": 0, "c": 3},
                {"name": "archer",  "r": 1, "c": 2}
            ],
            "reward_gold": 7
        },
        {
            "board": {"cols": 5, "rows": 5},
            "enemies": [
                {"name": "warrior", "r": 0, "c": 1},
                {"name": "lancer",  "r": 0, "c": 2},
                {"name": "warrior", "r": 0, "c": 3},
                {"name": "archer",  "r": 1, "c": 2}
            ],
            "reward_gold": 8
        },
        {
            "board": {"cols": 7, "rows": 5},
            "enemies": [
                {"name": "warrior", "r": 0, "c": 2},
                {"name": "lancer",  "r": 0, "c": 3},
                {"name": "warrior", "r": 0, "c": 4},
                {"name": "archer",  "r": 1, "c": 1},
                {"name": "archer",  "r": 1, "c": 5}
            ],
            "reward_gold": 9
        },
        {
            "board": {"cols": 7, "rows": 5},
            "enemies": [
                {"name": "warrior", "r": 0, "c": 2},
                {"name": "warrior", "r": 0, "c": 4},
                {"name": "monk",    "r": 1, "c": 3},
                {"name": "archer",  "r": 1, "c": 1},
                {"name": "archer",  "r": 1, "c": 5}
            ],
            "reward_gold": 10
        },
        {
            "board": {"cols": 9, "rows": 6},
            "enemies": [
                {"name": "warrior", "r": 0, "c": 2},
                {"name": "lancer",  "r": 0, "c": 3},
                {"name": "warrior", "r": 0, "c": 4},
                {"name": "lancer",  "r": 0, "c": 5},
                {"name": "warrior", "r": 0, "c": 6},
                {"name": "archer",  "r": 1, "c": 2},
                {"name": "archer",  "r": 1, "c": 6}
            ],
            "reward_gold": 11
        },
        {
            "board": {"cols": 9, "rows": 6},
            "enemies": [
                {"name": "warrior", "r": 0, "c": 1},
                {"name": "warrior", "r": 0, "c": 3},
                {"name": "warrior", "r": 0, "c": 5},
                {"name": "warrior", "r": 0, "c": 7},
                {"name": "monk",    "r": 1, "c": 3},
                {"name": "monk",    "r": 1, "c": 5},
                {"name": "archer",  "r": 2, "c": 2},
                {"name": "archer",  "r": 2, "c": 6}
            ],
            "reward_gold": 12
        },
        {
            "board": {"cols": 9, "rows": 6},
            "enemies": [
                {"name": "lancer",  "r": 0, "c": 1},
                {"name": "warrior", "r": 0, "c": 3},
                {"name": "warrior", "r": 0, "c": 5},
                {"name": "lancer",  "r": 0, "c": 7},
                {"name": "monk",    "r": 1, "c": 4},
                {"name": "archer",  "r": 1, "c": 2},
                {"name": "archer",  "r": 1, "c": 6}
            ],
            "reward_gold": 13
        },
        {
            "board": {"cols": 9, "rows": 6},
            "enemies": [
                {"name": "warrior", "r": 0, "c": 1},
                {"name": "lancer",  "r": 0, "c": 2},
                {"name": "warrior", "r": 0, "c": 3},
                {"name": "lancer",  "r": 0, "c": 4},
                {"name": "warrior", "r": 0, "c": 5},
                {"name": "lancer",  "r": 0, "c": 6},
                {"name": "monk",    "r": 1, "c": 3},
                {"name": "monk",    "r": 1, "c": 5},
                {"name": "archer",  "r": 2, "c": 2},
                {"name": "archer",  "r": 2, "c": 4},
                {"name": "archer",  "r": 2, "c": 6}
            ],
            "reward_gold": 15
        }
    ]
}


class RoundManager:
    """Loads and provides round configurations.
    """

    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._rounds_by_number: Dict[int, Dict[str, Any]] = {}
        self._load()

    def _load(self):
        # Always use embedded configuration
        cfg = DEFAULT_CONFIG
        self._config = cfg
        rounds: List[Dict[str, Any]] = self._config.get("rounds", [])
        self._rounds_by_number = {i + 1: r for i, r in enumerate(rounds)}

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
