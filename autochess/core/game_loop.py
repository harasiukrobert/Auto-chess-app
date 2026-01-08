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
from config.setting import (COLOR_BG, COLOR_HIGHLIGHT, COLOR_SUBTLE,
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

        # Create a window first (we may switch to fullscreen after reading settings)
        # FIX: ensure we pass exactly two numbers (width, height)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("HEXA")

        # States
        self.state = "MENU"
        # start with a sensible default; may be overridden by settings screen/app saved state
        self.volume = DEFAULT_VOLUME
        self.sfx_volume = DEFAULT_VOLUME

        # track currently-playing music path so we don't reload unnecessarily
        self._current_music_path = None

        # Try load menu music early (volume will be applied again after settings are loaded)
        self._ensure_play_music(MUSIC_PATH, self.volume)

        # Core
        self.board = Board(hex_center=(SCREEN_WIDTH // 2 + title_size, SCREEN_HEIGHT // 2))
        self.clock = pygame.time.Clock()
        # Turn-based phases inside PLAY
        self.phase = 'PLANNING'  # 'PLANNING' | 'COMBAT'
        # End screen UI (created lazily later)
        self.end_screen = EndScreen(
            screen=self.screen,
            colors={"text": COLOR_TEXT, "highlight": COLOR_HIGHLIGHT, "subtle": COLOR_SUBTLE},
        )

        # Shop overlay (planning only)
        self.shop = Shop(
            screen=self.screen,
            items=['warrior', 'archer', 'lancer', 'monk', 'assassin', 'witch'],
            colors={"bg": (20, 20, 28), "border": COLOR_HIGHLIGHT, "text": COLOR_TEXT},
            on_spawn=self._shop_spawn_unit,
            on_get_gold=self._get_gold,
            on_deduct_gold=self._deduct_gold,
            on_can_spawn=self._can_spawn_blue,
        )

        # Static archer background (scaled+cropped)
        self.menu_bg = BackgroundStatic(
            screen=self.screen, image_path="files/ui/bg_archer.png", overlay_alpha=28
        )

        # UI: pass the new logo path
        self.menu = Menu(
            screen=self.screen,
            options=[("Play", "play"), ("Options", "settings"), ("Quit", "exit")],
            colors={"text": COLOR_TEXT, "highlight": COLOR_HIGHLIGHT, "subtle": COLOR_SUBTLE},
            logo_path="files/ui/hexa2.png",
        )

        # Settings screen: give a ref so it can apply volume/fullscreen immediately
        self.settings_screen = SettingsScreen(
            screen=self.screen,
            volume=self.volume,
            sfx_volume=self.sfx_volume,
            colors={"text": COLOR_TEXT, "highlight": COLOR_HIGHLIGHT, "subtle": COLOR_SUBTLE},
            game_ref=self,
        )

        # Read saved settings / current mixer and apply to game audio state
        try:
            # SettingsScreen now exposes getters and also prefers persisted values
            self.volume = getattr(self.settings_screen, "volume", self.settings_screen.get_music_volume())
            self.sfx_volume = getattr(self.settings_screen, "sfx_volume", self.settings_screen.get_sfx_volume())
            self.set_volume(self.volume)
            self.set_sfx_volume(self.sfx_volume)
        except Exception:
            pass

        # Apply fullscreen at startup if settings indicate so (default/saved)
        try:
            if self.settings_screen.is_fullscreen():
                self.apply_fullscreen(True)
        except Exception:
            pass

        # Planning phase advance button (UI component)
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

        # Speed control (combat sim speed)
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

    def _on_speed_change(self, value: float):
        """Apply speed change to current board's hex manager (combat sim speed)."""
        try:
            if hasattr(self.board, 'hex_manager') and self.board.hex_manager:
                self.board.hex_manager.set_sim_speed(float(value))
        except Exception:
            pass

    def _shop_spawn_unit(self, name: str, pos):
        """Spawn a blue unit via Board, return the instance for drag selection."""
        try:
            u = self.board.spawn_blue_unit(name, pos)
            # Do NOT auto-select while the mouse is still pressed; avoid jumping to shop click
            # Player can click the unit afterwards to drag it.
            return u
        except Exception as e:
            print(f"Error spawning unit {name}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _can_spawn_blue(self, name: str):
        """Return True if there's at least one free player hex for a new blue unit."""
        try:
            return bool(self.board.has_free_player_hex())
        except Exception:
            return False

    def _get_gold(self):
        """Get current player gold from board."""
        return self.board.gold

    def _deduct_gold(self, amount: int):
        """Try to deduct gold. Returns True if successful, False if insufficient funds."""
        if self.board.gold >= amount:
            self.board.gold -= amount
            return True
        return False

    def _ensure_play_music(self, path, vol):
        """
        Load and play the given music path on loop if different from the currently playing track.
        If pygame.mixer isn't available or file doesn't exist, do nothing silently.
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
            if path and os.path.exists(path):
                try:
                    pygame.mixer.music.load(path)
                    pygame.mixer.music.set_volume(vol)
                    pygame.mixer.music.play(-1)  # loop forever
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
        # Backwards-compatible loader - kept for compatibility with older calls
        try:
            if os.path.exists(path):
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(vol)
                pygame.mixer.music.play(-1)  # loop forever
                self._current_music_path = path
        except Exception:
            # if file not found or load fails, ignore silently
            pass

    # helpers used by settings
    def set_volume(self, vol):
        try:
            pygame.mixer.music.set_volume(vol)
        except Exception:
            pass
        self.volume = vol

    def set_sfx_volume(self, vol):
        # store sfx volume; if you have SFX sounds, set their volume when playing
        self.sfx_volume = vol

    def apply_fullscreen(self, fullscreen):
        flags = pygame.FULLSCREEN if fullscreen else 0
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
        # reassign screens & rebuild scaled backgrounds
        self.menu.screen = self.screen
        self.settings_screen.screen = self.screen
        if hasattr(self, 'shop'):
            self.shop.screen = self.screen
        self.menu_bg = BackgroundStatic(
            screen=self.screen, image_path="files/ui/bg_archer.png", overlay_alpha=28
        )
        # settings_screen will rebuild its internal scaled modal on next draw if needed.
        # update UI controls with new screen
        if hasattr(self, 'advance_btn'):
            self.advance_btn.screen = self.screen
        if hasattr(self, 'speed_ui'):
            self.speed_ui.screen = self.screen

    def startgame(self):
        # path for PLAY music
        play_music_path = "files/audio/buying_phase.wav"
        menu_music_path = MUSIC_PATH  # from config (menu.wav)

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit(0)

                if self.state == "MENU":
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        sys.exit(0)
                    action = self.menu.handle_event(event)
                    if action == "play":
                        self.state = "PLAY"
                        # switch to play music
                        self._ensure_play_music(play_music_path, self.volume)
                        # Round 1 is already applied in Board.__init__(), just save snapshot
                        try:
                            self.board.save_pre_planning_snapshot()
                        except Exception:
                            pass
                    elif action == "settings":
                        self.state = "SETTINGS"
                        # ensure menu music is playing while in settings
                        self._ensure_play_music(menu_music_path, self.volume)
                    elif action == "exit":
                        sys.exit(0)

                elif self.state == "SETTINGS":
                    # Esc returns to menu (do NOT quit)
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.state = "MENU"
                        # ensure menu music is playing when returning to menu
                        self._ensure_play_music(menu_music_path, self.volume)
                        continue

                    # pass events to settings screen
                    result = self.settings_screen.handle_event(event)
                    if result == "changed":
                        # read new values from settings_screen attributes and apply immediately
                        self.volume = getattr(self.settings_screen, "volume", self.settings_screen.get_music_volume())
                        self.sfx_volume = getattr(self.settings_screen, "sfx_volume",
                                                  self.settings_screen.get_sfx_volume())
                        self.set_volume(self.volume)
                        self.set_sfx_volume(self.sfx_volume)
                    elif result == "back":
                        self.state = "MENU"
                        # ensure menu music is playing
                        self._ensure_play_music(menu_music_path, self.volume)


                elif self.state == "PLAY":
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.state = "MENU"
                            # self._ensure_play_music(menu_music_path, self.volume)
                            continue
                        elif event.key == pygame.K_TAB:
                            # Toggle combat only from planning
                            if self.phase == 'PLANNING':
                                # Freeze baseline roster for carry-over on win
                                self.board.finalize_planning_baseline()
                                # (Optional) snapshot enemies; not required for rollback
                                self.board.snapshot_enemy_layout()
                                self.phase = 'COMBAT'
                                self.board.hex_manager.toggle_combat()
                    # Handle planning button click before routing to shop
                    if self.phase == 'PLANNING':
                        result = self.advance_btn.handle_event(event)
                        if result == "clicked":
                            # Same behavior as pressing TAB
                            self.board.finalize_planning_baseline()
                            self.board.snapshot_enemy_layout()
                            self.phase = 'COMBAT'
                            self.board.hex_manager.toggle_combat()
                            # Skip sending this click to the shop
                            continue
                    # route mouse events to shop only in planning phase
                    if self.phase == 'PLANNING':
                        _ = self.shop.handle_event(event)
                    # Speed control only in COMBAT phase
                    if self.phase == 'COMBAT':
                        _ = self.speed_ui.handle_event(event)

                elif self.state == "END":
                    # Handle end screen interactions here so events aren't drained earlier
                    action = self.end_screen.handle_event(event)
                    if action == 'menu':
                        try:
                            # Reset to a fresh run and go back to MENU
                            self.board.current_round = 1
                            self.board.apply_round(1, initial=True)
                            self.board.gold = int(self.board.rounds.starting_gold)
                        except Exception:
                            pass
                        self.state = "MENU"
                        # ensure menu music is active after returning
                        self._ensure_play_music(menu_music_path, self.volume)
                    elif action == 'exit':
                        sys.exit(0)

            # Draw per state
            if self.state == "MENU":
                # draw archer background and menu
                self.menu_bg.draw()
                self.menu.draw(skip_clear=True)
            elif self.state == "SETTINGS":
                # draw the normal menu background behind the centered modal
                self.menu_bg.draw()
                # SettingsScreen draws the centered modal and interactive bars
                self.settings_screen.draw()
            elif self.state == "PLAY":
                # ensure play music is active (in case something external changed it)
                self._ensure_play_music(play_music_path, self.volume)
                self.screen.fill("black")
                self.board.run()
                if self.phase == 'PLANNING':
                    # Draw shop UI above the board during planning
                    self.shop.draw()
                    # Draw the advance-to-combat button (UI component)
                    self.advance_btn.draw()
                # Draw speed control only during COMBAT phase
                if self.phase == 'COMBAT':
                    self.speed_ui.draw()

                # Draw current round label at top center
                try:
                    # Lazy-init a font once
                    if not hasattr(self, '_round_font') or self._round_font is None:
                        self._round_font = pygame.font.SysFont(None, 64)
                    label = f"ROUND {getattr(self.board, 'current_round', 1)}"
                    text_surf = self._round_font.render(label, True, COLOR_TEXT)
                    w, _h = self.screen.get_size()
                    text_rect = text_surf.get_rect(midtop=(w // 2, 10))
                    # Subtle shadow for readability
                    shadow = self._round_font.render(label, True, (0, 0, 0))
                    shadow_rect = shadow.get_rect(midtop=(text_rect.centerx, text_rect.top + 2))
                    self.screen.blit(shadow, shadow_rect)
                    self.screen.blit(text_surf, text_rect)
                except Exception:
                    pass

                # Round end detection during combat
                if self.phase == 'COMBAT' and self.board.hex_manager.is_combat_active():
                    blue_alive, red_alive = self.board.team_alive_counts()
                    if blue_alive == 0 or red_alive == 0:
                        # End of round
                        player_won = blue_alive > 0 and red_alive == 0
                        # Reset combat visuals
                        self.board.hex_manager.toggle_combat()  # back to planning
                        if player_won:
                            # Advance round, reset units and add new enemies
                            prev_round = self.board.current_round
                            next_round = prev_round + 1
                            # Award reward for completed round
                            try:
                                self.board.gold += int(self.board.get_round_reward(prev_round))
                            except Exception:
                                pass
                            # Give AI the same round reward
                            try:
                                self.board._enemy_ai.add_gold(int(self.board.get_round_reward(prev_round)))
                            except Exception:
                                pass
                            # Check if there is a next round
                            if self.board.rounds.has_round(next_round):
                                self.board.current_round = next_round
                                # keep player's current roster (baseline updated by snapshot during planning)
                                self.board.reset_units_to_initial()
                                # Apply next round config (grid + enemies)
                                self.board.apply_round(self.board.current_round, initial=False)
                                # New planning phase begins: capture snapshot for potential rollback on loss
                                try:
                                    self.board.save_pre_planning_snapshot()
                                except Exception:
                                    pass
                            else:
                                # No more rounds: show end screen
                                self.state = "END"
                        else:
                            # Loss: restore last planning layout to retry
                            self.board.restore_from_pre_planning_snapshot()
                            # Rebuild enemies from pre-combat snapshot to original positions
                            try:
                                self.board.rebuild_enemies_from_snapshot(include_extras=False, round_num=self.board.current_round)
                            except Exception:
                                # Fallback to round config if snapshot missing
                                self.board.respawn_current_round_enemies()
                            # Placeholder: reverse purchases from snapshot
                            # TODO: rollback buys stored in snapshot
                            # New planning cycle begins after loss: capture snapshot so future losses
                            # roll back to this restored state (including levels/positions)
                            try:
                                self.board.save_pre_planning_snapshot()
                            except Exception:
                                pass
                        self.phase = 'PLANNING'
            elif self.state == "END":
                # Draw menu background and end screen overlay during END state
                self.menu_bg.draw()
                self.end_screen.draw()

            pygame.display.update()
            self.clock.tick(FPS)


if __name__ == "__main__":
    Game()