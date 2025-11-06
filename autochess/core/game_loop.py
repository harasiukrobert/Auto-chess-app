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
            # If mixer fails (e.g., no audio device), continue without music
            pass

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('Podróba TFT')

        # State: MENU, PLAY, SETTINGS
        self.state = 'MENU'

        # Music
        self.volume = DEFAULT_VOLUME
        self._load_music(MUSIC_PATH, self.volume)

        # Core objects
        self.board = Board()
        self.clock = pygame.time.Clock()

        # UI
        self.menu = Menu(
            screen=self.screen,
            options=[('Play', 'play'), ('Settings', 'settings'), ('Exit', 'exit')],
            colors={'text': COLOR_TEXT, 'highlight': COLOR_HIGHLIGHT, 'subtle': COLOR_SUBTLE},
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
            pygame.mixer.music.play(-1)  # loop forever
        except Exception:
            # Music file may be missing or mixer isn't initialized; ignore
            pass

    def startgame(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit(0)

                if self.state == 'MENU':
                    # Esc exits from menu
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
                    result = self.settings_screen.handle_event(event)
                    if result == 'changed':
                        self.volume = self.settings_screen.volume
                        try:
                            pygame.mixer.music.set_volume(self.volume)
                        except Exception:
                            pass

                elif self.state == 'PLAY':
                    # Esc returns to MENU (no hints shown in PLAY)
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.state = 'MENU'
                        continue
                    # Game-specific events can go here

            # Draw per state
            if self.state == 'MENU':
                self.menu.draw(bg_color=COLOR_BG)

            elif self.state == 'SETTINGS':
                self.settings_screen.draw(bg_color=COLOR_BG)

            elif self.state == 'PLAY':
                self.screen.fill('black')
                self.board.run()

            pygame.display.update()
            self.clock.tick(FPS)


if __name__ == "__main__":
    Game()