import pygame

class SpeedControl:
    """Simple speed selector UI for combat simulation speed.
    Renders buttons: 0.25x, 0.5x, 1x, 2x, 5x.
    """

    def __init__(self, screen, on_change, colors=None, position=None):
        self.screen = screen
        self.on_change = on_change  # callback(float)
        self.colors = colors or {
            "bg": (30, 30, 35),
            "border": (90, 90, 120),
            "text": (220, 220, 230),
            "hover": (60, 60, 80),
            "active": (120, 180, 255),
        }
        self.font = pygame.font.SysFont(None, 24)
        self.values = [0.25, 0.5, 1.0, 2.0, 5.0]
        self.labels = ["0.25x", "0.5x", "1x", "2x", "5x"]
        # top-right default
        self.position = position or (self.screen.get_width() - 16, 16)
        self._button_rects = []
        self.current_value = 1.0
        self.size = (72, 30)
        self.spacing = 8
        self._layout_buttons()

    def _layout_buttons(self):
        self._button_rects.clear()
        x, y = self.position
        # align from right edge
        right = x
        for _ in self.values:
            right -= (self.size[0] + self.spacing)
        start_x = right + self.spacing
        bx = start_x
        by = y
        for _ in self.values:
            rect = pygame.Rect(bx, by, self.size[0], self.size[1])
            self._button_rects.append(rect)
            bx += self.size[0] + self.spacing

    def set_value(self, v: float):
        self.current_value = float(v)

    def handle_event(self, event):
        if event.type == pygame.VIDEORESIZE:
            self.position = (self.screen.get_width() - 16, 16)
            self._layout_buttons()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            for rect, val in zip(self._button_rects, self.values):
                if rect.collidepoint(pos):
                    self.set_value(val)
                    if callable(self.on_change):
                        self.on_change(val)
                    return "changed"
        return None

    def draw(self):
        mouse_pos = pygame.mouse.get_pos()
        for rect, label, val in zip(self._button_rects, self.labels, self.values):
            is_hover = rect.collidepoint(mouse_pos)
            is_active = (abs(self.current_value - val) < 1e-6)
            bg = self.colors["bg"]
            if is_hover:
                bg = self.colors["hover"]
            pygame.draw.rect(self.screen, bg, rect, border_radius=6)
            border_col = self.colors["border"]
            if is_active:
                border_col = self.colors["active"]
            pygame.draw.rect(self.screen, border_col, rect, 2, border_radius=6)
            # text
            surf = self.font.render(label, True, self.colors["text"])
            ts = surf.get_rect(center=rect.center)
            self.screen.blit(surf, ts)
