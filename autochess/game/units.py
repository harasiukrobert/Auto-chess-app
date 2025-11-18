import os
from autochess.utils.config import *
from config.setting import *


class Unit(pygame.sprite.Sprite):
    def __init__(self, groups, pos, name, team, z=Layer['Units']):
        super().__init__(groups)
        #graphic

        self.alive=True

        #animation
        self.status='Idle'
        self.name = name
        self.team = team
        self.index=0

        self.import_assets()

        #image setup
        self.image=self.animations[self.status][self.index]
        self.rect=self.image.get_rect(topleft=pos)
        self.z=z
        self.hitbox=self.rect.copy().inflate(-self.rect.width * 0.7, -self.rect.height * 0.7)


    def import_assets(self):
        self.animations = {'Idle': [],
                           'Run': [],
                           'Attack': [],
                           'Attack_down': [],
                           'Attack_up': [],}

        for animation in self.animations.keys():
            path = f'files/units/{self.team}_units/{self.name}/{animation}.png'
            if os.path.exists(path):
                self.animations[animation] = import_img(path, 192)

    def animate(self):
        self.index += 0.10
        if self.index >= len(self.animations[self.status]):
            self.index = 0
        self.image = self.animations[self.status][int(self.index)]

    def update(self):
        self.animate()
