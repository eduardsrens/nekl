from collections import deque
from pathlib import Path
import tkinter as tk


MAZE_FILE = Path(__file__).parent / "maze_25x41.txt"


def load_maze(path):
    rows = [line.rstrip("\n\r") for line in path.read_text(encoding="utf-8").splitlines()]
    start = end = None
    for row, line in enumerate(rows):
        for col, char in enumerate(line):
            if char == "A":
                start = (row, col)
            elif char == "B":
                end = (row, col)
    if start is None or end is None:
        raise ValueError("Labirintam jābūt ar 'A' sākuma punktu un 'B' mērķi.")
    return rows, start, end


class MazeSolver:
    def __init__(self, root):
        self.root = root
        self.root.title("Labirinta atrisinājums 25x41")

        self.rows, self.start, self.end = load_maze(MAZE_FILE)
        self.height = len(self.rows)
        self.width = max(len(row) for row in self.rows)
        self.cell_size = 22
        self.running = False
        self.delay = 25

        self.canvas = tk.Canvas(
            root,
            width=self.width * self.cell_size,
            height=self.height * self.cell_size,
            bg="#101827",
            highlightthickness=0,
        )
        self.canvas.pack(padx=12, pady=12)

        tk.Label(
            root,
            text="Skaitlis šūnā ir attālums soļos no A; BFS pārbauda šūnas pa attāluma slāņiem.",
        ).pack(pady=(0, 8))

        controls = tk.Frame(root)
        controls.pack(pady=(0, 12))
        tk.Button(controls, text="Atrisināt", width=12, command=self.solve).pack(
            side=tk.LEFT, padx=4
        )
        tk.Button(controls, text="Atiestatīt", width=12, command=self.reset).pack(
            side=tk.LEFT, padx=4
        )

        self.status = tk.StringVar(value="Nospied 'Atrisināt'")
        tk.Label(root, textvariable=self.status).pack(pady=(0, 10))
        self.reset()

    def reset(self):
        self.running = False
        self.canvas.delete("all")
        for row in range(self.height):
            for col in range(self.width):
                char = self.rows[row][col] if col < len(self.rows[row]) else "#"
                x1 = col * self.cell_size
                y1 = row * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                color = "#263044" if char == "#" else "#f7fafc"
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=color, outline="#d8dee8", width=1
                )

        self.draw_marker(self.start, "#42d392", "A")
        self.draw_marker(self.end, "#ff6b81", "B")
        self.status.set("Nospied 'Atrisināt'")

    def draw_marker(self, position, color, text):
        row, col = position
        x1 = col * self.cell_size
        y1 = row * self.cell_size
        x2 = x1 + self.cell_size
        y2 = y1 + self.cell_size
        self.canvas.create_oval(x1 + 4, y1 + 4, x2 - 4, y2 - 4, fill=color, outline="")
        self.canvas.create_text(
            (x1 + x2) // 2,
            (y1 + y2) // 2,
            text=text,
            fill="#ffffff",
            font=("Segoe UI", 9, "bold"),
        )

    def is_open(self, row, col):
        return (
            0 <= row < self.height
            and 0 <= col < self.width
            and col < len(self.rows[row])
            and self.rows[row][col] != "#"
        )

    def solve(self):
        if self.running:
            return
        self.reset()
        self.running = True
        self.status.set("Meklē īsāko ceļu...")

        queue = deque([self.start])
        visited = {self.start: None}
        distance = {self.start: 0}
        directions = ((-1, 0), (0, 1), (1, 0), (0, -1))

        while queue:
            row, col = queue.popleft()
            current_distance = distance[(row, col)]
            self.status.set(
                f"BFS slānis: {current_distance} | rindā vēl {len(queue)} šūnas"
            )
            self.canvas.update()
            if (row, col) == self.end:
                break

            for row_offset, col_offset in directions:
                neighbor = (row + row_offset, col + col_offset)
                neighbor_row, neighbor_col = neighbor
                if neighbor not in visited and self.is_open(neighbor_row, neighbor_col):
                    visited[neighbor] = (row, col)
                    distance[neighbor] = current_distance + 1
                    queue.append(neighbor)
                    self.animate_search(neighbor, distance[neighbor])

        if self.end not in visited:
            self.status.set("Ceļš nav atrodams.")
            self.running = False
            return

        path = []
        position = self.end
        while position is not None:
            path.append(position)
            position = visited[position]
        path.reverse()
        self.animate_path(path)

    def animate_search(self, position, distance):
        row, col = position
        x1 = col * self.cell_size + 5
        y1 = row * self.cell_size + 5
        x2 = x1 + self.cell_size - 10
        y2 = y1 + self.cell_size - 10
        self.canvas.create_oval(
            x1, y1, x2, y2, fill="#4cc9f0", outline="#ffffff", width=1
        )
        self.canvas.create_text(
            (x1 + x2) // 2,
            (y1 + y2) // 2,
            text=str(distance),
            fill="#102033",
            font=("Segoe UI", 6, "bold"),
        )
        self.canvas.update()
        self.root.after(self.delay)

    def animate_path(self, path):
        for position in path:
            if position not in (self.start, self.end):
                row, col = position
                x1 = col * self.cell_size + 3
                y1 = row * self.cell_size + 3
                x2 = x1 + self.cell_size - 6
                y2 = y1 + self.cell_size - 6
                self.canvas.create_oval(
                    x1, y1, x2, y2, fill="#ffd166", outline="#fff4bf", width=2
                )
                self.canvas.update()
                self.root.after(self.delay)

        self.draw_finish_flag()
        self.status.set(f"Finišs sasniegts! Ceļā {len(path) - 1} soļi.")
        self.running = False

    def draw_finish_flag(self):
        row, col = self.end
        x1 = col * self.cell_size
        y1 = row * self.cell_size
        pole_x = x1 + 5
        pole_top = y1 + 3
        pole_bottom = y1 + self.cell_size - 3
        self.canvas.create_line(
            pole_x, pole_top, pole_x, pole_bottom, fill="#172033", width=2
        )
        self.canvas.create_polygon(
            pole_x + 1,
            pole_top + 1,
            x1 + self.cell_size - 2,
            pole_top + 4,
            pole_x + 1,
            pole_top + 8,
            fill="#e63946",
            outline="#172033",
        )
        self.canvas.update()


if __name__ == "__main__":
    root = tk.Tk()
    MazeSolver(root)
    root.mainloop()
