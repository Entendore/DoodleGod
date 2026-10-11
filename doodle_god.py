#!/usr/bin/env python3
"""
Doodle God - Element Combination Puzzle Game (SQLite Edition)
A Pygame recreation of the classic element-mixing puzzle.
All game data (elements, combinations, categories) is stored in SQLite.

Run init_doodle_db.py first to create the database, then run this game.

Controls:
  - Click and drag elements from the panel into the workspace
  - Drop one element onto another to attempt a combination
  - Scroll the element panel with the mouse wheel
  - Right-click a placed element to remove it from the workspace
  - Press H for hints (shows which undiscovered elements can be made)
  - Press R to reset progress
"""

import pygame
import sys
import math
import random
import time
import sqlite3
import os

pygame.init()

# ── DATABASE ──────────────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "doodle_god.db")


class GameDB:
    """Loads and caches all game data from SQLite into Python dicts
    for fast in-memory lookups during gameplay."""

    def __init__(self, db_path=DB_PATH):
        if not os.path.exists(db_path):
            raise FileNotFoundError(
                f"Database not found: {db_path}\n"
                "Run init_doodle_db.py first to create it."
            )
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys=ON")

        self.elements = {}      # key -> dict(name, cat, color, icon, desc)
        self.combinations = {}  # (sorted_key_a, sorted_key_b) -> result
        self.categories = {}    # key -> dict(name, color)
        self.starting_elements = []

        self._load()

    def _load(self):
        c = self.conn.cursor()

        # Load categories
        for row in c.execute("SELECT key, name, color_r, color_g, color_b FROM categories"):
            self.categories[row[0]] = {
                "name": row[1],
                "color": (row[2], row[3], row[4]),
            }

        # Load elements
        for row in c.execute(
            "SELECT key, name, category, color_r, color_g, color_b, icon, description "
            "FROM elements"
        ):
            self.elements[row[0]] = {
                "name": row[1],
                "cat": row[2],
                "color": (row[3], row[4], row[5]),
                "icon": row[6],
                "desc": row[7],
            }

        # Load combinations (already sorted in DB)
        for row in c.execute("SELECT elem_a, elem_b, result FROM combinations"):
            self.combinations[(row[0], row[1])] = row[2]

        # Load starting elements
        for row in c.execute("SELECT element_key FROM starting_elements"):
            self.starting_elements.append(row[0])

        c.close()

    def get_hints(self, discovered):
        """Return combos where both inputs are discovered but result is not."""
        c = self.conn.cursor()
        placeholders = ",".join("?" for _ in discovered)
        rows = c.execute(
            f"SELECT elem_a, elem_b, result FROM combinations "
            f"WHERE elem_a IN ({placeholders}) AND elem_b IN ({placeholders}) "
            f"AND result NOT IN ({placeholders})",
            list(discovered) * 3
        ).fetchall()
        c.close()
        return [(r[0], r[1], r[2]) for r in rows]

    def get_total_elements(self):
        return len(self.elements)


# ── CONSTANTS ────────────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1200, 800
FPS = 60

# Colors
C_BG          = (25, 25, 40)
C_PANEL_BG    = (35, 35, 55)
C_WORKSPACE   = (45, 42, 65)
C_WORKSPACE_BD= (80, 75, 120)
C_TEXT        = (230, 230, 240)
C_TEXT_DIM    = (140, 140, 160)
C_ACCENT      = (120, 100, 220)
C_ACCENT2     = (220, 120, 80)
C_SUCCESS     = (80, 220, 120)
C_FAIL        = (220, 80, 80)
C_SLOT_BG     = (55, 52, 78)
C_SLOT_BD     = (100, 95, 140)
C_BTN         = (70, 65, 105)
C_BTN_HOVER   = (90, 85, 135)
C_BTN_TEXT    = (230, 230, 245)
C_PROGRESS_BG = (50, 48, 72)
C_PROGRESS_FG = (120, 100, 220)
C_CATEGORY_BG = (42, 40, 60)
C_TOOLTIP_BG  = (50, 48, 72)
C_TOOLTIP_BD  = (100, 95, 140)

# Layout
PANEL_W = 300
PANEL_X = 0
WORKSPACE_X = PANEL_W
WORKSPACE_W = SCREEN_W - PANEL_W
WORKSPACE_Y = 60
WORKSPACE_H = SCREEN_H - 60
HEADER_H = 60

# Element card size
CARD_W = 120
CARD_H = 60
CARD_MARGIN = 8

# Workspace drop zones
DROP_ZONE_W = 160
DROP_ZONE_H = 80
DROP_ZONE_Y = (SCREEN_H - DROP_ZONE_H) // 2 + 30
DROP_ZONE_1_X = WORKSPACE_X + (WORKSPACE_W // 2) - DROP_ZONE_W - 40
DROP_ZONE_2_X = WORKSPACE_X + (WORKSPACE_W // 2) + 40


# ── DRAWING HELPERS ───────────────────────────────────────────────────────────

def draw_icon(surface, icon_type, cx, cy, size, color):
    if icon_type == "circle":
        pygame.draw.circle(surface, color, (cx, cy), size)
    elif icon_type == "diamond":
        points = [(cx, cy - size), (cx + size, cy), (cx, cy + size), (cx - size, cy)]
        pygame.draw.polygon(surface, color, points)
    elif icon_type == "triangle":
        points = [(cx, cy - size), (cx + size, cy + size), (cx - size, cy + size)]
        pygame.draw.polygon(surface, color, points)
    elif icon_type == "star":
        points = []
        for i in range(10):
            angle = math.radians(i * 36 - 90)
            r = size if i % 2 == 0 else size * 0.4
            points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        pygame.draw.polygon(surface, color, points)
    elif icon_type == "cross":
        w = max(1, size // 3)
        pygame.draw.rect(surface, color, (cx - w, cy - size, w * 2, size * 2))
        pygame.draw.rect(surface, color, (cx - size, cy - w, size * 2, w * 2))
    elif icon_type == "wave":
        for i in range(3):
            y_off = (i - 1) * (size // 2)
            pts = []
            for j in range(20):
                x = cx - size + (2 * size * j) / 19
                y = cy + y_off + math.sin(j * 0.8) * (size // 3)
                pts.append((x, y))
            if len(pts) > 1:
                pygame.draw.lines(surface, color, False, pts, max(1, size // 4))
    elif icon_type == "flame":
        points = [
            (cx, cy - size),
            (cx + size * 0.7, cy),
            (cx + size * 0.4, cy + size * 0.5),
            (cx + size * 0.5, cy + size * 0.8),
            (cx, cy + size * 0.4),
            (cx - size * 0.5, cy + size * 0.8),
            (cx - size * 0.4, cy + size * 0.5),
            (cx - size * 0.7, cy),
        ]
        pygame.draw.polygon(surface, color, points)
    elif icon_type == "drop":
        points = [
            (cx, cy - size),
            (cx + size * 0.6, cy + size * 0.2),
            (cx + size * 0.5, cy + size * 0.6),
            (cx + size * 0.2, cy + size * 0.9),
            (cx - size * 0.2, cy + size * 0.9),
            (cx - size * 0.5, cy + size * 0.6),
            (cx - size * 0.6, cy + size * 0.2),
        ]
        pygame.draw.polygon(surface, color, points)
    elif icon_type == "leaf":
        points = [
            (cx, cy - size),
            (cx + size * 0.6, cy - size * 0.3),
            (cx + size * 0.5, cy + size * 0.3),
            (cx, cy + size),
            (cx - size * 0.5, cy + size * 0.3),
            (cx - size * 0.6, cy - size * 0.3),
        ]
        pygame.draw.polygon(surface, color, points)
        darker = tuple(max(0, c - 40) for c in color)
        pygame.draw.line(surface, darker, (cx, cy - size), (cx, cy + size), 2)


def lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


# ── PARTICLE SYSTEM ──────────────────────────────────────────────────────────

class Particle:
    __slots__ = ['x', 'y', 'vx', 'vy', 'life', 'max_life', 'color', 'size']

    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1, 5)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - 2
        self.life = random.uniform(0.5, 1.5)
        self.max_life = self.life
        self.color = color
        self.size = random.uniform(2, 6)

    def update(self, dt):
        self.x += self.vx * 60 * dt
        self.y += self.vy * 60 * dt
        self.vy += 3 * dt
        self.life -= dt

    def draw(self, surface):
        alpha = max(0.0, self.life / self.max_life)
        r, g, b = self.color
        size = max(1, int(self.size * alpha))
        c = (min(255, int(r * alpha + 100 * (1 - alpha))),
             min(255, int(g * alpha + 100 * (1 - alpha))),
             min(255, int(b * alpha + 100 * (1 - alpha))))
        pygame.draw.circle(surface, c, (int(self.x), int(self.y)), size)


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit(self, x, y, color, count=30):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))

    def update(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)


# ── NOTIFICATION ─────────────────────────────────────────────────────────────

class Notification:
    def __init__(self, text, color, duration=3.0):
        self.text = text
        self.color = color
        self.duration = duration
        self.timer = duration
        self.y_offset = 0

    def update(self, dt):
        self.timer -= dt
        if self.timer < 0.5:
            self.y_offset = int((0.5 - self.timer) * 30)

    def is_alive(self):
        return self.timer > 0


# ── MAIN GAME ────────────────────────────────────────────────────────────────

class DoodleGodGame:
    def __init__(self):
        # Load all game data from SQLite
        self.db = GameDB()
        ELEMENTS = self.db.elements
        CATEGORIES = self.db.categories
        COMBINATIONS = self.db.combinations

        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Doodle God - Element Combination Puzzle (SQLite)")
        self.clock = pygame.time.Clock()

        self.font_lg = pygame.font.SysFont("dejavusans", 32, bold=True)
        self.font_md = pygame.font.SysFont("dejavusans", 20)
        self.font_sm = pygame.font.SysFont("dejavusans", 16)
        self.font_xs = pygame.font.SysFont("dejavusans", 13)

        self.discovered = set(self.db.starting_elements)
        self.dragging = None
        self.drag_pos = (0, 0)
        self.drag_from_panel = True
        self.slot1 = None
        self.slot2 = None

        self.panel_scroll = 0
        self.content_height = 0
        self.notifications = []
        self.particles = ParticleSystem()
        self.show_hints = False
        self.combination_flash = None
        self.hover_element = None
        self.tooltip = None
        self.active_category = "all"
        self.new_discovery_anim = None

        self.total_elements = self.db.get_total_elements()

        self.stars = [(random.randint(0, SCREEN_W), random.randint(0, SCREEN_H),
                       random.uniform(0.5, 2), random.uniform(0.3, 1.0))
                      for _ in range(100)]

        self.buttons = [
            {"rect": pygame.Rect(WORKSPACE_X + 10, 10, 90, 36), "text": "Hints (H)", "action": "hints"},
            {"rect": pygame.Rect(WORKSPACE_X + 110, 10, 100, 36), "text": "Reset (R)", "action": "reset"},
            {"rect": pygame.Rect(WORKSPACE_X + 220, 10, 120, 36), "text": "Clear Slots", "action": "clear"},
        ]

    def get_category_elements(self):
        ELEMENTS = self.db.elements
        if self.active_category == "all":
            return sorted(self.discovered, key=lambda e: (ELEMENTS[e]["cat"], ELEMENTS[e]["name"]))
        else:
            return sorted([e for e in self.discovered if ELEMENTS[e]["cat"] == self.active_category],
                          key=lambda e: ELEMENTS[e]["name"])

    def combine(self, e1, e2):
        if e1 is None or e2 is None:
            return
        ELEMENTS = self.db.elements
        COMBINATIONS = self.db.combinations
        key = tuple(sorted([e1, e2]))
        result = COMBINATIONS.get(key)

        if result and result not in self.discovered:
            self.discovered.add(result)
            elem = ELEMENTS[result]
            self.notifications.append(Notification(f"NEW: {elem['name']}!", C_SUCCESS, 4.0))
            self.particles.emit(SCREEN_W // 2, SCREEN_H // 2, elem["color"], 60)
            self.combination_flash = (C_SUCCESS, 1.0)
            self.new_discovery_anim = (result, 2.0, time.time())
            if len(self.discovered) == self.total_elements:
                self.notifications.append(Notification("YOU CREATED EVERYTHING!", C_ACCENT, 10.0))
                self.particles.emit(SCREEN_W // 2, SCREEN_H // 2, (255, 215, 0), 200)
        elif result and result in self.discovered:
            self.notifications.append(
                Notification(f"{ELEMENTS[e1]['name']} + {ELEMENTS[e2]['name']} = {ELEMENTS[result]['name']} (known)",
                             C_TEXT_DIM, 2.5))
            self.combination_flash = (C_TEXT_DIM, 0.5)
        else:
            self.notifications.append(Notification("Nothing happened...", C_FAIL, 2.0))
            self.combination_flash = (C_FAIL, 0.8)
            self.particles.emit(SCREEN_W // 2, SCREEN_H // 2, C_FAIL, 15)

        self.slot1 = None
        self.slot2 = None

    def add_to_slot(self, element_key):
        if self.slot1 is None:
            self.slot1 = element_key
        elif self.slot2 is None:
            self.slot2 = element_key
        else:
            self.combine(self.slot1, self.slot2)

    def reset(self):
        self.discovered = set(self.db.starting_elements)
        self.slot1 = None
        self.slot2 = None
        self.dragging = None
        self.notifications = []
        self.show_hints = False
        self.panel_scroll = 0
        self.active_category = "all"

    def get_hints(self):
        return self.db.get_hints(self.discovered)

    def draw_background(self):
        self.screen.fill(C_BG)
        t = time.time()
        for x, y, size, brightness in self.stars:
            alpha = (math.sin(t * brightness + x) + 1) / 2
            c = int(80 * brightness * alpha)
            pygame.draw.circle(self.screen, (c, c, min(255, int(c * 1.2))), (int(x), int(y)), max(1, int(size)))

    def draw_header(self):
        ELEMENTS = self.db.elements
        title = self.font_lg.render("Doodle God", True, C_ACCENT)
        self.screen.blit(title, (PANEL_X + 15, 12))
        progress = len(self.discovered) / self.total_elements
        bar_x, bar_y = PANEL_X + 15, 48
        bar_w = PANEL_W - 30
        pygame.draw.rect(self.screen, C_PROGRESS_BG, (bar_x, bar_y, bar_w, 8), border_radius=4)
        if progress > 0:
            pygame.draw.rect(self.screen, C_PROGRESS_FG, (bar_x, bar_y, int(bar_w * progress), 8), border_radius=4)
        pct = self.font_xs.render(f"{len(self.discovered)}/{self.total_elements}", True, C_TEXT_DIM)
        self.screen.blit(pct, (bar_x + bar_w + 5, bar_y - 2))

    def draw_panel(self):
        ELEMENTS = self.db.elements
        CATEGORIES = self.db.categories
        pygame.draw.rect(self.screen, C_PANEL_BG, (PANEL_X, 0, PANEL_W, SCREEN_H))
        pygame.draw.line(self.screen, C_WORKSPACE_BD, (PANEL_X + PANEL_W - 1, 0),
                         (PANEL_X + PANEL_W - 1, SCREEN_H), 2)
        self.draw_header()

        # Category tabs
        tab_y, tab_h = 62, 28
        cats = [("all", "All")] + [(k, v["name"]) for k, v in CATEGORIES.items()]
        tab_w = (PANEL_W - 10) // len(cats)
        mouse_pos = pygame.mouse.get_pos()

        for i, (cat_key, cat_name) in enumerate(cats):
            tx = PANEL_X + 5 + i * tab_w
            rect = pygame.Rect(tx, tab_y, tab_w - 2, tab_h)
            is_active = self.active_category == cat_key
            is_hover = rect.collidepoint(mouse_pos)
            color = C_ACCENT if is_active else (C_BTN_HOVER if is_hover else C_BTN)
            pygame.draw.rect(self.screen, color, rect, border_radius=4)
            count = len(self.discovered) if cat_key == "all" else len(
                [e for e in self.discovered if ELEMENTS[e]["cat"] == cat_key])
            text = self.font_xs.render(f"{cat_name} ({count})", True, C_BTN_TEXT)
            self.screen.blit(text, text.get_rect(center=rect.center))

        # Element list
        list_y = tab_y + tab_h + 8
        list_h = SCREEN_H - list_y - 5
        clip_rect = pygame.Rect(PANEL_X, list_y, PANEL_W, list_h)
        self.screen.set_clip(clip_rect)

        elements = self.get_category_elements()
        current_cat = None
        y = list_y + self.panel_scroll

        for elem_key in elements:
            elem = ELEMENTS[elem_key]
            if elem["cat"] != current_cat:
                current_cat = elem["cat"]
                cat_info = CATEGORIES.get(current_cat, {})
                cat_rect = pygame.Rect(PANEL_X + 5, y, PANEL_W - 10, 24)
                if cat_rect.bottom > list_y and cat_rect.top < list_y + list_h:
                    pygame.draw.rect(self.screen, C_CATEGORY_BG, cat_rect, border_radius=3)
                    cat_text = self.font_xs.render(cat_info.get("name", current_cat), True,
                                                   cat_info.get("color", C_TEXT_DIM))
                    self.screen.blit(cat_text, (cat_rect.x + 8, cat_rect.y + 4))
                y += 28

            card_rect = pygame.Rect(PANEL_X + 5, y, CARD_W + 10, CARD_H + 4)
            is_hover = card_rect.collidepoint(mouse_pos) and not self.dragging
            bg_color = lerp_color(C_SLOT_BG, elem["color"], 0.15 if not is_hover else 0.3)

            if card_rect.bottom > list_y and card_rect.top < list_y + list_h:
                pygame.draw.rect(self.screen, bg_color, card_rect, border_radius=6)
                pygame.draw.rect(self.screen, lerp_color(elem["color"], (100, 100, 100), 0.3),
                                 card_rect, 2, border_radius=6)
                icon_x = card_rect.x + 25
                icon_y = card_rect.centery
                # Glow
                glow_surf = pygame.Surface((64, 64), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*elem["color"], 30), (32, 32), 32)
                self.screen.blit(glow_surf, (icon_x - 32, icon_y - 32))
                draw_icon(self.screen, elem["icon"], icon_x, icon_y, 16, elem["color"])
                name_text = self.font_sm.render(elem["name"], True, C_TEXT)
                self.screen.blit(name_text, (card_rect.x + 50, card_rect.y + 10))
                cat_color = CATEGORIES.get(elem["cat"], {}).get("color", C_TEXT_DIM)
                pygame.draw.circle(self.screen, cat_color, (card_rect.right - 15, card_rect.y + 15), 5)
                if is_hover:
                    self.hover_element = elem_key
                    self.tooltip = (elem["name"], elem["desc"])

            y += CARD_H + CARD_MARGIN

        self.content_height = y - self.panel_scroll - list_y
        self.screen.set_clip(None)

        # Scrollbar
        if self.content_height > list_h:
            sb_x = PANEL_X + PANEL_W - 8
            sb_h = max(20, int(list_h * (list_h / self.content_height)))
            sb_y = list_y + int(max(0, self.panel_scroll * (list_h / max(1, self.content_height))))
            sb_y = max(list_y, min(list_y + list_h - sb_h, sb_y))
            pygame.draw.rect(self.screen, C_ACCENT, (sb_x, sb_y, 5, sb_h), border_radius=3)

    def draw_workspace(self):
        ELEMENTS = self.db.elements
        ws_rect = pygame.Rect(WORKSPACE_X, WORKSPACE_Y, WORKSPACE_W, WORKSPACE_H)
        pygame.draw.rect(self.screen, C_WORKSPACE, ws_rect, border_radius=4)
        pygame.draw.rect(self.screen, C_WORKSPACE_BD, ws_rect, 2, border_radius=4)

        ws_title = self.font_md.render("Combination Altar", True, C_TEXT_DIM)
        self.screen.blit(ws_title, ws_title.get_rect(centerx=WORKSPACE_X + WORKSPACE_W // 2, y=WORKSPACE_Y + 10))

        if self.slot1 is None and self.slot2 is None and not self.dragging:
            inst = self.font_sm.render("Drag elements here to combine them", True,
                                        lerp_color(C_TEXT_DIM, C_TEXT, 0.3))
            self.screen.blit(inst, inst.get_rect(centerx=WORKSPACE_X + WORKSPACE_W // 2,
                                                  y=DROP_ZONE_Y + DROP_ZONE_H + 20))

        plus_x = WORKSPACE_X + WORKSPACE_W // 2
        plus_y = DROP_ZONE_Y + DROP_ZONE_H // 2
        self.screen.blit(self.font_lg.render("+", True, C_ACCENT),
                         self.font_lg.render("+", True, C_ACCENT).get_rect(center=(plus_x, plus_y)))

        self._draw_drop_zone(DROP_ZONE_1_X, DROP_ZONE_Y, self.slot1, "Slot 1")
        self._draw_drop_zone(DROP_ZONE_2_X, DROP_ZONE_Y, self.slot2, "Slot 2")

        if self.combination_flash:
            color, timer = self.combination_flash
            flash_surf = pygame.Surface((WORKSPACE_W, WORKSPACE_H), pygame.SRCALPHA)
            pygame.draw.rect(flash_surf, (*color, min(60, int(255 * timer))), (0, 0, WORKSPACE_W, WORKSPACE_H))
            self.screen.blit(flash_surf, (WORKSPACE_X, WORKSPACE_Y))

        self.particles.draw(self.screen)

        if self.show_hints:
            self._draw_hints()

    def _draw_drop_zone(self, x, y, element_key, label):
        ELEMENTS = self.db.elements
        rect = pygame.Rect(x, y, DROP_ZONE_W, DROP_ZONE_H)
        if element_key:
            elem = ELEMENTS[element_key]
            bg = lerp_color(C_SLOT_BG, elem["color"], 0.25)
            pygame.draw.rect(self.screen, bg, rect, border_radius=10)
            pygame.draw.rect(self.screen, elem["color"], rect, 3, border_radius=10)
            draw_icon(self.screen, elem["icon"], x + 35, y + DROP_ZONE_H // 2, 22, elem["color"])
            name = self.font_md.render(elem["name"], True, C_TEXT)
            self.screen.blit(name, (x + 65, y + (DROP_ZONE_H - name.get_height()) // 2))
            hint = self.font_xs.render("Right-click to remove", True, C_TEXT_DIM)
            self.screen.blit(hint, (x + 65, y + DROP_ZONE_H - 20))
        else:
            pygame.draw.rect(self.screen, C_SLOT_BG, rect, border_radius=10)
            pygame.draw.rect(self.screen, C_SLOT_BD, rect, 2, border_radius=10)
            lbl = self.font_sm.render(label, True, C_TEXT_DIM)
            self.screen.blit(lbl, lbl.get_rect(center=rect.center))

    def _draw_hints(self):
        ELEMENTS = self.db.elements
        hints = self.get_hints()
        ox, oy = WORKSPACE_X + 20, WORKSPACE_Y + 40
        if not hints:
            t = self.font_md.render("No hints available!", True, C_TEXT)
            self.screen.blit(t, t.get_rect(centerx=WORKSPACE_X + WORKSPACE_W // 2, y=oy))
            return
        h = min(400, 40 + len(hints[:8]) * 30)
        overlay = pygame.Surface((WORKSPACE_W - 40, h), pygame.SRCALPHA)
        overlay.fill((20, 20, 35, 200))
        self.screen.blit(overlay, (ox, oy))
        title = self.font_md.render(f"Hints ({len(hints)} possible)", True, C_ACCENT)
        self.screen.blit(title, (ox + 10, oy + 5))
        for i, (a, b, result) in enumerate(hints[:8]):
            ry = oy + 35 + i * 30
            pygame.draw.circle(self.screen, ELEMENTS[a]["color"], (ox + 15, ry + 10), 6)
            pygame.draw.circle(self.screen, ELEMENTS[b]["color"], (ox + 27, ry + 10), 6)
            pygame.draw.circle(self.screen, ELEMENTS[result]["color"], (ox + 39, ry + 10), 6)
            text = self.font_sm.render(f"{ELEMENTS[a]['name']} + {ELEMENTS[b]['name']} = ???", True, C_TEXT_DIM)
            self.screen.blit(text, (ox + 50, ry))
        if len(hints) > 8:
            more = self.font_xs.render(f"...and {len(hints) - 8} more", True, C_TEXT_DIM)
            self.screen.blit(more, (ox + 50, oy + 35 + 8 * 30))

    def draw_tooltip(self):
        if self.tooltip and self.dragging is None:
            name, desc = self.tooltip
            mx, my = pygame.mouse.get_pos()
            lines = [name, desc]
            max_w = max(self.font_sm.size(t)[0] for t in lines) + 20
            h = len(lines) * 22 + 12
            tx = min(mx + 15, SCREEN_W - max_w - 5)
            ty = max(5, my - h - 5)
            pygame.draw.rect(self.screen, C_TOOLTIP_BG, (tx, ty, max_w, h), border_radius=5)
            pygame.draw.rect(self.screen, C_TOOLTIP_BD, (tx, ty, max_w, h), 1, border_radius=5)
            for i, line in enumerate(lines):
                color = C_TEXT if i == 0 else C_TEXT_DIM
                self.screen.blit(self.font_sm.render(line, True, color), (tx + 10, ty + 6 + i * 22))

    def draw_dragging(self):
        ELEMENTS = self.db.elements
        if self.dragging:
            elem = ELEMENTS[self.dragging]
            mx, my = self.drag_pos
            card_w, card_h = DROP_ZONE_W, DROP_ZONE_H
            rect = pygame.Rect(mx - card_w // 2, my - card_h // 2, card_w, card_h)
            surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            pygame.draw.rect(surf, (*lerp_color(C_SLOT_BG, elem["color"], 0.3), 200), (0, 0, card_w, card_h),
                             border_radius=10)
            pygame.draw.rect(surf, (*elem["color"], 255), (0, 0, card_w, card_h), 3, border_radius=10)
            self.screen.blit(surf, rect.topleft)
            draw_icon(self.screen, elem["icon"], rect.centerx - 30, rect.centery, 22, elem["color"])
            name = self.font_md.render(elem["name"], True, C_TEXT)
            self.screen.blit(name, name.get_rect(center=(rect.centerx + 20, rect.centery)))

    def draw_buttons(self):
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.buttons:
            is_hover = btn["rect"].collidepoint(mouse_pos)
            color = C_BTN_HOVER if is_hover else C_BTN
            pygame.draw.rect(self.screen, color, btn["rect"], border_radius=6)
            pygame.draw.rect(self.screen, C_SLOT_BD, btn["rect"], 1, border_radius=6)
            text = self.font_sm.render(btn["text"], True, C_BTN_TEXT)
            self.screen.blit(text, text.get_rect(center=btn["rect"].center))

    def draw_notifications(self):
        y = SCREEN_H - 10
        for notif in reversed(self.notifications):
            alpha = min(1.0, notif.timer / 0.5)
            dimmed = tuple(int(c * alpha) for c in notif.color)
            text = self.font_md.render(notif.text, True, dimmed)
            y -= 30 - notif.y_offset
            text_rect = text.get_rect(centerx=WORKSPACE_X + WORKSPACE_W // 2, y=y)
            bg_rect = text_rect.inflate(20, 8)
            bg_surf = pygame.Surface((bg_rect.w, bg_rect.h), pygame.SRCALPHA)
            pygame.draw.rect(bg_surf, (*C_BG, int(180 * alpha)), (0, 0, bg_rect.w, bg_rect.h), border_radius=5)
            self.screen.blit(bg_surf, bg_rect.topleft)
            self.screen.blit(text, text_rect)

    def draw_new_discovery(self):
        ELEMENTS = self.db.elements
        if self.new_discovery_anim:
            elem_key, duration, start = self.new_discovery_anim
            elapsed = time.time() - start
            if elapsed > duration:
                self.new_discovery_anim = None
                return
            elem = ELEMENTS[elem_key]
            progress = elapsed / duration
            scale = min(1.0, progress * 3) * (1.0 if progress < 0.7 else max(0, 1.0 - (progress - 0.7) / 0.3))
            cx = WORKSPACE_X + WORKSPACE_W // 2
            cy = WORKSPACE_Y + WORKSPACE_H // 2
            size = int(60 * scale)
            if size > 0:
                glow_surf = pygame.Surface((size * 6, size * 6), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*elem["color"], int(80 * scale)), (size * 3, size * 3), size * 3)
                self.screen.blit(glow_surf, (cx - size * 3, cy - size * 3))
                draw_icon(self.screen, elem["icon"], cx, cy, size, elem["color"])
                alpha = min(1.0, progress * 2)
                name_color = tuple(int(c * alpha) for c in C_SUCCESS)
                name = self.font_lg.render(elem["name"], True, name_color)
                self.screen.blit(name, name.get_rect(centerx=cx, y=cy + size + 10))

    def _get_card_rects(self):
        ELEMENTS = self.db.elements
        card_rects = []
        elements = self.get_category_elements()
        list_y = 62 + 28 + 8
        current_cat = None
        y = list_y + self.panel_scroll
        for elem_key in elements:
            elem = ELEMENTS[elem_key]
            if elem["cat"] != current_cat:
                current_cat = elem["cat"]
                y += 28
            card_rects.append((elem_key, pygame.Rect(PANEL_X + 5, y, CARD_W + 10, CARD_H + 4)))
            y += CARD_H + CARD_MARGIN
        return card_rects

    def handle_click(self, pos, button):
        CATEGORIES = self.db.categories
        mx, my = pos
        # Category tabs
        tab_y, tab_h = 62, 28
        cats = ["all"] + list(CATEGORIES.keys())
        tab_w = (PANEL_W - 10) // len(cats)
        for i, cat_key in enumerate(cats):
            tx = PANEL_X + 5 + i * tab_w
            rect = pygame.Rect(tx, tab_y, tab_w - 2, tab_h)
            if rect.collidepoint(mx, my):
                self.active_category = cat_key
                self.panel_scroll = 0
                return

        # Buttons
        for btn in self.buttons:
            if btn["rect"].collidepoint(mx, my):
                if btn["action"] == "hints":
                    self.show_hints = not self.show_hints
                elif btn["action"] == "reset":
                    self.reset()
                elif btn["action"] == "clear":
                    self.slot1 = None
                    self.slot2 = None
                return

        # Element cards
        if button == 1:
            for elem_key, rect in self._get_card_rects():
                if rect.collidepoint(mx, my):
                    self.dragging = elem_key
                    self.drag_from_panel = True
                    self.drag_pos = (mx, my)
                    return

            # Drop zones (grab from slot)
            dz1 = pygame.Rect(DROP_ZONE_1_X, DROP_ZONE_Y, DROP_ZONE_W, DROP_ZONE_H)
            dz2 = pygame.Rect(DROP_ZONE_2_X, DROP_ZONE_Y, DROP_ZONE_W, DROP_ZONE_H)
            if dz1.collidepoint(mx, my) and self.slot1:
                self.dragging = self.slot1
                self.drag_from_panel = False
                self.slot1 = None
                self.drag_pos = (mx, my)
                return
            if dz2.collidepoint(mx, my) and self.slot2:
                self.dragging = self.slot2
                self.drag_from_panel = False
                self.slot2 = None
                self.drag_pos = (mx, my)
                return

        elif button == 3:
            dz1 = pygame.Rect(DROP_ZONE_1_X, DROP_ZONE_Y, DROP_ZONE_W, DROP_ZONE_H)
            dz2 = pygame.Rect(DROP_ZONE_2_X, DROP_ZONE_Y, DROP_ZONE_W, DROP_ZONE_H)
            if dz1.collidepoint(mx, my):
                self.slot1 = None
                return
            if dz2.collidepoint(mx, my):
                self.slot2 = None
                return

    def handle_drop(self, pos):
        if not self.dragging:
            return
        mx, my = pos
        elem_key = self.dragging
        self.dragging = None
        dz1 = pygame.Rect(DROP_ZONE_1_X, DROP_ZONE_Y, DROP_ZONE_W, DROP_ZONE_H)
        dz2 = pygame.Rect(DROP_ZONE_2_X, DROP_ZONE_Y, DROP_ZONE_W, DROP_ZONE_H)

        if dz1.collidepoint(mx, my) or dz2.collidepoint(mx, my):
            self.add_to_slot(elem_key)
            if self.slot1 and self.slot2:
                self.combine(self.slot1, self.slot2)
        elif not self.drag_from_panel:
            if self.slot1 is None:
                self.slot1 = elem_key
            elif self.slot2 is None:
                self.slot2 = elem_key

    def handle_scroll(self, dy):
        list_y = 62 + 28 + 8
        list_h = SCREEN_H - list_y - 5
        if self.content_height > list_h:
            max_scroll = 0
            min_scroll = -(self.content_height - list_h)
            self.panel_scroll = max(min_scroll, min(max_scroll, self.panel_scroll + dy * 30))

    def run(self):
        running = True
        last_time = time.time()

        while running:
            current_time = time.time()
            dt = min(current_time - last_time, 0.05)
            last_time = current_time

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button in (1, 3):
                        self.handle_click(event.pos, event.button)
                    elif event.button == 4:
                        self.handle_scroll(1)
                    elif event.button == 5:
                        self.handle_scroll(-1)
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.handle_drop(event.pos)
                elif event.type == pygame.MOUSEMOTION:
                    self.drag_pos = event.pos
                elif event.type == pygame.MOUSEWHEEL:
                    self.handle_scroll(event.y)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_h:
                        self.show_hints = not self.show_hints
                    elif event.key == pygame.K_r:
                        self.reset()
                    elif event.key == pygame.K_ESCAPE:
                        running = False

            self.particles.update(dt)
            for n in self.notifications:
                n.update(dt)
            self.notifications = [n for n in self.notifications if n.is_alive()]

            if self.combination_flash:
                color, timer = self.combination_flash
                timer -= dt
                self.combination_flash = (color, timer) if timer > 0 else None

            self.hover_element = None
            self.tooltip = None

            self.draw_background()
            self.draw_panel()
            self.draw_workspace()
            self.draw_buttons()
            self.draw_notifications()
            self.draw_dragging()
            self.draw_new_discovery()
            self.draw_tooltip()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = DoodleGodGame()
    game.run()
