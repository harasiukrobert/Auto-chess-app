import pygame
import json
import os

SETTINGS_PATH = 'config/user_settings.json'
DEFAULTS = {
    'music_volume': 0.10,   # default 10%
    'sfx_volume': 0.10,     # default 10%
    'fullscreen': False
}

class SettingsScreen:
    """
    Settings with full mouse + keyboard support:
    - Click or drag sliders (music + sfx)
    - Click fullscreen box to toggle
    - Click buttons (Play test SFX, Reset, Back)
    - Keyboard controls still work
    - Exposes .volume and .sfx_volume for Game compatibility
    """
    def __init__(self, screen, volume=None, sfx_volume=None, colors=None, game_ref=None):
        self.screen = screen
        self.game_ref = game_ref
        self.w, self.h = self.screen.get_size()
        colors = colors or {}
        self.color_text = colors.get('text', (230, 230, 230))
        self.color_highlight = colors.get('highlight', (80, 125, 170))
        self.color_subtle = colors.get('subtle', (150, 150, 150))

        # fonts
        self.font = pygame.font.SysFont(None, 44)
        self.title_font = pygame.font.SysFont(None, 72)

        # load persistent settings
        self.settings = DEFAULTS.copy()
        self._load()

        # override with init args if provided
        if volume is not None:
            self.settings['music_volume'] = float(volume)
        if sfx_volume is not None:
            self.settings['sfx_volume'] = float(sfx_volume)

        # expose compatibility attributes
        self.volume = float(self.settings['music_volume'])
        self.sfx_volume = float(self.settings['sfx_volume'])

        # UI state
        self.selected = 0  # which option is selected
        self.option_count = 6  # music, sfx, fullscreen, test, reset, back

        # button visuals (match menu)
        self.btn_base = (40, 55, 80)
        self.btn_border = (90, 120, 160)
        self.btn_hover_base = (225, 240, 255)
        self.btn_hover_border = (160, 200, 240)
        self.color_hover_text = (20, 40, 70)

        # Test SFX
        click_path = 'files/audio/ui_click.wav'
        self.test_sfx = None
        if os.path.exists(click_path):
            try:
                self.test_sfx = pygame.mixer.Sound(click_path)
            except Exception:
                self.test_sfx = None

        # Mouse / dragging state for sliders
        self.dragging = None  # None | 'music' | 'sfx'

    # Persistence
    def _load(self):
        try:
            if os.path.exists(SETTINGS_PATH):
                with open(SETTINGS_PATH, 'r') as f:
                    data = json.load(f)
                    for k in DEFAULTS:
                        if k in data:
                            self.settings[k] = data[k]
        except Exception:
            pass

    def _save(self):
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        try:
            with open(SETTINGS_PATH, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception:
            pass

    # Public getters for Game to apply
    def get_music_volume(self):
        return float(self.settings.get('music_volume', DEFAULTS['music_volume']))

    def get_sfx_volume(self):
        return float(self.settings.get('sfx_volume', DEFAULTS['sfx_volume']))

    def is_fullscreen(self):
        return bool(self.settings.get('fullscreen', DEFAULTS['fullscreen']))

    # Layout helpers to make mouse math consistent with draw
    def _slider_bar_rect(self, y):
        bar_w = 620
        bar_h = 18
        bar_x = self.w // 2 - bar_w // 2
        return pygame.Rect(bar_x, y, bar_w, bar_h)

    def _toggle_box_rect(self, y):
        box_w, box_h = 120, 36
        box_x = self.w // 2 + 200
        return pygame.Rect(box_x, y - box_h//2, box_w, box_h)

    # map mouse x->normalized value (0..1)
    def _value_from_x(self, mx, bar_rect):
        rel = (mx - bar_rect.left) / float(bar_rect.width)
        return max(0.0, min(1.0, rel))

    def handle_event(self, event):
        """
        Returns:
         - 'changed' when a setting changed (so Game can re-read)
         - 'back' when user pressed Back
         - None otherwise
        """
        changed = False
        action = None

        # Keyboard navigation (unchanged behavior)
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % self.option_count
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % self.option_count
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                if self.selected == 0:
                    self.settings['music_volume'] = max(0.0, round(self.settings['music_volume'] - 0.05, 2)); changed=True
                elif self.selected == 1:
                    self.settings['sfx_volume'] = max(0.0, round(self.settings['sfx_volume'] - 0.05, 2)); changed=True
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                if self.selected == 0:
                    self.settings['music_volume'] = min(1.0, round(self.settings['music_volume'] + 0.05, 2)); changed=True
                elif self.selected == 1:
                    self.settings['sfx_volume'] = min(1.0, round(self.settings['sfx_volume'] + 0.05, 2)); changed=True
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.selected == 2:
                    self.settings['fullscreen'] = not self.settings['fullscreen']; changed=True
                    if self.game_ref:
                        try:
                            self.game_ref.apply_fullscreen(self.settings['fullscreen'])
                        except Exception:
                            pass
                elif self.selected == 3:
                    if self.test_sfx:
                        try:
                            self.test_sfx.set_volume(self.settings['sfx_volume'])
                            self.test_sfx.play()
                        except Exception:
                            pass
                elif self.selected == 4:
                    self.settings = DEFAULTS.copy()
                    changed = True
                    if self.game_ref:
                        try:
                            self.game_ref.set_volume(self.settings['music_volume'])
                            self.game_ref.set_sfx_volume(self.settings['sfx_volume'])
                            self.game_ref.apply_fullscreen(self.settings['fullscreen'])
                        except Exception:
                            pass
                elif self.selected == 5:
                    action = 'back'

        # Mouse: motion, click, drag, release
        elif event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            # always update hover/selection by actual control hit-testing (so mouse and keyboard cooperate)
            # check sliders/toggle first
            music_bar = self._slider_bar_rect(self._music_y())
            sfx_bar = self._slider_bar_rect(self._sfx_y())
            toggle_box = self._toggle_box_rect(self._toggle_y())
            if music_bar.collidepoint(mx, my):
                self.selected = 0
            elif sfx_bar.collidepoint(mx, my):
                self.selected = 1
            elif toggle_box.collidepoint(mx, my):
                self.selected = 2
            else:
                # fallback to earlier region test for buttons
                self._update_hover_by_mouse(mx, my)

            # if dragging, update value
            if self.dragging is not None:
                if self.dragging == 'music':
                    bar = music_bar
                    self.settings['music_volume'] = round(self._value_from_x(mx, bar), 2)
                    changed = True
                elif self.dragging == 'sfx':
                    bar = sfx_bar
                    self.settings['sfx_volume'] = round(self._value_from_x(mx, bar), 2)
                    changed = True

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # check slider hit areas first (no keyboard selection required)
            music_bar = self._slider_bar_rect(self._music_y())
            sfx_bar = self._slider_bar_rect(self._sfx_y())
            if music_bar.collidepoint(mx, my):
                self.settings['music_volume'] = round(self._value_from_x(mx, music_bar), 2)
                self.dragging = 'music'
                self.selected = 0
                changed = True
            elif sfx_bar.collidepoint(mx, my):
                self.settings['sfx_volume'] = round(self._value_from_x(mx, sfx_bar), 2)
                self.dragging = 'sfx'
                self.selected = 1
                changed = True
            else:
                # toggle box click?
                toggle_box = self._toggle_box_rect(self._toggle_y())
                if toggle_box.collidepoint(mx, my):
                    self.settings['fullscreen'] = not self.settings['fullscreen']
                    self.selected = 2
                    changed = True
                    if self.game_ref:
                        try:
                            self.game_ref.apply_fullscreen(self.settings['fullscreen'])
                        except Exception:
                            pass
                else:
                    # check buttons / other clickable options
                    clicked = self._option_at_pos(mx, my)
                    if clicked is not None:
                        self.selected = clicked
                        # emulate Enter/activate
                        return self.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            # stop dragging on release
            if self.dragging is not None:
                self.dragging = None

        if changed:
            # update exposed attributes
            self.volume = float(self.settings['music_volume'])
            self.sfx_volume = float(self.settings['sfx_volume'])
            # apply to Game if available
            if self.game_ref:
                try:
                    self.game_ref.set_volume(self.volume)
                    self.game_ref.set_sfx_volume(self.sfx_volume)
                except Exception:
                    pass
            self._save()
            return 'changed'
        return action

    # mouse helpers (use same positions as draw)
    def _music_y(self):
        base_y = self.h // 2 - 40
        spacing = 80
        return base_y + 0 * spacing

    def _sfx_y(self):
        base_y = self.h // 2 - 40
        spacing = 80
        return base_y + 1 * spacing

    def _toggle_y(self):
        base_y = self.h // 2 - 40
        spacing = 80
        return base_y + 2 * spacing

    def _update_hover_by_mouse(self, mx, my):
        base_y = self.h // 2 - 40
        spacing = 80
        width = int(self.w * 0.5)
        left = (self.w - width) // 2
        right = left + width
        for i in range(self.option_count):
            y = base_y + i * spacing
            top = y - 28
            bottom = y + 28
            if left <= mx <= right and top <= my <= bottom:
                self.selected = i
                break

    def _option_at_pos(self, mx, my):
        # check sliders and toggle first
        music_bar = self._slider_bar_rect(self._music_y())
        sfx_bar = self._slider_bar_rect(self._sfx_y())
        toggle_box = self._toggle_box_rect(self._toggle_y())
        if music_bar.collidepoint(mx, my):
            return 0
        if sfx_bar.collidepoint(mx, my):
            return 1
        if toggle_box.collidepoint(mx, my):
            return 2

        base_y = self.h // 2 - 40
        spacing = 80
        width = int(self.w * 0.5)
        left = (self.w - width) // 2
        right = left + width
        for i in range(self.option_count):
            y = base_y + i * spacing
            top = y - 28
            bottom = y + 28
            if left <= mx <= right and top <= my <= bottom:
                return i
        return None

    def draw(self, bg_color=(10, 10, 10)):
        # draws settings controls on the current screen
        w, h = self.w, self.h
        # Title
        title_surf = self.title_font.render("Settings", True, self.color_highlight)
        title_rect = title_surf.get_rect(center=(w // 2, h // 6))
        self.screen.blit(title_surf, title_rect)

        base_y = h // 2 - 40
        spacing = 80

        # Music slider (label moved up a bit)
        music_y = base_y + 0 * spacing - 16
        self._draw_slider("Music Volume", self.settings['music_volume'], music_y, is_selected=(self.selected==0))

        # SFX slider
        sfx_y = base_y + 1 * spacing - 16
        self._draw_slider("SFX Volume", self.settings['sfx_volume'], sfx_y, is_selected=(self.selected==1))

        # Fullscreen toggle
        toggle_y = base_y + 2 * spacing
        self._draw_toggle("Fullscreen", self.settings['fullscreen'], toggle_y, is_selected=(self.selected==2))

        # Buttons (styled like main menu)
        self._draw_menu_button("Play test SFX", 3, base_y + 3 * spacing, is_selected=(self.selected==3))
        self._draw_menu_button("Reset to defaults", 4, base_y + 4 * spacing, is_selected=(self.selected==4))
        self._draw_menu_button("Back", 5, base_y + 5 * spacing, is_selected=(self.selected==5))

    def _draw_slider(self, label, value, y, is_selected=False):
        w = self.w
        # label above slider
        lbl = self.font.render(label, True, self.color_text)
        lbl_rect = lbl.get_rect(midleft=(w // 2 - 260, y - 24))
        self.screen.blit(lbl, lbl_rect)

        # larger slider (wider + taller)
        bar_w = 620
        bar_h = 18
        bar_x = w // 2 - bar_w // 2
        bar_rect = pygame.Rect(bar_x, y, bar_w, bar_h)
        pygame.draw.rect(self.screen, (60,60,60), bar_rect, border_radius=10)

        fill_w = int(bar_w * value)
        fill_rect = pygame.Rect(bar_x, y, fill_w, bar_h)
        pygame.draw.rect(self.screen, self.color_highlight, fill_rect, border_radius=10)

        knob_x = bar_x + fill_w
        knob_rect = pygame.Rect(knob_x - 10, y - 6, 20, bar_h + 12)
        pygame.draw.rect(self.screen, (230,230,230) if is_selected else (200,200,200), knob_rect, border_radius=8)

        # numeric percentage now black for readability
        val = self.font.render(f"{int(value*100)}%", True, (0, 0, 0))
        val_rect = val.get_rect(midleft=(bar_x + bar_w + 18, y + bar_h//2))
        self.screen.blit(val, val_rect)

    def _draw_toggle(self, label, toggled, y, is_selected=False):
        w = self.w
        lbl = self.font.render(label, True, self.color_text)
        lbl_rect = lbl.get_rect(midleft=(w // 2 - 260, y))
        self.screen.blit(lbl, lbl_rect)

        box_w, box_h = 120, 36
        box_x = self.w // 2 + 200
        box_rect = pygame.Rect(box_x, y - box_h//2, box_w, box_h)
        pygame.draw.rect(self.screen, (70,70,70), box_rect, border_radius=8)
        if toggled:
            inner = pygame.Rect(box_x + 6, y - box_h//2 + 6, box_w - 12, box_h - 12)
            pygame.draw.rect(self.screen, self.color_highlight, inner, border_radius=6)

    def _draw_menu_button(self, label, idx, y, is_selected=False):
        # draws a button styled like main menu
        w = self.w
        is_hover = is_selected
        text_color = self.color_hover_text if is_selected else self.color_text
        surf = self.font.render(label, True, text_color)
        rect = surf.get_rect(center=(w // 2, y))
        box_rect = pygame.Rect(rect.left - 18, rect.top - 8, rect.width + 36, rect.height + 16)

        base_col = self.btn_hover_base if is_hover else self.btn_base
        border_col = self.btn_hover_border if is_hover else self.btn_border

        pygame.draw.rect(self.screen, base_col, box_rect, border_radius=10)
        pygame.draw.rect(self.screen, border_col, box_rect, width=2, border_radius=10)
        self.screen.blit(surf, rect)