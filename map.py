import pygame
from pytmx.util_pygame import load_pygame
from sprites import Generic, Animate
from setting import *
from support import *
from random import choice, randrange

class Level:
    def __init__(self):
        self.all_sprites = CameraGroup()
        self.collision_sprites = pygame.sprite.Group()

        self.setup()

    def setup(self):
        tmx_data = load_pygame('Files/map_tiled/map.tmx')
        tile_w, tile_h = tmx_data.tilewidth, tmx_data.tileheight

        for layer in tmx_data.layernames:
            if layer == 'Area':
                for x, y, surf in tmx_data.get_layer_by_name(layer).tiles():
                    Generic(surf, (x * tile_w, y * tile_h), [self.all_sprites, self.collision_sprites], Layer[layer])

            if layer in ('Decoration', 'Decoration2', 'Background2', 'Background'):
                for x, y, surf in tmx_data.get_layer_by_name(layer).tiles():
                    Generic(surf, (x * tile_w, y * tile_h), self.all_sprites, Layer[layer])

            if layer == 'ObjectsDecorations':
                for obj in tmx_data.get_layer_by_name(layer):
                    Generic(obj.image, (obj.x, obj.y), self.all_sprites, Layer[layer])

            if layer == 'Sheep':
                for x, y, _ in tmx_data.get_layer_by_name(layer).tiles():
                    surfs = import_img('Files/assets/Sheep_Idle.png', 128)
                    k = randrange(len(surfs)) if surfs else 0
                    surfs = surfs[k:] + surfs[:k]
                    w = surfs[0].get_width()
                    h = surfs[0].get_height()

                    base_x = x * tile_w
                    base_y = y * tile_h

                    offset_x = (w - tile_w) // 2
                    offset_y = h - tile_h
                    Animate(surfs, (base_x - offset_x, base_y - offset_y), self.all_sprites, Layer[layer])

            if layer == 'Tree':
                tree_layer = tmx_data.get_layer_by_name(layer)
                for x, y, _ in tree_layer.tiles():
                    file_name = choice([f for f in ['Tree1', 'Tree2', 'Tree3', 'Tree4']])
                    pixelsize_two = 256 if file_name == 'Tree1' or file_name=='Tree2' else 192
                    surfs = import_img_two_diff_sizes(f'Files/assets/{file_name}.png', 192, pixelsize_two)
                    k = randrange(len(surfs)) if surfs else 0
                    surfs = surfs[k:] + surfs[:k]
                    w = surfs[0].get_width()
                    h = surfs[0].get_height()

                    base_x = x * tile_w
                    base_y = y * tile_h

                    offset_x = (w - tile_w) // 2
                    offset_y = h - tile_h

                    Animate(surfs,(base_x - offset_x, base_y - offset_y),self.all_sprites,Layer[layer])

            if layer == 'Rock':
                tree_layer = tmx_data.get_layer_by_name(layer)
                for x, y, _ in tree_layer.tiles():
                    file_name = choice([f for f in ['Water Rocks_01', 'Water Rocks_02', 'Water Rocks_03', 'Water Rocks_04']])
                    surfs = import_img(f'Files/assets/{file_name}.png', 64)
                    k = randrange(len(surfs)) if surfs else 0
                    surfs = surfs[k:] + surfs[:k]

                    Animate(surfs,(x * tile_w, y * tile_h),self.all_sprites,Layer[layer])

    def run(self):
        self.all_sprites.custom_draw()
        self.all_sprites.update()


class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surf = pygame.display.get_surface()

    def custom_draw(self):
        for layer in Layer.values():
            for sprite in self.sprites():
                if layer == sprite.z:
                    self.display_surf.blit(sprite.image, sprite.rect)
                    # Debug hitboxów (opcjonalnie):
                    # hitbox_surf = pygame.Surface((sprite.hitbox.width, sprite.hitbox.height))
                    # hitbox_surf.fill('red')
                    # self.display_surf.blit(hitbox_surf, sprite.hitbox)
                    # if hasattr(sprite, 'hitbox_b'):
                    #     hitbox_b_surf = pygame.Surface((sprite.hitbox_b.width, sprite.hitbox_b.height))
                    #     hitbox_b_surf.fill('blue')
                    #     self.display_surf.blit(hitbox_b_surf, sprite.hitbox_b)