import pygame


class EndScreen:
    def __init__(self, screen, colors=None):
        self.screen = screen
        colors = colors or {}
        self.color_text = colors.get('text', (230, 230, 230))
        self.color_highlight = colors.get('highlight', (80, 125, 170))
        self.color_subtle = colors.get('subtle', (130, 130, 130))
        self.font_title = pygame.font.SysFont(None, 72, bold=True)
        self.font_btn = pygame.font.SysFont(None, 36, bold=True)
        self._compute_layout()

    def _compute_layout(self):
        w, h = self.screen.get_size()
        btn_w, btn_h = 280, 64
        spacing = 24
        cx = w // 2
        cy = h // 2
        self.title_pos = (cx, cy - 140)
        self.btn_menu = pygame.Rect(cx - btn_w // 2, cy - btn_h // 2, btn_w, btn_h)
        self.btn_exit = pygame.Rect(cx - btn_w // 2, cy - btn_h // 2 + btn_h + spacing, btn_w, btn_h)

    def handle_event(self, event):
        if event.type == pygame.VIDEORESIZE:
            self._compute_layout()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.btn_menu.collidepoint(mx, my):
                return 'menu'
            if self.btn_exit.collidepoint(mx, my):
                return 'exit'
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return 'menu'
            if event.key in (pygame.K_ESCAPE, pygame.K_q):
                return 'exit'
        return None

    def draw(self):
        w, h = self.screen.get_size()
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((10, 10, 16, 200))
        self.screen.blit(overlay, (0, 0))
        # Title
        title_surf = self.font_title.render('Victory!', True, self.color_text)
        self.screen.blit(title_surf, title_surf.get_rect(center=self.title_pos))
        # Buttons
        for rect, label in ((self.btn_menu, 'Return to Menu'), (self.btn_exit, 'Exit Game')):
            pygame.draw.rect(self.screen, self.color_highlight, rect, border_radius=10)
            inner = rect.inflate(-6, -6)
            pygame.draw.rect(self.screen, (20, 20, 28), inner, border_radius=10)
            txt = self.font_btn.render(label, True, self.color_text)
            self.screen.blit(txt, txt.get_rect(center=rect.center))
