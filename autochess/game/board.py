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
        # round state helpers
        self.current_round = 1
        self._planning_snapshot = None  # stores unit layout and purchases for retry
        self._enemy_snapshot = None  # stores enemy layout before combat to carry forward

        # Gold tracking
        self.gold = 10  # Starting gold

        # Note: no initial user (blue) units are spawned.
        # Players will place units manually via the shop using spawn_blue_unit.

        # team2
        Unit(groups=[self.all_sprites, self.units],
             pos=(1000, 300),
             name='warrior',
             team='red')
        Unit(groups=[self.all_sprites, self.units],
             pos=(900, 300),
             name='warrior',
             team='red')
        Unit(groups=[self.all_sprites, self.units],
             pos=(800, 300),
             name='warrior',
             team='red')

        Unit(groups=[self.all_sprites, self.units],
             pos=(1100, 200),
             name='lancer',
             team='red')

        Unit(groups=[self.all_sprites, self.units],
             pos=(1000, 200),
             name='monk',
             team='red')

        Unit(groups=[self.all_sprites, self.units],
             pos=(1100, 200),
             name='archer',
             team='red')

        self.hex_center_pos = hex_center

        # Draw hex grid behind other sprites
        self.hex_manager = HexGridManager(
            cols=9,
            rows=6,
            center_pos=self.hex_center_pos,
            group=self.all_sprites,
            units=self.units,
            layer=Layer['Positions']
        )
        self.setup()
        # store initial positions/specs for reset (blue team)
        self._initial_positions = {u: (u.rect.centerx, u.rect.centery) for u in self.units}
        self._blue_initial_specs = [
            {
                'name': u.name,
                'pos': (u.rect.centerx, u.rect.centery)
            }
            for u in self.units if getattr(u, 'team', None) == 'blue'
        ]
        # current round baseline for blue units, updated each planning snapshot
        self._blue_round_base = list(self._blue_initial_specs)
        # baseline enemy list (red team) captured from initial board
        self._enemy_round_base = [
            {
                'name': u.name,
                'pos': (u.rect.centerx, u.rect.centery)
            }
            for u in self.units if getattr(u, 'team', None) == 'red'
        ]

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
                    pixelsize_two = 256 if file_name == 'Tree1' or file_name == 'Tree2' else 192
                    surfs = import_img_two_diff_sizes(f'files/tiles/{file_name}.png', 192, pixelsize_two)
                    k = randrange(len(surfs)) if surfs else 0
                    surfs = surfs[k:] + surfs[:k]
                    w = surfs[0].get_width()
                    h = surfs[0].get_height()

                    base_x = x * tile_w
                    base_y = y * tile_h

                    offset_x = (w - tile_w) // 2
                    offset_y = h - tile_h

                    Animate(surfs, (base_x - offset_x, base_y - offset_y), self.all_sprites, Layer[layer])

            if layer == 'Rock':
                tree_layer = tmx_data.get_layer_by_name(layer)
                for x, y, _ in tree_layer.tiles():
                    file_name = choice(
                        [f for f in ['Water Rocks_01', 'Water Rocks_02', 'Water Rocks_03', 'Water Rocks_04']])
                    surfs = import_img(f'files/tiles/{file_name}.png', 64)
                    k = randrange(len(surfs)) if surfs else 0
                    surfs = surfs[k:] + surfs[:k]

                    Animate(surfs, (x * tile_w, y * tile_h), self.all_sprites, Layer[layer])

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

                    Animate(surfs, (base_x - offset_x, base_y - offset_y), self.all_sprites, Layer[layer])

    def run(self):
        # ensure occupancy is initialized once grid generated
        if not getattr(self, '_occ_init_done', False) and getattr(self.hex_manager, 'generated', False):
            self.hex_manager.initialize_occupancy()
            self._occ_init_done = True
        self.hex_manager.update()
        self.all_sprites.custom_draw()
        self.all_sprites.update()

    # --- Round helpers ---
    def snapshot_planning_layout(self):
        """Save current unit layout and placeholder purchases for retry."""
        self._planning_snapshot = {
            'positions': {u: (u.rect.centerx, u.rect.centery) for u in self.units if u.alive},
            # shop placeholders:
            'purchases': []  # TODO: fill with buy data when shop is implemented
        }
        # Update blue round baseline so post-win reset reflects current roster
        self._blue_round_base = [
            {'name': u.name, 'pos': (u.rect.centerx, u.rect.centery)}
            for u in self.units if getattr(u, 'team', None) == 'blue'
        ]

    def snapshot_enemy_layout(self):
        """Save current enemy configuration to carry forward to next round."""
        self._enemy_snapshot = [
            {'name': u.name, 'pos': (u.rect.centerx, u.rect.centery)}
            for u in self.units if getattr(u, 'team', None) == 'red'
        ]

    def rebuild_enemies_from_snapshot(self, include_extras=False, round_num: int = 1):
        """Recreate enemies strictly from the latest snapshot.
        Optionally include per-round extras. Used on loss to ensure enemies return
        to their planning positions instead of death positions.
        """
        base = self._enemy_snapshot if self._enemy_snapshot is not None else self._enemy_round_base
        # remove all current red units
        for u in list(self.units):
            if getattr(u, 'team', None) == 'red':
                u.kill()
        recreated = []
        # recreate snapshot enemies at their center positions
        for spec in base:
            new_u = Unit(groups=[self.all_sprites, self.units], pos=spec['pos'], name=spec['name'], team='red')
            new_u.rect.center = spec['pos']
            new_u.sync_pos_from_rect()
            new_u.hitbox = new_u.rect.copy().inflate(-new_u.rect.width * 0.7, -new_u.rect.height * 0.7)
            self._reset_unit_state(new_u)
            recreated.append({'name': spec['name'], 'pos': spec['pos']})

        if include_extras:
            extra_count = max(0, round_num - 1)
            for i in range(extra_count):
                pos = (1100 - i * 60, 220 + (i % 2) * 80)
                new_u = Unit(groups=[self.all_sprites, self.units], pos=pos, name='warrior', team='red')
                new_u.rect.center = pos
                new_u.sync_pos_from_rect()
                new_u.hitbox = new_u.rect.copy().inflate(-new_u.rect.width * 0.7, -new_u.rect.height * 0.7)
                self._reset_unit_state(new_u)
                recreated.append({'name': 'warrior', 'pos': pos})

        self._enemy_round_base = recreated
        self.hex_manager.initialize_occupancy()

    def restore_planning_layout(self):
        """Restore unit positions to last snapshot (used on loss retry)."""
        if not self._planning_snapshot:
            return
        for u, pos in self._planning_snapshot.get('positions', {}).items():
            if u.alive:
                u.rect.center = pos
                u.sync_pos_from_rect()
                u.hitbox = u.rect.copy().inflate(-u.rect.width * 0.7, -u.rect.height * 0.7)
                self._reset_unit_state(u)

    def reset_units_to_initial(self):
        """Rebuild player (blue) units to the latest planning baseline for the next round."""
        # remove all current blue units
        for u in list(self.units):
            if getattr(u, 'team', None) == 'blue':
                u.kill()
        # recreate from round baseline
        for spec in self._blue_round_base:
            new_u = Unit(groups=[self.all_sprites, self.units], pos=spec['pos'], name=spec['name'], team='blue')
            new_u.rect.center = spec['pos']
            new_u.sync_pos_from_rect()
            new_u.hitbox = new_u.rect.copy().inflate(-new_u.rect.width * 0.7, -new_u.rect.height * 0.7)
            self._reset_unit_state(new_u)
        # refresh occupancy after rebuild
        self.hex_manager.initialize_occupancy()

    def add_enemies_for_round(self, round_num: int):
        """Rebuild enemies from last snapshot/base and add extras for scaling."""
        # choose snapshot if available, else baseline
        base = self._enemy_snapshot if self._enemy_snapshot is not None else self._enemy_round_base
        # remove all current red units
        for u in list(self.units):
            if getattr(u, 'team', None) == 'red':
                u.kill()
        # recreate base enemies
        recreated = []
        for spec in base:
            new_u = Unit(groups=[self.all_sprites, self.units], pos=spec['pos'], name=spec['name'], team='red')
            # Treat stored position as center, not topleft
            new_u.rect.center = spec['pos']
            new_u.sync_pos_from_rect()
            new_u.hitbox = new_u.rect.copy().inflate(-new_u.rect.width * 0.7, -new_u.rect.height * 0.7)
            self._reset_unit_state(new_u)
            recreated.append({'name': spec['name'], 'pos': spec['pos']})
        # add extras based on round number
        extra_count = max(0, round_num - 1)
        for i in range(extra_count):
            pos = (1100 - i * 60, 220 + (i % 2) * 80)
            new_u = Unit(groups=[self.all_sprites, self.units], pos=pos, name='warrior', team='red')
            # Center-based placement for consistency
            new_u.rect.center = pos
            new_u.sync_pos_from_rect()
            new_u.hitbox = new_u.rect.copy().inflate(-new_u.rect.width * 0.7, -new_u.rect.height * 0.7)
            self._reset_unit_state(new_u)
            recreated.append({'name': 'warrior', 'pos': pos})
        # update base for next round progression
        self._enemy_round_base = recreated
        # refresh occupancy after enemies
        self.hex_manager.initialize_occupancy()

    def team_alive_counts(self):
        blue = sum(1 for u in self.units if getattr(u, 'team', None) == 'blue' and u.alive)
        red = sum(1 for u in self.units if getattr(u, 'team', None) == 'red' and u.alive)
        return blue, red

    def _reset_unit_state(self, u):
        """Clear combat/animation flags and cooldowns to prevent freeze."""
        u.status = 'Idle'
        u.attack_cooldown = 0
        u.heal_cooldown = 0
        u.is_attacking = False
        u.is_healing = False
        u.pending_shot = False
        u.shot_target = None
        u.shot_delay = 0
        u.pending_heal = False
        u.heal_target = None
        u.heal_action_delay = 0
        u.target = None

    def spawn_blue_unit(self, name: str, pos: tuple[int, int]):
        """Create a new blue unit and place it on the closest free hex.
        Important: Do not add the unit to any group until a free hex is found,
        so it never appears under the shop overlay.
        """
        # Determine the closest free hex to the click position
        free_hexes = [hx for hx in self.hex_manager.hexes if self.hex_manager.is_hex_free(hx)]
        if not free_hexes:
            return None
        chosen_hex = min(
            free_hexes,
            key=lambda hh: (hh.rect.centerx - pos[0]) ** 2 + (hh.rect.centery - pos[1]) ** 2
        )

        # Create the unit only now, once we know we can place it
        u = Unit(groups=[self.all_sprites, self.units], pos=chosen_hex.rect.center, name=name, team='blue')
        u.rect.center = chosen_hex.rect.center
        u.sync_pos_from_rect()
        u.hitbox = u.rect.copy().inflate(-u.rect.width * 0.7, -u.rect.height * 0.7)
        self._reset_unit_state(u)

        # Assign to occupancy map for that hex (guaranteed free)
        self.hex_manager.assign_unit_to_hex(u, chosen_hex)
        return u


class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surf = pygame.display.get_surface()

    def _draw_hp_bar(self, sprite):
        """Rysuje pasek HP nad daną jednostką."""
        if not (hasattr(sprite, 'hp') and hasattr(sprite, 'max_hp') and getattr(sprite, 'alive', True)):
            return

        max_hp = max(1, sprite.max_hp)
        ratio = max(0, min(sprite.hp / max_hp, 1))

        # Szerokość dopasowana do jednostki (lekko mniejsza niż sprite)
        base_width = sprite.rect.width
        bar_width = int(base_width * 0.9)
        bar_width = max(30, min(bar_width, 80))
        bar_height = 5

        bar_x = sprite.rect.centerx - bar_width // 2
        # Pasek przesunięty wyżej względem sprite'a (top - 40)
        bar_y = sprite.rect.top + 40

        bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)

        # Kolor wypełnienia zależny od drużyny i poziomu HP
        if hasattr(sprite, 'team') and sprite.team == 'red':
            # AI – czerwony pasek, od jasnego do ciemnego odcienia w zależności od HP
            if ratio > 0.5:
                fill_color = (220, 60, 60)
            elif ratio > 0.2:
                fill_color = (200, 40, 40)
            else:
                fill_color = (150, 20, 20)
        else:
            # Gracz / inne – niebieski pasek, jaśniejszy przy wysokim HP
            if ratio > 0.5:
                fill_color = (50, 150, 255)
            elif ratio > 0.2:
                fill_color = (40, 110, 220)
            else:
                fill_color = (20, 70, 150)

        # Tło (ciemne) + wypełnienie
        pygame.draw.rect(self.display_surf, (20, 20, 20), bg_rect)

        fg_width = int(bar_width * ratio)
        if fg_width > 0:
            fg_rect = pygame.Rect(bar_x, bar_y, fg_width, bar_height)
            pygame.draw.rect(self.display_surf, fill_color, fg_rect)

        # Wspólna, cienka czarna ramka dla wszystkich jednostek
        pygame.draw.rect(self.display_surf, (0, 0, 0), bg_rect, 1)

    def custom_draw(self):
        # Najpierw rysujemy wszystkie sprite'y warstwami
        for layer in Layer.values():
            for sprite in self.sprites():
                if layer == sprite.z:
                    self.display_surf.blit(sprite.image, sprite.rect)
                    # Debug hitboxów (opcjonalnie):
                    # if layer == Layer['Units']:
                    #     hitbox_surf = pygame.Surface((sprite.hitbox.width, sprite.hitbox.height))
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

        # Na końcu osobno rysujemy paski HP dla jednostek, żeby były na wierzchu
        for sprite in self.sprites():
            if sprite.z == Layer['Units']:
                self._draw_hp_bar(sprite)
