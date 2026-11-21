from collections import deque
import tkinter as tk


maze = [
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
]

CELL_SIZE = 30
PADDING = 12


def find_cell(grid, marker):
    for row_index, row in enumerate(grid):
        for column_index, cell in enumerate(row):
            if cell == marker:
                return row_index, column_index
    return None


def solve_maze(grid):
    start = find_cell(grid, "A")
    goal = find_cell(grid, "B")
    if start is None or goal is None:
        return None

    queue = deque([start])
    previous = {start: None}
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))

    while queue:
        row, column = queue.popleft()
        if (row, column) == goal:
            break

        for row_delta, column_delta in directions:
            next_row = row + row_delta
            next_column = column + column_delta
            position = (next_row, next_column)
            if (
                0 <= next_row < len(grid)
                and 0 <= next_column < len(grid[next_row])
                and grid[next_row][next_column] != "#"
                and position not in previous
            ):
                previous[position] = (row, column)
                queue.append(position)
    else:
        return None

    path = []
    position = goal
    while position is not None:
        path.append(position)
        position = previous[position]
    path.reverse()
    return path


def find_all_routes(grid):
    start = find_cell(grid, "A")
    goal = find_cell(grid, "B")
    if start is None or goal is None:
        return []

    routes = []
    path = [start]
    visited = {start}
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))

    def search(position):
        if position == goal:
            routes.append(path.copy())
            return

        row, column = position
        for row_delta, column_delta in directions:
            next_row = row + row_delta
            next_column = column + column_delta
            next_position = (next_row, next_column)
            if (
                0 <= next_row < len(grid)
                and 0 <= next_column < len(grid[next_row])
                and grid[next_row][next_column] != "#"
                and next_position not in visited
            ):
                visited.add(next_position)
                path.append(next_position)
                search(next_position)
                path.pop()
                visited.remove(next_position)

    search(start)
    return routes


class MazeGame:
    def __init__(self, root):
        self.root = root
        self.start = find_cell(maze, "A")
        self.goal = find_cell(maze, "B")
        self.solution = solve_maze(maze)
        self.routes = find_all_routes(maze)
        self.route_colors = ("#fb7185", "#facc15", "#34d399", "#a78bfa")
        self.player = self.start
        self.visited = []
        self.solving = False
        self.show_routes = False
        self.animation_id = None

        root.title("Maze Runner")
        root.configure(bg="#0b1220")
        root.resizable(False, False)
        root.bind("<KeyPress>", self.handle_key)

        title = tk.Label(
            root,
            text="MAZE RUNNER",
            font=("Segoe UI", 20, "bold"),
            fg="#e2e8f0",
            bg="#0b1220",
        )
        title.pack(pady=(14, 2))
        tk.Label(
            root,
            text="Find your way from START to EXIT",
            font=("Segoe UI", 10),
            fg="#94a3b8",
            bg="#0b1220",
        ).pack(pady=(0, 12))

        columns = max(len(row) for row in maze)
        self.canvas = tk.Canvas(
            root,
            width=columns * CELL_SIZE,
            height=len(maze) * CELL_SIZE,
            bg="#0b1220",
            highlightthickness=0,
        )
        self.canvas.pack(padx=PADDING, pady=(0, 10))

        legend = tk.Frame(root, bg="#0b1220")
        legend.pack(pady=(0, 8))
        for route_number, color in enumerate(self.route_colors, start=1):
            tk.Label(
                legend,
                text=f"Route {route_number}",
                font=("Segoe UI", 8, "bold"),
                fg=color,
                bg="#0b1220",
            ).pack(side="left", padx=8)

        footer = tk.Frame(root, bg="#0b1220")
        footer.pack(fill="x", padx=16, pady=(0, 14))
        self.status = tk.Label(
            footer,
            text="Use arrow keys or WASD to move.",
            font=("Segoe UI", 10),
            fg="#cbd5e1",
            bg="#0b1220",
            anchor="w",
        )
        self.status.pack(side="left", fill="x", expand=True)
        self.routes_button = tk.Button(
            footer,
            text="Show routes",
            command=self.toggle_routes,
            font=("Segoe UI", 9, "bold"),
            bg="#1e293b",
            fg="#e2e8f0",
            activebackground="#334155",
            relief="flat",
            padx=12,
            pady=7,
            cursor="hand2",
        )
        self.routes_button.pack(side="right", padx=(8, 0))
        tk.Button(
            footer,
            text="Solve for me",
            command=self.solve_automatically,
            font=("Segoe UI", 9, "bold"),
            bg="#22c55e",
            fg="#052e16",
            activebackground="#4ade80",
            relief="flat",
            padx=12,
            pady=7,
            cursor="hand2",
        ).pack(side="right", padx=(8, 0))
        tk.Button(
            footer,
            text="Restart",
            command=self.restart,
            font=("Segoe UI", 9, "bold"),
            bg="#1e293b",
            fg="#e2e8f0",
            activebackground="#334155",
            relief="flat",
            padx=12,
            pady=7,
            cursor="hand2",
        ).pack(side="right")

        self.draw()
        root.focus_set()

    def draw(self):
        self.canvas.delete("all")
        for row_index, row in enumerate(maze):
            for column_index, cell in enumerate(row):
                x1 = column_index * CELL_SIZE
                y1 = row_index * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE

                if cell == "#":
                    self.canvas.create_rectangle(
                        x1 + 1, y1 + 1, x2 - 1, y2 - 1,
                        fill="#334155", outline="#475569", width=1,
                    )
                    self.canvas.create_line(
                        x1 + 4, y1 + 4, x2 - 4, y1 + 4,
                        fill="#64748b", width=2,
                    )
                else:
                    self.canvas.create_rectangle(
                        x1, y1, x2, y2,
                        fill="#172554", outline="#1e3a5f", width=1,
                    )
                    if (row_index, column_index) in self.visited:
                        self.canvas.create_oval(
                            x1 + 11, y1 + 11, x2 - 11, y2 - 11,
                            fill="#22c55e", outline="",
                        )

        if self.show_routes:
            offsets = ((-6, -6), (6, -6), (-6, 6), (6, 6))
            for route_index, route in enumerate(self.routes):
                color = self.route_colors[route_index % len(self.route_colors)]
                offset_x, offset_y = offsets[route_index % len(offsets)]
                for current, following in zip(route, route[1:]):
                    row, column = current
                    next_row, next_column = following
                    self.canvas.create_line(
                        column * CELL_SIZE + CELL_SIZE / 2 + offset_x,
                        row * CELL_SIZE + CELL_SIZE / 2 + offset_y,
                        next_column * CELL_SIZE + CELL_SIZE / 2 + offset_x,
                        next_row * CELL_SIZE + CELL_SIZE / 2 + offset_y,
                        fill=color,
                        width=4,
                        capstyle=tk.ROUND,
                    )

        for row_index, row in enumerate(maze):
            for column_index, cell in enumerate(row):
                x1 = column_index * CELL_SIZE
                y1 = row_index * CELL_SIZE
                if cell == "A":
                    self.canvas.create_text(
                        x1 + CELL_SIZE / 2, y1 + CELL_SIZE / 2,
                        text="START", fill="#86efac",
                        font=("Segoe UI", 7, "bold"),
                    )
                elif cell == "B":
                    self.canvas.create_text(
                        x1 + CELL_SIZE / 2, y1 + CELL_SIZE / 2,
                        text="EXIT", fill="#fda4af",
                        font=("Segoe UI", 8, "bold"),
                    )

        row, column = self.player
        center_x = column * CELL_SIZE + CELL_SIZE / 2
        center_y = row * CELL_SIZE + CELL_SIZE / 2
        self.canvas.create_oval(
            center_x - 9, center_y - 9, center_x + 9, center_y + 9,
            fill="#38bdf8", outline="#e0f2fe", width=2,
        )
        self.canvas.create_oval(
            center_x - 4, center_y - 4, center_x - 1, center_y - 1,
            fill="#ffffff", outline="",
        )

    def handle_key(self, event):
        moves = {
            "Up": (-1, 0), "w": (-1, 0), "W": (-1, 0),
            "Down": (1, 0), "s": (1, 0), "S": (1, 0),
            "Left": (0, -1), "a": (0, -1), "A": (0, -1),
            "Right": (0, 1), "d": (0, 1), "D": (0, 1),
        }
        if self.solving or event.keysym not in moves:
            return

        row_delta, column_delta = moves[event.keysym]
        row, column = self.player
        next_row = row + row_delta
        next_column = column + column_delta
        if (
            0 <= next_row < len(maze)
            and 0 <= next_column < len(maze[next_row])
            and maze[next_row][next_column] != "#"
        ):
            self.player = (next_row, next_column)
            self.draw()
            if self.player == self.goal:
                self.status.config(text="You escaped the maze! Great job!")

    def solve_automatically(self):
        if self.solution is None:
            self.status.config(text="There is no route from START to EXIT.")
            return
        self.restart()
        self.solving = True
        self.status.config(text="Solving the maze...")
        self.animate_step(1)

    def animate_step(self, index):
        if index >= len(self.solution):
            self.solving = False
            self.status.config(text="Maze solved! You reached the exit.")
            return

        self.player = self.solution[index]
        self.visited.append(self.player)
        self.draw()
        self.animation_id = self.root.after(90, self.animate_step, index + 1)

    def toggle_routes(self):
        if self.show_routes:
            self.show_routes = False
            self.routes_button.config(text="Show routes")
            self.draw()
            self.status.config(text="Use arrow keys or WASD to move.")
            return

        self.restart()
        if not self.routes:
            self.status.config(text="There are no routes from START to EXIT.")
            return

        self.show_routes = True
        self.routes_button.config(text="Hide routes")
        self.draw()
        self.status.config(
            text=f"Showing {len(self.routes)} routes (without revisiting cells)."
        )

    def restart(self):
        if self.animation_id is not None:
            self.root.after_cancel(self.animation_id)
            self.animation_id = None
        self.solving = False
        self.show_routes = False
        self.routes_button.config(text="Show routes")
        self.player = self.start
        self.visited = []
        self.status.config(text="Use arrow keys or WASD to move.")
        self.draw()


if __name__ == "__main__":
    window = tk.Tk()
    MazeGame(window)
    window.mainloop()
