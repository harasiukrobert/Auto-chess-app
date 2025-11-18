from random import choice, randrange

from pytmx.util_pygame import load_pygame

from autochess.utils.config import *
from config.setting import *

from .hex_board import HexGridManager
from .sprites import Animate, Generic
from .units import Unit

class Board:
    def __init__(self, hex_center=(640, 360)):
        self.all_sprites = CameraGroup()
        self.units = pygame.sprite.Group()

        self.unit = Unit(groups = [self.all_sprites, self.units],
                         pos = (500,500),
                         name = 'warrior',
                         team= 'blue')

        self.hex_center_pos = hex_center

        # Draw hex grid behind other sprites
        self.hex_manager = HexGridManager(
            cols=9,
            rows=6,
            center_pos=self.hex_center_pos,
            group=self.all_sprites,
            units = self.units,
            layer=Layer['Positions']
        )
        self.setup()


    def setup(self):
        self.hex_manager.generate()

        tmx_data = load_pygame('files/map_tiled/map.tmx')
        tile_w, tile_h = tmx_data.tilewidth, tmx_data.tileheight

        for layer in tmx_data.layernames:
            if layer == 'Area':
                for x, y, surf in tmx_data.get_layer_by_name(layer).tiles():
                    Generic(surf, (x * tile_w, y * tile_h), self.all_sprites, Layer[layer])

            if layer in ('Decoration', 'Decoration2', 'Background2', 'Background'):
                for x, y, surf in tmx_data.get_layer_by_name(layer).tiles():
                    Generic(surf, (x * tile_w, y * tile_h), self.all_sprites, Layer[layer])

            if layer == 'ObjectsDecorations':
                for obj in tmx_data.get_layer_by_name(layer):
                    Generic(obj.image, (obj.x, obj.y), self.all_sprites, Layer[layer])

            if layer == 'Sheep':
                for x, y, _ in tmx_data.get_layer_by_name(layer).tiles():
                    surfs = import_img('files/tiles/Sheep_Idle.png', 128)
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
                    surfs = import_img_two_diff_sizes(f'files/tiles/{file_name}.png', 192, pixelsize_two)
                    k = randrange(len(surfs)) if surfs else 0
                    surfs = surfs[k:] + surfs[:k]
                    w = surfs[0].get_width()
                    h = surfs[0].get_height()

                    base_x = x * tile_w
                    base_y = y * tile_h

                    offset_x = (w - tile_w) // 2
                    offset_y = h - tile_h

                    Animate(surfs,(base_x - offset_x, base_y - offset_y), self.all_sprites, Layer[layer])

            if layer == 'Rock':
                tree_layer = tmx_data.get_layer_by_name(layer)
                for x, y, _ in tree_layer.tiles():
                    file_name = choice([f for f in ['Water Rocks_01', 'Water Rocks_02', 'Water Rocks_03', 'Water Rocks_04']])
                    surfs = import_img(f'files/tiles/{file_name}.png', 64)
                    k = randrange(len(surfs)) if surfs else 0
                    surfs = surfs[k:] + surfs[:k]

                    Animate(surfs,(x * tile_w, y * tile_h), self.all_sprites, Layer[layer])

            if layer == 'Bushes':
                tree_layer = tmx_data.get_layer_by_name(layer)
                for x, y, _ in tree_layer.tiles():
                    file_name = choice([f for f in ['Bushe1', 'Bushe2', 'Bushe3', 'Bushe4']])
                    surfs = import_img(f'files/tiles/{file_name}.png', 128)
                    k = randrange(len(surfs)) if surfs else 0
                    surfs = surfs[k:] + surfs[:k]
                    w = surfs[0].get_width()
                    h = surfs[0].get_height()

                    base_x = x * tile_w
                    base_y = y * tile_h

                    offset_x = (w - tile_w) // 2
                    offset_y = h - tile_h

                    Animate(surfs,(base_x - offset_x, base_y - offset_y), self.all_sprites, Layer[layer])

    def run(self):
        self.hex_manager.update()
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
                    if layer == Layer['Units']:
                        hitbox_surf = pygame.Surface((sprite.hitbox.width, sprite.hitbox.height))
                    #     hitbox_surf.fill('red')
                    #     self.display_surf.blit(hitbox_surf, sprite.hitbox)
                    # if layer == Layer['Positions']:
                    #     hitbox_surf = pygame.Surface((sprite.hitbox.width, sprite.hitbox.height))
                    #     hitbox_surf.fill('blue')
                    #     self.display_surf.blit(hitbox_surf, sprite.hitbox)
                    # if hasattr(sprite, 'hitbox_b'):
                    #     hitbox_b_surf = pygame.Surface((sprite.hitbox_b.width, sprite.hitbox_b.height))
                    #     hitbox_b_surf.fill('blue')
                    #     self.display_surf.blit(hitbox_b_surf, sprite.hitbox_b)