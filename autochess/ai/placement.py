"""
Simple heuristic AI for enemy unit placement.
Places units based on their role:
- Frontline (warrior, lancer): closer to the middle (higher rows in enemy zone)
- Backline (archer, monk): top of map (lower rows in enemy zone)
"""

# Unit role definitions
FRONTLINE_UNITS = {'warrior', 'lancer'}
BACKLINE_UNITS = {'archer', 'monk'}


def get_unit_role(unit_name: str) -> str:
    """Returns 'frontline', 'backline', or 'unknown'."""
    name_lower = unit_name.lower()
    if name_lower in FRONTLINE_UNITS:
        return 'frontline'
    elif name_lower in BACKLINE_UNITS:
        return 'backline'
    return 'unknown'


def compute_enemy_placement(unit_specs: list, hex_manager) -> list:
    """
    Given a list of unit specs [{'name': .. ., 'lvl': ... }, ...] and a hex_manager,
    compute optimal hex positions for each unit.

    Returns list of specs with 'hex' key added:  [{'name': .. ., 'lvl': .. ., 'hex':  HexSprite}, ...]
    """
    # Get all enemy territory hexes
    enemy_hexes = [h for h in hex_manager.hexes if hex_manager.is_enemy_territory(h)]

    if not enemy_hexes:
        return unit_specs  # No hexes available

    # Sort units:  backline first (so they get top rows), then frontline
    backline_specs = [s for s in unit_specs if get_unit_role(s.get('name', '')) == 'backline']
    frontline_specs = [s for s in unit_specs if get_unit_role(s.get('name', '')) == 'frontline']
    unknown_specs = [s for s in unit_specs if get_unit_role(s.get('name', '')) == 'unknown']

    # Sort hexes by row
    # Backline wants low row numbers (top), frontline wants high row numbers (bottom of enemy zone)
    backline_hexes = sorted(enemy_hexes, key=lambda h: (h.r, h.c))  # top first
    frontline_hexes = sorted(enemy_hexes, key=lambda h: (-h.r, h.c))  # bottom first

    result = []
    used_hexes = set()

    # Place backline units (top rows)
    for spec in backline_specs:
        for h in backline_hexes:
            if (h.r, h.c) not in used_hexes:
                used_hexes.add((h.r, h.c))
                result.append({**spec, 'hex': h})
                break

    # Place frontline units (bottom rows of enemy zone)
    for spec in frontline_specs:
        for h in frontline_hexes:
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
                result.append({**spec, 'hex': h})
                break

    return result