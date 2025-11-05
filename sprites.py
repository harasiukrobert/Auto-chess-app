import pygame
cos

class Generic(pygame.sprite.Sprite):
    def __init__(self,surf,pos,groups,z):
        super().__init__(groups)
        self.image=surf
        self.rect=self.image.get_rect(topleft=pos)
        self.z=z
        # self.hitbox = self.rect.copy().inflate(-self.rect.width * 0.5, -self.rect.height * 0.5)

class Animate(Generic):
    def __init__(self,surfs,pos,groups,z):
        self.surfs=surfs
        self.z=z
        self.index=0
        self.speed= 0.100

        super().__init__(surf=surfs[self.index],
                         pos=pos,
                         groups=groups,
                         z=z)

    def animation(self):
        self.index += self.speed
        if self.index >= len(self.surfs):
            self.index = 0
        self.image = self.surfs[int(self.index)]

    def update(self):
        self.animation()


