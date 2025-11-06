import pygame

class Menu:
    def __init__(self, screen, options, font=None, colors=None):
        self.screen = screen
        self.options = options  # list of (label, action_key)
        self.selected = 0
        self.font = font or pygame.font.SysFont(None, 64)
        colors = colors or {}
        self.color_text = colors.get('text', (230, 230, 230))
        self.color_highlight = colors.get('highlight', (255, 215, 0))
        self.color_subtle = colors.get('subtle', (130, 130, 130))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                # return the action key of the selected option
                return self.options[self.selected][1]
        return None

    def draw(self, bg_color=(10, 10, 10)):
        self.screen.fill(bg_color)
        w, h = self.screen.get_size()

        title_font = pygame.font.SysFont(None, 92)
        title_surf = title_font.render("Auto Chess", True, self.color_highlight)
        title_rect = title_surf.get_rect(center=(w // 2, h // 4))
        self.screen.blit(title_surf, title_rect)

        start_y = h // 2
        spacing = 72

        for i, (label, _) in enumerate(self.options):
            is_sel = (i == self.selected)
            color = self.color_highlight if is_sel else self.color_text
            text = f"> {label} <" if is_sel else label
            surf = self.font.render(text, True, color)
            rect = surf.get_rect(center=(w // 2, start_y + i * spacing))
            self.screen.blit(surf, rect)

        hint_font = pygame.font.SysFont(None, 28)
        # Use text names instead of glyphs to avoid missing-glyph squares
        hint = hint_font.render("Use Up/Down and Enter", True, self.color_subtle)
        hint_rect = hint.get_rect(center=(w // 2, h - 60))
        self.screen.blit(hint, hint_rect)