import colorsys
import math
import tkinter as tk


MAZE = """\
#########################
#A  #       #           #
# # # ##### # ######### #
# #   #   #   #       # #
# ##### # ##### ##### # #
#     # #     #     #   #
##### # ##### ##### ### #
#   # #     #     #   # #
# # # ##### ##### # # # #
# #       #     #   #   #
# ####### ##### ####### #
#       #     #       # #
# ##### ##### # ##### # #
#     #       #     #  B#
#########################
"""

CELL_SIZE = 32
PADDING = 20
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
    paths: list[list[tuple[int, int]]],
) -> None:
    for row_index, row in enumerate(rows):
        for column_index, cell in enumerate(row):
            left = PADDING + column_index * CELL_SIZE
            top = PADDING + row_index * CELL_SIZE
            if cell == "#":
                canvas.create_rectangle(
                    left + 2,
                    top + 2,
                    left + CELL_SIZE - 2,
                    top + CELL_SIZE - 2,
                    fill=WALL_COLOR,
                    outline=WALL_OUTLINE,
                    width=1,
                )
            elif cell not in "AB":
                center_x = left + CELL_SIZE / 2
                center_y = top + CELL_SIZE / 2
                canvas.create_oval(
                    center_x - 2,
                    center_y - 2,
                    center_x + 2,
                    center_y + 2,
                    fill=PELLET_COLOR,
                    outline="",
                )

    for index, path in enumerate(paths):
        color = path_color(index, len(paths))
        angle = 2 * math.pi * index / max(len(paths), 1)
        offset_x = 6 * math.cos(angle)
        offset_y = 6 * math.sin(angle)
        points = []
        for row, column in path:
            points.extend(
                (
                    PADDING + column * CELL_SIZE + CELL_SIZE / 2 + offset_x,
                    PADDING + row * CELL_SIZE + CELL_SIZE / 2 + offset_y,
                )
            )
        if len(points) >= 4:
            canvas.create_line(
                *points,
                fill=color,
                width=4,
                capstyle=tk.ROUND,
                joinstyle=tk.ROUND,
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
            font=("Arial", 12, "bold"),
        )

    legend_y = PADDING + len(rows) * CELL_SIZE + 22
    for index, _path in enumerate(paths):
        x = PADDING + index * 145
        color = path_color(index, len(paths))
        canvas.create_line(x, legend_y, x + 24, legend_y, fill=color, width=5)
        canvas.create_text(
            x + 32,
            legend_y,
            text=f"Ceļš {index + 1}",
            fill="white",
            anchor="w",
            font=("Arial", 10),
        )


def main() -> None:
    rows, start, goal = read_maze(MAZE)
    paths = find_all_paths(rows, start, goal)

    root = tk.Tk()
    root.title("Pac-Man labirints — visi ceļi")
    root.configure(background=BACKGROUND)
    root.resizable(False, False)

    title = tk.Label(
        root,
        text=f"Visi iespējamie ceļi no A līdz B: {len(paths)}",
        bg=BACKGROUND,
        fg="white",
        font=("Arial", 15, "bold"),
        pady=10,
    )
    title.pack()

    canvas_width = PADDING * 2 + len(rows[0]) * CELL_SIZE
    canvas_height = PADDING * 2 + len(rows) * CELL_SIZE + 48
    canvas = tk.Canvas(
        root,
        width=canvas_width,
        height=canvas_height,
        background=BACKGROUND,
        highlightthickness=0,
    )
    canvas.pack(padx=10, pady=(0, 10))
    draw_maze(canvas, rows, start, goal, paths)

    if not paths:
        canvas.create_text(
            canvas_width / 2,
            canvas_height - 18,
            text="Ceļš no A līdz B nav atrasts.",
            fill="white",
            font=("Arial", 10),
        )

    root.mainloop()


if __name__ == "__main__":
    main()