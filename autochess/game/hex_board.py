import math
import pygame

HEX_RADIUS = 64
HEX_MARGIN = 5
ANIMATION_SPEED = 0.05
WAVE_SPEED = 10
HEX_COLOR = (128, 128, 128, 100)
HEX_BORDER_COLOR = (64, 64, 64)


class HexSprite(pygame.sprite.Sprite):
    """Pojedynczy heks na planszy"""

    def __init__(self, r, c, x, y, radius, groups, layer):
        super().__init__(groups)
        self.r = r
        self.c = c
        self.radius = radius
        self.z = layer

        self.scale = 0.0
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
        if self.shrinking:
            if self.scale > 0.0:
                self.scale -= ANIMATION_SPEED
                if self.scale < 0.0:
                    self.scale = 0.0
                self.redraw()
        else:
            if self.active and self.scale < 1.0:
                self.scale += ANIMATION_SPEED
                if self.scale > 1.0:
                    self.scale = 1.0
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

        pygame.draw.polygon(self.image, HEX_COLOR, current_points)
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

        if self.selected_unit is None:
            for sprite in self.units:
                if sprite.hitbox.collidepoint(mouse_pos) and press:
                    self.selected_unit = sprite
        else:
            if not press:
                self.selected_unit = None

        if self.selected_unit:
            self.selected_unit.rect = self.selected_unit.image.get_rect(center=mouse_pos)
            self.selected_unit.hitbox = self.selected_unit.rect.copy().inflate(
                -self.selected_unit.rect.width * 0.7, -self.selected_unit.rect.height * 0.7)

    def set_the_center(self):
        """Przyciągaj jednostki do środka heksów"""
        if self.combat_mode:
            return

        for sprite in self.units:
            for pos in self.hexes:
                if sprite.hitbox.colliderect(pos.hitbox):
                    if not self.selected_unit:
                        sprite.rect = sprite.image.get_rect(center=pos.rect.center)
                        sprite.hitbox = sprite.rect.copy().inflate(-sprite.rect.width * 0.7,
                                                                   -sprite.rect.height * 0.7)

    def update_combat(self):
        """Aktualizuj logikę walki dla wszystkich jednostek"""
        if not self.combat_mode or not self.grid_fully_hidden:
            return

        from autochess.game.units import Unit
        all_units = [u for u in self.units if isinstance(u, Unit) and u.alive]

        for unit in all_units:
            unit.combat_update(all_units)

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