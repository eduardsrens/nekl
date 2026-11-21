import random
import tkinter as tk

COLS = 40
ROWS = 25
CELL_SIZE = 22
STEP_MS = 110


class GameOfLife:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Conway dzīvības spēle")
        self.root.configure(bg="#111318")
        self.root.resizable(False, False)

        self.grid = [[False for _ in range(COLS)] for _ in range(ROWS)]
        self.running = False
        self.timer_id: str | None = None

        title = tk.Label(
            root,
            text="DZĪVĪBAS SPĒLE",
            font=("Segoe UI", 20, "bold"),
            fg="#f4f6f8",
            bg="#111318",
        )
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(12, 8))

        self.status_text = tk.StringVar(value="Apturēts")
        status = tk.Label(
            root,
            textvariable=self.status_text,
            font=("Segoe UI", 10),
            fg="#9da5b1",
            bg="#111318",
        )
        status.grid(row=0, column=1, sticky="e", padx=14, pady=(12, 8))

        self.canvas = tk.Canvas(
            root,
            width=COLS * CELL_SIZE,
            height=ROWS * CELL_SIZE,
            bg="#181b21",
            highlightthickness=1,
            highlightbackground="#2b3038",
            cursor="crosshair",
        )
        self.canvas.grid(row=1, column=0, columnspan=2, padx=14)

        self.canvas.bind("<Button-1>", self.start_painting)
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", lambda _event: None)
        self.canvas.bind("<Button-3>", self.start_erasing)
        self.canvas.bind("<B3-Motion>", self.erase)

        controls = tk.Frame(root, bg="#111318")
        controls.grid(row=2, column=0, sticky="w", padx=14, pady=14)

        button_style = {
            "font": ("Segoe UI", 10, "bold"),
            "relief": "flat",
            "padx": 14,
            "pady": 8,
            "cursor": "hand2",
        }
        tk.Button(
            controls,
            text="Sākt",
            command=self.start,
            fg="#102217",
            bg="#55d68b",
            activebackground="#68dfa0",
            **button_style,
        ).grid(row=0, column=0, padx=(0, 6))

        tk.Button(
            controls,
            text="Apturēt",
            command=self.stop,
            fg="#f4f6f8",
            bg="#20242b",
            activebackground="#292d35",
            **button_style,
        ).grid(row=0, column=1, padx=6)

        tk.Button(
            controls,
            text="Notīrīt",
            command=self.clear,
            fg="#f4f6f8",
            bg="#20242b",
            activebackground="#292d35",
            **button_style,
        ).grid(row=0, column=2, padx=6)

        tk.Button(
            controls,
            text="Izlases",
            command=self.randomize,
            fg="#f4f6f8",
            bg="#20242b",
            activebackground="#292d35",
            **button_style,
        ).grid(row=0, column=3, padx=6)

        help_label = tk.Label(
            root,
            text="kreisais: pievienot  •  labais: dzēst",
            font=("Segoe UI", 9),
            fg="#9da5b1",
            bg="#111318",
        )
        help_label.grid(row=2, column=1, sticky="e", padx=14)

        self.draw()

    def get_cell(self, event: tk.Event) -> tuple[int, int]:
        x = max(0, min(COLS - 1, event.x // CELL_SIZE))
        y = max(0, min(ROWS - 1, event.y // CELL_SIZE))
        return x, y

    def stop_before_edit(self) -> None:
        if self.running:
            self.stop()

    def start_painting(self, event: tk.Event) -> None:
        self.stop_before_edit()
        self.paint(event)

    def paint(self, event: tk.Event) -> None:
        x, y = self.get_cell(event)
        self.grid[y][x] = True
        self.draw()

    def start_erasing(self, event: tk.Event) -> None:
        self.stop_before_edit()
        self.erase(event)

    def erase(self, event: tk.Event) -> None:
        x, y = self.get_cell(event)
        self.grid[y][x] = False
        self.draw()

    def count_neighbors(self, x: int, y: int) -> int:
        count = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < COLS and 0 <= ny < ROWS:
                    count += self.grid[ny][nx]
        return count

    def step(self) -> None:
        next_grid = [[False for _ in range(COLS)] for _ in range(ROWS)]
        for y in range(ROWS):
            for x in range(COLS):
                neighbors = self.count_neighbors(x, y)
                alive = self.grid[y][x]
                next_grid[y][x] = neighbors == 3 or (alive and neighbors == 2)

        self.grid = next_grid
        self.draw()

        if self.running:
            self.timer_id = self.root.after(STEP_MS, self.step)

    def start(self) -> None:
        if self.running:
            return
        self.running = True
        self.status_text.set("Darbojas")
        self.timer_id = self.root.after(STEP_MS, self.step)

    def stop(self) -> None:
        self.running = False
        self.status_text.set("Apturēts")
        if self.timer_id is not None:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

    def clear(self) -> None:
        self.stop()
        self.grid = [[False for _ in range(COLS)] for _ in range(ROWS)]
        self.draw()

    def randomize(self) -> None:
        self.stop()
        self.grid = [[random.random() < 0.28 for _ in range(COLS)] for _ in range(ROWS)]
        self.draw()

    def draw(self) -> None:
        self.canvas.delete("all")
        self.canvas.configure(bg="#181b21")

        for y in range(ROWS):
            for x in range(COLS):
                left = x * CELL_SIZE
                top = y * CELL_SIZE
                right = left + CELL_SIZE
                bottom = top + CELL_SIZE

                if self.grid[y][x]:
                    self.canvas.create_rectangle(
                        left + 1,
                        top + 1,
                        right - 1,
                        bottom - 1,
                        fill="#55d68b",
                        outline="",
                    )

                self.canvas.create_line(
                    left,
                    top,
                    right,
                    top,
                    fill="#292d35",
                )
                self.canvas.create_line(
                    left,
                    top,
                    left,
                    bottom,
                    fill="#292d35",
                )


if __name__ == "__main__":
    window = tk.Tk()
    GameOfLife(window)
    window.mainloop()
