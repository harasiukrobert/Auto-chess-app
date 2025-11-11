import pygame
import os

class Menu:
    def __init__(self, screen, options, font=None, colors=None, logo_path='files/ui/hexa2.png'):
        """
        Menu that uses artwork button images if present.
        Expects button images at files/ui/buttons/<key>.png where key is 'play', 'options', 'quit'
        """
        self.screen = screen
        self.options = options  # list of (label, action_key)
        self.selected = 0
        self.hovered = None
        self.font = font or pygame.font.SysFont(None, 64)
        colors = colors or {}
        self.color_text = colors.get('text', (230, 230, 230))
        self.color_highlight = colors.get('highlight', (80, 125, 170))
        self.color_subtle = colors.get('subtle', (150, 150, 150))
        self.color_hover_text = (20, 40, 70)

        # Button image map: tries to load files/ui/buttons/<key>.png
        self.button_images = {}
        for label, _ in self.options:
            key = label.strip().lower()
            path = f'files/ui/buttons/{key}.png'
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    self.button_images[key] = img
                except Exception:
                    # ignore load errors; fallback to drawn buttons
                    pass

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
        self.spacing = 160                              # vertical spacing between buttons
        # Reduced vertical padding so the button boxes don't become taller than the art
        self.pad_x, self.pad_y = 60, 12
        self.button_rects = []  # populated every draw for hover hit-testing

    def handle_event(self, event):
        # Mouse motion: update hovered and sync selected
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self.hovered = None
            for i, rect in enumerate(self.button_rects):
                if rect.collidepoint(mx, my):
                    self.hovered = i
                    break
            if self.hovered is not None:
                self.selected = self.hovered

        # Mouse click: return option under mouse
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered is not None:
                self.selected = self.hovered
                return self.options[self.hovered][1]

        # Keyboard: update selected and keep hovered in sync
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

            # Determine button rect (we'll size around the text baseline to keep layout consistent)
            surf_text = self.font.render(label, True, self.color_text)
            y = self.base_y + (i * self.spacing)
            rect = surf_text.get_rect(center=(w // 2, y))
            if i == 0:
                # Only calculate once
                all_widths = [self.font.render(lbl, True, self.color_text).get_width() for lbl, _ in self.options]
                max_width = max(all_widths) + self.pad_x * 2
                max_height = self.font.get_height() + self.pad_y * 2

            y = self.base_y + (i * self.spacing)
            box_rect = pygame.Rect(0, 0, max_width, max_height)
            box_rect.center = (w // 2, y)

            # If we have an image for this button, blit scaled image and optionally tint on hover.
            # New behavior: scale down images to fit box, but do not upscale smaller source art.
            key = label.strip().lower()
            img = self.button_images.get(key)
            if img:
                try:
                    iw, ih = img.get_width(), img.get_height()
                    bw, bh = box_rect.width, box_rect.height
                    # compute scale to fit inside box, but don't upscale beyond original size
                    scale = min(bw / iw, bh / ih, 1.0)
                    target_w, target_h = int(iw * scale), int(ih * scale)
                    img_s = pygame.transform.smoothscale(img, (target_w, target_h))
                    img_rect = img_s.get_rect(center=box_rect.center)
                    self.screen.blit(img_s, img_rect)

                    # draw subtle hover overlay if interactive feedback desired
                    if is_sel or is_hover:
                        overlay = pygame.Surface((box_rect.width, box_rect.height), pygame.SRCALPHA)
                        pygame.draw.rect(
                            overlay,
                            (255, 230, 100, 80),  # yellowish tint
                            overlay.get_rect(),
                            border_radius=18
                        )
                        self.screen.blit(overlay, box_rect.topleft)
                except Exception:
                    # fallback to safe blit if scaling fails
                    self.screen.blit(img, box_rect.topleft)
            else:
                # --- Fallback: draw stylized rounded rectangle button (if no art) ---
                base_col = (40, 55, 80)
                border_col = (90, 120, 160)
                text_color = self.color_text

                # Hover or selected state
                if is_sel or is_hover:
                    base_col = (60, 70, 90)
                    border_col = (255, 230, 100)  # yellow border
                    text_color = (20, 40, 70)

                # Draw base rounded button
                pygame.draw.rect(self.screen, base_col, box_rect, border_radius=18)
                pygame.draw.rect(self.screen, border_col, box_rect, width=3, border_radius=18)

                # Draw rounded yellow hover overlay
                if is_sel or is_hover:
                    overlay = pygame.Surface((box_rect.width, box_rect.height), pygame.SRCALPHA)
                    inner_rect = pygame.Rect(2, 2, box_rect.width - 4, box_rect.height - 4)  # inset by 2px
                    pygame.draw.rect(
                        overlay,
                        (255, 230, 100, 80),
                        inner_rect,
                        border_radius=16  # slightly reduced to match inset shape
                    )
                    self.screen.blit(overlay, box_rect.topleft)

                # Draw text
                surf = self.font.render(label, True, text_color)
                surf_rect = surf.get_rect(center=box_rect.center)
                self.screen.blit(surf, surf_rect)

            self.button_rects.append(box_rect)

        # Hint text at the bottom
        hint_font = pygame.font.SysFont(None, 24)
        hint = hint_font.render("Up/Down + Enter • Mouse hover/click • Esc exits", True, self.color_subtle)
        hint_rect = hint.get_rect(center=(w // 2, h - 40))
        self.screen.blit(hint, hint_rect)
