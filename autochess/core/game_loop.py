import os
import sys

import pygame

from autochess.game.board import Board
from autochess.ui.advance_button import PlanningAdvanceButton
from autochess.ui.background import \
    BackgroundStatic  # static background helper
from autochess.ui.end_screen import EndScreen
from autochess.ui.menu import Menu
from autochess.ui.settings import SettingsScreen
from autochess.ui.shop import Shop
from autochess.ui.speed_control import SpeedControl
from autochess.utils.resource import resource_path
from config.setting import (BOARD_CENTER_OFFSET_X, BOARD_CENTER_OFFSET_Y,
                            COLOR_BG, COLOR_HIGHLIGHT, COLOR_SUBTLE,
                            COLOR_TEXT, DEFAULT_VOLUME, FPS, MUSIC_PATH,
                            SCREEN_HEIGHT, SCREEN_WIDTH, title_size)


class Game:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
            self._mixer_ready = True
        except Exception:
            self._mixer_ready = False

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("HEXA")

        self.state = "MENU"
        self.volume = DEFAULT_VOLUME
        self.sfx_volume = DEFAULT_VOLUME

        self._current_music_path = None

        self.menu_music_path = MUSIC_PATH
        self.play_music_path = "files/audio/buying_phase.wav"

        self._ensure_play_music(self.menu_music_path, self.volume)

        self.board = Board(
            hex_center=(
                (SCREEN_WIDTH // 2 + title_size) + int(BOARD_CENTER_OFFSET_X),
                (SCREEN_HEIGHT // 2) + int(BOARD_CENTER_OFFSET_Y),
            )
        )
        self.clock = pygame.time.Clock()
        self.phase = 'PLANNING'
        self._surrender_requested = False
        self.end_screen = EndScreen(
            screen=self.screen,
            colors={"text": COLOR_TEXT, "highlight": COLOR_HIGHLIGHT, "subtle": COLOR_SUBTLE},
        )

        self.shop = Shop(
            screen=self.screen,
            items=['warrior', 'archer', 'lancer', 'monk', 'assassin', 'witch'],
            colors={"bg": (20, 20, 28), "border": COLOR_HIGHLIGHT, "text": COLOR_TEXT},
            on_spawn=self._shop_spawn_unit,
            on_get_gold=self._get_gold,
            on_deduct_gold=self._deduct_gold,
            on_can_spawn=self._can_spawn_blue,
        )

        self._pre_planning_shop_snapshot = None

        self.menu_bg = BackgroundStatic(
            screen=self.screen, image_path="files/ui/bg_archer.png", overlay_alpha=28
        )

        self.menu = Menu(
            screen=self.screen,
            options=[("Play", "play"), ("Options", "settings"), ("Quit", "exit")],
            colors={"text": COLOR_TEXT, "highlight": COLOR_HIGHLIGHT, "subtle": COLOR_SUBTLE},
            logo_path="files/ui/hexa2.png",
        )

        self.settings_screen = SettingsScreen(
            screen=self.screen,
            volume=self.volume,
            sfx_volume=self.sfx_volume,
            colors={"text": COLOR_TEXT, "highlight": COLOR_HIGHLIGHT, "subtle": COLOR_SUBTLE},
            game_ref=self,
        )

        try:
            self.volume = getattr(self.settings_screen, "volume", self.settings_screen.get_music_volume())
            self.sfx_volume = getattr(self.settings_screen, "sfx_volume", self.settings_screen.get_sfx_volume())
            self.set_volume(self.volume)
            self.set_sfx_volume(self.sfx_volume)
        except Exception:
            pass

        try:
            if self.settings_screen.is_fullscreen():
                self.apply_fullscreen(True)
        except Exception:
            pass

        self.advance_btn = PlanningAdvanceButton(
            screen=self.screen,
            label="FIGHT!",
            colors={
                "bg": (180, 42, 42),
                "hover": (200, 60, 60),
                "border": COLOR_HIGHLIGHT,
                "text": COLOR_TEXT,
            },
            size=(220, 56),
            margin=16,
            radius=6,
        )

        self.speed_ui = SpeedControl(
            screen=self.screen,
            on_change=self._on_speed_change,
            colors={
                "bg": (30, 30, 35),
                "border": COLOR_SUBTLE,
                "text": COLOR_TEXT,
                "hover": (60, 60, 80),
                "active": COLOR_HIGHLIGHT,
            },
        )

        self.startgame()

    def _start_new_run(self):
        """Rozpoczyna nową rozgrywkę po wejściu w PLAY z menu głównego."""
        try:
            self.board.reset_run()
        except Exception:
            pass

        self._surrender_requested = False
        self.phase = 'PLANNING'

        try:
            self.shop.locked = False
            self.shop.reroll_free()
        except Exception:
            pass

        self._pre_planning_shop_snapshot = None
        self._save_pre_planning_snapshot()

    def _go_to_menu(self, *, reset_run: bool = False):
        """Powraca do menu głównego w spójnym, bezpiecznym stanie."""
        if reset_run:
            try:
                self.board.reset_run()
            except Exception:
                pass

        self._surrender_requested = False
        self.phase = 'PLANNING'
        try:
            if hasattr(self.board, 'hex_manager') and self.board.hex_manager and self.board.hex_manager.is_combat_active():
                self.board.hex_manager.toggle_combat()
        except Exception:
            pass
        try:
            self.advance_btn.label = "FIGHT!"
        except Exception:
            pass

        try:
            self.menu.hovered = None
            self.menu.selected = 0
            self.menu.button_rects = []
        except Exception:
            pass

        self.state = "MENU"
        self._ensure_play_music(self.menu_music_path, self.volume)

    def _save_pre_planning_snapshot(self):
        """Zapisuje stan planszy i sklepu na początku planowania."""
        try:
            self.board.save_pre_planning_snapshot()
        except Exception:
            pass
        try:
            self._pre_planning_shop_snapshot = self.shop.get_state()
        except Exception:
            self._pre_planning_shop_snapshot = None

    def _restore_from_pre_planning_snapshot(self):
        """Przywraca stan planszy i sklepu do snapshotu z początku planowania (używane przy przegranej)."""
        try:
            self.board.restore_from_pre_planning_snapshot()
        except Exception:
            pass
        try:
            if self._pre_planning_shop_snapshot is not None:
                self.shop.set_state(self._pre_planning_shop_snapshot)
        except Exception:
            pass

    def _on_speed_change(self, value: float):
        """Zastosowuje zmianę prędkości do hex managera bieżącej planszy (prędkość symulacji walki)."""
        try:
            if hasattr(self.board, 'hex_manager') and self.board.hex_manager:
                self.board.hex_manager.set_sim_speed(float(value))
        except Exception:
            pass

    def _shop_spawn_unit(self, name: str, pos):
        """Tworzy niebieską jednostkę przez Board, zwraca instancję do zaznaczenia przeciąganiem."""
        try:
            u = self.board.spawn_blue_unit(name, pos)
            return u
        except Exception as e:
            print(f"Error spawning unit {name}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _can_spawn_blue(self, name: str):
        """Zwraca True jeśli jest przynajmniej jeden wolny heks gracza dla nowej niebieskiej jednostki."""
        try:
            return bool(self.board.has_free_player_hex())
        except Exception:
            return False

    def _get_gold(self):
        """Pobiera aktualne złoto gracza z planszy."""
        return self.board.gold

    def _deduct_gold(self, amount: int):
        """Próbuje odjąć złoto. Zwraca True jeśli się powiodło, False jeśli brak środków."""
        if self.board.gold >= amount:
            self.board.gold -= amount
            return True
        return False

    def _ensure_play_music(self, path, vol):
        """
        Ładuje i odtwarza muzykę w pętli jeśli różni się od aktualnie granej.
        Jeśli pygame.mixer nie jest dostępny lub plik nie istnieje, nic nie robi.
        """
        if not self._mixer_ready:
            return
        try:
            if path == self._current_music_path:
                try:
                    pygame.mixer.music.set_volume(vol)
                except Exception:
                    pass
                return
            resolved = resource_path(path) if path else None
            if resolved and os.path.exists(resolved):
                try:
                    pygame.mixer.music.load(resolved)
                    pygame.mixer.music.set_volume(vol)
                    pygame.mixer.music.play(-1)
                    self._current_music_path = path
                except Exception:
                    self._current_music_path = None
            else:
                try:
                    pygame.mixer.music.stop()
                except Exception:
                    pass
                self._current_music_path = None
        except Exception:
            self._current_music_path = None

    def _load_music(self, path, vol):
        try:
            resolved = resource_path(path) if path else None
            if resolved and os.path.exists(resolved):
                pygame.mixer.music.load(resolved)
                pygame.mixer.music.set_volume(vol)
                pygame.mixer.music.play(-1)
                self._current_music_path = path
        except Exception:
            pass

    def set_volume(self, vol):
        try:
            pygame.mixer.music.set_volume(vol)
        except Exception:
            pass
        self.volume = vol

    def set_sfx_volume(self, vol):
        self.sfx_volume = vol

    def apply_fullscreen(self, fullscreen):
        flags = pygame.FULLSCREEN if fullscreen else 0
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
        self.menu.screen = self.screen
        self.settings_screen.screen = self.screen
        if hasattr(self, 'shop'):
            self.shop.screen = self.screen
        self.menu_bg = BackgroundStatic(
            screen=self.screen, image_path="files/ui/bg_archer.png", overlay_alpha=28
        )
        if hasattr(self, 'advance_btn'):
            self.advance_btn.screen = self.screen
        if hasattr(self, 'speed_ui'):
            self.speed_ui.screen = self.screen

    def startgame(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit(0)

                if self.state == "MENU":
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        sys.exit(0)
                    action = self.menu.handle_event(event)
                    if action == "play":
                        self._start_new_run()
                        self.state = "PLAY"
                        self._ensure_play_music(self.play_music_path, self.volume)
                    elif action == "settings":
                        self.state = "SETTINGS"
                        self._ensure_play_music(self.menu_music_path, self.volume)
                    elif action == "exit":
                        sys.exit(0)

                elif self.state == "SETTINGS":
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self._go_to_menu(reset_run=False)
                        continue

                    result = self.settings_screen.handle_event(event)
                    if result == "changed":
                        self.volume = getattr(self.settings_screen, "volume", self.settings_screen.get_music_volume())
                        self.sfx_volume = getattr(self.settings_screen, "sfx_volume",
                                                  self.settings_screen.get_sfx_volume())
                        self.set_volume(self.volume)
                        self.set_sfx_volume(self.sfx_volume)
                    elif result == "back":
                        self._go_to_menu(reset_run=False)


                elif self.state == "PLAY":
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self._go_to_menu(reset_run=False)
                            continue
                        elif event.key == pygame.K_TAB:
                            if self.phase == 'PLANNING':
                                self.board.finalize_planning_baseline()
                                self.board.snapshot_enemy_layout()
                                self.phase = 'COMBAT'
                                self.board.hex_manager.toggle_combat()
                                try:
                                    self.advance_btn.label = "SURRENDER"
                                except Exception:
                                    pass
                    if self.phase == 'PLANNING':
                        result = self.advance_btn.handle_event(event)
                        if result == "clicked":
                            self.board.finalize_planning_baseline()
                            self.board.snapshot_enemy_layout()
                            self.phase = 'COMBAT'
                            self.board.hex_manager.toggle_combat()
                            try:
                                self.advance_btn.label = "SURRENDER"
                            except Exception:
                                pass
                            continue
                    if self.phase == 'COMBAT':
                        result = self.advance_btn.handle_event(event)
                        if result == "clicked":
                            self._surrender_requested = True
                            continue
                    if self.phase == 'PLANNING':
                        _ = self.shop.handle_event(event)
                    if self.phase == 'COMBAT':
                        _ = self.speed_ui.handle_event(event)

                elif self.state == "END":
                    action = self.end_screen.handle_event(event)
                    if action == 'menu':
                        self._go_to_menu(reset_run=True)
                    elif action == 'exit':
                        sys.exit(0)

            if self.state == "MENU":
                self.menu_bg.draw()
                self.menu.draw(skip_clear=True)
            elif self.state == "SETTINGS":
                self.menu_bg.draw()
                self.settings_screen.draw()
            elif self.state == "PLAY":
                self._ensure_play_music(self.play_music_path, self.volume)
                self.screen.fill("black")
                self.board.run()

                if self.phase == 'COMBAT' and getattr(self, '_surrender_requested', False):
                    self._surrender_requested = False
                    try:
                        self.board.hex_manager.toggle_combat()
                    except Exception:
                        pass
                    self._restore_from_pre_planning_snapshot()
                    try:
                        self.board.rebuild_enemies_from_snapshot(include_extras=False, round_num=self.board.current_round)
                    except Exception:
                        self.board.respawn_current_round_enemies()
                    self._save_pre_planning_snapshot()
                    self.phase = 'PLANNING'
                    try:
                        self.advance_btn.label = "FIGHT!"
                    except Exception:
                        pass
                try:
                    self.advance_btn.label = "FIGHT!" if self.phase == 'PLANNING' else "SURRENDER"
                except Exception:
                    pass
                if self.phase == 'PLANNING':
                    self.shop.draw()
                self.advance_btn.draw()
                if self.phase == 'COMBAT':
                    self.speed_ui.draw()

                try:
                    if not hasattr(self, '_round_font') or self._round_font is None:
                        self._round_font = pygame.font.SysFont(None, 64)
                    label = f"ROUND {getattr(self.board, 'current_round', 1)}"
                    text_surf = self._round_font.render(label, True, COLOR_TEXT)
                    w, _h = self.screen.get_size()
                    text_rect = text_surf.get_rect(midtop=(w // 2, 10))
                    shadow = self._round_font.render(label, True, (0, 0, 0))
                    shadow_rect = shadow.get_rect(midtop=(text_rect.centerx, text_rect.top + 2))
                    self.screen.blit(shadow, shadow_rect)
                    self.screen.blit(text_surf, text_rect)
                except Exception:
                    pass

                if self.phase == 'COMBAT' and self.board.hex_manager.is_combat_active():
                    blue_alive, red_alive = self.board.team_alive_counts()
                    if blue_alive == 0 or red_alive == 0:
                        player_won = blue_alive > 0 and red_alive == 0
                        self.board.hex_manager.toggle_combat()
                        if player_won:
                            prev_round = self.board.current_round
                            next_round = prev_round + 1
                            try:
                                self.board.gold += int(self.board.get_round_reward(prev_round))
                            except Exception:
                                pass
                            try:
                                self.board._enemy_ai.add_gold(int(self.board.get_round_reward(prev_round)))
                            except Exception:
                                pass
                            if self.board.rounds.has_round(next_round):
                                self.board.current_round = next_round
                                self.board.reset_units_to_initial()
                                self.board.apply_round(self.board.current_round, initial=False)
                                try:
                                    self.shop.reroll_for_new_round()
                                except Exception:
                                    pass
                                self._save_pre_planning_snapshot()
                            else:
                                self.state = "END"
                        else:
                            self._restore_from_pre_planning_snapshot()
                            try:
                                self.board.rebuild_enemies_from_snapshot(include_extras=False, round_num=self.board.current_round)
                            except Exception:
                                self.board.respawn_current_round_enemies()
                            self._save_pre_planning_snapshot()
                        self.phase = 'PLANNING'
                        try:
                            self.advance_btn.label = "FIGHT!"
                        except Exception:
                            pass
            elif self.state == "END":
                self.menu_bg.draw()
                self.end_screen.draw()

            pygame.display.update()
            self.clock.tick(FPS)


if __name__ == "__main__":
    Game()