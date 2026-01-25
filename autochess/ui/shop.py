import os
import random

import pygame

from autochess.game.units import UNITS_DATA
from autochess.utils.resource import resource_path


class Shop:
    """
    Nakładka sklepu dla fazy planowania.
    """

    def __init__(self, screen, items, colors=None, on_spawn=None, on_get_gold=None, on_deduct_gold=None, on_can_spawn=None):
        self.screen = screen
        self.pool_items = list(items)
        self.offer_count = 4
        self.offers = []

        self.locked = False

        self.CARD_SIZE_MULTIPLIER = 1.29

        self.card_offsets = [
            (77, 0),
            (57, 0),
            (39, 0),
            (20, 0)
        ]

        self.reroll_offsets = (25, 0, 54, 0)

        self.lock_offsets = (0, 0, 0, 0)

        self.lock_size_multiplier = 0.72

        self.gold_offset = (0, 50)

        self.on_spawn = on_spawn
        self.on_get_gold = on_get_gold
        self.on_deduct_gold = on_deduct_gold
        self.on_can_spawn = on_can_spawn

        self.show_hitboxes = False
        self.debug_btn_rect = pygame.Rect(10, 10, 50, 30)

        colors = colors or {}
        self.color_text = colors.get('text', (230, 230, 230))
        self.font = pygame.font.SysFont(None, 28)

        self.font_cost = pygame.font.SysFont(None, 24, bold=True)

        self.font_gold = pygame.font.SysFont(None, 64, bold=True)
        self.font_debug = pygame.font.SysFont(None, 20)

        self.height = 180
        self.rect = self._compute_rect()
        self.button_rects = []

        self.reroll_cost = 2
        self.reroll_rect = None
        self.lock_rect = None
        self.bar_rect = None

        # Shake feedback state (used when purchase blocked due to no space)
        self._shake_until = 0
        self._shake_mag = 0
        self._shake_speed_ms = 40

        self.units_data = self._load_units_data()

        # Asset paths
        # Prefer the unified runtime asset root used across the project.
        self.assets_root = resource_path(os.path.join('files', 'ui'))
        if not os.path.exists(self.assets_root):
            alt = resource_path(os.path.join('Files', 'ui'))
            if os.path.exists(alt):
                self.assets_root = alt
            else:
                base_path = os.getcwd()
                if not os.path.exists(os.path.join(base_path, 'Files')):
                    parent = os.path.dirname(base_path)
                    if os.path.exists(os.path.join(parent, 'Files')):
                        base_path = parent
                self.assets_root = os.path.join(base_path, 'Files', 'ui')
        bar_path = os.path.join(self.assets_root, 'shop_bar.png')
        coin_path = os.path.join(self.assets_root, 'coin.png')

        self.shop_bar = self._safe_load_image(bar_path, convert_alpha=True)
        self.coin_img = self._safe_load_image(coin_path, convert_alpha=True)
        if self.coin_img:
            self.coin_img = pygame.transform.smoothscale(self.coin_img, (44, 44))

        self.card_images = {}
        self.card_cache = {}
        for name in self.pool_items:
            filename = f'{name}_card.png'
            card_path = os.path.join(self.assets_root, 'cards', filename)
            self.card_images[name] = self._safe_load_image(card_path, convert_alpha=True)

        self._roll_offers(initial=True)

    def _safe_load_image(self, path, convert_alpha=False):
        try:
            load_path = path
            if not os.path.isabs(load_path):
                load_path = resource_path(load_path)
            img = pygame.image.load(load_path)
            return img.convert_alpha() if convert_alpha else img.convert()
        except Exception as e:
            return None

    def _load_units_data(self):
        return UNITS_DATA

    def _compute_rect(self):
        w, h = self.screen.get_size()
        return pygame.Rect(0, h - self.height, w, self.height)

    def _draw_bar(self):
        if not self.shop_bar:
            return

        sw, sh = self.shop_bar.get_size()

        target_width_pct = 0.55
        target_width = self.rect.width * target_width_pct
        scale = target_width / sw

        new_size = (int(sw * scale), int(sh * scale))
        bar_surface = pygame.transform.smoothscale(self.shop_bar, new_size)

        bw, bh = bar_surface.get_size()
        x = self.rect.centerx - bw // 2
        y = self.rect.bottom - bh - 5

        sx, sy = self._get_shake_offset()
        x += sx
        y += sy

        self.bar_rect = pygame.Rect(x, y, bw, bh)

        shadow = pygame.Surface((bw, bh), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 90))
        self.screen.blit(shadow, (x, y + 4))

        self.screen.blit(bar_surface, (x, y))

    def _get_cached_portrait(self, name, target_size):
        key = (name, target_size)
        surf = self.card_cache.get(key)
        if surf is not None:
            return surf

        portrait = self.card_images.get(name)
        if not portrait:
            return None

        surf = pygame.transform.smoothscale(portrait, target_size)
        self.card_cache[key] = surf
        return surf

    def handle_event(self, event):
        if event.type == pygame.VIDEORESIZE:
            self.rect = self._compute_rect()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            if self.debug_btn_rect.collidepoint(mx, my):
                self.show_hitboxes = not self.show_hitboxes
                return None

            if hasattr(self, 'bar_rect') and self.bar_rect.collidepoint(mx, my):
                if self.lock_rect and self.lock_rect.collidepoint(mx, my):
                    self.locked = not bool(self.locked)
                    return None

                if self.reroll_rect and self.reroll_rect.collidepoint(mx, my):
                    current_gold = self.on_get_gold() if callable(self.on_get_gold) else 0
                    if current_gold >= self.reroll_cost:
                        if callable(self.on_deduct_gold) and self.on_deduct_gold(self.reroll_cost):
                            self._roll_offers(initial=False)
                    return None

                for idx, brect in enumerate(self.button_rects):
                    if brect.collidepoint(mx, my) and idx < len(self.offers):
                        name = self.offers[idx]
                        current_gold = self.on_get_gold() if callable(self.on_get_gold) else 0
                        cost = self._get_unit_cost(name)
                        if callable(getattr(self, 'on_can_spawn', None)):
                            try:
                                if not self.on_can_spawn(name):
                                    self._trigger_shake()
                                    return None
                            except Exception:
                                self._trigger_shake()
                                return None
                        if current_gold >= cost:
                            if callable(self.on_deduct_gold) and self.on_deduct_gold(cost):
                                if callable(self.on_spawn):
                                    return self.on_spawn(name, (mx, my))
        return None

    def draw(self):
        self._draw_bar()

        current_gold = self.on_get_gold() if callable(self.on_get_gold) else 0
        gold_surf = self.font_gold.render(str(current_gold), True, (255, 215, 0))

        if hasattr(self, 'bar_rect'):
            gold_x = self.bar_rect.right + 20
            gold_y = self.bar_rect.centery - gold_surf.get_height() // 2
        else:
            gold_x = self.rect.right - 150
            gold_y = self.rect.top + 10

        gold_x += self.gold_offset[0]
        gold_y += self.gold_offset[1]

        if self.coin_img:
            self.screen.blit(self.coin_img, (gold_x, gold_y))
            self.screen.blit(gold_surf, (gold_x + 50, gold_y + 2))
        else:
            self.screen.blit(gold_surf, (gold_x, gold_y))

        btn_color = (50, 200, 50) if self.show_hitboxes else (200, 50, 50)
        pygame.draw.rect(self.screen, btn_color, self.debug_btn_rect)
        debug_txt = self.font_debug.render("DBG", True, (255, 255, 255))
        self.screen.blit(debug_txt, debug_txt.get_rect(center=self.debug_btn_rect.center))

        if not hasattr(self, 'bar_rect') or not self.offers:
            self.button_rects = []
            return

        bw = self.bar_rect.width
        bh = self.bar_rect.height

        section_count = 6
        section_w = bw / section_count

        base_card_w = section_w * 0.65
        base_card_h = bh * 0.68

        card_w = base_card_w * self.CARD_SIZE_MULTIPLIER
        card_h = base_card_h * self.CARD_SIZE_MULTIPLIER

        card_y = self.bar_rect.centery - (card_h / 2)

        self.button_rects = []
        mouse_pos = pygame.mouse.get_pos()

        start_section_index = 1

        for idx, name in enumerate(self.offers):
            section_x = self.bar_rect.left + (start_section_index + idx) * section_w

            bx = section_x + (section_w - card_w) / 2
            by = card_y

            if idx < len(self.card_offsets):
                off_x, off_y = self.card_offsets[idx]
                bx += off_x
                by += off_y

            brect = pygame.Rect(bx, by, card_w, card_h)

            portrait_scaled = self._get_cached_portrait(name, (int(brect.width), int(brect.height)))

            if portrait_scaled:
                self.screen.blit(portrait_scaled, brect)

                if brect.collidepoint(mouse_pos):
                    highlight = pygame.Surface((brect.width, brect.height), pygame.SRCALPHA)
                    highlight.fill((255, 255, 255, 40))
                    self.screen.blit(highlight, brect)
            else:
                pygame.draw.rect(self.screen, (50, 50, 50), brect)
                initials = name[:2].upper()
                txt = self.font.render(initials, True, (255, 255, 255))
                self.screen.blit(txt, txt.get_rect(center=brect.center))

            cost = self._get_unit_cost(name)
            cost_text = str(cost)
            cost_surf = self.font_cost.render(cost_text, True, (255, 215, 0))
            cost_shadow = self.font_cost.render(cost_text, True, (0, 0, 0))

            pad = max(3, int(min(brect.width, brect.height) * 0.03))
            bottom_strip_h = max(14, int(brect.height * 0.18))
            coin_d = max(10, int(bottom_strip_h * 0.55))
            coin_x = int(brect.right - pad - coin_d)
            coin_y = int(brect.bottom - pad - coin_d)

            cx = int(coin_x - 2 - cost_surf.get_width())
            cy = int(coin_y + (coin_d - cost_surf.get_height()) / 2)
            cy = max(int(brect.bottom - bottom_strip_h + 2), min(cy, int(brect.bottom - cost_surf.get_height() - 2)))
            self.screen.blit(cost_shadow, (cx + 1, cy + 1))
            self.screen.blit(cost_surf, (cx, cy))

            if self.show_hitboxes:
                debug_surf = pygame.Surface((brect.width, brect.height), pygame.SRCALPHA)
                debug_surf.fill((0, 255, 0, 100))
                self.screen.blit(debug_surf, brect)
                pygame.draw.rect(self.screen, (0, 255, 0), brect, 2)

            self.button_rects.append(brect)

        reroll_w = section_w
        reroll_h = bh * 0.8
        rx = self.bar_rect.left
        ry = self.bar_rect.centery - (reroll_h / 2)

        rx += self.reroll_offsets[0]
        ry += self.reroll_offsets[1]
        reroll_w += self.reroll_offsets[2]
        reroll_h += self.reroll_offsets[3]

        self.reroll_rect = pygame.Rect(rx, ry, reroll_w, reroll_h)

        lock_section_left = self.bar_rect.left + (section_w * (section_count - 1))
        lock_section_cx = lock_section_left + (section_w / 2)
        lock_section_cy = self.bar_rect.centery

        lock_size = min(section_w, bh) * float(self.lock_size_multiplier)
        lock_w = lock_size
        lock_h = lock_size
        lx = lock_section_cx - (lock_w / 2)
        ly = lock_section_cy - (lock_h / 2)

        lx += self.lock_offsets[0]
        ly += self.lock_offsets[1]
        lock_w += self.lock_offsets[2]
        lock_h += self.lock_offsets[3]

        self.lock_rect = pygame.Rect(lx, ly, lock_w, lock_h)

        if self.locked and self.lock_rect:
            overlay = pygame.Surface((self.lock_rect.width, self.lock_rect.height), pygame.SRCALPHA)
            overlay.fill((35, 35, 35, 150))
            self.screen.blit(overlay, self.lock_rect)
            pygame.draw.rect(self.screen, (90, 90, 90), self.lock_rect, 2)

        if self.show_hitboxes and self.reroll_rect:
            debug_surf = pygame.Surface((self.reroll_rect.width, self.reroll_rect.height), pygame.SRCALPHA)
            debug_surf.fill((255, 0, 0, 100))
            self.screen.blit(debug_surf, self.reroll_rect)
            pygame.draw.rect(self.screen, (255, 0, 0), self.reroll_rect, 2)

        if self.show_hitboxes and self.lock_rect:
            debug_surf = pygame.Surface((self.lock_rect.width, self.lock_rect.height), pygame.SRCALPHA)
            debug_surf.fill((200, 200, 0, 90))
            self.screen.blit(debug_surf, self.lock_rect)
            pygame.draw.rect(self.screen, (255, 255, 0), self.lock_rect, 2)

    def _roll_offers(self, initial=False):
        self.offers = []
        if not self.pool_items:
            return
        if len(self.pool_items) >= self.offer_count:
            self.offers = random.sample(self.pool_items, self.offer_count)
        else:
            self.offers = random.choices(self.pool_items, k=self.offer_count)

    def reroll_free(self):
        self._roll_offers(initial=False)

    def reroll_for_new_round(self):
        """Automatycznie losuje oferty na początku nowej rundy, chyba że zablokowane."""
        if not bool(self.locked):
            self._roll_offers(initial=False)

    def get_state(self) -> dict:
        """Zwraca snapshot-bezpieczną reprezentację stanu sklepu."""
        return {
            'offers': list(self.offers) if isinstance(self.offers, list) else [],
            'locked': bool(self.locked),
        }

    def set_state(self, state: dict):
        """Przywraca stan sklepu ze snapshotu."""
        if not isinstance(state, dict):
            return
        offers = state.get('offers', None)
        if isinstance(offers, list):
            self.offers = list(offers)
        if 'locked' in state:
            self.locked = bool(state.get('locked'))

    def _get_unit_cost(self, name: str) -> int:
        try:
            data = self.units_data.get(name, {})
            cost = int(data.get('cost', 1))
            return cost if cost > 0 else 1
        except Exception:
            return 1

    def _trigger_shake(self, duration_ms: int = 280, magnitude: int = 10):
        try:
            now = pygame.time.get_ticks()
        except Exception:
            now = 0
        self._shake_until = now + int(max(0, duration_ms))
        self._shake_mag = int(max(0, magnitude))

    def _get_shake_offset(self):
        try:
            now = pygame.time.get_ticks()
        except Exception:
            return (0, 0)
        if now >= self._shake_until or self._shake_mag <= 0:
            return (0, 0)
        step = (now // max(1, self._shake_speed_ms)) % 2
        sign = 1 if step == 0 else -1
        return (sign * self._shake_mag, 0)