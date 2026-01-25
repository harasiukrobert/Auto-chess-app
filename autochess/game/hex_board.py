import math

import pygame

HEX_SCALE = 0.9
BASE_HEX_RADIUS = 64
BASE_HEX_MARGIN = 5
HEX_RADIUS = int(round(BASE_HEX_RADIUS * HEX_SCALE))
HEX_MARGIN = max(0, int(round(BASE_HEX_MARGIN * HEX_SCALE)))
ANIMATION_SPEED = 0.05
WAVE_SPEED = 10
HEX_COLOR = (128, 128, 128, 100)
HEX_BORDER_COLOR = (64, 64, 64)
HEX_BORDER_WIDTH = 3
DRAG_FREE_COLOR = (128, 128, 128, 100)
DRAG_OCCUPIED_COLOR = (64, 64, 64, 150)
MERGE_TARGET_COLOR = (60, 180, 75, 160)
ENEMY_TERRITORY_COLOR = (200, 60, 60, 120)


class HexSprite(pygame.sprite.Sprite):
    """Pojedynczy heks na planszy"""

    def __init__(self, r, c, x, y, radius, groups, layer):
        super().__init__(groups)
        self.r = r
        self.c = c
        self.radius = radius
        self.z = layer

        self.scale = 0.0
        self.dynamic_color = None
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
        pygame.draw.polygon(self.image, HEX_BORDER_COLOR, current_points, HEX_BORDER_WIDTH)

        pygame.draw.aalines(self.image, HEX_BORDER_COLOR, True, current_points)


class HexGridManager:
    """Menedżer siatki heksagonalnej"""

    def __init__(self, cols, rows, center_pos, group, units, layer, allow_enemy_drag: bool = False):
        self.cols = cols
        self.rows = rows
        self.center_pos = center_pos
        self.group = group
        self.layer = layer
        self.hexes = []
        self.units = units
        self.selected_unit = None
        self.allow_enemy_drag = allow_enemy_drag

        self.wave_radius = 0
        self.max_dist = 0
        self.generated = False

        self.combat_mode = False
        self.shrink_wave_radius = 0
        self.shrinking_started = False
        self.grid_fully_hidden = False
        self.occupancy = {}
        self._drag_prev_center = None
        self._drag_prev_hex_key = None
        self.sim_speed = 1.0
        self._sim_fraction_accum = 0.0

    def set_sim_speed(self, value: float):
        """Ustawia mnożnik prędkości symulacji dla aktualizacji walki."""
        try:
            v = float(value)
        except Exception:
            v = 1.0
        # clamp to sensible range
        if v < 0.1:
            v = 0.1
        if v > 10.0:
            v = 10.0
        self.sim_speed = v

    def is_player_territory(self, hex_sprite) -> bool:
        """
        Zwraca True jeśli heks jest w dolnej połowie (terytorium gracza).
        Gracz może umieszczać jednostki tylko w swoim terytorium (dolna połowa mapy).
        """
        return hex_sprite.r >= (self.rows + 1) // 2

    def is_enemy_territory(self, hex_sprite) -> bool:
        """
        Zwraca True jeśli heks jest w górnej połowie (terytorium wroga).
        Gracz nie może tutaj umieszczać jednostek.
        """
        return hex_sprite.r < (self.rows + 1) // 2

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

                pos_x = int(round(start_x + x_base + x_offset))
                pos_y = int(round(start_y + (r * (h_height * 0.75 + HEX_MARGIN)) + HEX_RADIUS))

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
        """Zwraca True gdy walka trwa i siatka jest całkowicie ukryta."""
        return self.combat_mode and self.grid_fully_hidden

    def initialize_occupancy(self):
        """Przypisuje bieżące jednostki do najbliższych środków heksów, aby zainicjować mapę zajętości."""
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
        """Zwraca słownik z heksem i dystansem do jego środka dla podanej pozycji na ekranie."""
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
        for k, v in self.occupancy.items():
            if v is unit:
                self.occupancy[k] = None
        if self.occupancy.get(key) is None:
            self.occupancy[key] = unit
            unit.rect.center = hex_sprite.rect.center
            if hasattr(unit, 'sync_pos_from_rect'):
                unit.sync_pos_from_rect()
            unit.hitbox = unit.rect.copy().inflate(
                -unit.rect.width * 0.7, -unit.rect.height * 0.7)
            return True
        return False

    def assign_unit_to_hex_animated(self, unit, hex_sprite, frames: int = 10):
        """Przypisuje jednostkę do heksu w mapie zajętości i animuje ruch do środka heksu."""
        key = (hex_sprite.r, hex_sprite.c)
        for k, v in self.occupancy.items():
            if v is unit:
                self.occupancy[k] = None
        if self.occupancy.get(key) is None:
            self.occupancy[key] = unit
            if hasattr(unit, 'start_snap_move'):
                unit.start_snap_move(hex_sprite.rect.center, frames=frames)
            else:
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

        mouse_pos = pygame. mouse.get_pos()
        press = pygame.mouse.get_pressed()[0]

        if self.selected_unit is None and press:
            for sprite in self.units:
                if not hasattr(sprite, 'hitbox'):
                    continue
                if getattr(sprite, 'team', None) == 'red' and not self. allow_enemy_drag:
                    continue
                if sprite.hitbox. collidepoint(mouse_pos):
                    self.selected_unit = sprite
                    try:
                        if hasattr(self.selected_unit, '_snap_move_active'):
                            self.selected_unit._snap_move_active = False
                    except Exception:
                        pass
                    self._drag_prev_center = sprite.rect.center
                    self._drag_prev_hex_key = None
                    for k, v in self. occupancy.items():
                        if v is sprite:
                            self._drag_prev_hex_key = k
                            break
                    for h in self.hexes:
                        if self.is_enemy_territory(h):
                            h. dynamic_color = ENEMY_TERRITORY_COLOR
                        else:
                            occ = self.occupancy.get((h.r, h. c))
                            if occ is None or occ is sprite:
                                if DRAG_FREE_COLOR is not None:
                                    h.dynamic_color = DRAG_FREE_COLOR
                            else:
                                if self._can_merge(self.selected_unit, occ):
                                    h.dynamic_color = MERGE_TARGET_COLOR
                                else:
                                    h.dynamic_color = None
                        h.redraw()
                    break

        if self.selected_unit and press:
            self.selected_unit.rect = self.selected_unit.image.get_rect(center=mouse_pos)
            self.selected_unit.hitbox = self.selected_unit.rect.copy().inflate(
                -self.selected_unit.rect.width * 0.7, -self.selected_unit.rect.height * 0.7)

        if self.selected_unit and not press:
            placed = False
            nearest = self.find_nearest_hex_center(self.selected_unit.rect.center)
            if nearest:
                h = nearest['hex']
                if self.is_player_territory(h) and self.selected_unit.hitbox.colliderect(h.hitbox):
                    occ = self.occupancy.get((h.r, h.c))
                    if (self.is_hex_free(h) or occ is self.selected_unit):
                        placed = self.assign_unit_to_hex_animated(self.selected_unit, h, frames=10)
                    else:
                        if self._can_merge(self.selected_unit, occ):
                            self._perform_merge(self.selected_unit, occ, h)
                            placed = True
                        else:
                            if self._can_swap(self.selected_unit, occ, h):
                                self._perform_swap(self.selected_unit, occ, h)
                                placed = True
            if not placed and self._drag_prev_center:
                revert_center = self._drag_prev_center
                if self._drag_prev_hex_key is not None:
                    r, c = self._drag_prev_hex_key
                    for hx in self.hexes:
                        if hx.r == r and hx.c == c:
                            revert_center = hx.rect.center
                            break
                if hasattr(self.selected_unit, 'start_snap_move'):
                    self.selected_unit.start_snap_move(revert_center, frames=10)
                else:
                    self.selected_unit.rect.center = revert_center
                    if hasattr(self.selected_unit, 'sync_pos_from_rect'):
                        self.selected_unit.sync_pos_from_rect()
                    self.selected_unit.hitbox = self.selected_unit.rect.copy().inflate(
                        -self.selected_unit.rect.width * 0.7, -self.selected_unit.rect.height * 0.7)
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
            if self.selected_unit is None:
                if hasattr(sprite, 'is_snap_moving') and sprite.is_snap_moving():
                    continue
                assigned_key = None
                for k, v in self.occupancy.items():
                    if v is sprite:
                        assigned_key = k
                        break
                if assigned_key is not None:
                    ar, ac = assigned_key
                    assigned_hex = None
                    for hx in self.hexes:
                        if hx.r == ar and hx.c == ac:
                            assigned_hex = hx
                            break
                    if assigned_hex is not None and sprite.rect.center != assigned_hex.rect.center:
                        if hasattr(sprite, 'start_snap_move'):
                            sprite.start_snap_move(assigned_hex.rect.center, frames=6)
                        else:
                            sprite.rect.center = assigned_hex.rect.center
                            if hasattr(sprite, 'sync_pos_from_rect'):
                                sprite.sync_pos_from_rect()
                            sprite.hitbox = sprite.rect.copy().inflate(
                                -sprite.rect.width * 0.7, -sprite.rect.height * 0.7)
                else:
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

        steps = int(self.sim_speed)
        self._sim_fraction_accum += (self.sim_speed - steps)
        if self._sim_fraction_accum >= 1.0:
            steps += 1
            self._sim_fraction_accum -= 1.0
        if steps < 1:
            steps = 1

        for _ in range(steps):
            for unit in all_units:
                unit.combat_update(all_units)

    def place_unit_on_free_hex(self, unit, prefer_top=True):
        """
        Umieszcza jednostkę na pierwszym wolnym heksie, skanując rzędy.
        prefer_top: True dla wroga (czerwony), False dla gracza (niebieski)
        """
        seq = sorted(self.hexes, key=lambda h: (h.r, h.c))
        if prefer_top:
            seq = sorted(seq, key=lambda h: h.r)
        else:
            seq = sorted(seq, key=lambda h: -h.r)
        for h in seq:
            if self.is_hex_free(h):
                self.assign_unit_to_hex(unit, h)
                return True
        return False

    def place_unit_on_free_hex_in_territory(self, unit, team:  str):
        """
        Umieszcza jednostkę na pierwszym wolnym heksie w odpowiednim terytorium.
        Niebieskie jednostki idą do terytorium gracza (dolna połowa).
        Czerwone jednostki idą do terytorium wroga (górna połowa).
        """
        if team == 'blue':
            valid_hexes = [h for h in self.hexes if self.is_player_territory(h)]
            valid_hexes = sorted(valid_hexes, key=lambda h: (-h.r, h.c))
        else:
            valid_hexes = [h for h in self.hexes if self.is_enemy_territory(h)]
            valid_hexes = sorted(valid_hexes, key=lambda h:  (h.r, h.c))

        for h in valid_hexes:
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

    def _can_merge(self, a, b) -> bool:
        """Zwraca True jeśli jednostki a i b mogą się połączyć (ta sama drużyna, nazwa i poziom)."""
        if a is None or b is None:
            return False
        if a is b:
            return False
        if getattr(a, 'team', None) != getattr(b, 'team', None):
            return False
        if getattr(a, 'name', None) != getattr(b, 'name', None):
            return False
        try:
            la = int(getattr(a, 'level', 1))
            lb = int(getattr(b, 'level', 1))
        except Exception:
            return False
        return la == lb

    def _perform_merge(self, dragged, target, target_hex):
        """
        Łączy przeciąganą jednostkę z jednostką docelową na target_hex.
        Jednostka docelowa ewoluuje; przeciągana jest usuwana. Cel pozostaje na swoim heksie.
        """
        if hasattr(target, 'evolve'):
            target.evolve()
        if self._drag_prev_hex_key is not None and self.occupancy.get(self._drag_prev_hex_key) is dragged:
            self.occupancy[self._drag_prev_hex_key] = None
        try:
            dragged.kill()
        except Exception:
            pass
        key = (target_hex.r, target_hex.c)
        self.occupancy[key] = target
        target.rect.center = target_hex.rect.center
        if hasattr(target, 'sync_pos_from_rect'):
            target.sync_pos_from_rect()
        target.hitbox = target.rect.copy().inflate(-target.rect.width * 0.7, -target.rect.height * 0.7)

    def _can_swap(self, a, b, hex_sprite) -> bool:
        """
        Zwraca True jeśli upuszczenie jednostki `a` na `b` powinno zamienić ich pozycje.
        Zasady:
        - Różny typ/poziom jednostki (tj. połączenie niemożliwe)
        - Docelowy heks musi być w terytorium gracza
        - Obie jednostki należą do tej samej drużyny (zazwyczaj 'blue')
        - Przeciągana jednostka musi mieć znany poprzedni heks do zamiany
        """
        if a is None or b is None:
            return False
        if a is b:
            return False
        if not self.is_player_territory(hex_sprite):
            return False
        if getattr(a, 'team', None) != getattr(b, 'team', None):
            return False
        if self._can_merge(a, b):
            return False
        if self._drag_prev_hex_key is None:
            return False
        return True

    def _perform_swap(self, dragged, other, target_hex):
        """
        Zamienia pozycje między `dragged` (aktualnie przemieszczaną) a `other` na `target_hex`.
        Używa `_drag_prev_hex_key` jako źródłowego heksu dla `dragged`.
        """
        prev_key = self._drag_prev_hex_key
        if prev_key is None:
            return
        target_key = (target_hex.r, target_hex.c)

        prev_hex_center = None
        for hx in self.hexes:
            if hx.r == prev_key[0] and hx.c == prev_key[1]:
                prev_hex_center = hx.rect.center
                break
        if prev_hex_center is None:
            prev_hex_center = self._drag_prev_center

        for k, v in list(self.occupancy.items()):
            if v is dragged or v is other:
                self.occupancy[k] = None

        self.occupancy[target_key] = dragged
        if hasattr(dragged, 'start_snap_move'):
            dragged.start_snap_move(target_hex.rect.center, frames=10)
        else:
            dragged.rect.center = target_hex.rect.center
            if hasattr(dragged, 'sync_pos_from_rect'):
                dragged.sync_pos_from_rect()
            dragged.hitbox = dragged.rect.copy().inflate(-dragged.rect.width * 0.7, -dragged.rect.height * 0.7)

        if prev_key is not None:
            self.occupancy[prev_key] = other
        if prev_hex_center is not None:
            if hasattr(other, 'start_snap_move'):
                other.start_snap_move(prev_hex_center, frames=10)
            else:
                other.rect.center = prev_hex_center
                if hasattr(other, 'sync_pos_from_rect'):
                    other.sync_pos_from_rect()
                other.hitbox = other.rect.copy().inflate(-other.rect.width * 0.7, -other.rect.height * 0.7)