# screen
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

# map settings
title_size = 64

# draw order for sprites
Layer = {
    'Background': 0,
    'Background2': 1,
    'ObjectsDecorations': 2,
    'Decoration2': 3,
    'Decoration': 4,
    'Area': 5,
    'Board': 6,
    'Sheep': 7,
    'Tree': 8,
    'Rock': 9,
    'Bushes': 10,
    'Positions': 11,
    'Units': 12,
}

# game loop settings
FPS = 120

# audio / UI settings
# default menu volume — changed to 50% so sliders start at a sensible level
DEFAULT_VOLUME = 0.50
# Point this to your menu music file (wav or ogg).Put menu.wav at files/audio/menu.wav
MUSIC_PATH = 'files/audio/menu.wav'

# simple UI colors (used as sensible defaults)
COLOR_BG = (10, 10, 10)
COLOR_TEXT = (230, 230, 230)
# main blue accent used across UI
COLOR_HIGHLIGHT = (80, 125, 170)
COLOR_SUBTLE = (130, 130, 130)

UNIT_STATS = {
    'warrior': {
        'hp': 25,
        'damage': 2,
        'attack_range': 80,
        'attack_delay': 80,
        'speed': 2,
        'is_ranged': False,
        'anim_speed': 0.10,
        'attack_anim_speed': 0.10,
    },
    'archer': {
        'hp': 15,
        'damage': 3,
        'attack_range': 300,
        'attack_delay': 120,
        'speed': 1.5,
        'is_ranged': True,
        'projectile_speed': 8,
        'anim_speed': 0.10,
        'attack_anim_speed': 0.10,
    },
    'lancer': {
        'hp': 20,
        'damage': 4,
        'attack_range': 120,
        'attack_delay': 100,
        'speed': 1.5,
        'is_ranged': False,
        'anim_speed': 0.10,
        'attack_anim_speed': 0.03,
    },
    'monk': {
        'hp': 18,
        'damage': 1,
        'attack_range': 80,
        'attack_delay': 60,
        'speed': 1.5,
        'is_ranged': False,
        'is_healer': True,
        'heal_amount': 3,
        'heal_range': 150,
        'heal_delay': 100,
        'anim_speed': 0.10,
        'attack_anim_speed': 0.10,
    },
}