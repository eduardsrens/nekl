import tkinter as tk


MAZE = (
    "#########################",
    "#A  #       #           #",
    "# # # ##### # ######### #",
    "# #   #   #   #       # #",
    "# ##### # ##### ##### # #",
    "#     # #     #     #   #",
    "##### # ##### ##### ### #",
    "#   # #     #     #   # #",
    "# # # ##### ##### # # # #",
    "# #       #     #   #   #",
    "# ####### ##### ####### #",
    "#       #     #       # #",
    "# ##### ##### # ##### # #",
    "#     #       #     #  B#",
    "#########################",
)
CELL_SIZE = 34
MOVES = ((1, 0), (0, 1), (-1, 0), (0, -1))


def find_all_paths(maze):
    start = next(
        (row, col)
        for row, line in enumerate(maze)
        for col, cell in enumerate(line)
        if cell == "A"
    )
    goal = next(
        (row, col)
        for row, line in enumerate(maze)
        for col, cell in enumerate(line)
        if cell == "B"
    )
    paths = []

    def search(cell, path, visited):
        if cell == goal:
            paths.append(path.copy())
            return

        row, col = cell
        for dr, dc in MOVES:
            neighbor = (row + dr, col + dc)
            nr, nc = neighbor
            if (
                0 <= nr < len(maze)
                and 0 <= nc < len(maze[nr])
                and maze[nr][nc] != "#"
                and neighbor not in visited
            ):
                visited.add(neighbor)
                path.append(neighbor)
                search(neighbor, path, visited)
                path.pop()
                visited.remove(neighbor)

    search(start, [start], {start})
    return paths


class MazeSolver:
    def __init__(self, root):
        self.root = root
        self.root.title("Labirints: ceļš no A līdz B")
        self.root.resizable(False, False)

        self.paths = find_all_paths(MAZE)
        self.path_index = 0
        self.step = 0
        self.running = False
        self.start = next(
            (row, col)
            for row, line in enumerate(MAZE)
            for col, cell in enumerate(line)
            if cell == "A"
        )

        self.status = tk.StringVar()
        tk.Label(
            root,
            text="Atrodi visus iespējamos ceļus cauri labirintam",
            font=("Segoe UI", 15, "bold"),
        ).pack(pady=(12, 4))

        self.canvas = tk.Canvas(
            root,
            width=len(MAZE[0]) * CELL_SIZE,
            height=len(MAZE) * CELL_SIZE,
            bg="#172033",
            highlightthickness=0,
        )
        self.canvas.pack(padx=16, pady=10)

        controls = tk.Frame(root)
        controls.pack(pady=(0, 8))
        tk.Button(controls, text="◀ Iepriekšējais", command=self.previous_path).pack(
            side=tk.LEFT, padx=4
        )
        tk.Button(controls, text="Nākamais ▶", command=self.next_path).pack(
            side=tk.LEFT, padx=4
        )
        self.play_button = tk.Button(controls, text="▶ Sākt", command=self.play)
        self.play_button.pack(side=tk.LEFT, padx=4)
        tk.Button(controls, text="■ Apturēt", command=self.stop).pack(
            side=tk.LEFT, padx=4
        )

        tk.Label(root, textvariable=self.status, font=("Segoe UI", 10)).pack(pady=(0, 12))
        self.show_path()

    def show_path(self):
        if not self.paths:
            self.status.set("No A līdz B ceļa nav.")
            self.draw_maze([])
            return
        path = self.paths[self.path_index]
        self.step = 0
        self.draw_maze(path)
        self.status.set(
            f"Ceļš {self.path_index + 1} no {len(self.paths)}"
            f"  |  {len(path) - 1} soļi"
        )

    def draw_maze(self, path):
        self.canvas.delete("all")
        path_cells = set(path)
        current = path[min(self.step, len(path) - 1)] if path else None
        for row, line in enumerate(MAZE):
            for col, cell in enumerate(line):
                x1 = col * CELL_SIZE
                y1 = row * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE
                if cell == "#":
                    color = "#24334f"
                elif (row, col) in path_cells:
                    color = "#ffe066"
                else:
                    color = "#f4f6fb"
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=color, outline="#d5dbe7", width=1
                )
                if cell in ("A", "B"):
                    marker_color = "#16803c" if cell == "A" else "#cf3030"
                    self.canvas.create_text(
                        x1 + CELL_SIZE // 2,
                        y1 + CELL_SIZE // 2,
                        text=cell,
                        fill=marker_color,
                        font=("Segoe UI", 14, "bold"),
                    )

        if current is not None:
            row, col = current
            inset = 5
            self.canvas.create_oval(
                col * CELL_SIZE + inset,
                row * CELL_SIZE + inset,
                (col + 1) * CELL_SIZE - inset,
                (row + 1) * CELL_SIZE - inset,
                fill="#ff9f1c",
                outline="#b45309",
                width=2,
            )

    def change_path(self, offset):
        if not self.paths:
            return
        self.stop()
        self.path_index = (self.path_index + offset) % len(self.paths)
        self.show_path()

    def previous_path(self):
        self.change_path(-1)

    def next_path(self):
        self.change_path(1)

    def play(self):
        if not self.paths or self.running:
            return
        self.running = True
        self.step = 0
        self.animate()

    def animate(self):
        if not self.running:
            return
        path = self.paths[self.path_index]
        if self.step >= len(path):
            self.running = False
            self.status.set(
                f"Ceļš {self.path_index + 1} no {len(self.paths)} sasniedza B!"
            )
            return
        self.draw_maze(path)
        self.step += 1
        self.root.after(140, self.animate)

    def stop(self):
        self.running = False
        if self.paths:
            self.show_path()


if __name__ == "__main__":
    root = tk.Tk()
    MazeSolver(root)
    root.mainloop()
