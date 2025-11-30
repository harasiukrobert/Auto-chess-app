import pygame
import os

DEBUG_BG = False  # set True temporarily to print load info

def load_and_cover(path: str, target_size: tuple[int, int]) -> pygame.Surface:
    """
    Load an image and scale it to cover target_size while preserving aspect ratio.
    Center-crops excess.Similar to CSS background-size: cover.
    """
    target_w, target_h = target_size
    raw = pygame.image.load(path).convert_alpha()
    iw, ih = raw.get_width(), raw.get_height()

    scale = max(target_w / iw, target_h / ih)
    new_w, new_h = int(iw * scale), int(ih * scale)
    scaled = pygame.transform.smoothscale(raw, (new_w, new_h))

    x_offset = (new_w - target_w) // 2
    y_offset = (new_h - target_h) // 2
    surface = pygame.Surface((target_w, target_h), pygame.SRCALPHA)
    surface.blit(scaled, (-x_offset, -y_offset))
    return surface


class BackgroundStatic:
    """
    Static background: loads one image and draws it with optional dark overlay.
    """
    def __init__(self, screen, image_path: str, overlay_alpha: int = 30):
        self.screen = screen
        self.w, self.h = self.screen.get_size()
        self.overlay_alpha = overlay_alpha

        loaded = False
        if os.path.exists(image_path):
            try:
                self.img = load_and_cover(image_path, (self.w, self.h))
                loaded = True
            except Exception as e:
                if DEBUG_BG:
                    print(f"[BG] Failed to load {image_path}: {e}")
                self.img = self._fallback()
        else:
            if DEBUG_BG:
                print(f"[BG] Path not found: {image_path}")
            self.img = self._fallback()

        if DEBUG_BG:
            print(f"[BG] Loaded={loaded} path={image_path} size={self.img.get_size()} overlay_alpha={self.overlay_alpha}")

    def _fallback(self):
        surf = pygame.Surface((self.w, self.h))
        surf.fill((30, 30, 45))
        return surf

    def draw(self):
        self.screen.blit(self.img, (0, 0))
        if self.overlay_alpha > 0:
            overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, self.overlay_alpha))
            self.screen.blit(overlay, (0, 0))