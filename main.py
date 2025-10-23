import pygame,sys
from setting import SCREEN_WIDTH, SCREEN_HEIGHT
from map import Level


class Game():
    def __init__(self):
        pygame.init()
        self.screen=pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
        pygame.display.set_caption('Podróba TFT')
        self.level = Level()
        self.startgame()

    def startgame(self):
        while True:
            self.event()
            self.refresh_screen()

    def event(self):
        for events in pygame.event.get():
            if events.type==pygame.QUIT:
                sys.exit(0)
            if events.type==pygame.KEYDOWN and events.key==pygame.K_ESCAPE:
                sys.exit(0)

    def refresh_screen(self):
        self.screen.fill('black')
        pygame.time.Clock().tick(120)
        self.level.run()
        pygame.display.update()

Game()