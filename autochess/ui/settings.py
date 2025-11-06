import pygame

class SettingsScreen:
    def __init__(self, screen, volume=0.5, colors=None):
        self.screen = screen
        self.volume = volume
        self.font = pygame.font.SysFont(None, 56)
        colors = colors or {}
        self.color_text = colors.get('text', (230, 230, 230))
        self.color_highlight = colors.get('highlight', (255, 215, 0))
        self.color_subtle = colors.get('subtle', (130, 130, 130))

    def handle_event(self, event):
        changed = False
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.volume = max(0.0, round(self.volume - 0.1, 2))
                changed = True
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.volume = min(1.0, round(self.volume + 0.1, 2))
                changed = True
            elif event.key == pygame.K_ESCAPE:
                return 'back'
        return 'changed' if changed else None

    def draw(self, bg_color=(10, 10, 10)):
        self.screen.fill(bg_color)
        w, h = self.screen.get_size()

        title_font = pygame.font.SysFont(None, 92)
        title_surf = title_font.render("Settings", True, self.color_highlight)
        title_rect = title_surf.get_rect(center=(w // 2, h // 4))
        self.screen.blit(title_surf, title_rect)

        # Volume label
        vol_label = self.font.render("Music Volume", True, self.color_text)
        vol_label_rect = vol_label.get_rect(center=(w // 2, h // 2 - 40))
        self.screen.blit(vol_label, vol_label_rect)

        # Volume slider (simple bar)
        bar_w, bar_h = 600, 16
        bar_x = (w - bar_w) // 2
        bar_y = h // 2 + 10
        pygame.draw.rect(self.screen, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h), border_radius=8)

        fill_w = int(bar_w * self.volume)
        pygame.draw.rect(self.screen, self.color_highlight, (bar_x, bar_y, fill_w, bar_h), border_radius=8)

        # Value text
        val_surf = self.font.render(f"{int(self.volume * 100)}%", True, self.color_text)
        val_rect = val_surf.get_rect(center=(w // 2, bar_y + 60))
        self.screen.blit(val_surf, val_rect)

        hint_font = pygame.font.SysFont(None, 28)
        hint = hint_font.render("Left/Right to adjust, Esc to go back", True, self.color_subtle)
        hint_rect = hint.get_rect(center=(w // 2, h - 60))
        self.screen.blit(hint, hint_rect)