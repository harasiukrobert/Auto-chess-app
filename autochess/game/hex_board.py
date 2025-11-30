import math

import pygame

HEX_RADIUS = 64
HEX_MARGIN = 5
ANIMATION_SPEED = 0.05
WAVE_SPEED = 10
HEX_COLOR = (128, 128, 128, 100)
HEX_BORDER_COLOR = (64, 64, 64)
# Drag colors used during unit dragging (no alpha overlay)
DRAG_FREE_COLOR = (128, 128, 128, 100)
DRAG_OCCUPIED_COLOR = (64, 64, 64, 150)


class HexSprite(pygame.sprite.Sprite):
    """Pojedynczy heks na planszy"""

    def __init__(self, r, c, x, y, radius, groups, layer):
        super().__init__(groups)
        self.r = r
        self.c = c
        self.radius = radius
        self.z = layer

        self.scale = 0.0
        self.dynamic_color = None  # temporary override fill color during drag
        self.active = False
        self.dist_from_center = 0
        self.shrinking = False

        size = int(radius * 2.2)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        self.hitbox = self.rect.copy().inflate(-self.rect.width * 0.5, -self.rect.height * 0.5)

        self.center_offset = (size / 2, size / 2)
        self.base_points = self._compute_vertices()

    def _compute_vertices(self):
        """Oblicz wierzchołki heksa"""
        points = []
        for i in range(6):
            angle_deg = 60 * i - 30
            angle_rad = math.radians(angle_deg)
            px = self.radius * math.cos(angle_rad)
            py = self.radius * math.sin(angle_rad)
            points.append((px, py))
        return points

    def activate(self):
        """Aktywuj heks"""
        self.active = True

    def start_shrink(self):
        """Rozpocznij animację kurczenia"""
        self.shrinking = True

    def is_fully_shrunk(self):
        """Czy heks całkowicie zniknął"""
        return self.scale <= 0.0

    def update(self):
        """Aktualizuj animację heksa"""
        # original scale animation
        scale_changed = False
        if self.shrinking:
            if self.scale > 0.0:
                self.scale -= ANIMATION_SPEED
                if self.scale < 0.0:
                    self.scale = 0.0
                scale_changed = True
        else:
            if self.active and self.scale < 1.0:
                self.scale += ANIMATION_SPEED
                if self.scale > 1.0:
                    self.scale = 1.0
                scale_changed = True
        # Force redraw if scale changed OR an overlay is currently applied
        if scale_changed or self.dynamic_color is not None:
            self.redraw()

    def redraw(self):
        """Przerysuj heks"""
        self.image.fill((0, 0, 0, 0))

        if self.scale <= 0.01:
            return

        cx, cy = self.center_offset
        current_points = []
        for (ox, oy) in self.base_points:
            nx = cx + (ox * self.scale)
            ny = cy + (oy * self.scale)
            current_points.append((nx, ny))

        base_color = self.dynamic_color if self.dynamic_color else HEX_COLOR
        pygame.draw.polygon(self.image, base_color, current_points)
        pygame.draw.polygon(self.image, HEX_BORDER_COLOR, current_points, 3)


class HexGridManager:
    """Menedżer siatki heksagonalnej"""

    def __init__(self, cols, rows, center_pos, group, units, layer):
        self.cols = cols
        self.rows = rows
        self.center_pos = center_pos
        self.group = group
        self.layer = layer
        self.hexes = []
        self.units = units
        self.selected_unit = None

        self.wave_radius = 0
        self.max_dist = 0
        self.generated = False

        self.combat_mode = False
        self.shrink_wave_radius = 0
        self.shrinking_started = False
        self.grid_fully_hidden = False
        # occupancy map: (r,c) -> Unit or None
        self.occupancy = {}
        # previous position for dragged unit to revert if drop invalid
        self._drag_prev_center = None
        # previous hex key to revert precisely back to original hex
        self._drag_prev_hex_key = None

    def generate(self):
        """Generuj siatkę heksów"""
        step_x = math.sqrt(3) * HEX_RADIUS + HEX_MARGIN
        step_y = HEX_RADIUS * 1.5 + HEX_MARGIN

        total_w = self.cols * step_x + (step_x / 2 if self.rows % 2 != 0 else 0) - HEX_MARGIN
        total_h = self.rows * step_y + HEX_RADIUS

        start_x = self.center_pos[0] - (total_w / 2)
        start_y = self.center_pos[1] - (total_h / 2)

        for r in range(self.rows):
            for c in range(self.cols):
                h_width = math.sqrt(3) * HEX_RADIUS
                h_height = 2 * HEX_RADIUS

                x_base = c * (h_width + HEX_MARGIN)
                x_offset = (h_width / 2 + HEX_MARGIN / 2) if r % 2 == 1 else 0

                pos_x = start_x + x_base + x_offset
                pos_y = start_y + (r * (h_height * 0.75 + HEX_MARGIN)) + HEX_RADIUS

                hex_sprite = HexSprite(r, c, pos_x, pos_y, HEX_RADIUS, [self.group], self.layer)

                dist = math.hypot(pos_x - self.center_pos[0], pos_y - self.center_pos[1])
                hex_sprite.dist_from_center = dist
                if dist > self.max_dist:
                    self.max_dist = dist

                self.hexes.append(hex_sprite)
                self.occupancy[(r, c)] = None

        self.generated = True

    def toggle_combat(self):
        """Przełącz tryb walki"""
        self.combat_mode = not self.combat_mode

        if self.combat_mode:
            self.shrinking_started = True
            self.shrink_wave_radius = 0
            self.grid_fully_hidden = False
        else:
            self.shrinking_started = False
            self.grid_fully_hidden = False
            for h in self.hexes:
                h.shrinking = False
                h.scale = 1.0
                h.redraw()

    def is_combat_active(self):
        """Return True when combat is ongoing and grid fully hidden."""
        return self.combat_mode and self.grid_fully_hidden

    # --- Occupancy helpers ---
    def initialize_occupancy(self):
        """Assign current units to nearest hex centers to seed occupancy."""
        for key in list(self.occupancy.keys()):
            self.occupancy[key] = None
        for u in self.units:
            hc = self.find_nearest_hex_center(u.rect.center)
            if hc:
                h = hc['hex']
                key = (h.r, h.c)
                if self.occupancy.get(key) is None:
                    self.occupancy[key] = u
                    u.rect.center = h.rect.center
                    if hasattr(u, 'sync_pos_from_rect'):
                        u.sync_pos_from_rect()

    def find_nearest_hex_center(self, pos):
        """Return dict with hex and distance to its center for given screen pos."""
        best = None
        bx, by = pos
        for h in self.hexes:
            d = math.hypot(h.rect.centerx - bx, h.rect.centery - by)
            if best is None or d < best['dist']:
                best = {'hex': h, 'dist': d}
        return best

    def is_hex_free(self, hex_sprite):
        return self.occupancy.get((hex_sprite.r, hex_sprite.c)) is None

    def assign_unit_to_hex(self, unit, hex_sprite):
        key = (hex_sprite.r, hex_sprite.c)
        # clear any previous assignment of this unit
        for k, v in self.occupancy.items():
            if v is unit:
                self.occupancy[k] = None
        # set new if free
        if self.occupancy.get(key) is None:
            self.occupancy[key] = unit
            unit.rect.center = hex_sprite.rect.center
            if hasattr(unit, 'sync_pos_from_rect'):
                unit.sync_pos_from_rect()
            unit.hitbox = unit.rect.copy().inflate(
                -unit.rect.width * 0.7, -unit.rect.height * 0.7)
            return True
        return False

    def update_shrink_animation(self):
        """Aktualizuj animację zanikania siatki"""
        if not self.shrinking_started:
            return

        if self.shrink_wave_radius < self.max_dist + HEX_RADIUS * 2:
            self.shrink_wave_radius += WAVE_SPEED

        for h in self.hexes:
            if not h.shrinking and h.dist_from_center <= self.shrink_wave_radius:
                h.start_shrink()

        all_shrunk = all(h.is_fully_shrunk() for h in self.hexes)
        if all_shrunk and not self.grid_fully_hidden:
            self.grid_fully_hidden = True
            for unit in self.units:
                unit.pos.x = unit.rect.centerx
                unit.pos.y = unit.rect.centery

    def collision(self):
        """Obsługa przeciągania jednostek"""
        if self.combat_mode:
            return

        mouse_pos = pygame.mouse.get_pos()
        press = pygame.mouse.get_pressed()[0]

        if self.selected_unit is None and press:
            # start drag
            for sprite in self.units:
                if not hasattr(sprite, 'hitbox'):
                    continue
                if sprite.hitbox.collidepoint(mouse_pos):
                    self.selected_unit = sprite
                    self._drag_prev_center = sprite.rect.center
                    # Remember which hex the unit currently occupies
                    self._drag_prev_hex_key = None
                    for k, v in self.occupancy.items():
                        if v is sprite:
                            self._drag_prev_hex_key = k
                            break
                    # apply color overrides: occupied vs free
                    for h in self.hexes:
                        if self.is_hex_free(h) or self.occupancy.get((h.r, h.c)) is sprite:
                            if DRAG_FREE_COLOR is not None:
                                h.dynamic_color = DRAG_FREE_COLOR
                        else:
                            if DRAG_OCCUPIED_COLOR is not None:
                                h.dynamic_color = DRAG_OCCUPIED_COLOR
                        h.redraw()
                    break

        if self.selected_unit and press:
            # dragging following mouse
            self.selected_unit.rect = self.selected_unit.image.get_rect(center=mouse_pos)
            self.selected_unit.hitbox = self.selected_unit.rect.copy().inflate(
                -self.selected_unit.rect.width * 0.7, -self.selected_unit.rect.height * 0.7)

        if self.selected_unit and not press:
            # release: attempt snap to nearest free hex; else revert
            placed = False
            nearest = self.find_nearest_hex_center(self.selected_unit.rect.center)
            if nearest:
                h = nearest['hex']
                if self.selected_unit.hitbox.colliderect(h.hitbox):
                    if (self.is_hex_free(h) or self.occupancy.get((h.r, h.c)) is self.selected_unit):
                        placed = self.assign_unit_to_hex(self.selected_unit, h)
            if not placed and self._drag_prev_center:
                # revert to original hex center if known
                revert_center = self._drag_prev_center
                if self._drag_prev_hex_key is not None:
                    r, c = self._drag_prev_hex_key
                    for hx in self.hexes:
                        if hx.r == r and hx.c == c:
                            revert_center = hx.rect.center
                            break
                self.selected_unit.rect.center = revert_center
                if hasattr(self.selected_unit, 'sync_pos_from_rect'):
                    self.selected_unit.sync_pos_from_rect()
                self.selected_unit.hitbox = self.selected_unit.rect.copy().inflate(
                    -self.selected_unit.rect.width * 0.7, -self.selected_unit.rect.height * 0.7)
            # clear drag state and color overrides
            for h in self.hexes:
                if h.dynamic_color is not None:
                    h.dynamic_color = None
                    h.redraw()
            self.selected_unit = None
            self._drag_prev_center = None
            self._drag_prev_hex_key = None

    def set_the_center(self):
        """Przyciągaj jednostki do środka heksów"""
        if self.combat_mode:
            return

        for sprite in self.units:
            if not hasattr(sprite, 'hitbox'):
                continue
            # Only snap when not dragging
            if self.selected_unit is None:
                nearest = self.find_nearest_hex_center(sprite.rect.center)
                if nearest:
                    h = nearest['hex']
                    self.assign_unit_to_hex(sprite, h)

    def update_combat(self):
        """Aktualizuj logikę walki dla wszystkich jednostek"""
        if not self.combat_mode or not self.grid_fully_hidden:
            return

        from autochess.game.units import Unit
        all_units = [u for u in self.units if isinstance(u, Unit) and u.alive]

        for unit in all_units:
            unit.combat_update(all_units)

    # placement used by spawners to ensure one unit per hex
    def place_unit_on_free_hex(self, unit, prefer_top=True):
        """Place unit on first free hex scanning rows.
        prefer_top: True for enemy (red), False for player (blue)
        """
        seq = sorted(self.hexes, key=lambda h: (h.r, h.c))
        if prefer_top:
            seq = sorted(seq, key=lambda h: h.r)  # small r is top
        else:
            seq = sorted(seq, key=lambda h: -h.r)
        for h in seq:
            if self.is_hex_free(h):
                self.assign_unit_to_hex(unit, h)
                return True
        return False

    def update(self):
        """Główna aktualizacja menedżera"""
        if not self.generated:
            return

        if self.wave_radius < self.max_dist + HEX_RADIUS * 2:
            self.wave_radius += WAVE_SPEED

        for h in self.hexes:
            if not h.active and h.dist_from_center <= self.wave_radius:
                h.activate()

        self.update_shrink_animation()
        self.collision()
        self.set_the_center()
        self.update_combat()