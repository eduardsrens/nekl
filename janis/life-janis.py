import tkinter as tk


ROWS = 40
COLS = 40
CELL_SIZE = 15
TICK_MS = 100


class GameOfLife:
    def __init__(self, root):
        self.root = root
        self.root.title("Conway Game of Life")

        self.grid = [[False for _ in range(COLS)] for _ in range(ROWS)]
        self.running = False
        self.after_id = None

        controls = tk.Frame(root)
        controls.pack(pady=8)

        self.start_button = tk.Button(
            controls, text="Start", width=10, command=self.start
        )
        self.start_button.pack(side=tk.LEFT, padx=4)

        self.stop_button = tk.Button(
            controls, text="Stop", width=10, command=self.stop, state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=4)

        tk.Button(controls, text="Notīrīt", width=10, command=self.clear).pack(
            side=tk.LEFT, padx=4
        )

        self.canvas = tk.Canvas(
            root,
            width=COLS * CELL_SIZE,
            height=ROWS * CELL_SIZE,
            bg="white",
            highlightthickness=1,
            highlightbackground="#888888",
        )
        self.canvas.pack(padx=10, pady=(0, 10))

        self.canvas.bind("<B1-Motion>", self.erase_on_left_click)
        self.canvas.bind("<Button-1>", self.erase_on_left_click)
        self.canvas.bind("<B3-Motion>", self.draw_on_right_click)
        self.canvas.bind("<Button-3>", self.draw_on_right_click)

        self.draw_grid()

    def erase_on_left_click(self, event):
        self.paint(event, False)

    def draw_on_right_click(self, event):
        self.paint(event, True)

    def draw_grid(self):
        self.canvas.delete("all")
        for row in range(ROWS):
            y1 = row * CELL_SIZE
            y2 = y1 + CELL_SIZE
            for col in range(COLS):
                x1 = col * CELL_SIZE
                x2 = x1 + CELL_SIZE
                color = "#22c55e" if self.grid[row][col] else "#1f2937"
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=color,
                    outline="#374151",
                    width=1,
                )

    def paint(self, event, value):
        col = event.x // CELL_SIZE
        row = event.y // CELL_SIZE
        if 0 <= row < ROWS and 0 <= col < COLS:
            if self.grid[row][col] != value:
                self.grid[row][col] = value
                x1 = col * CELL_SIZE
                y1 = row * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE
                color = "#22c55e" if value else "#1f2937"
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=color,
                    outline="#374151",
                    width=1,
                )

    def count_neighbors(self, row, col):
        total = 0
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr = (row + dr) % ROWS
                nc = (col + dc) % COLS
                total += self.grid[nr][nc]
        return total

    def step(self):
        next_grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]
        for row in range(ROWS):
            for col in range(COLS):
                neighbors = self.count_neighbors(row, col)
                if self.grid[row][col]:
                    next_grid[row][col] = 1 if neighbors in (2, 3) else 0
                else:
                    next_grid[row][col] = 1 if neighbors == 3 else 0
        self.grid = next_grid
        self.draw_grid()

    def start(self):
        if not self.running:
            self.running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.animate()

    def stop(self):
        self.running = False
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def animate(self):
        if not self.running:
            self.after_id = None
            return
        self.step()
        self.after_id = self.root.after(TICK_MS, self.animate)

    def clear(self):
        self.stop()
        self.grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]
        self.draw_grid()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    GameOfLife(root).run()
