import pygame
import os

class Menu:
    def __init__(self, screen, options, font=None, colors=None, logo_path='files/ui/logo.png'):
        self.screen = screen
        self.options = options  # list of (label, action_key)
        self.selected = 0
        self.hovered = None
        self.font = font or pygame.font.SysFont(None, 64)
        colors = colors or {}
        self.color_text = colors.get('text', (230, 230, 230))
        # main blue highlight (used for slider fill, accents)
        self.color_highlight = colors.get('highlight', (80, 125, 170))
        self.color_subtle = colors.get('subtle', (150, 150, 150))
        self.color_hover_text = (20, 40, 70)  # dark-blue text on light-blue hover

        # Button color scheme
        self.btn_base = (40, 55, 80)         # normal button background (dark blue)
        self.btn_border = (90, 120, 160)     # normal border
        # Hover / selected: very light blue background (soft, almost white)
        self.btn_hover_base = (225, 240, 255)  # very light blue
        self.btn_hover_border = (160, 200, 240) # blue border for hover

        # Logo
        self.logo = None
        if os.path.exists(logo_path):
            try:
                raw_logo = pygame.image.load(logo_path).convert_alpha()
                max_w = self.screen.get_width() * 0.55
                scale = min(1.0, max_w / raw_logo.get_width())
                new_size = (int(raw_logo.get_width() * scale),
                            int(raw_logo.get_height() * scale))
                self.logo = pygame.transform.smoothscale(raw_logo, new_size)
            except Exception:
                self.logo = None

        # Layout
        self.base_y = self.screen.get_height() // 2     # Play position
        self.spacing = 160                              # user set to 160
        self.pad_x, self.pad_y = 60, 28
        self.button_rects = []  # populated every draw for hover hit-testing

    def handle_event(self, event):
        # Mouse move: update hovered and sync selected
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self.hovered = None
            for i, rect in enumerate(self.button_rects):
                if rect.collidepoint(mx, my):
                    self.hovered = i
                    break
            # keep keyboard and mouse in sync: if user moves mouse, selection follows
            if self.hovered is not None:
                self.selected = self.hovered

        # Mouse click: return option under mouse
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered is not None:
                # synchronize selection with the clicked item
                self.selected = self.hovered
                return self.options[self.hovered][1]

        # Keyboard: update selected then sync hovered so mouse/keyboard are unified
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.options)
                self.hovered = self.selected
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.options)
                self.hovered = self.selected
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.options[self.selected][1]
        return None

    def draw(self, skip_clear=False):
        if not skip_clear:
            self.screen.fill((15, 15, 20))

        w, h = self.screen.get_size()

        # Logo or fallback title
        if self.logo:
            logo_rect = self.logo.get_rect(center=(w // 2, h // 4))
            self.screen.blit(self.logo, logo_rect)
        else:
            title_font = pygame.font.SysFont(None, 100)
            title_surf = title_font.render("HEXA", True, self.color_highlight)
            title_rect = title_surf.get_rect(center=(w // 2, h // 4))
            self.screen.blit(title_surf, title_rect)

        # Draw buttons
        self.button_rects = []
        for i, (label, _) in enumerate(self.options):
            is_sel = (i == self.selected)
            is_hover = (i == self.hovered)
            text_color = self.color_hover_text if (is_sel or is_hover) else self.color_text

            surf = self.font.render(label, True, text_color)
            y = self.base_y + (i * self.spacing)  # Play at base_y, others below
            rect = surf.get_rect(center=(w // 2, y))

            box_rect = pygame.Rect(rect.left - self.pad_x,
                                   rect.top - self.pad_y,
                                   rect.width + self.pad_x * 2,
                                   rect.height + self.pad_y * 2)

            if is_sel or is_hover:
                base_col = self.btn_hover_base
                border_col = self.btn_hover_border
            else:
                base_col = self.btn_base
                border_col = self.btn_border

            pygame.draw.rect(self.screen, base_col, box_rect, border_radius=18)
            pygame.draw.rect(self.screen, border_col, box_rect, width=3, border_radius=18)

            if is_sel:
                # slight inner highlight for keyboard-selected
                inner = pygame.Rect(box_rect.left + 4, box_rect.top + 4,
                                    box_rect.width - 8, box_rect.height - 8)
                pygame.draw.rect(self.screen, (255, 255, 255, 20), inner, border_radius=14)

            self.screen.blit(surf, rect)
            self.button_rects.append(box_rect)

        # Hint
        hint_font = pygame.font.SysFont(None, 24)
        hint = hint_font.render("Up/Down + Enter • Mouse hover/click • Esc exits", True, self.color_subtle)
        hint_rect = hint.get_rect(center=(w // 2, h - 40))
        self.screen.blit(hint, hint_rect)