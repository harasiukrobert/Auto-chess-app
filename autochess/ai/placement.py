"""
Simple heuristic AI for enemy unit placement.
Places units based on their role:
- Frontline tanks (warrior, lancer): closest to middle (highest rows in enemy zone)
- Midline assassins:  behind tanks but still forward
- Backline (archer, monk, witch): top of map (lowest rows in enemy zone)
"""

# Unit role definitions
TANK_UNITS = {'warrior', 'lancer'}
MIDLINE_UNITS = {'assassin'}
BACKLINE_UNITS = {'archer', 'monk', 'witch'}


def get_unit_role(unit_name: str) -> str:
    """Returns 'tank', 'midline', 'backline', or 'unknown'."""
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
    Given a list of unit specs [{'name': .. ., 'lvl': ... }, ...] and a hex_manager,
    compute optimal hex positions for each unit.

    Returns list of specs with 'hex' key added:  [{'name': .. ., 'lvl': ..., 'hex':  HexSprite}, ...]
    """
    # Get all enemy territory hexes
    enemy_hexes = [h for h in hex_manager.hexes if hex_manager.is_enemy_territory(h)]

    if not enemy_hexes:
        return unit_specs  # No hexes available

    # Categorize units by role
    backline_specs = [s for s in unit_specs if get_unit_role(s.get('name', '')) == 'backline']
    midline_specs = [s for s in unit_specs if get_unit_role(s.get('name', '')) == 'midline']
    tank_specs = [s for s in unit_specs if get_unit_role(s. get('name', '')) == 'tank']
    unknown_specs = [s for s in unit_specs if get_unit_role(s.get('name', '')) == 'unknown']

    # Sort hexes by row priority
    # Backline wants lowest row numbers (furthest from player - top of map)
    backline_hexes = sorted(enemy_hexes, key=lambda h: (h.r, h.c))  # top first
    # Midline wants middle rows
    midline_hexes = sorted(enemy_hexes, key=lambda h: (h.r, h.c))  # will filter by row later
    # Tanks want highest row numbers (closest to player - bottom of enemy zone)
    tank_hexes = sorted(enemy_hexes, key=lambda h: (-h.r, h.c))  # bottom first

    result = []
    used_hexes = set()

    # Place backline units first (top rows - furthest from battle)
    for spec in backline_specs:
        for h in backline_hexes:
            if (h.r, h. c) not in used_hexes:
                used_hexes. add((h.r, h. c))
                result.append({**spec, 'hex': h})
                break

    # Place midline units (assassins) - prefer middle rows if available, otherwise behind tanks
    # Get row range for midline positioning
    if enemy_hexes:
        min_row = min(h.r for h in enemy_hexes)
        max_row = max(h.r for h in enemy_hexes)
        mid_row = (min_row + max_row) // 2

        # Prefer hexes around the middle row
        midline_preferred = sorted(
            [h for h in enemy_hexes if (h.r, h.c) not in used_hexes],
            key=lambda h: (abs(h.r - mid_row), h.r, h.c)
        )

        for spec in midline_specs:
            for h in midline_preferred:
                if (h.r, h.c) not in used_hexes:
                    used_hexes.add((h. r, h.c))
                    result.append({**spec, 'hex': h})
                    break

    # Place tank units last (bottom rows - front line)
    for spec in tank_specs:
        for h in tank_hexes:
            if (h.r, h.c) not in used_hexes:
                used_hexes.add((h.r, h.c))
                result.append({**spec, 'hex': h})
                break

    # Place unknown units anywhere available
    all_available = sorted(enemy_hexes, key=lambda h: (h.r, h.c))
    for spec in unknown_specs:
        for h in all_available:
            if (h.r, h.c) not in used_hexes:
                used_hexes.add((h.r, h.c))
                result.append({**spec, 'hex':  h})
                break

    return result