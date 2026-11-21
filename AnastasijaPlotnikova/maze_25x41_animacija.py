import colorsys
import math
import tkinter as tk
from collections.abc import Callable


MAZE = """\
#########################################
#A  #       #           #       #       #
# # # ##### # ######### # ##### # ##### #
# #   #   #   #       #   #   #   #     #
# ##### # ##### ##### ##### # ##### ### #
#     # #     #     #     # #     #   # #
##### # ##### ##### ##### # ##### ### # #
#   # #     #     #     # #     #   # # #
# # # ##### ##### ##### # ##### ### # # #
# #       #     #     # #     #   #   # #
# ####### ##### ##### # ##### ### ##### #
#       #     #     # #     #   #       #
# ##### ##### ##### # ##### ### ####### #
#     #     #     # #     #   #       # #
##### ##### ##### # ##### ### ####### # #
#   #     #     # #     #   #       # # #
# # ##### ##### # ##### ### ####### # # #
# #     #     # #     #   #       # # # #
# ##### ##### # ##### ### ####### # # # #
#     #     # #     #   #       #   # # #
##### ##### # ##### ### ####### ##### # #
#   #     # #     #   #       #     # # #
# # ##### # ##### ### ####### ##### # # #
# #       #         #               #  B#
#########################################
"""

CELL_SIZE = 22
PADDING = 18
BACKGROUND = "#050814"
WALL_COLOR = "#1746a2"
WALL_OUTLINE = "#397bff"
PELLET_COLOR = "#fff1a8"


def read_maze(maze: str) -> tuple[list[str], tuple[int, int], tuple[int, int]]:
    rows = maze.splitlines()
    if not rows or any(len(row) != len(rows[0]) for row in rows):
        raise ValueError("Labirintam jābūt taisnstūrveida režģim.")

    starts = [(r, c) for r, row in enumerate(rows) for c, cell in enumerate(row) if cell == "A"]
    goals = [(r, c) for r, row in enumerate(rows) for c, cell in enumerate(row) if cell == "B"]
    if len(starts) != 1 or len(goals) != 1:
        raise ValueError("Labirintā jābūt tieši vienam punktam A un vienam punktam B.")
    if any(cell not in "# AB" for row in rows for cell in row):
        raise ValueError("Labirintā drīkst izmantot tikai sienas (#), ejas, A un B.")

    return rows, starts[0], goals[0]


def find_all_paths(
    rows: list[str], start: tuple[int, int], goal: tuple[int, int]
) -> list[list[tuple[int, int]]]:
    paths: list[list[tuple[int, int]]] = []
    path = [start]
    visited = {start}

    def search(row: int, column: int) -> None:
        if (row, column) == goal:
            paths.append(path.copy())
            return

        for next_cell in (
            (row - 1, column),
            (row + 1, column),
            (row, column - 1),
            (row, column + 1),
        ):
            next_row, next_column = next_cell
            if (
                0 <= next_row < len(rows)
                and 0 <= next_column < len(rows[0])
                and rows[next_row][next_column] != "#"
                and next_cell not in visited
            ):
                visited.add(next_cell)
                path.append(next_cell)
                search(next_row, next_column)
                path.pop()
                visited.remove(next_cell)

    search(*start)
    return paths


def path_color(index: int, count: int) -> str:
    red, green, blue = colorsys.hsv_to_rgb(index / max(count, 1), 0.78, 1)
    return f"#{int(red * 255):02x}{int(green * 255):02x}{int(blue * 255):02x}"


def draw_maze(
    canvas: tk.Canvas,
    rows: list[str],
    start: tuple[int, int],
    goal: tuple[int, int],
) -> None:
    for row_index, row in enumerate(rows):
        for column_index, cell in enumerate(row):
            left = PADDING + column_index * CELL_SIZE
            top = PADDING + row_index * CELL_SIZE
            if cell == "#":
                canvas.create_rectangle(
                    left + 1,
                    top + 1,
                    left + CELL_SIZE - 1,
                    top + CELL_SIZE - 1,
                    fill=WALL_COLOR,
                    outline=WALL_OUTLINE,
                    width=1,
                )
            elif cell not in "AB":
                center_x = left + CELL_SIZE / 2
                center_y = top + CELL_SIZE / 2
                canvas.create_oval(
                    center_x - 1.5,
                    center_y - 1.5,
                    center_x + 1.5,
                    center_y + 1.5,
                    fill=PELLET_COLOR,
                    outline="",
                )

    for point, label, fill in (
        (start, "A", "#35e06f"),
        (goal, "B", "#ff4d67"),
    ):
        row, column = point
        center_x = PADDING + column * CELL_SIZE + CELL_SIZE / 2
        center_y = PADDING + row * CELL_SIZE + CELL_SIZE / 2
        radius = CELL_SIZE * 0.34
        canvas.create_oval(
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
            fill=fill,
            outline="white",
            width=2,
        )
        canvas.create_text(
            center_x,
            center_y,
            text=label,
            fill=BACKGROUND,
            font=("Arial", 9, "bold"),
        )

class PathAnimator:
    frames_per_cell = 3
    frame_delay_ms = 25
    route_pause_ms = 900
    pacman_radius = CELL_SIZE * 0.3

    def __init__(
        self,
        root: tk.Tk,
        canvas: tk.Canvas,
        status: tk.Label,
        pause_button: tk.Button,
        paths: list[list[tuple[int, int]]],
    ) -> None:
        self.root = root
        self.canvas = canvas
        self.status = status
        self.pause_button = pause_button
        self.paths = paths
        self.route_index = 0
        self.segment_index = 0
        self.frame = 0
        self.route: list[tuple[int, int]] = []
        self.trace: list[float] = []
        self.line_id: int | None = None
        self.pacman_id: int | None = None
        self.mouth_id: int | None = None
        self.after_id: str | None = None
        self.paused = False
        self.finished = False

    def start_animation(self) -> None:
        if not self.paths:
            self.status.configure(text="Ceļš no A līdz B nav atrasts.", fg="white")
            self.pause_button.configure(state=tk.DISABLED)
            return
        self._begin_route()

    def _canvas_point(self, cell: tuple[int, int]) -> tuple[float, float]:
        row, column = cell
        return (
            PADDING + column * CELL_SIZE + CELL_SIZE / 2,
            PADDING + row * CELL_SIZE + CELL_SIZE / 2,
        )

    def _begin_route(self) -> None:
        self.route = self.paths[self.route_index]
        self.segment_index = 0
        self.frame = 0
        x, y = self._canvas_point(self.route[0])
        self.trace = [x, y]
        color = path_color(self.route_index, len(self.paths))
        self.line_id = self.canvas.create_line(
            x,
            y,
            x,
            y,
            fill=color,
            width=3,
            capstyle=tk.ROUND,
            joinstyle=tk.ROUND,
        )
        radius = self.pacman_radius
        self.pacman_id = self.canvas.create_oval(
            x - radius,
            y - radius,
            x + radius,
            y + radius,
            fill="#ffe100",
            outline="#fff59d",
            width=1,
        )
        self.mouth_id = self.canvas.create_polygon(
            x,
            y,
            x,
            y,
            x,
            y,
            fill=BACKGROUND,
            outline=BACKGROUND,
        )
        self.canvas.tag_raise(self.pacman_id)
        self.canvas.tag_raise(self.mouth_id)
        self.status.configure(
            text=f"Ceļš {self.route_index + 1}/{len(self.paths)}: A → B",
            fg=color,
        )
        self._schedule(250, self._animate_frame)

    def _schedule(self, delay_ms: int, callback: Callable[[], None]) -> None:
        self.after_id = self.root.after(delay_ms, callback)

    def _animate_frame(self) -> None:
        self.after_id = None
        if self.paused or self.finished:
            return

        if self.segment_index >= len(self.route) - 1:
            self.status.configure(
                text=f"Ceļš {self.route_index + 1}/{len(self.paths)} sasniedza B!",
                fg=path_color(self.route_index, len(self.paths)),
            )
            self._schedule(self.route_pause_ms, self._next_route)
            return

        start_x, start_y = self._canvas_point(self.route[self.segment_index])
        end_x, end_y = self._canvas_point(self.route[self.segment_index + 1])
        segment_index = self.segment_index
        progress = (self.frame + 1) / self.frames_per_cell
        x = start_x + (end_x - start_x) * progress
        y = start_y + (end_y - start_y) * progress

        if self.frame + 1 == self.frames_per_cell:
            self.trace.extend((end_x, end_y))
            self.segment_index += 1
            self.frame = 0
        else:
            self.frame += 1

        if self.line_id is not None:
            self.canvas.coords(self.line_id, *self.trace, x, y)
        self._position_pacman(x, y, end_x - start_x, end_y - start_y)

        percent = int(100 * (segment_index + progress) / (len(self.route) - 1))
        self.status.configure(
            text=f"Ceļš {self.route_index + 1}/{len(self.paths)} — {percent}%",
            fg=path_color(self.route_index, len(self.paths)),
        )
        self._schedule(self.frame_delay_ms, self._animate_frame)

    def _position_pacman(self, x: float, y: float, dx: float, dy: float) -> None:
        radius = self.pacman_radius
        if self.pacman_id is not None:
            self.canvas.coords(
                self.pacman_id,
                x - radius,
                y - radius,
                x + radius,
                y + radius,
            )

        angle = math.atan2(dy, dx)
        mouth_angle = 0.38
        tip_radius = radius * 1.15
        mouth_points = (
            x,
            y,
            x + tip_radius * math.cos(angle - mouth_angle),
            y + tip_radius * math.sin(angle - mouth_angle),
            x + tip_radius * math.cos(angle + mouth_angle),
            y + tip_radius * math.sin(angle + mouth_angle),
        )
        if self.mouth_id is not None:
            self.canvas.coords(self.mouth_id, *mouth_points)

    def _next_route(self) -> None:
        self.after_id = None
        if self.paused:
            return
        self._clear_animation()
        self.route_index += 1
        if self.route_index >= len(self.paths):
            self.finished = True
            self.status.configure(text="Visi ceļi no A līdz B ir parādīti.", fg="white")
            self.pause_button.configure(state=tk.DISABLED)
            return
        self._begin_route()

    def _clear_animation(self) -> None:
        for item_id in (self.line_id, self.pacman_id, self.mouth_id):
            if item_id is not None:
                self.canvas.delete(item_id)
        self.line_id = None
        self.pacman_id = None
        self.mouth_id = None

    def toggle_pause(self) -> None:
        if self.finished or not self.paths:
            return
        self.paused = not self.paused
        if self.paused:
            if self.after_id is not None:
                self.root.after_cancel(self.after_id)
                self.after_id = None
            self.pause_button.configure(text="Turpināt")
            self.status.configure(text=f"{self.status.cget('text')} — pauze")
        else:
            self.pause_button.configure(text="Pauze")
            self._schedule(0, self._animate_frame)

    def restart(self) -> None:
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        self.paused = False
        self.finished = False
        self.route_index = 0
        self._clear_animation()
        if self.paths:
            self.pause_button.configure(state=tk.NORMAL, text="Pauze")
            self._begin_route()
        else:
            self.status.configure(text="Ceļš no A līdz B nav atrasts.", fg="white")


def main() -> None:
    rows, start, goal = read_maze(MAZE)
    paths = find_all_paths(rows, start, goal)

    root = tk.Tk()
    root.title("Pac-Man labirints — ceļu animācija")
    root.configure(background=BACKGROUND)
    root.resizable(False, False)

    title = tk.Label(
        root,
        text=f"Pac-Man izies visus ceļus no A līdz B ({len(paths)})",
        bg=BACKGROUND,
        fg="white",
        font=("Arial", 14, "bold"),
        pady=8,
    )
    title.pack()

    canvas_width = PADDING * 2 + len(rows[0]) * CELL_SIZE
    canvas_height = PADDING * 2 + len(rows) * CELL_SIZE + 20
    canvas = tk.Canvas(
        root,
        width=canvas_width,
        height=canvas_height,
        background=BACKGROUND,
        highlightthickness=0,
    )
    canvas.pack(padx=8)
    draw_maze(canvas, rows, start, goal)

    status = tk.Label(
        root,
        text="Sagatavojas animācijai...",
        bg=BACKGROUND,
        fg="white",
        font=("Arial", 10, "bold"),
        pady=8,
    )
    status.pack()

    controls = tk.Frame(root, bg=BACKGROUND)
    controls.pack(pady=(0, 10))
    pause_button = tk.Button(controls, text="Pauze", width=12)
    pause_button.pack(side=tk.LEFT, padx=5)
    restart_button = tk.Button(controls, text="Sākt no jauna", width=14)
    restart_button.pack(side=tk.LEFT, padx=5)

    animator = PathAnimator(root, canvas, status, pause_button, paths)
    pause_button.configure(command=animator.toggle_pause)
    restart_button.configure(command=animator.restart)
    animator.start_animation()
    root.mainloop()


if __name__ == "__main__":
    main()