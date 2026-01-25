"""
Prosta heurystyczna AI do rozmieszczania jednostek przeciwnika.
Rozmieszcza jednostki na podstawie ich roli:
- Tanki na pierwszej linii (warrior, lancer): najbliżej środka (najwyższe rzędy w strefie wroga)
- Zabójcy na środkowej linii: za tankami, ale wciąż z przodu
- Tylna linia (archer, monk, witch): góra mapy (najniższe rzędy w strefie wroga)
"""

TANK_UNITS = {'warrior', 'lancer'}
MIDLINE_UNITS = {'assassin'}
BACKLINE_UNITS = {'archer', 'monk', 'witch'}


def get_unit_role(unit_name: str) -> str:
    """Zwraca 'tank', 'midline', 'backline' lub 'unknown'."""
    name_lower = unit_name.lower()
    if name_lower in TANK_UNITS:
        return 'tank'
    elif name_lower in MIDLINE_UNITS:
        return 'midline'
    elif name_lower in BACKLINE_UNITS:
        return 'backline'
    return 'unknown'


def compute_enemy_placement(unit_specs: list, hex_manager) -> list:
    """
    Na podstawie listy specyfikacji jednostek [{'name': ..., 'lvl': ...}, ...] i hex_managera
    oblicza optymalne pozycje heksów dla każdej jednostki.

    Zwraca listę specyfikacji z dodanym kluczem 'hex': [{'name': ..., 'lvl': ..., 'hex': HexSprite}, ...]
    """
    enemy_hexes = [h for h in hex_manager.hexes if hex_manager.is_enemy_territory(h)]

    if not enemy_hexes:
        return unit_specs

    backline_specs = [s for s in unit_specs if get_unit_role(s.get('name', '')) == 'backline']
    midline_specs = [s for s in unit_specs if get_unit_role(s.get('name', '')) == 'midline']
    tank_specs = [s for s in unit_specs if get_unit_role(s. get('name', '')) == 'tank']
    unknown_specs = [s for s in unit_specs if get_unit_role(s.get('name', '')) == 'unknown']

    try:
        cols = int(getattr(hex_manager, 'cols', 0) or 0)
    except Exception:
        cols = 0
    center_c = (cols - 1) / 2.0 if cols > 0 else 0.0

    backline_hexes = sorted(enemy_hexes, key=lambda h: (h.r, abs(h.c - center_c), h.c))
    midline_hexes = sorted(enemy_hexes, key=lambda h: (h.r, abs(h.c - center_c), h.c))
    tank_hexes = sorted(enemy_hexes, key=lambda h: (-h.r, abs(h.c - center_c), h.c))

    result = []
    used_hexes = set()

    for spec in backline_specs:
        for h in backline_hexes:
            if (h.r, h. c) not in used_hexes:
                used_hexes. add((h.r, h. c))
                result.append({**spec, 'hex': h})
                break

    if enemy_hexes:
        min_row = min(h.r for h in enemy_hexes)
        max_row = max(h.r for h in enemy_hexes)
        mid_row = (min_row + max_row) // 2

        midline_preferred = sorted(
            [h for h in enemy_hexes if (h.r, h.c) not in used_hexes],
            key=lambda h: (abs(h.r - mid_row), abs(h.c - center_c), h.r, h.c)
        )

        for spec in midline_specs:
            for h in midline_preferred:
                if (h.r, h.c) not in used_hexes:
                    used_hexes.add((h. r, h.c))
                    result.append({**spec, 'hex': h})
                    break

    for spec in tank_specs:
        for h in tank_hexes:
            if (h.r, h.c) not in used_hexes:
                used_hexes.add((h.r, h.c))
                result.append({**spec, 'hex': h})
                break

    all_available = sorted(enemy_hexes, key=lambda h: (h.r, abs(h.c - center_c), h.c))
    for spec in unknown_specs:
        for h in all_available:
            if (h.r, h.c) not in used_hexes:
                used_hexes.add((h.r, h.c))
                result.append({**spec, 'hex':  h})
                break

    return result