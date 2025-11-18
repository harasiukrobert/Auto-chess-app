import math

import pygame

# hex settings
HEX_RADIUS = 64
HEX_MARGIN = 5
ANIMATION_SPEED = 0.05
WAVE_SPEED = 10
HEX_COLOR = (128, 128, 128, 100)
HEX_BORDER_COLOR = (64, 64, 64)

class HexSprite(pygame.sprite.Sprite):
    def __init__(self, r, c, x, y, radius, groups, layer):
        super().__init__(groups)
        self.r = r
        self.c = c
        self.radius = radius
        self.z = layer

        self.scale = 0.0
        self.active = False
        self.dist_from_center = 0
        
        size = int(radius * 2.2)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        
        self.center_offset = (size / 2, size / 2)
        self.base_points = self._compute_vertices()

    def _compute_vertices(self):
        points = []
        for i in range(6):
            angle_deg = 60 * i - 30
            angle_rad = math.radians(angle_deg)
            px = self.radius * math.cos(angle_rad)
            py = self.radius * math.sin(angle_rad)
            points.append((px, py))
        return points

    def activate(self):
        self.active = True

    def update(self):
        # place animation
        if self.active and self.scale < 1.0:
            self.scale += ANIMATION_SPEED
            if self.scale > 1.0: self.scale = 1.0
            self.redraw()
            
    def redraw(self):
        self.image.fill((0,0,0,0))
        
        if self.scale <= 0.01: return

        cx, cy = self.center_offset
        current_points = []
        for (ox, oy) in self.base_points:
            nx = cx + (ox * self.scale)
            ny = cy + (oy * self.scale)
            current_points.append((nx, ny))

        pygame.draw.polygon(self.image, HEX_COLOR, current_points)
        pygame.draw.polygon(self.image, HEX_BORDER_COLOR, current_points, 3)

class HexGridManager:
    def __init__(self, cols, rows, center_pos, group, layer):
        self.cols = cols
        self.rows = rows
        self.center_pos = center_pos
        self.group = group
        self.layer = layer
        self.hexes = []
        
        self.wave_radius = 0
        self.max_dist = 0
        self.generated = False

    def generate(self):
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
                if dist > self.max_dist: self.max_dist = dist
                
                self.hexes.append(hex_sprite)
        
        self.generated = True

    def update(self):
        if not self.generated: return
        
        if self.wave_radius < self.max_dist + HEX_RADIUS * 2:
            self.wave_radius += WAVE_SPEED
            
        for h in self.hexes:
            if not h.active and h.dist_from_center <= self.wave_radius:
                h.activate()