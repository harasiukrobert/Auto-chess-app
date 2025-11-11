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
    'Positions': 7,
    'Sheep': 8,
    'Tree': 9,
    'Rock': 10,
    'Bushes': 11,
    'Units': 12,
}

# game loop settings
FPS = 120

# audio / UI settings
# default menu volume — changed to 50% so sliders start at a sensible level
DEFAULT_VOLUME = 0.50
# Point this to your menu music file (wav or ogg). Put menu.wav at files/audio/menu.wav
MUSIC_PATH = 'files/audio/menu.wav'

# simple UI colors (used as sensible defaults)
COLOR_BG = (10, 10, 10)
COLOR_TEXT = (230, 230, 230)
# main blue accent used across UI
COLOR_HIGHLIGHT = (80, 125, 170)
COLOR_SUBTLE = (130, 130, 130)