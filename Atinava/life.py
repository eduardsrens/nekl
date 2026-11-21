import random
import tkinter as tk


ROWS = 30
COLS = 50
CELL_SIZE = 16


def next_generation(grid):
    """Apply John Conway's Game of Life rules."""
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    new_grid = [[False for _ in range(cols)] for _ in range(rows)]

    for row in range(rows):
        for col in range(cols):
            neighbors = 0
            for row_offset in (-1, 0, 1):
                for col_offset in (-1, 0, 1):
                    if row_offset == 0 and col_offset == 0:
                        continue
                    neighbor_row = row + row_offset
                    neighbor_col = col + col_offset
                    if (
                        0 <= neighbor_row < rows
                        and 0 <= neighbor_col < cols
                        and grid[neighbor_row][neighbor_col]
                    ):
                        neighbors += 1

            if grid[row][col]:
                new_grid[row][col] = neighbors in (2, 3)
            else:
                new_grid[row][col] = neighbors == 3

    return new_grid


class GameOfLife:
    def __init__(self, root):
        self.root = root
        self.root.title("Game of Life - John Conway")
        self.grid = [[False for _ in range(COLS)] for _ in range(ROWS)]
        self.running = False
        self.generation = 0
        self.delay = 150
        self.paint_value = True
        self.painting = False

        self.canvas = tk.Canvas(
            root,
            width=COLS * CELL_SIZE,
            height=ROWS * CELL_SIZE,
            bg="#e7e7e7",
            highlightthickness=1,
            highlightbackground="#777777",
        )
        self.canvas.pack(padx=10, pady=10)

        controls = tk.Frame(root)
        controls.pack(pady=(0, 10))

        self.start_button = tk.Button(
            controls, text="Start", width=10, command=self.toggle_running
        )
        self.start_button.pack(side=tk.LEFT, padx=3)
        tk.Button(controls, text="Next", width=10, command=self.step).pack(
            side=tk.LEFT, padx=3
        )
        tk.Button(controls, text="Random", width=10, command=self.randomize).pack(
            side=tk.LEFT, padx=3
        )
        tk.Button(controls, text="Clear", width=10, command=self.clear).pack(
            side=tk.LEFT, padx=3
        )

        self.status = tk.StringVar(value="Pauze | Paaudze: 0")
        tk.Label(root, textvariable=self.status).pack(pady=(0, 8))

        self.canvas.bind("<Button-1>", self.begin_paint)
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.end_paint)
        self.canvas.bind("<Button-3>", self.clear_cell)

        self.draw()

    def cell_from_event(self, event):
        col = max(0, min(COLS - 1, event.x // CELL_SIZE))
        row = max(0, min(ROWS - 1, event.y // CELL_SIZE))
        return row, col

    def begin_paint(self, event):
        self.painting = True
        row, col = self.cell_from_event(event)
        self.paint_value = not self.grid[row][col]
        self.grid[row][col] = self.paint_value
        self.draw()

    def paint(self, event):
        if self.painting:
            row, col = self.cell_from_event(event)
            self.grid[row][col] = self.paint_value
            self.draw()

    def end_paint(self, event):
        self.painting = False

    def clear_cell(self, event):
        row, col = self.cell_from_event(event)
        self.grid[row][col] = False
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        for row in range(ROWS):
            y1 = row * CELL_SIZE
            y2 = y1 + CELL_SIZE
            for col in range(COLS):
                x1 = col * CELL_SIZE
                x2 = x1 + CELL_SIZE
                fill = "#20242a" if self.grid[row][col] else "#ffffff"
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=fill, outline="#d3d7dc", width=1
                )
        self.update_status()

    def update_status(self):
        state = "Darbojas" if self.running else "Pauze"
        self.status.set(f"{state} | Paaudze: {self.generation}")

    def toggle_running(self):
        self.running = not self.running
        self.start_button.config(text="Pauze" if self.running else "Start")
        self.update_status()
        if self.running:
            self.run()

    def run(self):
        if not self.running:
            return
        self.step(update_status=False)
        self.root.after(self.delay, self.run)

    def step(self, update_status=True):
        self.grid = next_generation(self.grid)
        self.generation += 1
        self.draw()
        if update_status:
            self.update_status()

    def randomize(self):
        self.running = False
        self.start_button.config(text="Start")
        self.generation = 0
        self.grid = [
            [random.random() < 0.25 for _ in range(COLS)] for _ in range(ROWS)
        ]
        self.draw()

    def clear(self):
        self.running = False
        self.start_button.config(text="Start")
        self.generation = 0
        self.grid = [[False for _ in range(COLS)] for _ in range(ROWS)]
        self.draw()


if __name__ == "__main__":
    root = tk.Tk()
    app = GameOfLife(root)
    root.mainloop()