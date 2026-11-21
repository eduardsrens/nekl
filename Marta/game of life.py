import tkinter as tk


CELL_SIZE = 20
COLUMNS = 40
ROWS = 30
TICK_MS = 150


class GameOfLife:
    def __init__(self, root):
        self.root = root
        self.root.title("Conway's Game of Life")
        self.root.resizable(False, False)

        self.cells = set()
        self.running = False
        self.generation = 0

        toolbar = tk.Frame(root, padx=10, pady=10)
        toolbar.pack(fill="x")

        self.start_button = tk.Button(toolbar, text="Sākt", width=10, command=self.start)
        self.start_button.pack(side="left", padx=(0, 6))
        self.stop_button = tk.Button(
            toolbar, text="Apturēt", width=10, command=self.stop, state="disabled"
        )
        self.stop_button.pack(side="left")
        self.generation_label = tk.Label(toolbar, text="Paaudze: 0", padx=12)
        self.generation_label.pack(side="left")

        self.canvas = tk.Canvas(
            root,
            width=COLUMNS * CELL_SIZE,
            height=ROWS * CELL_SIZE,
            background="#f7fafc",
            highlightthickness=0,
        )
        self.canvas.pack(padx=10, pady=(0, 10))
        self.canvas.bind("<Button-1>", self.draw_cell)
        self.canvas.bind("<B1-Motion>", self.draw_cell)
        self.canvas.bind("<Button-3>", self.erase_cell)
        self.canvas.bind("<B3-Motion>", self.erase_cell)

        self.draw_board()

    def draw_cell(self, event):
        self.set_cell(event, alive=True)

    def erase_cell(self, event):
        self.set_cell(event, alive=False)

    def set_cell(self, event, alive):
        column = event.x // CELL_SIZE
        row = event.y // CELL_SIZE
        if not (0 <= column < COLUMNS and 0 <= row < ROWS):
            return

        cell = (column, row)
        if alive:
            self.cells.add(cell)
        else:
            self.cells.discard(cell)
        self.draw_board()

    def draw_board(self):
        self.canvas.delete("all")
        for column, row in self.cells:
            x1 = column * CELL_SIZE + 1
            y1 = row * CELL_SIZE + 1
            self.canvas.create_rectangle(
                x1,
                y1,
                x1 + CELL_SIZE - 2,
                y1 + CELL_SIZE - 2,
                fill="#2563eb",
                outline="",
            )

        for column in range(COLUMNS + 1):
            x = column * CELL_SIZE
            self.canvas.create_line(x, 0, x, ROWS * CELL_SIZE, fill="#dbe4ef")
        for row in range(ROWS + 1):
            y = row * CELL_SIZE
            self.canvas.create_line(0, y, COLUMNS * CELL_SIZE, y, fill="#dbe4ef")

    def start(self):
        if self.running:
            return
        self.running = True
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.advance()

    def stop(self):
        self.running = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")

    def advance(self):
        if not self.running:
            return

        neighbor_counts = {}
        for column, row in self.cells:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    neighbor = (column + dx, row + dy)
                    if 0 <= neighbor[0] < COLUMNS and 0 <= neighbor[1] < ROWS:
                        neighbor_counts[neighbor] = neighbor_counts.get(neighbor, 0) + 1

        self.cells = {
            cell
            for cell, count in neighbor_counts.items()
            if count == 3 or (count == 2 and cell in self.cells)
        }
        self.generation += 1
        self.generation_label.config(text=f"Paaudze: {self.generation}")
        self.draw_board()
        self.root.after(TICK_MS, self.advance)


if __name__ == "__main__":
    window = tk.Tk()
    GameOfLife(window)
    window.mainloop()
