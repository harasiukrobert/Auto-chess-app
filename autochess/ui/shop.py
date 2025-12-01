import json
import os
import pygame


class Shop:
    """
    Shop overlay for the planning phase with unit cards showing costs.
    - Shows a bottom bar with unit cards displaying name, cost, and icon.
    - On click, spawns a blue unit if player has enough gold.
    - Deducts gold on purchase and updates HUD gold counter.
    """

    def __init__(self, screen, items, colors=None, on_spawn=None, on_get_gold=None, on_deduct_gold=None):
        self.screen = screen
        self.items = items  # list of unit names e.g., ['warrior','archer','lancer','monk']
        self.on_spawn = on_spawn  # callback: (name:str, pos:tuple) -> Unit or None
        self.on_get_gold = on_get_gold  # callback: () -> int (get current gold)
        self.on_deduct_gold = on_deduct_gold  # callback: (amount:int) -> bool (try to deduct gold)
        colors = colors or {}
        self.color_bg = colors.get('bg', (20, 20, 28))
        self.color_border = colors.get('border', (90, 120, 160))
        self.color_text = colors.get('text', (230, 230, 230))
        self.color_highlight = colors.get('highlight', (255, 230, 100))
        self.color_gold = (255, 215, 0)  # Gold color for cost display
        self.color_insufficient = (150, 150, 150)  # Gray for insufficient funds
        self.font = pygame.font.SysFont(None, 28)
        self.font_small = pygame.font.SysFont(None, 22)
        self.font_gold = pygame.font.SysFont(None, 32, bold=True)

        # Layout constants
        self.padding = 10
        self.gold_margin = 20  # Right margin for gold counter
        self.card_padding = 8  # Padding inside unit cards
        self.height = 110
        self.button_size = (140, 60)
        self.button_gap = 18
        self.rect = self._compute_rect()
        self.button_rects = []

        # Load unit data (costs)
        self.units_data = self._load_units_data()

    def _load_units_data(self):
        """Load unit data from JSON file."""
        units_data_path = os.path.join('config', 'units_data.json')
        try:
            with open(units_data_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # Fallback to hardcoded values if file not found or invalid
            print(f"Warning: Could not load units data from {units_data_path}: {e}")
            return {
                'warrior': {'name': 'Warrior', 'cost': 3, 'icon': None},
                'archer': {'name': 'Archer', 'cost': 3, 'icon': None},
                'lancer': {'name': 'Lancer', 'cost': 4, 'icon': None},
                'monk': {'name': 'Monk', 'cost': 5, 'icon': None}
            }

    def _compute_rect(self):
        w, h = self.screen.get_size()
        r = pygame.Rect(0, h - self.height, w, self.height)
        return r

    def handle_event(self, event):
        if event.type == pygame.VIDEORESIZE:
            self.rect = self._compute_rect()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.rect.collidepoint(mx, my):
                for idx, brect in enumerate(self.button_rects):
                    if brect.collidepoint(mx, my):
                        name = self.items[idx]
                        unit_data = self.units_data.get(name, {})
                        cost = unit_data.get('cost', 0)

                        # Check if player has enough gold
                        current_gold = self.on_get_gold() if callable(self.on_get_gold) else 0
                        if current_gold >= cost:
                            # Try to deduct gold
                            if callable(self.on_deduct_gold) and self.on_deduct_gold(cost):
                                # Spawn unit if gold was successfully deducted
                                if callable(self.on_spawn):
                                    unit = self.on_spawn(name, (mx, my))
                                    return unit  # Game can mark it as selected for dragging
        return None

    def draw(self):
        # background bar
        pygame.draw.rect(self.screen, self.color_bg, self.rect)
        pygame.draw.rect(self.screen, self.color_border, self.rect, width=2)

        # Get current gold
        current_gold = self.on_get_gold() if callable(self.on_get_gold) else 0

        # Draw gold counter in top-right of HUD
        gold_text = f"Gold: {current_gold}"
        gold_surf = self.font_gold.render(gold_text, True, self.color_gold)
        gold_rect = gold_surf.get_rect(right=self.rect.right - self.gold_margin, centery=self.rect.centery)
        self.screen.blit(gold_surf, gold_rect)

        # layout buttons centered horizontally (but leave space for gold counter)
        w = self.rect.width
        x = self.rect.left + self.padding
        y = self.rect.top + (self.rect.height - self.button_size[1]) // 2
        total_buttons_w = len(self.items) * self.button_size[0] + (len(self.items) - 1) * self.button_gap
        start_x = self.rect.left + (w - total_buttons_w) // 2

        self.button_rects = []
        for idx, name in enumerate(self.items):
            bx = start_x + idx * (self.button_size[0] + self.button_gap)
            by = y
            brect = pygame.Rect(bx, by, *self.button_size)

            # Get unit data
            unit_data = self.units_data.get(name, {})
            cost = unit_data.get('cost', 0)
            display_name = unit_data.get('name', name.capitalize())

            # Check if player can afford this unit
            can_afford = current_gold >= cost
            button_color = (40, 55, 80) if can_afford else (30, 35, 45)
            text_color = self.color_text if can_afford else self.color_insufficient

            # Draw button
            pygame.draw.rect(self.screen, button_color, brect, border_radius=10)
            pygame.draw.rect(self.screen, self.color_border, brect, width=2, border_radius=10)

            # Draw unit name (top part of button)
            label_surf = self.font_small.render(display_name, True, text_color)
            label_rect = label_surf.get_rect(centerx=brect.centerx, top=brect.top + self.card_padding)
            self.screen.blit(label_surf, label_rect)

            # Draw cost (bottom part of button)
            cost_text = f"Cost: {cost}"
            cost_surf = self.font_small.render(cost_text, True,
                                               self.color_gold if can_afford else self.color_insufficient)
            cost_rect = cost_surf.get_rect(centerx=brect.centerx, bottom=brect.bottom - self.card_padding)
            self.screen.blit(cost_surf, cost_rect)

            self.button_rects.append(brect)
