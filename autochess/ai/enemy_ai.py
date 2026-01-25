"""
Menedżer AI przeciwnika - obsługuje złoto, zakupy i decyzje o rozmieszczeniu jednostek.
AI zachowuje jednostki między rundami i gromadzi złoto podobnie jak gracz.
Zawiera inteligentną logikę ewolucji.
"""

from autochess. game. units import UNITS_DATA
from autochess.ai.placement import get_unit_role

TARGET_TANK_RATIO = 0.3
TARGET_BACKLINE_RATIO = 0.5


class EnemyAI:
    """Zarządza decyzjami AI dla drużyny przeciwnika."""

    def __init__(self, starting_gold: int = 2):
        self.gold = starting_gold + 0
        self.roster = []

    def add_gold(self, amount:  int):
        """Dodaje złoto do banku AI (np. z nagród za rundę)."""
        self.gold += amount

    def get_gold(self) -> int:
        """Zwraca aktualne złoto AI."""
        return self.gold

    def set_gold(self, amount: int):
        """Ustawia złoto AI na określoną wartość."""
        self.gold = amount

    def get_unit_cost(self, unit_name: str) -> int:
        """Pobiera koszt jednostki z UNITS_DATA."""
        data = UNITS_DATA.get(unit_name. lower(), {})
        return int(data.get('cost', 3))

    def get_available_units(self) -> list:
        """Zwraca listę wszystkich dostępnych typów jednostek do zakupu."""
        return list(UNITS_DATA.keys())

    def count_by_role(self, roster: list) -> dict:
        """Zlicza jednostki typu tank, midline, backline w rosterze."""
        counts = {'tank': 0, 'midline': 0, 'backline': 0, 'total': 0}
        for spec in roster:
            role = get_unit_role(spec. get('name', ''))
            if role in ['tank', 'midline', 'backline']:
                counts[role] += 1
            counts['total'] += 1
        return counts

    def decide_next_purchase(self, current_roster: list, gold: int) -> str | None:
        """
        Decyduje, którą jednostkę kupić na podstawie obecnego rostera i złota.
        Zwraca nazwę jednostki lub None, jeśli nie można/nie należy kupować.
        """
        counts = self. count_by_role(current_roster)
        total = counts['total']

        if total == 0:
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

        affordable = []
        for unit_name in self.get_available_units():
            cost = self.get_unit_cost(unit_name)
            if cost <= gold:
                role = get_unit_role(unit_name)
                affordable. append({'name': unit_name, 'cost': cost, 'role': role})

        if not affordable:
            return None

        preferred = [u for u in affordable if u['role'] == preferred_role]

        if not preferred:
            preferred = affordable

        preferred.sort(key=lambda u: u['cost'])

        if gold >= 8 and len(preferred) > 1:
            import random
            if random.random() > 0.5:
                preferred. sort(key=lambda u: -u['cost'])

        return preferred[0]['name'] if preferred else None

    def should_evolve_units(self) -> list:
        """
        Decyduje, które jednostki powinny zostać zewoluowane (połączone).
        Zwraca listę krotek: [(nazwa_jednostki, z_poziomu), ...]

        Ewolucja następuje gdy:
        1. Miejsce na planszy się kończy (roster > 6 jednostek)
        2. Mamy duplikaty tej samej jednostki na tym samym poziomie
        3. Ewolucja znacząco wzmocni jednostkę
        """
        if len(self.roster) <= 6:
            return []

        unit_counts = {}
        for spec in self. roster:
            name = spec.get('name', '')
            lvl = spec.get('lvl', 1)
            key = (name, lvl)
            unit_counts[key] = unit_counts.get(key, 0) + 1

        evolution_candidates = []
        for (name, lvl), count in unit_counts.items():
            if count >= 2:
                evolution_candidates.append((name, lvl))

        return evolution_candidates

    def perform_evolution(self, unit_name: str, from_level: int):
        """
        Ewoluuje (łączy) dwie jednostki o tej samej nazwie i poziomie w jedną jednostkę wyższego poziomu.
        Usuwa 2 jednostki z rostera, dodaje 1 zewoluowaną jednostkę.
        """
        removed_count = 0
        new_roster = []
        evolved = False

        for spec in self.roster:
            if (not evolved and
                spec.get('name') == unit_name and
                spec.get('lvl', 1) == from_level and
                removed_count < 2):
                removed_count += 1
                if removed_count == 2:
                    new_roster. append({'name': unit_name, 'lvl': from_level + 1})
                    evolved = True
            else:
                new_roster. append(spec)

        self.roster = new_roster

    def apply_evolution_logic(self):
        """
        Sprawdza, czy jakieś jednostki powinny zostać zewoluowane i wykonuje ewolucję.
        Wywoływane przed zakupami w każdej rundzie.
        """
        candidates = self.should_evolve_units()
        for unit_name, from_level in candidates:
            print(f"[AI Evolution] Merging 2x {unit_name} (Lv{from_level}) -> 1x {unit_name} (Lv{from_level + 1})")
            self.perform_evolution(unit_name, from_level)

    def shop_for_round(self, round_num: int) -> list:
        """
        Decyduje, które NOWE jednostki kupić w tej rundzie.
        Dodaje nowe zakupy do stałego rostera.
        Zwraca listę nowo zakupionych specyfikacji jednostek.
        """
        self.apply_evolution_logic()

        roster_before = len(self.roster)
        gold_before = self.gold

        new_purchases = []

        max_attempts = 50
        attempts = 0

        while attempts < max_attempts and self.gold > 0:
            attempts += 1

            combined_roster = self.roster + new_purchases
            next_unit = self.decide_next_purchase(combined_roster, self.gold)

            if next_unit is None:
                break

            cost = self.get_unit_cost(next_unit)
            if cost > self.gold:
                break

            self.gold -= cost
            new_purchases.append({'name': next_unit, 'lvl': 1})

        self.roster.extend(new_purchases)

        print(f"[AI] Round {round_num}:  Had {roster_before} units, Gold {gold_before} -> {self.gold}, Bought {len(new_purchases)} new, Total roster: {len(self.roster)}")

        return new_purchases

    def reset(self, starting_gold: int = 2):
        """Resetuje stan AI dla nowej gry."""
        self. gold = starting_gold
        self.roster = []