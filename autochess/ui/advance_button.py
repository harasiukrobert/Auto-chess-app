import pygame


class PlanningAdvanceButton:
    """
    Prosty przycisk w prawym dolnym rogu wyświetlany podczas planowania, aby rozpocząć walkę.
    Tylko rysowanie; wywołujący kontroluje kiedy pokazać i obsługuje wynik kliknięcia.
    """

    def __init__(self, screen, label="FIGHT!", colors=None, size=None, margin=16, radius=6):
        self.screen = screen
        self.label = label
        self.margin = margin
        self.radius = radius  # lower radius = less rounded
        self.size = size or (220, 56)  # bigger than initial 170x48

        colors = colors or {}
        # Default red theme
        self.color_bg = colors.get("bg", (180, 42, 42))
        self.color_hover = colors.get("hover", (200, 60, 60))
        self.color_border = colors.get("border", (255, 255, 255))
        self.color_text = colors.get("text", (240, 240, 240))

        self.font = pygame.font.SysFont(None, 28, bold=True)

    def rect(self):
        w, h = self.screen.get_size()
        bw, bh = self.size
        return pygame.Rect(w - bw - self.margin, h - bh - self.margin, bw, bh)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect().collidepoint(event.pos):
                return "clicked"
        return None

    def draw(self):
        r = self.rect()
        hovered = r.collidepoint(pygame.mouse.get_pos())
        bg = self.color_hover if hovered else self.color_bg

        pygame.draw.rect(self.screen, bg, r, border_radius=self.radius)
        pygame.draw.rect(self.screen, self.color_border, r, width=2, border_radius=self.radius)

        label_surf = self.font.render(self.label, True, self.color_text)
        self.screen.blit(label_surf, label_surf.get_rect(center=r.center))
