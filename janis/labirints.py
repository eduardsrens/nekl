from colorsys import hsv_to_rgb
from math import cos, pi, sin
from pathlib import Path
import tkinter as tk


CELL_SIZE = 16
WALL_COLOR = "#2037c4"
FLOOR_COLOR = "#080808"
PATH_OFFSET = 5


def find_all_paths(maze, start, goal):
    pending = [(start, [start], {start})]
    paths = []

    while pending:
        position, path, visited = pending.pop()
        if position == goal:
            paths.append(path)
            continue

        row, col = position
        for row_step, col_step in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            neighbor = (row + row_step, col + col_step)
            next_row, next_col = neighbor
            if (
                0 <= next_row < len(maze)
                and 0 <= next_col < len(maze[0])
                and maze[next_row][next_col] != "#"
                and neighbor not in visited
            ):
                pending.append((neighbor, path + [neighbor], visited | {neighbor}))

    return paths


def find_marker(maze, marker):
    positions = [
        (row, col)
        for row, line in enumerate(maze)
        for col, cell in enumerate(line)
        if cell == marker
    ]
    if len(positions) != 1:
        raise ValueError(f"Labirintā jābūt tieši vienam marķierim {marker}.")
    return positions[0]


class MazePaths:
    def __init__(self, root, maze_filename="Labirints", cell_size=CELL_SIZE):
        self.root = root
        self.root.title(f"{Path(maze_filename).stem}: ceļi no A līdz B")
        self.root.resizable(False, False)
        self.cell_size = cell_size

        maze_path = Path(__file__).with_name(maze_filename)
        maze_text = maze_path.read_text(encoding="utf-8").strip("\r\n")
        self.maze = maze_text.splitlines()
        if not self.maze or len({len(row) for row in self.maze}) != 1:
            raise ValueError("Labirinta kartes rindām jābūt vienāda garuma.")

        self.start = find_marker(self.maze, "A")
        self.goal = find_marker(self.maze, "B")
        self.paths = find_all_paths(self.maze, self.start, self.goal)
        if not self.paths:
            raise ValueError("Starp A un B nav iespējams nokļūt.")
        self.selected_path = None

        tk.Label(
            root,
            text=f"No A līdz B atrasti {len(self.paths)} dažādi ceļi.",
            font=("Arial", 12),
        ).pack(pady=(10, 2))
        tk.Label(
            root,
            text="Katram ceļam ir sava krāsa; vienā ceļā šūnas neatkārtojas.",
            font=("Arial", 10),
        ).pack(pady=(0, 8))

        self.canvas = tk.Canvas(
            root,
            width=len(self.maze[0]) * self.cell_size,
            height=len(self.maze) * self.cell_size,
            bg=FLOOR_COLOR,
            highlightthickness=0,
        )
        self.canvas.pack(padx=10, pady=(0, 10))
        self.draw_board()

        controls = tk.Frame(root)
        controls.pack(pady=(0, 10))
        self.path_buttons = []
        for index, color in enumerate(self.path_colors()):
            button = tk.Button(
                controls,
                text=f"Ceļš {index + 1}",
                fg=color,
                command=lambda path_index=index: self.show_path(path_index),
            )
            button.pack(side=tk.LEFT, padx=4)
            self.path_buttons.append(button)
        self.show_all_button = tk.Button(
            controls, text="Rādīt visus", command=self.show_all_paths
        )
        self.show_all_button.pack(side=tk.LEFT, padx=4)
        self.update_button_states()

    def path_colors(self):
        colors = []
        total = len(self.paths)
        for index in range(total):
            red, green, blue = hsv_to_rgb(index / total, 0.45, 0.68)
            colors.append(
                f"#{round(red * 255):02x}{round(green * 255):02x}{round(blue * 255):02x}"
            )
        return colors

    def draw_board(self):
        self.canvas.delete("all")
        for row, line in enumerate(self.maze):
            for col, cell in enumerate(line):
                x1 = col * self.cell_size
                y1 = row * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                color = WALL_COLOR if cell == "#" else FLOOR_COLOR
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=color, outline=color
                )

        colors = self.path_colors()
        if self.selected_path is None:
            path_indices = range(len(self.paths))
        else:
            path_indices = (self.selected_path,)

        for index in path_indices:
            path = self.paths[index]
            if self.selected_path is None:
                angle = 2 * pi * index / len(self.paths)
                offset_x = PATH_OFFSET * cos(angle)
                offset_y = PATH_OFFSET * sin(angle)
            else:
                offset_x = 0
                offset_y = 0
            points = []
            for row, col in path:
                points.extend(
                    (
                        (col + 0.5) * self.cell_size + offset_x,
                        (row + 0.5) * self.cell_size + offset_y,
                    )
                )
            self.canvas.create_line(
                *points,
                fill=colors[index],
                width=max(3, self.cell_size // 6),
                capstyle=tk.ROUND,
                joinstyle=tk.ROUND,
            )

        for position, fill, label in (
            (self.start, "#25c05a", "A"),
            (self.goal, "#f04444", "B"),
        ):
            row, col = position
            center_x = (col + 0.5) * self.cell_size
            center_y = (row + 0.5) * self.cell_size
            marker_radius = self.cell_size / 3
            self.canvas.create_oval(
                center_x - marker_radius,
                center_y - marker_radius,
                center_x + marker_radius,
                center_y + marker_radius,
                fill=fill,
                outline="white",
            )
            self.canvas.create_text(
                center_x,
                center_y,
                text=label,
                fill="white",
                font=("Arial", 9, "bold"),
            )

    def show_path(self, index):
        self.selected_path = index
        self.draw_board()
        self.update_button_states()

    def show_all_paths(self):
        self.selected_path = None
        self.draw_board()
        self.update_button_states()

    def update_button_states(self):
        for index, button in enumerate(self.path_buttons):
            relief = "sunken" if self.selected_path == index else "raised"
            button.config(relief=relief)
        relief = "sunken" if self.selected_path is None else "raised"
        self.show_all_button.config(relief=relief)


if __name__ == "__main__":
    root = tk.Tk()
    MazePaths(root)
    root.mainloop()
