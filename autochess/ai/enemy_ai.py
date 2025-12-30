"""
Enemy AI Manager - Handles gold, shopping, and unit placement decisions.
AI persists units between rounds and accumulates gold like the player.
"""

from autochess.game. units import UNITS_DATA
from autochess.ai.placement import get_unit_role

# Target composition ratios
TARGET_FRONTLINE_RATIO = 0.5  # 50% frontline, 50% backline


class EnemyAI:
    """Manages AI decisions for enemy team."""

    def __init__(self, starting_gold: int = 2):
        self.roster = []

    def add_gold(self, amount:  int):
        """Add gold to AI's bank (e.g., from round rewards)."""
        self.gold += amount

    def get_gold(self) -> int:
        """Get current AI gold."""
        return self.gold

    def set_gold(self, amount:  int):
        """Set AI gold to specific amount."""
        self.gold = amount

    def get_unit_cost(self, unit_name: str) -> int:
        """Get cost of a unit from UNITS_DATA."""
        data = UNITS_DATA.get(unit_name. lower(), {})
        return int(data.get('cost', 3))

    def get_available_units(self) -> list:
        """Get list of all purchasable unit types."""
        return list(UNITS_DATA.keys())

    def count_by_role(self, roster: list) -> dict:
        """Count frontline vs backline in a roster."""
        counts = {'frontline': 0, 'backline': 0, 'total': 0}
        for spec in roster:
            role = get_unit_role(spec. get('name', ''))
            if role in counts:
                counts[role] += 1
            counts['total'] += 1
        return counts

    def decide_next_purchase(self, current_roster: list, gold: int) -> str | None:
        """
        Decide what unit to buy next based on current roster and gold.
        Returns unit name or None if can't/shouldn't buy.
        """
        counts = self.count_by_role(current_roster)
        total = counts['total']

        # Calculate what we need
        if total == 0:
            # First unit - get a frontliner
            need_frontline = True
        else:
            current_frontline_ratio = counts['frontline'] / total
            need_frontline = current_frontline_ratio < TARGET_FRONTLINE_RATIO

        # Get affordable units
        affordable = []
        for unit_name in self.get_available_units():
            cost = self.get_unit_cost(unit_name)
            if cost <= gold:
                role = get_unit_role(unit_name)
                affordable.append({'name': unit_name, 'cost':  cost, 'role': role})

        if not affordable:
            return None

        # Filter by what we need
        if need_frontline:
            preferred = [u for u in affordable if u['role'] == 'frontline']
        else:
            preferred = [u for u in affordable if u['role'] == 'backline']

        # If no preferred available, take any
        if not preferred:
            preferred = affordable

        # Sort by cost (prefer cheaper for efficiency)
        preferred.sort(key=lambda u: u['cost'])

        # If we have lots of gold, maybe go for a more expensive unit
        if gold >= 8 and len(preferred) > 1:
            import random
            if random.random() > 0.5:
                preferred.sort(key=lambda u: -u['cost'])

        return preferred[0]['name'] if preferred else None

    def sync_roster_from_units(self, units_group, team: str = 'red'):
        """Sync internal roster from actual unit sprites on the board."""
        self.roster = []
        for u in units_group:
            if getattr(u, 'team', None) == team and getattr(u, 'alive', True):
                self.roster.append({
                    'name': u.name,
                    'lvl': int(getattr(u, 'level', 1))
                })

    def shop_for_round(self, round_num: int) -> list:
        """
        Decide what NEW units to buy this round.
        Adds new purchases to the persistent roster.
        Returns list of new unit specs that were purchased.
        """
        roster_before = len(self.roster)
        gold_before = self.gold

        new_purchases = []

        # Safety limit to prevent infinite loop
        max_attempts = 50
        attempts = 0

        # Buy units until we run out of gold or can't afford anything
        while attempts < max_attempts and self.gold > 0:
            attempts += 1

            # Decide what to buy based on current roster + new purchases
            combined_roster = self.roster + new_purchases
            next_unit = self.decide_next_purchase(combined_roster, self.gold)

            if next_unit is None:
                break

            cost = self.get_unit_cost(next_unit)
            if cost > self.gold:
                break

            # Make the purchase
            self.gold -= cost
            new_purchases.append({'name': next_unit, 'lvl': 1})

        # Add new purchases to persistent roster
        self.roster.extend(new_purchases)

        # DEBUG - remove later
        print(
            f"[AI] Round {round_num}:  Had {roster_before} units, Gold {gold_before} -> {self.gold}, Bought {len(new_purchases)} new, Total roster: {len(self.roster)}")

        return new_purchases

    def reset(self, starting_gold: int = 2):
        """Reset AI state for a new game."""
        self.gold = starting_gold + 2  # AI starts with bonus gold
        self.roster = []