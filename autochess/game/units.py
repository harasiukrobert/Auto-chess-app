import math
import os

from autochess.utils.config import *
from config.setting import *


class HealEffect(pygame.sprite.Sprite):
    """Efekt wizualny leczenia"""

    def __init__(self, groups, target, team, z=Layer['Units']):
        super().__init__(groups)
        self.target = target
        self.z = z

        path = f'files/units/{team}_units/monk/Heal_effect.png'

        self.frames = []
        if os.path.exists(path):
            self.frames = import_img(path, 192)

        self.index = 0
        self.anim_speed = 0.15

        if self.frames:
            self.image = self.frames[0]
        else:
            self.image = pygame.Surface((64, 64), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (50, 255, 50, 150), (32, 32), 30)

        self.rect = self.image.get_rect(center=target.rect.center)

    def update(self):
        if self.target and self.target.alive:
            self.rect.center = self.target.rect.center

        if self.frames:
            self.index += self.anim_speed

            if self.index >= len(self.frames):
                self.kill()
                return

            self.image = self.frames[int(self.index)]
        else:
            self.index += 0.1
            if self.index >= 10:
                self.kill()


class Projectile(pygame.sprite.Sprite):
    """Klasa dla pocisków (strzały, magiczne pociski itp.)"""

    def __init__(self, groups, start_pos, target, speed=8, z=Layer['Units']):
        super().__init__(groups)
        self.groups_ref = groups

        self.pos = pygame.math.Vector2(start_pos)
        self.target = target
        self.target_pos = pygame.math.Vector2(target.rect.center)
        self.speed = speed
        self.z = z

        self.direction = self.target_pos - self.pos
        if self.direction.length() > 0:
            self.direction = self.direction.normalize()

        self.angle = math.degrees(math.atan2(-self.direction.y, self.direction.x))

        self.original_image = self.create_arrow_image()
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=start_pos)

        self.hit = False
        self.damage = 1

    def create_arrow_image(self):
        """Tworzy obrazek strzały"""
        surf = pygame.Surface((20, 6), pygame.SRCALPHA)
        pygame.draw.rect(surf, (139, 69, 19), (0, 2, 14, 2))
        pygame.draw.polygon(surf, (169, 169, 169), [(14, 0), (20, 3), (14, 6)])
        pygame.draw.polygon(surf, (200, 50, 50), [(0, 0), (4, 3), (0, 6)])
        return surf

    def update(self):
        if self.hit:
            return

        if not self.target.alive:
            self.kill()
            return

        self.target_pos = pygame.math.Vector2(self.target.rect.center)

        direction_to_target = self.target_pos - self.pos
        distance = direction_to_target.length()

        if distance > 0:
            self.direction = direction_to_target.normalize()
            self.angle = math.degrees(math.atan2(-self.direction.y, self.direction.x))
            self.image = pygame.transform.rotate(self.original_image, self.angle)

        self.pos += self.direction * self.speed
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

        if distance < 15:
            self.hit = True
            self.target.take_damage(self.damage)
            self.kill()


class Unit(pygame.sprite.Sprite):
    """Klasa bazowa dla wszystkich jednostek"""

    def __init__(self, groups, pos, name, team, z=Layer['Units']):
        super().__init__(groups)
        self.groups_ref = groups
        self.alive = True

        stats = UNIT_STATS.get(name, UNIT_STATS['warrior'])

        self.max_hp = stats['hp']
        self.hp = stats['hp']
        self.damage = stats['damage']
        self.attack_range = stats['attack_range']
        self.attack_delay = stats['attack_delay']
        self.speed = stats['speed']
        self.is_ranged = stats.get('is_ranged', False)
        self.projectile_speed = stats.get('projectile_speed', 8)

        self.is_healer = stats.get('is_healer', False)
        self.heal_amount = stats.get('heal_amount', 1)
        self.heal_range = stats.get('heal_range', 100)
        self.heal_delay = stats.get('heal_delay', 90)
        self.heal_cooldown = 0

        self.anim_speed = stats.get('anim_speed', 0.10)
        self.attack_anim_speed = stats.get('attack_anim_speed', 0.10)

        self.status = 'Idle'
        self.name = name
        self.team = team
        self.index = 0

        self.facing_right = True
        self.direction = 'side'

        self.target = None
        self.attack_cooldown = 0

        self.is_attacking = False
        self.is_healing = False

        self.pending_shot = False
        self.shot_target = None
        self.shot_delay = 0

        self.pending_heal = False
        self.heal_target = None
        self.heal_action_delay = 0

        self.pos = pygame.math.Vector2(pos)

        self.import_assets()

        self.image = self.animations[self.status][self.index]
        self.rect = self.image.get_rect(topleft=pos)
        self.z = z
        self.hitbox = self.rect.copy().inflate(-self.rect.width * 0.7, -self.rect.height * 0.7)

    def import_assets(self):
        """Importuj animacje jednostki"""
        self.animations = {
            'Idle': [],
            'Run': [],
            'Attack': [],
            'Attack_down': [],
            'Attack_up': [],
            'Attack_downright': [],
            'Attack_upright': [],
            'Heal': [],
        }

        for animation in self.animations.keys():
            pixle_size = 320 if self.name == 'lancer' else 192
            path = f'files/units/{self.team}_units/{self.name}/{animation}.png'
            if os.path.exists(path):
                self.animations[animation] = import_img(path, pixle_size)

    def get_distance_to(self, other):
        """Oblicz dystans do innej jednostki"""
        return math.hypot(
            self.rect.centerx - other.rect.centerx,
            self.rect.centery - other.rect.centery
        )

    def find_nearest_enemy(self, all_units):
        """Znajdź najbliższego wroga"""
        nearest = None
        min_dist = float('inf')

        for unit in all_units:
            if not isinstance(unit, Unit):
                continue

            if unit.team != self.team and unit.alive:
                dist = self.get_distance_to(unit)
                if dist < min_dist:
                    min_dist = dist
                    nearest = unit

        return nearest

    def find_wounded_ally(self, all_units):
        """Znajdź najbliższego rannego sojusznika"""
        nearest = None
        min_dist = float('inf')

        for unit in all_units:
            if not isinstance(unit, Unit):
                continue

            if unit.team == self.team and unit.alive and unit != self:
                if unit.hp < unit.max_hp:
                    dist = self.get_distance_to(unit)
                    if dist < min_dist:
                        min_dist = dist
                        nearest = unit

        return nearest

    def update_facing_direction(self, dx, dy):
        """Aktualizuj kierunek patrzenia na podstawie ruchu"""
        if abs(dx) > 0.1:
            self.facing_right = dx > 0

        angle = math.degrees(math.atan2(dy, abs(dx)))

        if angle < -70:
            self.direction = 'up'
        elif angle < -35:
            self.direction = 'up_side'
        elif angle < 35:
            self.direction = 'side'
        elif angle < 70:
            self.direction = 'down_side'
        else:
            self.direction = 'down'

    def get_attack_animation(self):
        """Pobierz odpowiednią animację ataku na podstawie kierunku"""
        if self.name == 'lancer':
            if self.direction == 'up' and self.animations['Attack_up']:
                return 'Attack_up'
            elif self.direction == 'down' and self.animations['Attack_down']:
                return 'Attack_down'
            elif self.direction == 'up_side' and self.animations['Attack_upright']:
                return 'Attack_upright'
            elif self.direction == 'down_side' and self.animations['Attack_downright']:
                return 'Attack_downright'
            elif self.animations['Attack']:
                return 'Attack'
            elif self.animations['Attack_downright']:
                return 'Attack_downright'
            else:
                return 'Attack_up'

        if self.direction == 'up' and self.animations['Attack_up']:
            return 'Attack_up'
        elif self.direction == 'down' and self.animations['Attack_down']:
            return 'Attack_down'
        elif self.animations['Attack']:
            return 'Attack'

        return 'Idle'

    def move_towards(self, target):
        """Ruszaj w kierunku celu"""
        if target is None:
            return

        dx = target.rect.centerx - self.rect.centerx
        dy = target.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)

        if dist > 0:
            self.update_facing_direction(dx, dy)

            move_dx = dx / dist * self.speed
            move_dy = dy / dist * self.speed

            self.pos.x += move_dx
            self.pos.y += move_dy

            self.rect.center = (int(self.pos.x), int(self.pos.y))
            self.hitbox.center = self.rect.center

    def shoot_projectile(self, target):
        """Wystrzel pocisk w kierunku celu"""
        start_pos = self.rect.center

        # Add projectile only to visual group (exclude units group to avoid drag logic)
        projectile = Projectile(
            groups=[self.groups_ref[0]],
            start_pos=start_pos,
            target=target,
            speed=self.projectile_speed,
            z=Layer['Units']
        )
        projectile.damage = self.damage

    def spawn_heal_effect(self, target):
        """Stwórz efekt leczenia na celu"""
        # Add heal effect only to visual group (exclude units group)
        HealEffect(
            groups=[self.groups_ref[0]],
            target=target,
            team=self.team,
            z=Layer['Units']
        )

    def attack(self, target):
        """Zaatakuj cel"""
        if self.is_attacking or self.is_healing or self.attack_cooldown > 0:
            return

        dx = target.rect.centerx - self.rect.centerx
        dy = target.rect.centery - self.rect.centery
        self.update_facing_direction(dx, dy)

        if self.is_ranged:
            self.pending_shot = True
            self.shot_target = target
            attack_anim = self.get_attack_animation()
            anim_length = len(self.animations[attack_anim])
            self.shot_delay = int(anim_length * 0.7 / self.attack_anim_speed)
        elif self.name == 'lancer':
            self.pending_shot = True
            self.shot_target = target
            attack_anim = self.get_attack_animation()
            anim_length = len(self.animations[attack_anim])
            self.shot_delay = int(anim_length * 0.8 / self.attack_anim_speed)
        else:
            target.take_damage(self.damage)

        self.attack_cooldown = self.attack_delay
        self.status = self.get_attack_animation()
        self.index = 0
        self.is_attacking = True

    def heal(self, target):
        """Ulecz sojusznika"""
        if self.is_attacking or self.is_healing or self.heal_cooldown > 0:
            return

        dx = target.rect.centerx - self.rect.centerx
        dy = target.rect.centery - self.rect.centery
        self.update_facing_direction(dx, dy)

        self.pending_heal = True
        self.heal_target = target

        if self.animations['Heal']:
            anim_length = len(self.animations['Heal'])
            self.heal_action_delay = int(anim_length * 0.5 / self.anim_speed)
            self.status = 'Heal'
        else:
            target.receive_heal(self.heal_amount)
            self.spawn_heal_effect(target)
            self.pending_heal = False

        self.heal_cooldown = self.heal_delay
        self.index = 0
        self.is_healing = True

    def receive_heal(self, amount):
        """Otrzymaj leczenie"""
        self.hp = min(self.hp + amount, self.max_hp)

    def take_damage(self, damage):
        """Otrzymaj obrażenia"""
        self.hp -= damage
        if self.hp <= 0:
            self.die()

    def die(self):
        """Jednostka ginie"""
        self.alive = False
        self.kill()

    def sync_pos_from_rect(self):
        """Zsynchronizuj pozycję z rect"""
        self.pos.x = self.rect.centerx
        self.pos.y = self.rect.centery

    def animate(self):
        """Animuj jednostkę"""
        if 'Attack' in self.status:
            current_speed = self.attack_anim_speed
        else:
            current_speed = self.anim_speed

        self.index += current_speed

        current_anim = self.animations[self.status]
        if len(current_anim) == 0:
            current_anim = self.animations['Idle']
            if len(current_anim) == 0:
                return

        if self.index >= len(current_anim):
            self.index = 0
            if 'Attack' in self.status:
                self.status = 'Idle'
                self.is_attacking = False
            if self.status == 'Heal':
                self.status = 'Idle'
                self.is_healing = False

        frame = current_anim[int(self.index)]

        if not self.facing_right:
            frame = pygame.transform.flip(frame, True, False)

        self.image = frame

        if self.pending_shot:
            self.shot_delay -= 1
            if self.shot_delay <= 0:
                if self.shot_target and self.shot_target.alive:
                    if self.is_ranged:
                        self.shoot_projectile(self.shot_target)
                    else:
                        self.shot_target.take_damage(self.damage)
                self.pending_shot = False
                self.shot_target = None

        if self.pending_heal:
            self.heal_action_delay -= 1
            if self.heal_action_delay <= 0:
                if self.heal_target and self.heal_target.alive:
                    old_hp = self.heal_target.hp
                    self.heal_target.hp = min(self.heal_target.hp + self.heal_amount, self.heal_target.max_hp)
                    print(
                        f"[HEAL] {self.heal_target.team} {self.heal_target.name}: {old_hp} HP -> {self.heal_target.hp} HP")
                    self.spawn_heal_effect(self.heal_target)
                self.pending_heal = False
                self.heal_target = None

    def combat_update(self, all_units):
        """Aktualizacja logiki walki"""
        if not self.alive:
            return

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        if self.heal_cooldown > 0:
            self.heal_cooldown -= 1

        if self.is_healer:
            wounded_ally = self.find_wounded_ally(all_units)

            if wounded_ally:
                dist = self.get_distance_to(wounded_ally)

                if dist <= self.heal_range:
                    self.heal(wounded_ally)
                else:
                    if not self.is_healing:
                        self.move_towards(wounded_ally)
                        if self.animations['Run']:
                            self.status = 'Run'
                        else:
                            self.status = 'Idle'
            else:
                if not self.is_healing:
                    self.status = 'Idle'
            return

        self.target = self.find_nearest_enemy(all_units)

        if self.target:
            dist = self.get_distance_to(self.target)

            if dist <= self.attack_range:
                self.attack(self.target)
            else:
                if not self.is_attacking:
                    self.move_towards(self.target)
                    if self.animations['Run']:
                        self.status = 'Run'
                    else:
                        self.status = 'Idle'
        else:
            if not self.is_attacking:
                self.status = 'Idle'

    def update(self):
        """Główna aktualizacja jednostki"""
        self.animate()