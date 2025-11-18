import os
import sys

import pygame

from autochess.game.board import Board
from autochess.ui.background import \
    BackgroundStatic  # static background helper
from autochess.ui.menu import Menu
from autochess.ui.settings import SettingsScreen
from config.setting import (COLOR_BG, COLOR_HIGHLIGHT, COLOR_SUBTLE,
                            COLOR_TEXT, DEFAULT_VOLUME, FPS, MUSIC_PATH,
                            SCREEN_HEIGHT, SCREEN_WIDTH, title_size)


class Game:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
        except Exception:
            pass

        # Create a window first (we may switch to fullscreen after reading settings)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('HEXA')

        # States
        self.state = 'MENU'
        # start with a sensible default; may be overridden by settings screen/app saved state
        self.volume = DEFAULT_VOLUME
        self.sfx_volume = DEFAULT_VOLUME

        # Try load menu music early (volume will be applied again after settings are loaded)
        self._load_music(MUSIC_PATH, self.volume)

        # Core
        self.board = Board(hex_center=(SCREEN_WIDTH // 2 + title_size, SCREEN_HEIGHT // 2))
        self.clock = pygame.time.Clock()

        # Static archer background (scaled+cropped)
        self.menu_bg = BackgroundStatic(screen=self.screen, image_path='files/ui/bg_archer.png', overlay_alpha=28)

        # UI: pass the new logo path
        self.menu = Menu(
            screen=self.screen,
            options=[('Play', 'play'), ('Options', 'settings'), ('Quit', 'exit')],
            colors={'text': COLOR_TEXT, 'highlight': COLOR_HIGHLIGHT, 'subtle': COLOR_SUBTLE},
            logo_path='files/ui/hexa2.png'
        )

        # Settings screen: give a ref so it can apply volume/fullscreen immediately
        self.settings_screen = SettingsScreen(
            screen=self.screen,
            volume=self.volume,
            sfx_volume=self.sfx_volume,
            colors={'text': COLOR_TEXT, 'highlight': COLOR_HIGHLIGHT, 'subtle': COLOR_SUBTLE},
            game_ref=self
        )

        # Read saved settings / current mixer and apply to game audio state
        try:
            # SettingsScreen now exposes getters and also prefers persisted values
            self.volume = getattr(self.settings_screen, 'volume', self.settings_screen.get_music_volume())
            self.sfx_volume = getattr(self.settings_screen, 'sfx_volume', self.settings_screen.get_sfx_volume())
            self.set_volume(self.volume)
            self.set_sfx_volume(self.sfx_volume)
        except Exception:
            pass

        # Apply fullscreen at startup if settings indicate so (default/saved)
        try:
            if self.settings_screen.is_fullscreen():
                self.apply_fullscreen(True)
        except Exception:
            pass

        self.startgame()

    def _load_music(self, path, vol):
        try:
            if os.path.exists(path):
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(vol)
                pygame.mixer.music.play(-1)  # loop forever
        except Exception:
            # if file not found or load fails, ignore silently
            pass

    # helpers used by settings
    def set_volume(self, vol):
        try:
            pygame.mixer.music.set_volume(vol)
        except Exception:
            pass
        self.volume = vol

    def set_sfx_volume(self, vol):
        # store sfx volume; if you have SFX sounds, set their volume when playing
        self.sfx_volume = vol

    def apply_fullscreen(self, fullscreen):
        flags = pygame.FULLSCREEN if fullscreen else 0
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
        # reassign screens & rebuild scaled backgrounds
        self.menu.screen = self.screen
        self.settings_screen.screen = self.screen
        self.menu_bg = BackgroundStatic(screen=self.screen, image_path='files/ui/bg_archer.png', overlay_alpha=28)
        # settings_screen will rebuild its internal scaled modal on next draw if needed.

    def startgame(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit(0)

                if self.state == 'MENU':
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        sys.exit(0)
                    action = self.menu.handle_event(event)
                    if action == 'play':
                        self.state = 'PLAY'
                    elif action == 'settings':
                        self.state = 'SETTINGS'
                    elif action == 'exit':
                        sys.exit(0)

                elif self.state == 'SETTINGS':
                    # Esc returns to menu (do NOT quit)
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.state = 'MENU'
                        continue

                    # pass events to settings screen
                    result = self.settings_screen.handle_event(event)
                    if result == 'changed':
                        # read new values from settings_screen attributes and apply immediately
                        self.volume = getattr(self.settings_screen, 'volume', self.settings_screen.get_music_volume())
                        self.sfx_volume = getattr(self.settings_screen, 'sfx_volume', self.settings_screen.get_sfx_volume())
                        self.set_volume(self.volume)
                        self.set_sfx_volume(self.sfx_volume)
                    elif result == 'back':
                        self.state = 'MENU'

                elif self.state == 'PLAY':
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.state = 'MENU'
                        continue
                    # future game events go here...

            # Draw per state
            if self.state == 'MENU':
                # draw archer background and menu
                self.menu_bg.draw()
                self.menu.draw(skip_clear=True)
            elif self.state == 'SETTINGS':
                # draw the normal menu background behind the centered modal
                self.menu_bg.draw()
                # SettingsScreen draws the centered modal and interactive bars
                self.settings_screen.draw()
            elif self.state == 'PLAY':
                self.screen.fill('black')
                self.board.run()

            pygame.display.update()
            self.clock.tick(FPS)


if __name__ == "__main__":
    Game()