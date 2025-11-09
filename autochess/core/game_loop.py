import pygame,sys

from config.setting import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    DEFAULT_VOLUME,
    MUSIC_PATH,
    COLOR_BG,
    COLOR_TEXT,
    COLOR_HIGHLIGHT,
    COLOR_SUBTLE,
)
from autochess.game.board import Board
from autochess.ui.menu import Menu
from autochess.ui.settings import SettingsScreen
from autochess.ui.background import BackgroundStatic  # static background helper


class Game:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
        except Exception:
            pass

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('HEXA')

        # States
        self.state = 'MENU'
        self.volume = DEFAULT_VOLUME
        self.sfx_volume = DEFAULT_VOLUME
        self._load_music(MUSIC_PATH, self.volume)

        # Core
        self.board = Board()
        self.clock = pygame.time.Clock()

        # Static archer background (scaled+cropped) - make sure file exists at files/ui/bg_archer.png
        self.menu_bg = BackgroundStatic(screen=self.screen, image_path='files/ui/bg_archer.png', overlay_alpha=28)

        # UI
        self.menu = Menu(
            screen=self.screen,
            options=[('Play', 'play'), ('Settings', 'settings'), ('Exit', 'exit')],
            colors={'text': COLOR_TEXT, 'highlight': COLOR_HIGHLIGHT, 'subtle': COLOR_SUBTLE},
            logo_path='files/ui/logo.png'
        )
        self.settings_screen = SettingsScreen(
            screen=self.screen,
            volume=self.volume,
            sfx_volume=self.sfx_volume,
            colors={'text': COLOR_TEXT, 'highlight': COLOR_HIGHLIGHT, 'subtle': COLOR_SUBTLE},
            game_ref=self
        )

        self.startgame()

    def _load_music(self, path, vol):
        try:
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
        self.sfx_volume = vol

    def apply_fullscreen(self, fullscreen):
        flags = pygame.FULLSCREEN if fullscreen else 0
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
        # reassign screens
        self.menu.screen = self.screen
        self.settings_screen.screen = self.screen
        self.menu_bg = BackgroundStatic(screen=self.screen, image_path='files/ui/bg_archer.png', overlay_alpha=28)

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
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.state = 'MENU'
                        continue
                    result = self.settings_screen.handle_event(event)
                    if result == 'changed':
                        # read new values from settings screen attributes
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

            # Draw per state
            if self.state == 'MENU':
                self.menu_bg.draw()
                self.menu.draw(skip_clear=True)
            elif self.state == 'SETTINGS':
                self.menu_bg.draw()  # same background for settings
                self.settings_screen.draw()
            elif self.state == 'PLAY':
                self.screen.fill('black')
                self.board.run()

            pygame.display.update()
            self.clock.tick(FPS)


if __name__ == "__main__":
    Game()