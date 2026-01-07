"""
Enemy AI Manager - Handles gold, shopping, and unit placement decisions.
AI persists units between rounds and accumulates gold like the player.
Includes smart evolution logic.
"""

from autochess. game. units import UNITS_DATA
from autochess.ai.placement import get_unit_role

# Target composition ratios
TARGET_TANK_RATIO = 0.3  # 30% tanks
TARGET_BACKLINE_RATIO = 0.5  # 50% backline (rest is midline)


class EnemyAI:
    """Manages AI decisions for enemy team."""

    def __init__(self, starting_gold: int = 2):
        self.gold = starting_gold + 0  # AI starts with bonus gold (can + more if needed)
        self.roster = []

    def add_gold(self, amount:  int):
        """Add gold to AI's bank (e.g., from round rewards)."""
        self.gold += amount

    def get_gold(self) -> int:
        """Get current AI gold."""
        return self.gold

    def set_gold(self, amount: int):
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
        """Count tank, midline, backline in a roster."""
        counts = {'tank': 0, 'midline': 0, 'backline': 0, 'total': 0}
        for spec in roster:
            role = get_unit_role(spec. get('name', ''))
            if role in ['tank', 'midline', 'backline']:
                counts[role] += 1
            counts['total'] += 1
        return counts

    def decide_next_purchase(self, current_roster: list, gold: int) -> str | None:
        """
        Decide what unit to buy next based on current roster and gold.
        Returns unit name or None if can't/shouldn't buy.
        """
        counts = self. count_by_role(current_roster)
        total = counts['total']

        # Calculate what we need
        if total == 0:
            # First unit - get a tank
            preferred_role = 'tank'
        else:
            tank_ratio = counts['tank'] / total
            backline_ratio = counts['backline'] / total

            if tank_ratio < TARGET_TANK_RATIO:
                preferred_role = 'tank'
            elif backline_ratio < TARGET_BACKLINE_RATIO:
                preferred_role = 'backline'
            else:
                preferred_role = 'midline'

        # Get affordable units
        affordable = []
        for unit_name in self.get_available_units():
            cost = self.get_unit_cost(unit_name)
            if cost <= gold:
                role = get_unit_role(unit_name)
                affordable. append({'name': unit_name, 'cost': cost, 'role': role})

        if not affordable:
            return None

        # Filter by preferred role
        preferred = [u for u in affordable if u['role'] == preferred_role]

        # If no preferred available, take any
        if not preferred:
            preferred = affordable

        # Sort by cost (prefer cheaper for efficiency)
        preferred.sort(key=lambda u: u['cost'])

        # If we have lots of gold, maybe go for a more expensive unit
        if gold >= 8 and len(preferred) > 1:
            import random
            if random.random() > 0.5:
                preferred. sort(key=lambda u: -u['cost'])

        return preferred[0]['name'] if preferred else None

    def should_evolve_units(self) -> list:
        """
        Decide which units should be evolved (merged).
        Returns list of tuples:  [(unit_name, from_level), ...]

        Evolution happens when:
        1. Board space is getting tight (roster > 6 units)
        2. We have duplicates of the same unit at the same level
        3.  Evolving would make the unit significantly stronger
        """
        if len(self.roster) <= 6:
            # Plenty of space, don't merge yet
            return []

        # Count units by name and level
        unit_counts = {}
        for spec in self. roster:
            name = spec.get('name', '')
            lvl = spec.get('lvl', 1)
            key = (name, lvl)
            unit_counts[key] = unit_counts.get(key, 0) + 1

        # Find candidates for evolution (units with 2+ copies at same level)
        evolution_candidates = []
        for (name, lvl), count in unit_counts.items():
            if count >= 2:
                # We can merge 2 units into 1 higher level unit
                evolution_candidates.append((name, lvl))

        return evolution_candidates

    def perform_evolution(self, unit_name: str, from_level: int):
        """
        Evolve (merge) two units of the same name and level into one higher level unit.
        Removes 2 units from roster, adds 1 evolved unit.
        """
        # Find first two matching units
        removed_count = 0
        new_roster = []
        evolved = False

        for spec in self.roster:
            if (not evolved and
                spec.get('name') == unit_name and
                spec.get('lvl', 1) == from_level and
                removed_count < 2):
                # Skip this unit (will be merged)
                removed_count += 1
                if removed_count == 2:
                    # Add evolved unit
                    new_roster. append({'name': unit_name, 'lvl': from_level + 1})
                    evolved = True
            else:
                new_roster. append(spec)

        self.roster = new_roster

    def apply_evolution_logic(self):
        """
        Check if any units should be evolved and perform the evolution.
        Called before shopping each round.
        """
        candidates = self.should_evolve_units()
        for unit_name, from_level in candidates:
            print(f"[AI Evolution] Merging 2x {unit_name} (Lv{from_level}) -> 1x {unit_name} (Lv{from_level + 1})")
            self.perform_evolution(unit_name, from_level)

    def shop_for_round(self, round_num: int) -> list:
        """
        Decide what NEW units to buy this round.
        Adds new purchases to the persistent roster.
        Returns list of new unit specs that were purchased.
        """
        # First, check if we should evolve any existing units
        self.apply_evolution_logic()

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
        print(f"[AI] Round {round_num}:  Had {roster_before} units, Gold {gold_before} -> {self.gold}, Bought {len(new_purchases)} new, Total roster: {len(self.roster)}")

        return new_purchases

    def reset(self, starting_gold: int = 2):
        """Reset AI state for a new game."""
        self. gold = starting_gold
        self.roster = []