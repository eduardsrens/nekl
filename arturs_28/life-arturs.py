import tkinter as tk


ROWS = 40
COLS = 40
CELL_SIZE = 15


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

        self.canvas.bind("<B1-Motion>", self.draw_on_left_click)
        self.canvas.bind("<Button-1>", self.draw_on_left_click)
        self.canvas.bind("<B3-Motion>", self.erase_on_right_click)
        self.canvas.bind("<Button-3>", self.erase_on_right_click)

        self.draw_grid()

    def draw_grid(self):
        self.canvas.delete("all")
        for row in range(ROWS):
            for col in range(COLS):
                x1 = col * CELL_SIZE
                y1 = row * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE
                color = "#222222" if self.grid[row][col] else "white"
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=color, outline="#dddddd"
                )

    def get_cell(self, event):
        col = max(0, min(COLS - 1, event.x // CELL_SIZE))
        row = max(0, min(ROWS - 1, event.y // CELL_SIZE))
        return row, col

    def set_cell(self, event, alive):
        row, col = self.get_cell(event)
        if self.grid[row][col] != alive:
            self.grid[row][col] = alive
            x1 = col * CELL_SIZE
            y1 = row * CELL_SIZE
            x2 = x1 + CELL_SIZE
            y2 = y1 + CELL_SIZE
            color = "#222222" if alive else "white"
            self.canvas.create_rectangle(
                x1, y1, x2, y2, fill=color, outline="#dddddd"
            )

    def draw_on_left_click(self, event):
        self.set_cell(event, True)

    def erase_on_right_click(self, event):
        self.set_cell(event, False)

    def count_neighbors(self, row, col):
        count = 0
        for row_offset in (-1, 0, 1):
            for col_offset in (-1, 0, 1):
                if row_offset == 0 and col_offset == 0:
                    continue
                neighbor_row = row + row_offset
                neighbor_col = col + col_offset
                if (
                    0 <= neighbor_row < ROWS
                    and 0 <= neighbor_col < COLS
                    and self.grid[neighbor_row][neighbor_col]
                ):
                    count += 1
        return count

    def update(self):
        next_grid = [[False for _ in range(COLS)] for _ in range(ROWS)]
        for row in range(ROWS):
            for col in range(COLS):
                neighbors = self.count_neighbors(row, col)
                if self.grid[row][col]:
                    next_grid[row][col] = neighbors in (2, 3)
                else:
                    next_grid[row][col] = neighbors == 3

        self.grid = next_grid
        self.draw_grid()
        if self.running:
            self.after_id = self.root.after(100, self.update)

    def start(self):
        if not self.running:
            self.running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.update()

    def stop(self):
        self.running = False
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def clear(self):
        self.stop()
        self.grid = [[False for _ in range(COLS)] for _ in range(ROWS)]
        self.draw_grid()


if __name__ == "__main__":
    root = tk.Tk()
    app = GameOfLife(root)
    root.mainloop()