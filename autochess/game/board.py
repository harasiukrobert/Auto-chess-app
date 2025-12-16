import os
from random import choice, randrange

from pytmx.util_pygame import load_pygame

from autochess.utils.config import *
from config.setting import *

from .hex_board import HexGridManager
from .rounds import RoundManager
from .sprites import Animate, Generic
from .units import Unit


class Board:
    def __init__(self, hex_center=(640, 360), allow_enemy_drag: bool = False):
        self.all_sprites = CameraGroup()
        self.units = pygame.sprite.Group()
        # round state helpers
        self.current_round = 1
        self._planning_snapshot = None  # stores unit layout and purchases for retry
        self._enemy_snapshot = None  # stores enemy layout before combat to carry forward
        # Snapshot taken at the START of each planning phase to allow full rollback on loss
        # Includes player gold and complete blue roster (names + positions).
        self._pre_planning_snapshot = None

        # Rounds configuration
        self.rounds = RoundManager(os.path.join('config', 'rounds.json'))

        # Gold tracking (from rounds config)
        self.gold = int(self.rounds.starting_gold)

        self.hex_center_pos = hex_center
        # Config: allow dragging enemy (red) units during planning
        self.allow_enemy_drag = bool(allow_enemy_drag)

        # Draw hex grid behind other sprites based on Round 1
        r1_size = self.rounds.get_board_size(1)
        self.hex_manager = HexGridManager(
            cols=r1_size.get('cols', 9),
            rows=r1_size.get('rows', 6),
            center_pos=self.hex_center_pos,
            group=self.all_sprites,
            units=self.units,
            layer=Layer['Positions'],
            allow_enemy_drag=self.allow_enemy_drag,
        )
        self.setup()
        # initialize round 1 contents (grid + player start + enemies)
        self.apply_round(self.current_round, initial=True)
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
        # baseline enemy list (red team) captured from current round
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

    # --- Round config application ---
    def _apply_board_size(self, cols: int, rows: int):
        # Remove previous hex sprites from group
        if hasattr(self, 'hex_manager') and self.hex_manager and self.hex_manager.hexes:
            for hx in list(self.hex_manager.hexes):
                try:
                    hx.kill()
                except Exception:
                    pass
        # Create new grid manager
        self.hex_manager = HexGridManager(
            cols=cols,
            rows=rows,
            center_pos=self.hex_center_pos,
            group=self.all_sprites,
            units=self.units,
            layer=Layer['Positions'],
            allow_enemy_drag=self.allow_enemy_drag,
        )
        self.hex_manager.generate()

    def set_allow_enemy_drag(self, enabled: bool):
        """Enable or disable dragging enemy (red) units during planning for the current game."""
        self.allow_enemy_drag = bool(enabled)
        # Propagate to current grid manager
        if hasattr(self, 'hex_manager') and self.hex_manager:
            self.hex_manager.allow_enemy_drag = self.allow_enemy_drag

    def _spawn_batch(self, specs, team: str):
        # Spawn exactly one unit per item using explicit hex coordinates (r,c).
        # If a target cell is invalid or occupied, fall back to side-preference placement.
        prefer_top = (team == 'red')
        for item in specs or []:
            name = item.get('name')
            r_exact = item.get('r')
            c_exact = item.get('c')
            u = Unit(groups=[self.all_sprites, self.units], pos=(0, 0), name=name, team=team)
            placed = False
            try:
                if r_exact is not None and c_exact is not None:
                    r_val = int(r_exact)
                    c_val = int(c_exact)
                    target_hex = None
                    for hx in self.hex_manager.hexes:
                        if hx.r == r_val and hx.c == c_val:
                            target_hex = hx
                            break
                    if target_hex and self.hex_manager.is_hex_free(target_hex):
                        placed = self.hex_manager.assign_unit_to_hex(u, target_hex)
            except Exception:
                placed = False
            if not placed:
                placed = self.hex_manager.place_unit_on_free_hex(u, prefer_top=prefer_top)
            if not placed:
                u.kill()

    def apply_round(self, round_num: int, initial: bool = False):
        cfg = self.rounds.get_round(round_num) or {}
        size = self.rounds.get_board_size(round_num)
        # Apply board size
        self._apply_board_size(size.get('cols', 9), size.get('rows', 6))
        # On initial round, clear all units; otherwise keep player units
        if initial:
            for u in list(self.units):
                u.kill()
            # spawn player starting units (round 1 only)
            pstart = self.rounds.get_player_start()
            self._spawn_batch(pstart, team='blue')
        else:
            # ensure all blue units snap to nearest hexes in the new grid
            self.hex_manager.initialize_occupancy()
        # (Re)spawn enemies per config for this round
        for u in list(self.units):
            if getattr(u, 'team', None) == 'red':
                u.kill()
        enemies = self.rounds.get_enemies(round_num)
        self._spawn_batch(enemies, team='red')

    # --- Round helpers ---
    def snapshot_planning_layout(self):
        """Deprecated partial snapshot kept for backward compatibility.
        Previously stored positions keyed by unit objects. No longer used for rollback.
        """
        self._planning_snapshot = {
            'positions': {u: (u.rect.centerx, u.rect.centery) for u in self.units if u.alive},
            'purchases': []
        }

    def save_pre_planning_snapshot(self):
        """Capture gold and full blue roster at the start of planning.
        This snapshot is used to rollback the player's state on a loss,
        effectively refunding all current-round purchases and placements.
        """
        blue_specs = [
            {'name': u.name, 'pos': (u.rect.centerx, u.rect.centery)}
            for u in self.units if getattr(u, 'team', None) == 'blue'
        ]
        self._pre_planning_snapshot = {
            'gold': int(self.gold),
            'blue_specs': blue_specs,
        }

    def finalize_planning_baseline(self):
        """Freeze current blue roster as the baseline carried into next round on win."""
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

    def restore_from_pre_planning_snapshot(self):
        """Fully restore blue roster and gold to the snapshot from planning start."""
        snap = self._pre_planning_snapshot
        if not snap:
            return
        # Restore gold (refund purchases)
        try:
            self.gold = int(snap.get('gold', self.gold))
        except Exception:
            pass
        # Remove all current blue units
        for u in list(self.units):
            if getattr(u, 'team', None) == 'blue':
                u.kill()
        # Recreate blue units from snapshot
        for spec in snap.get('blue_specs', []):
            new_u = Unit(groups=[self.all_sprites, self.units], pos=spec['pos'], name=spec['name'], team='blue')
            new_u.rect.center = spec['pos']
            new_u.sync_pos_from_rect()
            new_u.hitbox = new_u.rect.copy().inflate(-new_u.rect.width * 0.7, -new_u.rect.height * 0.7)
            self._reset_unit_state(new_u)
        # Refresh occupancy after rebuild
        self.hex_manager.initialize_occupancy()

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
        """Deprecated: now driven by rounds config. Kept for compatibility."""
        self.apply_round(round_num, initial=False)

    def respawn_current_round_enemies(self):
        """Respawn enemies strictly from current round config (used on loss)."""
        self.apply_round(self.current_round, initial=False)

    def get_round_reward(self, round_num: int) -> int:
        return self.rounds.get_reward(round_num)

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
