from collections import Counter
from tkinter import Button, Canvas, Frame, Label, Tk


CELL_SIZE = 20
GRID_WIDTH = 40
GRID_HEIGHT = 30
STEP_DELAY_MS = 120


def next_generation(alive_cells):
    neighbor_counts = Counter(
        (x + dx, y + dy)
        for x, y in alive_cells
        for dx in (-1, 0, 1)
        for dy in (-1, 0, 1)
        if dx != 0 or dy != 0
    )
    return {
        cell
        for cell, count in neighbor_counts.items()
        if count == 3 or (count == 2 and cell in alive_cells)
    }


class GameOfLife:
    def __init__(self, root):
        self.root = root
        self.root.title("Conway's Game of Life")
        self.root.resizable(False, False)

        self.alive_cells = set()
        self.generation = 0
        self.running = False
        self.after_id = None

        self.canvas = Canvas(
            root,
            width=CELL_SIZE * GRID_WIDTH,
            height=CELL_SIZE * GRID_HEIGHT,
            background="white",
            highlightthickness=0,
        )
        self.canvas.pack()
        self._draw_grid()

        controls = Frame(root)
        controls.pack(fill="x", padx=8, pady=8)

        Button(controls, text="Start", width=10, command=self._start).pack(
            side="left"
        )
        Button(controls, text="Stop", width=10, command=self._stop).pack(
            side="left", padx=(6, 0)
        )

        self.status_label = Label(controls, anchor="w")
        self.status_label.pack(side="left", padx=12)
        self._update_status()

        self.canvas.bind("<Button-1>", self._draw_cell)
        self.canvas.bind("<B1-Motion>", self._draw_cell)
        self.canvas.bind("<Button-3>", self._erase_cell)
        self.canvas.bind("<B3-Motion>", self._erase_cell)

    def _draw_grid(self):
        for x in range(0, CELL_SIZE * GRID_WIDTH + 1, CELL_SIZE):
            self.canvas.create_line(
                x, 0, x, CELL_SIZE * GRID_HEIGHT, fill="#e5e7eb"
            )
        for y in range(0, CELL_SIZE * GRID_HEIGHT + 1, CELL_SIZE):
            self.canvas.create_line(
                0, y, CELL_SIZE * GRID_WIDTH, y, fill="#e5e7eb"
            )

    def _draw_cell(self, event):
        self._set_cell(event, True)

    def _erase_cell(self, event):
        self._set_cell(event, False)

    def _set_cell(self, event, alive):
        x = event.x // CELL_SIZE
        y = event.y // CELL_SIZE
        if not (0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT):
            return

        cell = (x, y)
        if (cell in self.alive_cells) == alive:
            return

        if alive:
            self.alive_cells.add(cell)
            self.canvas.create_rectangle(
                x * CELL_SIZE + 1,
                y * CELL_SIZE + 1,
                (x + 1) * CELL_SIZE,
                (y + 1) * CELL_SIZE,
                fill="#2563eb",
                outline="",
                tags=("cell", "cell_{}_{}".format(x, y)),
            )
        else:
            self.alive_cells.remove(cell)
            self.canvas.delete("cell_{}_{}".format(x, y))
        self._update_status()

    def _start(self):
        if not self.running:
            self.running = True
            self._step()

    def _stop(self):
        self.running = False
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def _step(self):
        if not self.running:
            return

        self.alive_cells = next_generation(self.alive_cells)
        self.generation += 1
        self.canvas.delete("cell")
        for x, y in self.alive_cells:
            self.canvas.create_rectangle(
                x * CELL_SIZE + 1,
                y * CELL_SIZE + 1,
                (x + 1) * CELL_SIZE,
                (y + 1) * CELL_SIZE,
                fill="#2563eb",
                outline="",
                tags=("cell", "cell_{}_{}".format(x, y)),
            )
        self._update_status()
        self.after_id = self.root.after(STEP_DELAY_MS, self._step)

    def _update_status(self):
        self.status_label.config(
            text="Generation: {}   Live cells: {}".format(
                self.generation, len(self.alive_cells)
            )
        )


if __name__ == "__main__":
    root = Tk()
    GameOfLife(root)
    root.mainloop()