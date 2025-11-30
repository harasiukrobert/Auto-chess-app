import pygame


class Shop:
    """
    Very simple shop overlay for the planning phase.
    - Shows a bottom bar with buttons for unit types.
    - On click, spawns a blue unit at the mouse position via on_spawn callback.
    - Dragging/placement is then handled by HexGridManager logic.
    """

    def __init__(self, screen, items, colors=None, on_spawn=None):
        self.screen = screen
        self.items = items  # list of unit names e.g., ['warrior','archer','lancer','monk']
        self.on_spawn = on_spawn  # callback: (name:str, pos:tuple) -> Unit or None
        colors = colors or {}
        self.color_bg = colors.get('bg', (20, 20, 28))
        self.color_border = colors.get('border', (90, 120, 160))
        self.color_text = colors.get('text', (230, 230, 230))
        self.color_highlight = colors.get('highlight', (255, 230, 100))
        self.font = pygame.font.SysFont(None, 28)

        self.padding = 10
        self.height = 110
        self.button_size = (140, 60)
        self.button_gap = 18
        self.rect = self._compute_rect()
        self.button_rects = []

    def _compute_rect(self):
        w, h = self.screen.get_size()
        r = pygame.Rect(0, h - self.height, w, self.height)
        return r

    def handle_event(self, event):
        if event.type == pygame.VIDEORESIZE:
            self.rect = self._compute_rect()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.rect.collidepoint(mx, my):
                for idx, brect in enumerate(self.button_rects):
                    if brect.collidepoint(mx, my):
                        name = self.items[idx]
                        if callable(self.on_spawn):
                            unit = self.on_spawn(name, (mx, my))
                            return unit  # Game can mark it as selected for dragging
        return None

    def draw(self):
        # background bar
        pygame.draw.rect(self.screen, self.color_bg, self.rect)
        pygame.draw.rect(self.screen, self.color_border, self.rect, width=2)

        # layout buttons centered horizontally
        w = self.rect.width
        x = self.rect.left + self.padding
        y = self.rect.top + (self.rect.height - self.button_size[1]) // 2
        total_buttons_w = len(self.items) * self.button_size[0] + (len(self.items) - 1) * self.button_gap
        start_x = self.rect.left + (w - total_buttons_w) // 2

        self.button_rects = []
        for idx, name in enumerate(self.items):
            bx = start_x + idx * (self.button_size[0] + self.button_gap)
            by = y
            brect = pygame.Rect(bx, by, *self.button_size)
            pygame.draw.rect(self.screen, (40, 55, 80), brect, border_radius=10)
            pygame.draw.rect(self.screen, self.color_border, brect, width=2, border_radius=10)
            label = name.capitalize()
            surf = self.font.render(label, True, self.color_text)
            srect = surf.get_rect(center=brect.center)
            self.screen.blit(surf, srect)
            self.button_rects.append(brect)
