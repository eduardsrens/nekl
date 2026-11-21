"""Conway's Game of Life. Run: python3.14 "Way of life.py"."""

from __future__ import annotations

from collections import Counter
import random
import tkinter as tk


def next_generation(
    cells: set[tuple[int, int]], rows: int, columns: int
) -> set[tuple[int, int]]:
    """Apply Conway's rules on a finite board with no wrapping edges."""
    neighbors = Counter()
    for row, column in cells:
        for row_offset in (-1, 0, 1):
            for column_offset in (-1, 0, 1):
                if row_offset == column_offset == 0:
                    continue
                neighbor = row + row_offset, column + column_offset
                if 0 <= neighbor[0] < rows and 0 <= neighbor[1] < columns:
                    neighbors[neighbor] += 1

    return {
        cell
        for cell, count in neighbors.items()
        if count == 3 or (count == 2 and cell in cells)
    }


class GameOfLife:
    ROWS = 32
    COLUMNS = 50
    CELL_SIZE = 18
    BACKGROUND = "#111827"
    BOARD_COLOR = "#172033"
    GRID_COLOR = "#293449"
    LIVE_COLOR = "#5eead4"
    TEXT_COLOR = "#e5e7eb"

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.cells: set[tuple[int, int]] = set()
        self.generation = 0
        self.running = False
        self.timer_id = None
        self.last_drawn_cell = None
        self.root.title("Conway's Game of Life")
        self.root.configure(bg=self.BACKGROUND)
        self.root.resizable(False, False)

        container = tk.Frame(root, bg=self.BACKGROUND, padx=20, pady=16)
        container.pack()

        tk.Label(
            container,
            text="Conway's Game of Life",
            font=("Segoe UI", 20, "bold"),
            fg=self.TEXT_COLOR,
            bg=self.BACKGROUND,
        ).pack(anchor="w")
        tk.Label(
            container,
            text="Left-click or drag to draw  |  Right-click or drag to erase",
            font=("Segoe UI", 10),
            fg="#aab8cc",
            bg=self.BACKGROUND,
        ).pack(anchor="w", pady=(4, 12))

        toolbar = tk.Frame(container, bg=self.BACKGROUND)
        toolbar.pack(fill="x", pady=(0, 12))
        self.start_button = self.make_button(toolbar, "Start", self.start, "#5eead4")
        self.stop_button = self.make_button(toolbar, "Stop", self.stop, "#fda4af")
        self.stop_button.configure(state=tk.DISABLED)
        self.step_button = self.make_button(toolbar, "Step", self.step)
        self.make_button(toolbar, "Clear", self.clear)
        self.make_button(toolbar, "Randomize", self.randomize)

        self.speed = tk.IntVar(value=10)
        tk.Label(
            toolbar,
            text="Speed (generations/sec)",
            fg=self.TEXT_COLOR,
            bg=self.BACKGROUND,
        ).pack(side="left", padx=(18, 6))
        tk.Scale(
            toolbar,
            from_=1,
            to=30,
            orient="horizontal",
            variable=self.speed,
            length=160,
            bg=self.BACKGROUND,
            fg=self.TEXT_COLOR,
            troughcolor=self.GRID_COLOR,
            highlightthickness=0,
        ).pack(side="left")

        self.canvas = tk.Canvas(
            container,
            width=self.COLUMNS * self.CELL_SIZE,
            height=self.ROWS * self.CELL_SIZE,
            bg=self.BOARD_COLOR,
            highlightthickness=0,
        )
        self.canvas.pack()
        self.rectangles = {}
        for row in range(self.ROWS):
            for column in range(self.COLUMNS):
                x, y = column * self.CELL_SIZE, row * self.CELL_SIZE
                self.rectangles[row, column] = self.canvas.create_rectangle(
                    x,
                    y,
                    x + self.CELL_SIZE,
                    y + self.CELL_SIZE,
                    fill=self.BOARD_COLOR,
                    outline=self.GRID_COLOR,
                )

        self.canvas.bind("<Button-1>", lambda event: self.paint(event, True))
        self.canvas.bind("<B1-Motion>", lambda event: self.paint(event, True))
        self.canvas.bind("<Button-3>", lambda event: self.paint(event, False))
        self.canvas.bind("<B3-Motion>", lambda event: self.paint(event, False))
        self.canvas.bind("<ButtonRelease-1>", self.end_stroke)
        self.canvas.bind("<ButtonRelease-3>", self.end_stroke)
        self.canvas.bind("<Leave>", self.end_stroke)

        self.status = tk.StringVar()
        tk.Label(
            container,
            textvariable=self.status,
            fg="#aab8cc",
            bg=self.BACKGROUND,
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(10, 0))
        self.update_status()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def make_button(self, parent, text, command, color="#cbd5e1"):
        button = tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg="#111827",
            activebackground=color,
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=12,
            pady=6,
            cursor="hand2",
        )
        button.pack(side="left", padx=(0, 6))
        return button

    def replace_cells(self, new_cells: set[tuple[int, int]]) -> None:
        for cell in self.cells ^ new_cells:
            self.canvas.itemconfigure(
                self.rectangles[cell],
                fill=self.LIVE_COLOR if cell in new_cells else self.BOARD_COLOR,
            )
        self.cells = new_cells
        self.update_status()

    def paint(self, event, alive: bool) -> None:
        column = event.x // self.CELL_SIZE
        row = event.y // self.CELL_SIZE
        if not (0 <= row < self.ROWS and 0 <= column < self.COLUMNS):
            self.last_drawn_cell = None
            return

        # Fill between mouse events so fast drags leave a continuous stroke.
        previous_row, previous_column = self.last_drawn_cell or (row, column)
        distance = max(abs(row - previous_row), abs(column - previous_column))
        new_cells = self.cells.copy()
        for index in range(distance + 1):
            fraction = index / distance if distance else 0
            cell = (
                round(previous_row + (row - previous_row) * fraction),
                round(previous_column + (column - previous_column) * fraction),
            )
            if alive:
                new_cells.add(cell)
            else:
                new_cells.discard(cell)
        self.last_drawn_cell = row, column
        self.replace_cells(new_cells)

    def end_stroke(self, _event=None) -> None:
        self.last_drawn_cell = None

    def step(self) -> None:
        self.generation += 1
        self.replace_cells(next_generation(self.cells, self.ROWS, self.COLUMNS))

    def tick(self) -> None:
        self.timer_id = None
        if self.running:
            self.step()
            self.timer_id = self.root.after(1000 // self.speed.get(), self.tick)

    def start(self) -> None:
        if self.running:
            return
        self.running = True
        self.start_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL)
        self.step_button.configure(state=tk.DISABLED)
        self.tick()

    def stop(self) -> None:
        self.running = False
        if self.timer_id is not None:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
        self.start_button.configure(state=tk.NORMAL)
        self.stop_button.configure(state=tk.DISABLED)
        self.step_button.configure(state=tk.NORMAL)
        self.update_status()

    def clear(self) -> None:
        self.stop()
        self.generation = 0
        self.end_stroke()
        self.replace_cells(set())

    def randomize(self) -> None:
        self.stop()
        self.generation = 0
        self.end_stroke()
        self.replace_cells({
            (row, column)
            for row in range(self.ROWS)
            for column in range(self.COLUMNS)
            if random.random() < 0.25
        })

    def update_status(self) -> None:
        state = "Running" if self.running else "Stopped"
        self.status.set(
            f"{state}  |  Generation: {self.generation}  |  "
            f"Living cells: {len(self.cells)}  |  Edges do not wrap"
        )

    def close(self) -> None:
        self.stop()
        self.root.destroy()


if __name__ == "__main__":
    window = tk.Tk()
    GameOfLife(window)
    window.mainloop()
