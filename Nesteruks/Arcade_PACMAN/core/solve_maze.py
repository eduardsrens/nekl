"""Maze Atelier: ranked maze solutions and a procedural arcade game.

Launch PLAY_ARCADE.py or PLAY_ARCADE.cmd in the parent folder.
Use --explorer to start with the original maze explorer, or --text for reports.
Routes move up/down/left/right and never visit the same cell twice.
"""

from __future__ import annotations

from itertools import groupby
from pathlib import Path
import argparse
import time
import tkinter as tk
from tkinter import messagebox


Cell = tuple[int, int]
DIRECTIONS = ((-1, 0), (0, 1), (1, 0), (0, -1))
MAZE_FILES = ("maze_15x25.txt", "maze_25x41.txt")


def read_maze(filename: Path) -> tuple[list[str], Cell, Cell]:
    maze = filename.read_text(encoding="utf-8-sig").splitlines()
    if not maze or not maze[0] or any(len(row) != len(maze[0]) for row in maze):
        raise ValueError(f"{filename.name}: the maze must be a nonempty rectangle.")

    starts, ends = [], []
    for row, line in enumerate(maze):
        for column, character in enumerate(line):
            if character not in "# AB":
                raise ValueError(f"{filename.name}: unexpected character {character!r}.")
            if character == "A":
                starts.append((row, column))
            elif character == "B":
                ends.append((row, column))

    if len(starts) != 1 or len(ends) != 1:
        raise ValueError(f"{filename.name}: expected exactly one A and one B.")
    return maze, starts[0], ends[0]


def find_routes(maze: list[str], start: Cell, end: Cell) -> list[list[Cell]]:
    """Use depth-first search to find every route without repeated cells."""
    open_cells = {
        (row, column)
        for row, line in enumerate(maze)
        for column, character in enumerate(line)
        if character != "#"
    }
    neighbors = {
        (row, column): [
            (row + dr, column + dc)
            for dr, dc in DIRECTIONS
            if (row + dr, column + dc) in open_cells
        ]
        for row, column in open_cells
    }

    routes = []
    path = [start]
    visited = {start}
    # An explicit stack also supports corridors longer than Python's recursion limit.
    stack = [iter(neighbors[start])]
    while stack:
        if path[-1] == end:
            routes.append(path.copy())
            stack.pop()
            visited.remove(path.pop())
            continue

        following = next(stack[-1], None)
        if following is None:
            stack.pop()
            visited.remove(path.pop())
        elif following not in visited:
            path.append(following)
            visited.add(following)
            stack.append(iter(neighbors[following]))

    return sorted(routes, key=lambda route: (len(route), route))


def route_directions(route: list[Cell]) -> str:
    labels = {(-1, 0): "U", (0, 1): "R", (1, 0): "D", (0, -1): "L"}
    moves = [
        labels[(second[0] - first[0], second[1] - first[1])]
        for first, second in zip(route, route[1:])
    ]
    return " ".join(
        f"{direction}{sum(1 for _ in group)}"
        for direction, group in groupby(moves)
    )


def draw_route(maze: list[str], route: list[Cell]) -> str:
    board = [list(row) for row in maze]
    for row, column in route[1:-1]:
        board[row][column] = "."
    return "\n".join("".join(row) for row in board)


def solve_maze(filename: Path) -> list[list[Cell]]:
    maze, start, end = read_maze(filename)
    routes = find_routes(maze, start, end)
    heading = f"{filename.name}: {len(routes)} routes from A to B"
    print(heading)
    report = [
        heading,
        "Routes are sorted from shortest to longest, with no repeated cells.",
        "Each step moves to an adjacent cell; diagonal moves are not allowed.",
        "Directions: U = up, D = down, L = left, R = right; numbers count steps.",
        "On each map, dots mark the route from A to B. # marks a wall.",
        "",
    ]

    if not routes:
        print("  No route exists.")
        report.append("No route exists.")

    for rank, route in enumerate(routes, 1):
        labels = []
        if len(route) == len(routes[0]):
            labels.append("shortest")
        if len(route) == len(routes[-1]):
            labels.append("longest")
        suffix = f" ({', '.join(labels)})" if labels else ""
        description = f"Route {rank}: {len(route) - 1} steps{suffix}"
        directions = route_directions(route)
        print(f"  {description}")
        print(f"    {directions}")
        report.extend([description, directions, draw_route(maze, route), ""])

    output = filename.with_name(f"{filename.stem}_solutions.txt")
    output.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"  Marked maps saved to {output.name}\n")
    return routes


class MazeExplorer:
    """A resizable, Canvas-drawn desktop interface; no extra packages needed."""

    BG = "#0b1018"
    PANEL = "#111a25"
    BORDER = "#253141"
    TEXT = "#edf3fa"
    MUTED = "#8b9ab0"
    ACCENT = "#78e5cd"
    GOLD = "#f2c786"
    COLORS = ("#78e5cd", "#8bbcff", "#c3a0fa", "#f2b08e")

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.folder = Path(__file__).resolve().parent.parent
        self.maze_folder = self.folder / "mazes"
        self.datasets = []
        for name in MAZE_FILES:
            grid, start, end = read_maze(self.maze_folder / name)
            self.datasets.append((grid, start, end, find_routes(grid, start, end)))

        self.maze_index = 0
        self.route_index = 0
        self.maze, self.start, self.end, self.routes = self.datasets[0]
        self.progress = float(len(self.route) - 1) if self.route else 0.0
        self.playing = False
        self.compare = False
        self.speed = 1.0
        self.timer_id = None
        self.resize_id = None
        self.last_frame = 0.0
        self.hits = []
        self.hovered = None
        self.scrubbing = False
        self.resume_after_scrub = False
        self.notice = "Every route, from A to B. No repeated cells."
        self.ids = {}
        self.closed = False
        self.page = "explorer"
        self.arcade = None
        self.focus_id = None

        root.title("Maze Atelier | Nesteruks")
        root.geometry("1280x850")
        root.minsize(1080, 760)
        root.configure(bg=self.BG)
        self.canvas = tk.Canvas(root, bg=self.BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self.on_resize)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Motion>", self.on_hover)
        self.canvas.bind("<Leave>", self.clear_hover)
        root.bind("<KeyPress>", self.on_key)
        root.bind("<FocusOut>", self.on_focus_out)
        root.protocol("WM_DELETE_WINDOW", self.close)

    @property
    def route(self) -> list[Cell]:
        return self.routes[self.route_index] if self.routes else []

    @property
    def steps(self) -> int:
        return max(0, len(self.route) - 1)

    @property
    def color(self) -> str:
        return self.COLORS[self.route_index % len(self.COLORS)]

    @staticmethod
    def blend(first: str, second: str, amount: float) -> str:
        channels = [
            round(int(first[i:i + 2], 16) * amount + int(second[i:i + 2], 16) * (1 - amount))
            for i in (1, 3, 5)
        ]
        return "#" + "".join(f"{channel:02x}" for channel in channels)

    def text(self, x, y, value, size=11, color=None, bold=False, anchor="w", **options):
        return self.canvas.create_text(
            x, y, text=value, fill=color or self.TEXT, anchor=anchor,
            font=("Segoe UI", size, "bold" if bold else "normal"), **options,
        )

    def rounded(self, x, y, width, height, fill, radius=12, outline="", **options):
        radius = min(radius, width / 2, height / 2)
        points = [
            x + radius, y, x + width - radius, y, x + width, y,
            x + width, y + radius, x + width, y + height - radius,
            x + width, y + height, x + width - radius, y + height,
            x + radius, y + height, x, y + height,
            x, y + height - radius, x, y + radius, x, y,
        ]
        return self.canvas.create_polygon(
            points, smooth=True, splinesteps=20, fill=fill, outline=outline,
            width=1, **options,
        )

    def hit(self, bounds, callback, shape=None, fill=None):
        self.hits.append((bounds, callback, shape, fill))

    def button(self, x, y, width, height, label, callback, primary=False, selected=False):
        fill = self.ACCENT if primary else ("#203a39" if selected else "#1b2735")
        shape = self.rounded(x, y, width, height, fill, radius=9)
        self.text(
            x + width / 2, y + height / 2, label, 10,
            color=self.BG if primary else (self.ACCENT if selected else self.TEXT),
            bold=True, anchor="center",
        )
        self.hit((x, y, x + width, y + height), callback, shape, fill)

    def render(self) -> None:
        if self.closed:
            return
        self.resize_id = None
        self.canvas.delete("all")
        self.hits = []
        self.hovered = None
        self.ids = {}
        self.width = max(1080, self.canvas.winfo_width())
        self.height = max(760, self.canvas.winfo_height())
        self.bottom = self.height - 56
        self.board_x = 302
        self.right = self.width - 28
        if self.page == "arcade":
            self.arcade.render()
            return
        self.canvas.configure(bg=self.BG)
        self.draw_header()
        self.draw_sidebar()
        self.draw_board()
        self.draw_trace()
        self.draw_transport()
        self.text(29, self.height - 25, self.notice, 9, self.MUTED)
        self.text(
            self.right, self.height - 25,
            "SPACE  Play / pause     \u2190 \u2192  Routes     R  Replay",
            9, self.MUTED, anchor="e",
        )

    def draw_header(self) -> None:
        self.rounded(28, 27, 42, 42, "#17352f", radius=12)
        self.canvas.create_line(
            39, 56, 39, 39, 49, 39, 49, 57, 59, 57, 59, 40,
            fill=self.ACCENT, width=3, capstyle="round", joinstyle="round",
        )
        self.text(84, 39, "MAZE ATELIER", 13, bold=True)
        self.text(84, 60, "N E S T E R U K S   /   R O U T E   E X P L O R E R", 8, self.MUTED)
        self.text(28, 112, "Find your way.", 27, bold=True)
        self.text(315, 117, "Two mazes. Every possibility.", 11, self.MUTED)
        self.button(self.right - 185, 97, 185, 33, "PLAY ARCADE   \u2192", self.show_arcade, primary=True)

        left = self.right - 300
        self.rounded(left, 30, 300, 43, "#131e2a", radius=11, outline=self.BORDER)
        for index, label in enumerate(("01   /   15 \u00d7 25", "02   /   25 \u00d7 41")):
            x = left + 4 + index * 147
            active = index == self.maze_index
            shape = self.rounded(x, 34, 145, 35, "#2b3d4c" if active else "#131e2a", radius=8)
            self.text(x + 72, 51, label, 10, self.TEXT if active else self.MUTED, active, "center")
            self.hit((x, 34, x + 145, 69), lambda i=index: self.select_maze(i), shape, "#2b3d4c" if active else "#131e2a")
        self.canvas.create_line(28, 143, self.right, 143, fill=self.BORDER)

    def draw_sidebar(self) -> None:
        self.rounded(28, 160, 256, self.bottom - 160, self.PANEL, outline=self.BORDER)
        self.text(48, 190, "All routes", 15, bold=True)
        self.text(48, 212, "SHORTEST TO LONGEST", 8, self.MUTED, True)
        self.text(264, 190, f"{len(self.routes):02}", 12, self.MUTED, anchor="e")
        slot = min(96, (self.bottom - 160 - 228) / max(1, len(self.routes)))

        for index, route in enumerate(self.routes):
            y, height = 231 + index * slot, slot - 10
            selected = index == self.route_index
            color = self.COLORS[index % len(self.COLORS)]
            fill = self.blend(color, self.PANEL, 0.11) if selected else "#16212e"
            shape = self.rounded(40, y, 232, height, fill, radius=10, outline=color if selected else "")
            self.text(55, y + 25, f"{index + 1:02}", 18, color if selected else "#61738b", True)
            self.text(94, y + 22, f"Route {index + 1:02}", 11, bold=True)
            self.text(256, y + 24, str(len(route) - 1), 22, color, True, "e")
            label = "Shortest route" if len(route) == len(self.routes[0]) else (
                "Longest route" if len(route) == len(self.routes[-1]) else "Alternative route"
            )
            self.text(94, y + 43, label, 8, self.MUTED)
            if height >= 73:
                self.text(255, y + 46, "STEPS", 7, self.MUTED, anchor="e")
            bar_y = y + height - 12
            self.canvas.create_line(95, bar_y, 255, bar_y, fill="#2a3747", width=3, capstyle="round")
            ratio = (len(route) - 1) / max(1, len(self.routes[-1]) - 1)
            self.canvas.create_line(95, bar_y, 95 + 160 * ratio, bar_y, fill=color, width=3, capstyle="round")
            self.hit((40, y, 272, y + height), lambda i=index: self.select_route(i), shape, fill)

        legend_y = self.bottom - 123
        self.canvas.create_line(48, legend_y - 20, 264, legend_y - 20, fill=self.BORDER)
        for x, color, letter, label in ((58, self.ACCENT, "A", "Start"), (164, self.GOLD, "B", "Finish")):
            self.canvas.create_oval(x - 10, legend_y - 10, x + 10, legend_y + 10, fill=self.blend(color, self.PANEL, 0.13), outline=color)
            self.text(x, legend_y, letter, 8, color, True, "center")
            self.text(x + 18, legend_y, label, 10, self.MUTED)
        self.button(48, self.bottom - 73, 216, 40, "Export all route maps   \u2197", self.export_reports)

    def draw_board(self) -> None:
        self.rounded(self.board_x, 160, self.right - self.board_x, self.bottom - 160, self.PANEL, outline=self.BORDER)
        title = "The compact labyrinth" if self.maze_index == 0 else "The grand labyrinth"
        self.text(self.board_x + 24, 189, title, 16, bold=True)
        self.text(
            self.board_x + 24, 214,
            f"{len(self.maze)} rows  \u00d7  {len(self.maze[0])} columns   /   {len(self.routes)} distinct routes",
            9, self.MUTED,
        )
        self.button(self.right - 190, 179, 73, 30, "Focus", lambda: self.set_compare(False), selected=not self.compare)
        self.button(self.right - 109, 179, 85, 30, "Compare", lambda: self.set_compare(True), selected=self.compare)

        left, top, right, bottom = self.board_x + 22, 239, self.right - 22, self.bottom - 150
        self.viewport = left, top, right, bottom
        self.rounded(left, top, right - left, bottom - top, "#0c131d", radius=12, outline="#1e2b3b")
        padding = 18
        size = min((right - left - padding * 2) / len(self.maze[0]), (bottom - top - padding * 2) / len(self.maze))
        grid_width, grid_height = size * len(self.maze[0]), size * len(self.maze)
        origin_x = (left + right - grid_width) / 2
        origin_y = (top + bottom - grid_height) / 2
        self.grid_geometry = origin_x, origin_y, size
        self.canvas.create_rectangle(origin_x, origin_y, origin_x + grid_width, origin_y + grid_height, fill="#101b27", outline="")
        for row, line in enumerate(self.maze):
            for column, character in enumerate(line):
                if character == "#":
                    x, y = origin_x + column * size, origin_y + row * size
                    self.canvas.create_rectangle(
                        x + 0.45, y + 0.45, x + size - 0.45, y + size - 0.45,
                        fill="#2b394b", outline="",
                    )

    def cell_center(self, cell: Cell) -> tuple[float, float]:
        x, y, size = self.grid_geometry
        return x + (cell[1] + 0.5) * size, y + (cell[0] + 0.5) * size

    def path_line(self, points, color, width, **options):
        if len(points) >= 2:
            self.canvas.create_line(
                [value for point in points for value in point],
                fill=color, width=width, capstyle="round", joinstyle="round",
                tags="trace", **options,
            )

    def draw_trace(self) -> None:
        self.canvas.delete("trace")
        size = self.grid_geometry[2]
        if self.compare:
            for index, route in enumerate(self.routes):
                if index != self.route_index:
                    self.path_line(
                        [self.cell_center(cell) for cell in route],
                        self.blend(self.COLORS[index % len(self.COLORS)], "#101b27", 0.38),
                        max(2, size * 0.15),
                    )

        if self.route:
            points = [self.cell_center(cell) for cell in self.route]
            self.path_line(points, "#334254", 1, dash=(2, 5))
            step = min(int(self.progress), self.steps)
            visible = points[:step + 1]
            if step < self.steps:
                fraction = self.progress - step
                a, b = points[step], points[step + 1]
                visible.append((a[0] + (b[0] - a[0]) * fraction, a[1] + (b[1] - a[1]) * fraction))
            self.path_line(visible, self.blend(self.color, "#101b27", 0.08), max(6, size * 0.80))
            self.path_line(visible, self.blend(self.color, "#101b27", 0.22), max(4, size * 0.45))
            self.path_line(visible, self.color, max(2, size * 0.16))
            if 0 < self.progress < self.steps:
                x, y = visible[-1]
                radius = max(5, size * 0.30)
                self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=self.blend(self.color, "#101b27", 0.30), outline="", tags="trace")
                self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="#ffffff", outline=self.color, width=1, tags="trace")

        for cell, letter, color in ((self.start, "A", self.ACCENT), (self.end, "B", self.GOLD)):
            x, y = self.cell_center(cell)
            radius = max(7, size * 0.37)
            self.canvas.create_oval(x - radius - 3, y - radius - 3, x + radius + 3, y + radius + 3, fill=self.blend(color, "#101b27", 0.10), outline="", tags="trace")
            self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill="#101b27", outline=color, width=1.5, tags="trace")
            self.text(x, y, letter, max(7, min(10, int(size * 0.38))), color, True, "center", tags="trace")

    def draw_transport(self) -> None:
        left, _, right, bottom = self.viewport
        if not self.routes:
            label = "No route found"
        elif self.steps == len(self.routes[0]) - 1:
            label = "Shortest route"
        elif self.steps == len(self.routes[-1]) - 1:
            label = "Longest route"
        else:
            label = "Alternative route"
        self.text(left + 3, bottom + 23, f"ROUTE {self.route_index + 1:02}   /   {label.upper()}", 8, self.color, True)
        self.ids["count"] = self.text(right - 3, bottom + 23, "", 9, self.MUTED, anchor="e")

        y = bottom + 47
        self.slider = left + 3, y, right - 3
        self.canvas.create_line(left + 3, y, right - 3, y, fill="#2b394b", width=3, capstyle="round")
        self.ids["track"] = self.canvas.create_line(left + 3, y, right - 3, y, fill=self.color, width=3, capstyle="round")
        self.ids["thumb"] = self.canvas.create_oval(0, 0, 0, 0, fill=self.color, outline=self.PANEL, width=2)
        self.button(left, bottom + 69, 126, 42, "\u2161   Pause" if self.playing else "\u25b6   Play route", self.toggle_play, primary=True)
        self.button(left + 136, bottom + 69, 75, 42, "Replay", self.replay)
        self.button(left + 221, bottom + 69, 95, 42, "Show route", self.show_route)
        self.text(right - 79, bottom + 90, "SPEED", 8, self.MUTED, anchor="e")
        self.button(right - 67, bottom + 69, 67, 42, f"{self.speed:g}\u00d7", self.cycle_speed)
        self.text(left, bottom + 130, "Drag the timeline to explore any point along the route.", 8, self.MUTED)
        self.update_progress()

    def update_progress(self) -> None:
        left, y, right = self.slider
        x = left + (right - left) * (self.progress / self.steps if self.steps else 0)
        self.canvas.coords(self.ids["track"], left, y, x, y)
        self.canvas.coords(self.ids["thumb"], x - 5, y - 5, x + 5, y + 5)
        self.canvas.itemconfigure(self.ids["count"], text=f"{min(self.steps, int(self.progress)):03} / {self.steps:03} steps")

    def pause(self) -> None:
        self.playing = False
        if self.timer_id is not None:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

    def toggle_play(self) -> None:
        if not self.route:
            return
        if self.playing:
            self.pause()
        else:
            if self.progress >= self.steps:
                self.progress = 0.0
            self.playing = True
            self.last_frame = time.perf_counter()
            self.timer_id = self.root.after(24, self.tick)
        self.render()

    def tick(self) -> None:
        self.timer_id = None
        if not self.playing or self.closed:
            return
        now = time.perf_counter()
        elapsed = min(0.1, now - self.last_frame)
        self.last_frame = now
        self.progress = min(float(self.steps), self.progress + elapsed * 18 * self.speed)
        self.draw_trace()
        self.update_progress()
        if self.progress >= self.steps:
            self.playing = False
            self.render()
        else:
            self.timer_id = self.root.after(24, self.tick)

    def replay(self) -> None:
        self.pause()
        self.progress = 0.0
        self.toggle_play()

    def show_route(self) -> None:
        self.pause()
        self.progress = float(self.steps)
        self.render()

    def select_maze(self, index: int) -> None:
        self.pause()
        self.maze_index = index
        self.route_index = 0
        self.maze, self.start, self.end, self.routes = self.datasets[index]
        self.progress = float(self.steps)
        self.notice = "Every route, from A to B. No repeated cells."
        self.render()

    def select_route(self, index: int) -> None:
        if not self.routes:
            return
        self.pause()
        self.route_index = index % len(self.routes)
        self.progress = float(self.steps)
        self.render()

    def change_route(self, direction: int) -> None:
        self.select_route(self.route_index + direction)

    def set_compare(self, enabled: bool) -> None:
        self.compare = enabled
        self.render()

    def cycle_speed(self) -> None:
        values = (0.5, 1.0, 2.0, 4.0)
        self.speed = values[(values.index(self.speed) + 1) % len(values)]
        self.render()

    def export_reports(self) -> None:
        try:
            for filename in MAZE_FILES:
                solve_maze(self.maze_folder / filename)
        except (OSError, ValueError) as error:
            messagebox.showerror("Could not export routes", str(error), parent=self.root)
            return
        self.notice = "Saved both route reports in the mazes folder."
        self.render()

    def on_resize(self, _event=None) -> None:
        if self.resize_id is not None:
            self.root.after_cancel(self.resize_id)
        self.resize_id = self.root.after(60, self.render)

    @staticmethod
    def contains(bounds, x, y) -> bool:
        left, top, right, bottom = bounds
        return left <= x <= right and top <= y <= bottom

    def seek(self, x: float) -> None:
        left, _, right = self.slider
        self.progress = max(0.0, min(1.0, (x - left) / (right - left))) * self.steps
        self.draw_trace()
        self.update_progress()

    def on_click(self, event) -> None:
        self.canvas.focus_set()
        if self.page == "arcade":
            for bounds, callback, _, _ in reversed(self.hits):
                if self.contains(bounds, event.x, event.y):
                    callback()
                    return
            return
        left, y, right = self.slider
        if self.route and self.contains((left - 8, y - 12, right + 8, y + 12), event.x, event.y):
            self.resume_after_scrub = self.playing
            self.pause()
            self.scrubbing = True
            self.render()
            self.seek(event.x)
            return
        for bounds, callback, _, _ in reversed(self.hits):
            if self.contains(bounds, event.x, event.y):
                callback()
                return

    def on_drag(self, event) -> None:
        if self.page == "explorer" and self.scrubbing:
            self.seek(event.x)

    def on_release(self, _event=None) -> None:
        if self.page == "explorer" and self.scrubbing:
            self.scrubbing = False
            if self.resume_after_scrub and self.progress < self.steps:
                self.toggle_play()
            else:
                self.render()
            self.resume_after_scrub = False

    def clear_hover(self, _event=None) -> None:
        if self.hovered:
            shape, fill = self.hovered
            self.canvas.itemconfigure(shape, fill=fill)
            self.hovered = None
        self.canvas.configure(cursor="")

    def on_hover(self, event) -> None:
        target = None
        for bounds, _, shape, fill in reversed(self.hits):
            if self.contains(bounds, event.x, event.y):
                target = (shape, fill)
                break
        if target != self.hovered:
            self.clear_hover()
            if target and target[0]:
                self.canvas.itemconfigure(target[0], fill=self.blend(self.TEXT, target[1], 0.08))
                self.hovered = target
        over_slider = False
        if self.page == "explorer":
            left, y, right = self.slider
            over_slider = self.contains((left, y - 12, right, y + 12), event.x, event.y)
        self.canvas.configure(cursor="hand2" if target or over_slider else "")

    def show_arcade(self) -> None:
        self.pause()
        self.scrubbing = False
        if self.arcade is None:
            if __package__:
                from .arcade_ui import ArcadePage
            else:
                from arcade_ui import ArcadePage
            self.arcade = ArcadePage(self)
        self.page = "arcade"
        self.root.title("Maze Arcade | Nesteruks")
        self.canvas.focus_set()
        self.render()
        self.arcade.enter()

    def show_explorer(self) -> None:
        if self.arcade is not None:
            self.arcade.leave()
        self.page = "explorer"
        self.root.title("Maze Atelier | Nesteruks")
        self.canvas.focus_set()
        self.render()

    def on_key(self, event):
        if isinstance(event.widget, tk.Entry):
            return None
        if self.page == "arcade":
            return self.arcade.on_key(event)
        actions = {"space": self.toggle_play, "Left": lambda: self.change_route(-1), "Right": lambda: self.change_route(1), "r": self.replay}
        action = actions.get(event.keysym)
        if action:
            action()
            return "break"
        return None

    def on_focus_out(self, _event=None):
        if self.focus_id is not None:
            self.root.after_cancel(self.focus_id)
        self.focus_id = self.root.after(30, self.check_focus)

    def check_focus(self):
        self.focus_id = None
        if self.page == "arcade" and not self.closed:
            focused = self.root.focus_get()
            if focused is None or focused is self.arcade.entry:
                self.arcade.pause_for_focus()

    def close(self) -> None:
        self.closed = True
        self.pause()
        if self.arcade is not None:
            self.arcade.leave()
        if self.focus_id is not None:
            self.root.after_cancel(self.focus_id)
            self.focus_id = None
        if self.resize_id is not None:
            self.root.after_cancel(self.resize_id)
            self.resize_id = None
        self.root.destroy()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--text", action="store_true", help="Write text reports without opening a window.")
    mode.add_argument("--explorer", action="store_true", help="Start in the original maze explorer.")
    arguments = parser.parse_args()
    if arguments.text:
        folder = Path(__file__).resolve().parent.parent / "mazes"
        for filename in MAZE_FILES:
            solve_maze(folder / filename)
        return

    root = tk.Tk()
    try:
        app = MazeExplorer(root)
        if not arguments.explorer:
            app.show_arcade()
    except (OSError, ValueError) as error:
        messagebox.showerror("Could not open the mazes", str(error), parent=root)
        root.destroy()
        return
    root.mainloop()


if __name__ == "__main__":
    main()
