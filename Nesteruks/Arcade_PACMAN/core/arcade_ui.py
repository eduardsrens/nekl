"""The Pac-Man-inspired arcade page hosted by Maze Atelier's single window."""

from __future__ import annotations

import math
import random
import time
import tkinter as tk

if __package__:
    from .arcade_core import ArcadeGame, DIFFICULTIES, ProfileStore, SIZES, alternative_routes, maze_filename
else:
    from arcade_core import ArcadeGame, DIFFICULTIES, ProfileStore, SIZES, alternative_routes, maze_filename


class ArcadePage:
    BG = "#070b19"
    PANEL = "#10182c"
    BORDER = "#273654"
    YELLOW = "#ffda55"
    BLUE = "#4a7cff"
    MUTED = "#8a9bbb"
    GHOST_COLORS = ("#ff668d", "#66e2ef", "#c79bff", "#ffa866")

    def __init__(self, host):
        self.host, self.canvas = host, host.canvas
        self.folder = host.folder
        self.profile = ProfileStore(self.folder / "saves")
        self.size_index, self.difficulty, self.mode, self.level = 1, "Arcade", "hunt", 1
        self.seed = tk.StringVar(master=host.root)
        self.entry = tk.Entry(
            self.canvas, textvariable=self.seed, bg="#0a1122", fg="#edf3fa",
            insertbackground=self.YELLOW, selectbackground=self.YELLOW, selectforeground=self.BG,
            relief="flat", font=("Consolas", 10), borderwidth=0,
        )
        self.entry.bind("<Return>", lambda _event: self.load_seed())
        self.entry.bind("<FocusIn>", lambda _event: self.pause_for_focus())
        self.timer_id = None
        self.last_frame = time.perf_counter()
        self.saved_terminal = False
        self.show_paths = False
        self.route_index = 0
        self.routes = []
        self.hint_route = []
        self.previous_remaining = set()
        self.message = ""
        self.game = None
        self.new_game(random_seed=True, redraw=False)

    def make_seed(self):
        return str(random.SystemRandom().randrange(1_000_000_000))

    def new_game(self, random_seed=False, redraw=True):
        value = self.make_seed() if random_seed else self.seed.get().strip()
        if not value:
            value = self.make_seed()
        if len(value) > 48:
            self.message = "Keep your seed to 48 characters or fewer."
            if redraw:
                self.host.render()
            return
        self.seed.set(value)
        self.game = ArcadeGame(value, self.size_index, self.difficulty, self.mode, self.level)
        self.after_new_game()
        if redraw:
            self.host.render()
            self.canvas.focus_set()

    def after_new_game(self):
        self.saved_terminal = False
        self.show_paths = False
        self.routes = []
        self.route_index = 0
        self.hint_route = []
        self.message = "Find the exit. Pellets are a bonus." if self.mode == "maze" else "Collect every dot to unlock the exit. Power orbs turn the tables."
        self.last_frame = time.perf_counter()

    def enter(self):
        self.last_frame = time.perf_counter()
        if self.timer_id is None:
            self.timer_id = self.host.root.after(30, self.tick)

    def leave(self):
        if self.game.state == "playing":
            self.game.state = "paused"
        if self.timer_id is not None:
            self.host.root.after_cancel(self.timer_id)
            self.timer_id = None
        self.entry.selection_clear()

    def text(self, *args, **kwargs):
        return self.host.text(*args, **kwargs)

    def box(self, *args, **kwargs):
        return self.host.rounded(*args, **kwargs)

    def button(self, x, y, width, height, label, callback, primary=False, selected=False, tags=()):
        fill = self.YELLOW if primary else ("#243971" if selected else "#1b2845")
        shape = self.box(x, y, width, height, fill, radius=8, outline=self.BLUE if selected else "", tags=tags)
        self.text(x + width / 2, y + height / 2, label, 9, self.BG if primary else "#eaf0ff", True, "center", tags=tags)
        self.host.hit((x, y, x + width, y + height), callback, shape, fill)

    def render(self):
        self.width, self.height = self.host.width, self.host.height
        self.right, self.bottom = self.width - 28, self.height - 56
        self.board_x = 314
        self.canvas.configure(bg=self.BG)
        self.draw_header()
        self.draw_settings()
        self.draw_board()
        self.draw_controls()
        self.draw_dynamic()
        self.draw_overlay()
        self.text(28, self.height - 25, "ARROWS / WASD  Move     SPACE  Pause     H  Hint     V  Paths", 9, self.MUTED)
        self.text(self.right, self.height - 25, "N  New maze     R  Retry     ENTER  Continue", 9, self.MUTED, anchor="e")

    def draw_header(self):
        self.box(28, 26, 45, 45, "#29251d", radius=12)
        self.canvas.create_arc(38, 36, 65, 63, start=35, extent=290, fill=self.YELLOW, outline="")
        self.text(87, 39, "MAZE / ARCADE", 17, bold=True)
        self.text(88, 62, "N E O N   N I G H T S   /   N E S T E R U K S", 8, self.MUTED)
        self.button(self.right - 158, 31, 158, 38, "\u2190  Route Explorer", self.host.show_explorer)
        self.text(self.right - 188, 43, "PROCEDURAL. REPLAYABLE.", 8, self.MUTED, anchor="e")
        self.text(28, 112, "ONE MORE LEVEL.", 27, bold=True)
        self.text(390, 118, "Classic chase. A different maze every time.", 11, self.MUTED)
        self.canvas.create_line(28, 143, self.right, 143, fill=self.BORDER)

    def draw_settings(self):
        self.box(28, 160, 268, self.bottom - 160, self.PANEL, outline=self.BORDER)
        self.text(48, 186, "MAKE IT YOURS", 12, bold=True)
        self.button(48, 211, 108, 33, "Pellet hunt", lambda: self.set_option("mode", "hunt"), selected=self.mode == "hunt")
        self.button(164, 211, 112, 33, "Maze run", lambda: self.set_option("mode", "maze"), selected=self.mode == "maze")
        self.text(48, 266, "MAZE SIZE", 8, self.MUTED, True)
        for index, (name, rows, columns) in enumerate(SIZES):
            x, y = 48 + (index % 2) * 118, 281 + (index // 2) * 38
            self.button(x, y, 110, 31, f"{name}  {rows}\u00d7{columns}", lambda i=index: self.set_option("size_index", i), selected=index == self.size_index)
        self.text(48, 372, "DIFFICULTY", 8, self.MUTED, True)
        for index, difficulty in enumerate(DIFFICULTIES):
            self.button(48 + index * 79, 386, 71, 32, difficulty, lambda value=difficulty: self.set_option("difficulty", value), selected=difficulty == self.difficulty)
        self.text(48, 449, "LEVEL", 8, self.MUTED, True)
        self.button(125, 433, 34, 32, "\u2212", lambda: self.set_level(-1))
        self.text(195, 449, f"{self.level:02}", 17, self.YELLOW, True, "center")
        self.button(242, 433, 34, 32, "+", lambda: self.set_level(1))
        self.text(48, 491, "SEED  /  REPLAY THE SAME WORLD", 8, self.MUTED, True)
        self.box(48, 507, 228, 35, "#0a1122", radius=7, outline=self.BORDER)
        self.canvas.create_window(59, 514, window=self.entry, width=205, height=21, anchor="nw")
        self.button(48, 553, 105, 35, "Load seed", self.load_seed)
        self.button(163, 553, 113, 35, "New random", lambda: self.new_game(random_seed=True), primary=True)
        if self.bottom >= 750:
            self.text(48, 621, "Bigger mazes every three levels.", 9, self.MUTED)
            self.text(48, 643, "4 sizes. 3 difficulties. 99 levels.", 9, self.MUTED)
            self.text(48, 675, "OPEN ROOMS + WINDING CORRIDORS", 7, self.YELLOW)
        self.button(48, self.bottom - 61, 228, 36, "Save this maze   \u2197", self.save_maze)

    def draw_board(self):
        game = self.game
        self.box(self.board_x, 160, self.right - self.board_x, self.bottom - 160, self.PANEL, outline=self.BORDER)
        spacing = (self.right - self.board_x - 48) / 4
        self.stat_ids = {}
        for index, (key, label) in enumerate((("score", "SCORE"), ("best", "PERSONAL BEST"), ("level", "LEVEL"), ("lives", "LIVES"))):
            x = self.board_x + 24 + index * spacing
            self.text(x, 184, label, 8, self.MUTED, True)
            self.stat_ids[key] = self.text(x, 210, "", 20, self.YELLOW if key in ("score", "lives") else "#edf3fa", True)
        left, top, right, bottom = self.board_x + 22, 242, self.right - 22, self.bottom - 123
        self.viewport = left, top, right, bottom
        self.box(left, top, right - left, bottom - top, "#050913", radius=12, outline="#213c79")
        maze = game.maze
        size = min((right - left - 32) / maze.columns, (bottom - top - 32) / maze.rows)
        x0, y0 = (left + right - size * maze.columns) / 2, (top + bottom - size * maze.rows) / 2
        self.geometry = x0, y0, size
        for row, column, height, width in maze.rooms:
            self.box(x0+column*size, y0+row*size, width*size, height*size, "#0d1729", radius=5, outline="#172642")
        for row, line in enumerate(maze.grid):
            for column, char in enumerate(line):
                if char == "#":
                    x, y = x0 + column * size, y0 + row * size
                    self.canvas.create_rectangle(x, y, x + size, y + size, fill="#101d43", outline="")
        for row, line in enumerate(maze.grid):
            for column, char in enumerate(line):
                if char != "#":
                    continue
                x, y = x0 + column * size, y0 + row * size
                edges = (((-1, 0), (x, y, x + size, y)), ((0, 1), (x + size, y, x + size, y + size)), ((1, 0), (x, y + size, x + size, y + size)), ((0, -1), (x, y, x, y + size)))
                for (dr, dc), points in edges:
                    if (row + dr, column + dc) in maze.neighbors:
                        self.canvas.create_line(*points, fill="#19366f", width=4, capstyle="round")
                        self.canvas.create_line(*points, fill="#4b78ef", width=1.2, capstyle="round")
        self.canvas.create_rectangle(x0, y0, x0 + maze.columns * size, y0 + maze.rows * size, outline="#244787")
        self.previous_remaining = game.pellets.copy()
        for cell in game.pellets:
            x, y = self.center(cell)
            r = max(1.1, size * 0.075)
            self.canvas.create_oval(x-r, y-r, x+r, y+r, fill="#ffe3a6", outline="", tags=self.pellet_tag(cell))

    @staticmethod
    def pellet_tag(cell):
        return f"pellet_{cell[0]}_{cell[1]}"

    def center(self, cell):
        x, y, size = self.geometry
        return x + (cell[1] + 0.5) * size, y + (cell[0] + 0.5) * size

    def draw_controls(self):
        left, _, right, bottom = self.viewport
        self.stat_ids["status"] = self.text(left + 2, bottom + 20, "", 8, self.MUTED)
        self.stat_ids["time"] = self.text(right - 2, bottom + 20, "", 9, self.MUTED, anchor="e")
        y = bottom + 39
        label = "Pause" if self.game.state == "playing" else ("Continue" if self.game.state == "paused" else "Start")
        self.button(left, y, 100, 38, label, self.toggle_pause, primary=True)
        self.button(left + 109, y, 67, 38, "Hint", self.hint)
        self.button(left + 185, y, 102, 38, "Hide ways" if self.show_paths else "Show ways", self.toggle_paths, selected=self.show_paths)
        self.button(left + 296, y, 108, 38, "Stop auto" if self.game.auto else "Auto solve", self.toggle_auto, selected=self.game.auto)
        self.button(left + 413, y, 78, 38, "Retry", self.retry)
        if self.show_paths and self.routes:
            self.button(left, bottom + 84, 27, 23, "\u2190", lambda: self.change_route(-1))
            self.text(left + 39, bottom + 96, f"PATH {self.route_index + 1:02}/{len(self.routes):02}  \u00b7  {len(self.routes[self.route_index])-1} steps", 8, self.YELLOW)
            self.button(left + 205, bottom + 84, 27, 23, "\u2192", lambda: self.change_route(1))
            self.text(right, bottom + 96, "Sampled alternatives \u00b7 ordered by length", 8, self.MUTED, anchor="e")
        else:
            self.stat_ids["message"] = self.text(left, bottom + 97, self.message, 8, self.MUTED)

    def line(self, cells, color, width=2):
        points = [coordinate for cell in cells for coordinate in self.center(cell)]
        if len(points) >= 4:
            self.canvas.create_line(points, fill=color, width=width, capstyle="round", joinstyle="round", tags="arcade_dynamic")

    def draw_dynamic(self):
        game, tag = self.game, "arcade_dynamic"
        self.canvas.delete(tag)
        for cell in self.previous_remaining - game.pellets:
            self.canvas.delete(self.pellet_tag(cell))
        self.previous_remaining = game.pellets.copy()
        size = self.geometry[2]
        if self.show_paths and self.routes:
            route = self.routes[self.route_index]
            self.line(route, "#263350", max(5, size * 0.45))
            self.line(route, "#7b96ff", max(1.5, size * 0.14))
        if self.hint_route:
            self.line(self.hint_route, "#776c2d", max(5, size * 0.4))
            self.line(self.hint_route, self.YELLOW, max(2, size * 0.17))
        pulse = 1 + 0.13 * math.sin(time.perf_counter() * 5)
        for cell in game.powers:
            x, y = self.center(cell)
            radius = max(3, size * 0.19) * pulse
            self.canvas.create_oval(x-radius*2, y-radius*2, x+radius*2, y+radius*2, fill="#2e2449", outline="", tags=tag)
            self.canvas.create_oval(x-radius, y-radius, x+radius, y+radius, fill="#e5bdff", outline="", tags=tag)

        x, y = self.center(game.maze.goal)
        radius = max(5, size * 0.32)
        color = "#79f3cb" if game.exit_open else "#d49df9"
        self.canvas.create_rectangle(x-radius, y-radius, x+radius, y+radius, fill="#132232", outline=color, width=2, tags=tag)
        self.text(x, y, "E" if game.exit_open else "\u00d7", max(7, int(size * 0.3)), color, True, "center", tags=tag)

        for index, ghost in enumerate(game.ghosts):
            if ghost.respawn:
                continue
            x, y = self.center(ghost.position)
            if ghost.previous is not None:
                px, py = self.center(ghost.previous)
                fraction = min(1.0, game.ghost_clock / game.ghost_interval)
                x, y = px + (x-px)*fraction, py + (y-py)*fraction
            color = "#557dff" if game.power_remaining else self.GHOST_COLORS[index % 4]
            self.draw_ghost(x, y, size * 0.38, color, tag)

        x, y = self.center(game.player)
        if game.previous_player != game.player and game.state == "playing":
            px, py = self.center(game.previous_player)
            fraction = min(1.0, game.player_clock / game.player_interval)
            x, y = px + (x-px)*fraction, py + (y-py)*fraction
        radius = max(4.5, size * 0.38)
        angle = {(0, 1): 0, (-1, 0): 90, (0, -1): 180, (1, 0): 270}[game.facing]
        mouth = 15 + 15 * abs(math.sin(time.perf_counter() * 11))
        color = "#9f8c42" if game.invulnerable and int(time.perf_counter()*8) % 2 else self.YELLOW
        self.canvas.create_oval(x-radius*1.5, y-radius*1.5, x+radius*1.5, y+radius*1.5, fill="#252415", outline="", tags=tag)
        self.canvas.create_arc(x-radius, y-radius, x+radius, y+radius, start=angle+mouth, extent=360-2*mouth, fill=color, outline="", tags=tag)
        eye_x, eye_y = x + radius*0.14, y - radius*0.47
        self.canvas.create_oval(eye_x-1, eye_y-1, eye_x+1, eye_y+1, fill="#1d2033", outline="", tags=tag)

        self.canvas.itemconfigure(self.stat_ids["score"], text=f"{game.score:06}")
        self.canvas.itemconfigure(self.stat_ids["best"], text=f"{self.profile.data['high_score']:06}")
        self.canvas.itemconfigure(self.stat_ids["level"], text=f"{game.level:02}  /  {SIZES[game.size_index][0]}")
        self.canvas.itemconfigure(self.stat_ids["lives"], text="\u25cf  " * game.lives)
        status = f"{game.remaining:03} DOTS   /   {game.moves:03} MOVES   /   {len(game.maze.rooms)} ROOMS"
        if game.power_remaining:
            status += f"   /   POWER {math.ceil(game.power_remaining)}s"
        if game.assisted:
            status += "   /   ASSISTED"
        minutes, seconds = divmod(int(game.elapsed), 60)
        self.canvas.itemconfigure(self.stat_ids["status"], text=status)
        self.canvas.itemconfigure(self.stat_ids["time"], text=f"{minutes:02}:{seconds:02}")
        if "message" in self.stat_ids:
            self.canvas.itemconfigure(self.stat_ids["message"], text=self.message)
        self.canvas.tag_raise("arcade_overlay")

    def draw_ghost(self, x, y, radius, color, tag):
        points = []
        for index in range(13):
            angle = math.pi - index * math.pi / 12
            points.extend((x + radius * math.cos(angle), y - radius * math.sin(angle)))
        points.extend((x+radius, y+radius, x+radius*.55, y+radius*.55, x+radius*.2, y+radius, x-radius*.2, y+radius*.55, x-radius*.55, y+radius, x-radius, y+radius*.65))
        self.canvas.create_polygon(points, fill=color, outline="", tags=tag)
        for offset in (-0.36, 0.36):
            ex, ey, r = x + radius*offset, y-radius*.08, radius*.24
            self.canvas.create_oval(ex-r, ey-r*1.3, ex+r, ey+r*1.3, fill="#f4f7ff", outline="", tags=tag)
            self.canvas.create_oval(ex-r*.25, ey-r*.3, ex+r*.7, ey+r*.7, fill="#152047", outline="", tags=tag)

    def draw_overlay(self):
        state = self.game.state
        if state == "playing" or (state == "paused" and (self.show_paths or self.hint_route)):
            return
        left, top, right, bottom = self.viewport
        width, height = min(390, right-left-32), 214
        x, y = (left+right-width)/2, (top+bottom-height)/2
        tag = "arcade_overlay"
        self.canvas.create_rectangle(left+2, top+2, right-2, bottom-2, fill=self.BG, stipple="gray50", outline="", tags=tag)
        self.box(x, y, width, height, "#101a32", radius=16, outline="#4665aa", tags=tag)
        if state == "ready":
            title, eyebrow = "READY, PLAYER ONE?", f"LEVEL {self.game.level:02}  /  {self.difficulty.upper()}"
            description = "Eat every dot, then reach the exit.\nPower orbs let you eat the ghosts." if self.mode == "hunt" else "Find the glowing exit. No ghosts.\nTake your own route, or ask for a hint."
            label, action = "LET'S PLAY", self.toggle_pause
        elif state == "paused":
            title, eyebrow = "TAKE A BREATHER.", "GAME PAUSED"
            description = "Your maze will be right here.\nPress Space or Continue when you're ready."
            label, action = "CONTINUE", self.toggle_pause
        elif state == "won":
            title, eyebrow = "MAZE CLEARED.", f"LEVEL {self.game.level:02} COMPLETE"
            description = f"{self.game.score:,} points  /  {self.game.moves} moves\n" + ("Assisted run. Personal records are unchanged." if self.game.assisted else "Clean run. Your personal record is saved.")
            label, action = "NEXT LEVEL  \u2192", self.continue_game
        else:
            title, eyebrow = "ONE MORE TRY?", "GAME OVER"
            description = f"{self.game.score:,} points. A little wiser.\nReplay the same maze and find your rhythm."
            label, action = "TRY AGAIN", self.retry
        self.text(x+width/2, y+28, eyebrow, 8, self.YELLOW, True, "center", tags=tag)
        self.text(x+width/2, y+65, title, 21, bold=True, anchor="center", tags=tag)
        self.text(x+width/2, y+111, description, 10, self.MUTED, anchor="center", justify="center", tags=tag)
        self.button(x+(width-176)/2, y+154, 176, 38, label, action, primary=True, tags=tag)

    def tick(self):
        self.timer_id = None
        if self.host.closed or self.host.page != "arcade":
            return
        now = time.perf_counter()
        previous_state = self.game.state
        previous_player = self.game.player
        self.game.advance(now - self.last_frame)
        self.last_frame = now
        if previous_player != self.game.player and self.hint_route:
            if self.game.player in self.hint_route:
                self.hint_route = self.hint_route[self.hint_route.index(self.game.player):]
            else:
                self.hint_route = []
        if self.game.state in ("won", "lost") and not self.saved_terminal:
            try:
                self.profile.record(self.game)
            except OSError:
                self.message = "Record could not be saved. Gameplay still works."
            self.saved_terminal = True
        for event in self.game.events:
            if event == "power":
                self.message = "POWER UP. The ghosts are running from you."
            elif event == "hit":
                self.message = "Caught! A short shield gives you time to get moving."
            elif event == "ghost":
                self.message = "GHOST EATEN  +200"
        self.game.events.clear()
        if previous_state != self.game.state:
            self.host.render()
        elif self.game.state == "playing":
            self.draw_dynamic()
        self.timer_id = self.host.root.after(30, self.tick)

    def set_option(self, name, value):
        setattr(self, name, value)
        self.new_game()

    def set_level(self, direction):
        self.level = max(1, min(99, self.level + direction))
        self.new_game()

    def load_seed(self):
        self.new_game()
        return "break"

    def toggle_pause(self):
        if self.game.state in ("won", "lost"):
            self.continue_game() if self.game.state == "won" else self.retry()
            return
        self.game.toggle_pause()
        self.last_frame = time.perf_counter()
        self.host.render()

    def pause_for_focus(self):
        if self.game.state == "playing":
            self.game.state = "paused"
            self.host.render()

    def hint(self):
        if self.game.state in ("won", "lost"):
            return
        self.hint_route = self.game.hint()
        if self.game.state == "ready":
            self.game.state = "paused"
        self.message = "Next steps highlighted. Hints mark this as an assisted run."
        self.host.render()

    def toggle_paths(self):
        self.show_paths = not self.show_paths
        if self.show_paths:
            self.game.assisted = True
            if not self.routes:
                self.routes = alternative_routes(self.game.maze)
            if self.game.state in ("playing", "ready"):
                self.game.state = "paused"
            self.message = "Shortest exit path plus sampled alternatives. Collect all dots first in Pellet Hunt."
        self.host.render()

    def change_route(self, direction):
        if self.routes:
            self.route_index = (self.route_index + direction) % len(self.routes)
            self.host.render()

    def toggle_auto(self):
        self.game.toggle_auto()
        self.message = "AUTO DEMO. Ghosts wait; records are disabled. Arrow keys let you take over." if self.game.auto else "You're back in control."
        self.host.render()

    def retry(self):
        self.new_game()

    def continue_game(self):
        if self.game.state == "won":
            if self.game.level >= 99:
                self.level = 1
                self.new_game(random_seed=True)
                return
            self.game = self.game.next_level()
            self.level = self.game.level
            self.after_new_game()
            self.host.render()
        else:
            self.toggle_pause()

    def save_maze(self):
        try:
            folder = self.folder / "saves" / "mazes"
            folder.mkdir(parents=True, exist_ok=True)
            target = folder / maze_filename(self.game)
            target.write_text("\n".join(self.game.maze.grid) + "\n", encoding="utf-8")
            self.message = "Maze saved in Arcade_PACMAN/saves/mazes. Keep the seed to replay it."
        except OSError:
            self.message = "Could not save the maze. Check folder permissions and try again."
        self.host.render()

    def on_key(self, event):
        directions = {"Up": (-1, 0), "w": (-1, 0), "Right": (0, 1), "d": (0, 1), "Down": (1, 0), "s": (1, 0), "Left": (0, -1), "a": (0, -1)}
        key = event.keysym if event.keysym in ("Up", "Down", "Left", "Right") else event.keysym.lower()
        if key in directions:
            state = self.game.state
            was_auto = self.game.auto
            self.game.turn(directions[key])
            if state != self.game.state or was_auto != self.game.auto:
                self.host.render()
        elif key in ("space", "escape", "p"):
            self.toggle_pause()
        elif key == "return":
            self.continue_game()
        elif key == "h":
            self.hint()
        elif key == "v":
            self.toggle_paths()
        elif key == "n":
            self.new_game(random_seed=True)
        elif key == "r":
            self.retry()
        return "break"
