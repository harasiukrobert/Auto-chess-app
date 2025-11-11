import pygame
import json
import os

SETTINGS_PATH = 'config/user_settings.json'
DEFAULTS = {
    'music_volume': 0.50,
    'sfx_volume': 0.50,
    'fullscreen': True
}

# ---------- TUNING (change these numbers to reposition & resize UI) ----------
# Pixel offsets applied to the computed positions. Change and re-run.
MUSIC_Y_ADJ = 33           # move music slider up/down (px)
SFX_Y_ADJ = 14             # move sfx slider up/down (px)
BAR_X_ADJ = 0              # move both bars left/right (px)
BAR_WIDTH_ADJ = -50        # expand/shrink bar width (px)
BAR_HEIGHT_ADJ = 15        # add pixels to slider height (makes slider thicker)
BUTTON_SIZE_DELTA = 20     # increase minus/plus button size by this many pixels
LEFT_CIRCLE_X_ADJ = 0      # shift left circular button horizontally (px)
RIGHT_CIRCLE_X_ADJ = -35   # shift right circular button horizontally (px)
X_BUTTON_Y_ADJ = -30       # shift the close-X vertically relative to modal (px)
X_BUTTON_X_ADJ = -20       # shift the close-X horizontally (negative = left)

# Discrete-step slider tuning (how many clicks from empty -> full)
STEPS = 15               # number of discrete steps from 0 -> full (e.g., 10 clicks)
STEP_PLUS_STEPS = 1      # how many steps the + button increments per click
STEP_MINUS_STEPS = 1     # how many steps the - button decrements per click

# If True, clicking +/- has no effect when value is already at 0.0 or 1.0 (prevents extra clicks)
ENFORCE_VISIBLE_LIMIT = True

# Debug mode: press F2 while running to toggle overlay of hit boxes (visual tuning).
DEBUG_POSITION_MODE = False
# ---------------------------------------------------------------------

class SettingsScreen:
    """
    Options screen using the art-panel and separate slider-fill / +/- / X assets.
    See top constants for easy tuning of positions and sizes.
    """
    def __init__(self, screen, volume=None, sfx_volume=None, colors=None, game_ref=None):
        self.screen = screen
        self.game_ref = game_ref
        self.w, self.h = self.screen.get_size()
        colors = colors or {}
        self.color_text = colors.get('text', (230, 230, 230))
        self.color_highlight = colors.get('highlight', (80, 125, 170))

        self.font = pygame.font.SysFont(None, 36)

        # load persistent settings
        self.settings = DEFAULTS.copy()
        self._load()

        # If a Game reference is provided, prefer Game's live values (so UI matches actual audio).
        if self.game_ref is not None:
            try:
                gm_vol = getattr(self.game_ref, 'volume', None)
                if gm_vol is None:
                    try:
                        gm_vol = pygame.mixer.music.get_volume()
                    except Exception:
                        gm_vol = None
                if gm_vol is not None:
                    self.settings['music_volume'] = float(gm_vol)
                gm_sfx = getattr(self.game_ref, 'sfx_volume', None)
                if gm_sfx is not None:
                    self.settings['sfx_volume'] = float(gm_sfx)
            except Exception:
                pass

        # override with init args if explicitly provided
        if volume is not None:
            self.settings['music_volume'] = float(volume)
        if sfx_volume is not None:
            self.settings['sfx_volume'] = float(sfx_volume)

        # compatibility attributes (kept for backward compat)
        self.volume = float(self.settings['music_volume'])
        self.sfx_volume = float(self.settings['sfx_volume'])

        # internal integer-step representation (keeps visuals/audio in lock-step)
        # Derive steps from the initial float volume values
        try:
            self.music_steps = int(round(float(self.settings.get('music_volume', 0.0)) * STEPS))
        except Exception:
            self.music_steps = 0
        try:
            self.sfx_steps = int(round(float(self.settings.get('sfx_volume', 0.0)) * STEPS))
        except Exception:
            self.sfx_steps = 0

        # UI state
        self.selected = 0
        self.option_count = 2

        # dragging state
        self.dragging = None  # 'music' | 'sfx' | None

        # load options art (if present)
        self.options_art = None
        self.options_art_path = 'files/ui/options_menu.png'
        if os.path.exists(self.options_art_path):
            try:
                raw = pygame.image.load(self.options_art_path).convert_alpha()
                # scale to 50% of screen width while preserving aspect ratio
                target_w = int(self.w * 0.5)
                scale = target_w / raw.get_width()
                target_h = int(raw.get_height() * scale)
                self.options_art = pygame.transform.smoothscale(raw, (target_w, target_h))
            except Exception:
                self.options_art = None

        # load slider and button assets (optional)
        self.slider_fill_img = None
        self.btn_minus_img = None
        self.btn_plus_img = None
        self.x_img = None

        try:
            if os.path.exists('files/ui/slider_fill.png'):
                self.slider_fill_img = pygame.image.load('files/ui/slider_fill.png').convert_alpha()
        except Exception:
            self.slider_fill_img = None

        try:
            if os.path.exists('files/ui/button_minus.png'):
                self.btn_minus_img = pygame.image.load('files/ui/button_minus.png').convert_alpha()
        except Exception:
            self.btn_minus_img = None

        try:
            if os.path.exists('files/ui/button_plus.png'):
                self.btn_plus_img = pygame.image.load('files/ui/button_plus.png').convert_alpha()
        except Exception:
            self.btn_plus_img = None

        try:
            if os.path.exists('files/ui/x.png'):
                self.x_img = pygame.image.load('files/ui/x.png').convert_alpha()
        except Exception:
            self.x_img = None

        # runtime debug toggle (press F2)
        self.debug = DEBUG_POSITION_MODE

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

    def get_music_volume(self):
        return float(self.settings.get('music_volume', DEFAULTS['music_volume']))

    def get_sfx_volume(self):
        return float(self.settings.get('sfx_volume', DEFAULTS['sfx_volume']))

    def is_fullscreen(self):
        return bool(self.settings.get('fullscreen', DEFAULTS['fullscreen']))

    # helpers to compute image + slider geometry
    def image_rect(self):
        """
        Returns the pygame.Rect of the centered options image (scaled already).
        If no image, returns centered rect sized at 60% of screen width/height.
        """
        if self.options_art:
            img = self.options_art
            rect = img.get_rect(center=(self.w // 2, self.h // 2))
            return rect
        # fallback box
        w = int(self.w * 0.6)
        h = int(self.h * 0.6)
        rect = pygame.Rect((self.w - w)//2, (self.h - h)//2, w, h)
        return rect

    def _music_bar_rect(self, img_rect):
        bar_w = int(img_rect.width * 0.62) + BAR_WIDTH_ADJ
        bar_h = max(int(img_rect.height * 0.06) + BAR_HEIGHT_ADJ, 14)
        bar_x = img_rect.left + (img_rect.width - bar_w) // 2 + BAR_X_ADJ
        bar_y = int(img_rect.top + img_rect.height * 0.36) + MUSIC_Y_ADJ
        hit_rect = pygame.Rect(bar_x, bar_y - 6, bar_w, bar_h + 12)
        return hit_rect

    def _sfx_bar_rect(self, img_rect):
        bar_w = int(img_rect.width * 0.62) + BAR_WIDTH_ADJ
        bar_h = max(int(img_rect.height * 0.06) + BAR_HEIGHT_ADJ, 14)
        bar_x = img_rect.left + (img_rect.width - bar_w) // 2 + BAR_X_ADJ
        bar_y = int(img_rect.top + img_rect.height * 0.62) + SFX_Y_ADJ
        hit_rect = pygame.Rect(bar_x, bar_y - 6, bar_w, bar_h + 12)
        return hit_rect

    def _left_circle_rect(self, bar_rect):
        size = int(bar_rect.height * 1.8) + BUTTON_SIZE_DELTA
        rect = pygame.Rect(bar_rect.left - size // 2 + LEFT_CIRCLE_X_ADJ,
                           bar_rect.centery - size // 2,
                           size, size)
        return rect

    def _right_circle_rect(self, bar_rect):
        size = int(bar_rect.height * 1.8) + BUTTON_SIZE_DELTA
        rect = pygame.Rect(bar_rect.right - size // 2 + RIGHT_CIRCLE_X_ADJ,
                           bar_rect.centery - size // 2,
                           size, size)
        return rect

    def _x_button_rect(self, img_rect):
        """
        Return a rect for the X button using either the x_img size or a fraction of modal.
        X is centered at bottom of the modal art.
        """
        if self.x_img:
            target_w = int(img_rect.width * 0.12) + BUTTON_SIZE_DELTA//2
            scale = min(1.0, target_w / max(1, self.x_img.get_width()))
            tw = int(self.x_img.get_width() * scale)
            th = int(self.x_img.get_height() * scale)
            cx = img_rect.centerx + X_BUTTON_X_ADJ
            cy = img_rect.bottom - int(img_rect.height * 0.07) + X_BUTTON_Y_ADJ
            rect = pygame.Rect(cx - tw//2, cy - th//2, tw, th)
            return rect
        else:
            cx = img_rect.centerx + X_BUTTON_X_ADJ
            cy = img_rect.bottom - int(img_rect.height * 0.07) + X_BUTTON_Y_ADJ
            r = int(img_rect.width * 0.06) + BUTTON_SIZE_DELTA//2
            return pygame.Rect(cx - r, cy - r, r*2, r*2)

    def _value_from_x(self, mx, bar_rect):
        rel = (mx - bar_rect.left) / float(bar_rect.width)
        return max(0.0, min(1.0, rel))

    # helper: apply integer step deltas and snap to edges (updates both steps + stored float)
    def _apply_step(self, key, delta_steps):
        """
        Adjusts the stored volume using integer steps.
        key: 'music_volume' or 'sfx_volume'
        delta_steps: integer (+1 or -1 or larger)
        """
        # choose which step counter to use
        if key == 'music_volume':
            cur_steps = getattr(self, 'music_steps', int(round(float(self.settings.get('music_volume', 0.0)) * STEPS)))
        else:
            cur_steps = getattr(self, 'sfx_steps', int(round(float(self.settings.get('sfx_volume', 0.0)) * STEPS)))

        new_steps = max(0, min(STEPS, cur_steps + int(delta_steps)))

        # If ENFORCE_VISIBLE_LIMIT is on and nothing changes, return early
        if ENFORCE_VISIBLE_LIMIT and new_steps == cur_steps:
            return

        # store step and quantized float
        if key == 'music_volume':
            self.music_steps = new_steps
            new_val = new_steps / float(STEPS)
            self.settings['music_volume'] = round(new_val, 3)
        else:
            self.sfx_steps = new_steps
            new_val = new_steps / float(STEPS)
            self.settings['sfx_volume'] = round(new_val, 3)

    def handle_event(self, event):
        """
        Returns 'changed' when settings changed, 'back' when user closes options.
        """
        changed = False
        action = None

        # toggle debug with F2
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F2:
            self.debug = not self.debug

        # keyboard
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                if self.selected == 0:
                    self._apply_step('music_volume', -STEP_MINUS_STEPS); changed = True
                elif self.selected == 1:
                    self._apply_step('sfx_volume', -STEP_MINUS_STEPS); changed = True
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                if self.selected == 0:
                    self._apply_step('music_volume', STEP_PLUS_STEPS); changed = True
                elif self.selected == 1:
                    self._apply_step('sfx_volume', STEP_PLUS_STEPS); changed = True
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % self.option_count
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % self.option_count
            elif event.key == pygame.K_ESCAPE:
                return 'back'

        # mouse
        elif event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            img_rect = self.image_rect()
            music_bar = self._music_bar_rect(img_rect)
            sfx_bar = self._sfx_bar_rect(img_rect)
            # update selection by hit-testing against bars
            if music_bar.collidepoint(mx, my):
                self.selected = 0
            elif sfx_bar.collidepoint(mx, my):
                self.selected = 1
            # if dragging, update value (quantized to steps)
            if self.dragging == 'music':
                raw = self._value_from_x(mx, music_bar)
                new_steps = int(round(raw * STEPS))
                self.music_steps = max(0, min(STEPS, new_steps))
                self.settings['music_volume'] = round(self.music_steps / float(STEPS), 3)
                changed = True
            elif self.dragging == 'sfx':
                raw = self._value_from_x(mx, sfx_bar)
                new_steps = int(round(raw * STEPS))
                self.sfx_steps = max(0, min(STEPS, new_steps))
                self.settings['sfx_volume'] = round(self.sfx_steps / float(STEPS), 3)
                changed = True

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            img_rect = self.image_rect()
            music_bar = self._music_bar_rect(img_rect)
            sfx_bar = self._sfx_bar_rect(img_rect)

            left_music = self._left_circle_rect(music_bar)
            right_music = self._right_circle_rect(music_bar)
            left_sfx = self._left_circle_rect(sfx_bar)
            right_sfx = self._right_circle_rect(sfx_bar)

            # music minus/plus
            if left_music.collidepoint(mx, my):
                self._apply_step('music_volume', -STEP_MINUS_STEPS)
                self.selected = 0
                changed = True
            elif right_music.collidepoint(mx, my):
                self._apply_step('music_volume', STEP_PLUS_STEPS)
                self.selected = 0
                changed = True
            # sfx minus/plus
            elif left_sfx.collidepoint(mx, my):
                self._apply_step('sfx_volume', -STEP_MINUS_STEPS)
                self.selected = 1
                changed = True
            elif right_sfx.collidepoint(mx, my):
                self._apply_step('sfx_volume', STEP_PLUS_STEPS)
                self.selected = 1
                changed = True
            # click inside bars (sets value quantized to steps and starts drag)
            elif music_bar.collidepoint(mx, my):
                raw = self._value_from_x(mx, music_bar)
                new_steps = int(round(raw * STEPS))
                self.music_steps = max(0, min(STEPS, new_steps))
                self.settings['music_volume'] = round(self.music_steps / float(STEPS), 3)
                self.dragging = 'music'
                self.selected = 0
                changed = True
            elif sfx_bar.collidepoint(mx, my):
                raw = self._value_from_x(mx, sfx_bar)
                new_steps = int(round(raw * STEPS))
                self.sfx_steps = max(0, min(STEPS, new_steps))
                self.settings['sfx_volume'] = round(self.sfx_steps / float(STEPS), 3)
                self.dragging = 'sfx'
                self.selected = 1
                changed = True
            else:
                # clicked X?
                x_rect = self._x_button_rect(img_rect)
                if x_rect.collidepoint(mx, my):
                    return 'back'

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging is not None:
                self.dragging = None

        if changed:
            # update exposed attributes from quantized steps
            self.volume = float(self.settings['music_volume'])
            self.sfx_volume = float(self.settings['sfx_volume'])
            if self.game_ref:
                try:
                    self.game_ref.set_volume(self.volume)
                    self.game_ref.set_sfx_volume(self.sfx_volume)
                except Exception:
                    pass
            self._save()
            return 'changed'
        return action

    def draw(self, bg_color=(10, 10, 10)):
        # Draw the centered options image scaled to ~50% width and sliders on top
        w, h = self.w, self.h
        img_rect = self.image_rect()

        if self.options_art:
            self.screen.blit(self.options_art, img_rect.topleft)
        else:
            pygame.draw.rect(self.screen, (60,40,20), img_rect, border_radius=12)

        # Draw sliders on top at positions matching the art
        music_bar = self._music_bar_rect(img_rect)
        sfx_bar = self._sfx_bar_rect(img_rect)

        # MUSIC: draw dark backing then scaled green fill from slider_fill_img (if provided)
        pygame.draw.rect(self.screen, (20,20,20), music_bar, border_radius=10)
        # derive fractional from integer steps to ensure visuals match audio
        music_frac = (getattr(self, 'music_steps', int(round(float(self.settings.get('music_volume', 0.0)) * STEPS)))) / float(STEPS)
        music_val_w = int(music_bar.width * music_frac)
        # ensure tiny positive values are visible (avoid audio non-zero with no green showing)
        if getattr(self, 'music_steps', 0) > 0 and music_val_w == 0:
            music_val_w = 1
        if self.slider_fill_img and music_val_w > 0:
            try:
                scaled_fill = pygame.transform.smoothscale(self.slider_fill_img, (max(1, music_val_w), music_bar.height))
                self.screen.blit(scaled_fill, (music_bar.left, music_bar.top))
            except Exception:
                pygame.draw.rect(self.screen, (95,190,80), (music_bar.left, music_bar.top, music_val_w, music_bar.height), border_radius=10)
        else:
            pygame.draw.rect(self.screen, (95,190,80), (music_bar.left, music_bar.top, music_val_w, music_bar.height), border_radius=10)

        # draw circle buttons (minus/plus) ON TOP to hide seams (scaled by BUTTON_SIZE_DELTA)
        left_music = self._left_circle_rect(music_bar)
        right_music = self._right_circle_rect(music_bar)
        if self.btn_minus_img:
            try:
                s = pygame.transform.smoothscale(self.btn_minus_img, (left_music.width, left_music.height))
                self.screen.blit(s, left_music.topleft)
            except Exception:
                pygame.draw.ellipse(self.screen, (200,150,60), left_music)
        if self.btn_plus_img:
            try:
                s2 = pygame.transform.smoothscale(self.btn_plus_img, (right_music.width, right_music.height))
                self.screen.blit(s2, right_music.topleft)
            except Exception:
                pygame.draw.ellipse(self.screen, (200,150,60), right_music)

        # SFX: same as music
        pygame.draw.rect(self.screen, (20,20,20), sfx_bar, border_radius=10)
        sfx_frac = (getattr(self, 'sfx_steps', int(round(float(self.settings.get('sfx_volume', 0.0)) * STEPS)))) / float(STEPS)
        sfx_val_w = int(sfx_bar.width * sfx_frac)
        if getattr(self, 'sfx_steps', 0) > 0 and sfx_val_w == 0:
            sfx_val_w = 1
        if self.slider_fill_img and sfx_val_w > 0:
            try:
                scaled_fill2 = pygame.transform.smoothscale(self.slider_fill_img, (max(1, sfx_val_w), sfx_bar.height))
                self.screen.blit(scaled_fill2, (sfx_bar.left, sfx_bar.top))
            except Exception:
                pygame.draw.rect(self.screen, (95,190,80), (sfx_bar.left, sfx_bar.top, sfx_val_w, sfx_bar.height), border_radius=10)
        else:
            pygame.draw.rect(self.screen, (95,190,80), (sfx_bar.left, sfx_bar.top, sfx_val_w, sfx_bar.height), border_radius=10)

        left_sfx = self._left_circle_rect(sfx_bar)
        right_sfx = self._right_circle_rect(sfx_bar)
        if self.btn_minus_img:
            try:
                s = pygame.transform.smoothscale(self.btn_minus_img, (left_sfx.width, left_sfx.height))
                self.screen.blit(s, left_sfx.topleft)
            except Exception:
                pygame.draw.ellipse(self.screen, (200,150,60), left_sfx)
        if self.btn_plus_img:
            try:
                s2 = pygame.transform.smoothscale(self.btn_plus_img, (right_sfx.width, right_sfx.height))
                self.screen.blit(s2, right_sfx.topleft)
            except Exception:
                pygame.draw.ellipse(self.screen, (200,150,60), right_sfx)

        # Draw X button on bottom center of modal
        x_rect = self._x_button_rect(img_rect)
        if self.x_img:
            try:
                sx = pygame.transform.smoothscale(self.x_img, (x_rect.width, x_rect.height))
                self.screen.blit(sx, x_rect.topleft)
            except Exception:
                pygame.draw.ellipse(self.screen, (255,255,255,30), x_rect)
        else:
            pygame.draw.circle(self.screen, (255,255,255,30), x_rect.center, x_rect.width//2)

        # Debug overlays for tuning
        if self.debug:
            overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            # music/sfx bars
            pygame.draw.rect(overlay, (255,0,0,80), music_bar)
            pygame.draw.rect(overlay, (255,0,0,80), sfx_bar)
            # left/right circles
            pygame.draw.rect(overlay, (0,255,0,80), left_music)
            pygame.draw.rect(overlay, (0,255,0,80), right_music)
            pygame.draw.rect(overlay, (0,255,0,80), left_sfx)
            pygame.draw.rect(overlay, (0,255,0,80), right_sfx)
            # X rect
            pygame.draw.rect(overlay, (0,0,255,80), x_rect)
            self.screen.blit(overlay, (0,0))