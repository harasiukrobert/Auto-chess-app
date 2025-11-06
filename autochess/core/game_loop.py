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
        self._load_music(MUSIC_PATH, self.volume)

        # Core
        self.board = Board()
        self.clock = pygame.time.Clock()

        # Static background (simple): load and scale to screen size
        # Make sure the file exists at files/ui/bg_archer.png
        try:
            bg = pygame.image.load('files/ui/bg_archer.png')
        except Exception:
            # Try JPG fallback if needed
            try:
                bg = pygame.image.load('files/ui/bg_archer.jpg')
            except Exception:
                bg = None

        if bg is not None:
            self.menu_bg = pygame.transform.smoothscale(bg.convert(), (SCREEN_WIDTH, SCREEN_HEIGHT))
        else:
            # Fallback if not found
            self.menu_bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.menu_bg.fill((20, 20, 30))

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
            colors={'text': COLOR_TEXT, 'highlight': COLOR_HIGHLIGHT, 'subtle': COLOR_SUBTLE},
        )

        self.startgame()

    def _load_music(self, path, vol):
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(vol)
            pygame.mixer.music.play(-1)
        except Exception:
            pass

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
                        self.volume = self.settings_screen.volume
                        try:
                            pygame.mixer.music.set_volume(self.volume)
                        except Exception:
                            pass

                elif self.state == 'PLAY':
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.state = 'MENU'
                        continue
                    # Future gameplay events go here.

            # Draw per state
            if self.state == 'MENU':
                # Draw archer background (static)
                self.screen.blit(self.menu_bg, (0, 0))
                self.menu.draw(skip_clear=True)
            elif self.state == 'SETTINGS':
                self.settings_screen.draw(bg_color=COLOR_BG)
            elif self.state == 'PLAY':
                self.screen.fill('black')
                self.board.run()

            pygame.display.update()
            self.clock.tick(FPS)


if __name__ == "__main__":
    Game()