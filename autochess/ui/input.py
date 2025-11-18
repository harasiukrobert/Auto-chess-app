import pygame
from autochess.utils.config import *
from config.setting import *


class Positions(pygame.sprite.Sprite):
    all_positions = pygame.sprite.Group()

    def __init__(self, surf, pos, groups, units, z=Layer['Positions']):
        super().__init__(groups, Positions.all_positions)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)
        self.z = z
        self.image.set_alpha(0)
        self.hitbox = self.rect.copy().inflate(-self.rect.width * 0.5, -self.rect.height * 0.5)

        self.units = units
        self.left_pressed = False

    def collision(self):
        mouse_pos = pygame.mouse.get_pos()
        press = pygame.mouse.get_pressed()[0]

        if self.left_pressed == False:
            for sprite in self.units:
                if sprite.hitbox.collidepoint(mouse_pos) and press:
                    self.left_pressed = True
        else:
            if not press:
                self.left_pressed = False

        alpha = 125 if self.left_pressed else 0
        for sprite in Positions.all_positions:
            sprite.image.set_alpha(alpha)

        for sprite in self.units:
            if self.left_pressed:
                sprite.rect=sprite.image.get_rect(center=mouse_pos)
                sprite.hitbox = sprite.rect.copy().inflate(-sprite.rect.width * 0.7, -sprite.rect.height * 0.7)

    def set_the_center(self):
        for sprite in self.units:
            for pos in Positions.all_positions:
                if sprite.hitbox.colliderect(pos.hitbox):
                    if not self.left_pressed:
                        sprite.rect = sprite.image.get_rect(center=pos.rect.center)
                        sprite.hitbox = sprite.rect.copy().inflate(-sprite.rect.width * 0.7, -sprite.rect.height * 0.7)


    def update(self):
        self.set_the_center()
        self.collision()