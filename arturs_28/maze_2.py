from collections import deque
import tkinter as tk
from tkinter import ttk


maze = [
    "#########################################",
    "#A  #       #           #       #       #",
    "# # # ##### # ######### # ##### # ##### #",
    "# #   #   #   #       #   #   #   #     #",
    "# ##### # ##### ##### ##### # ##### ### #",
    "#     # #     #     #     # #     #   # #",
    "##### # ##### ##### ##### # ##### ### # #",
    "#   # #     #     #     # #     #   # # #",
    "# # # ##### ##### ##### # ##### ### # # #",
    "# #       #     #     # #     #   #   # #",
    "# ####### ##### ##### # ##### ### ##### #",
    "#       #     #     # #     #   #       #",
    "# ##### ##### ##### # ##### ### ####### #",
    "#     #     #     # #     #   #       # #",
    "##### ##### ##### # ##### ### ####### # #",
    "#   #     #     # #     #   #       # # #",
    "# # ##### ##### # ##### ### ####### # # #",
    "# #     #     # #     #   #       # # # #",
    "# ##### ##### # ##### ### ####### # # # #",
    "#     #     # #     #   #       #   # # #",
    "##### ##### # ##### ### ####### ##### # #",
    "#   #     # #     #   #       #     # # #",
    "# # ##### # ##### ### ####### ##### # # #",
    "# #       #         #               #  B#",
    "#########################################",
]

CELL_SIZE = 22
PADDING = 10
DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))
ROUTE_COLORS = ("#fb7185", "#facc15", "#34d399", "#a78bfa")
FASTEST_COLOR = "#38bdf8"


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

    while queue:
        row, column = queue.popleft()
        if (row, column) == goal:
            break

        for row_delta, column_delta in DIRECTIONS:
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

    def search(position):
        if position == goal:
            routes.append(path.copy())
            return

        row, column = position
        for row_delta, column_delta in DIRECTIONS:
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
        self.shortest_route_number = min(
            range(len(self.routes)),
            key=lambda index: len(self.routes[index]),
            default=None,
        )
        self.player = self.start
        self.visited = []
        self.character_frame = 0
        self.solving = False
        self.show_routes = False
        self.animation_id = None
        self.animation_route = None
        self.animation_label = ""
        self.robot_positions = None
        self.robot_route_steps = []
        self.racing = False

        root.title("Pip's Maze Adventure")
        root.configure(bg="#0b1220")
        root.resizable(False, False)
        root.bind("<KeyPress>", self.handle_key)

        tk.Label(
            root,
            text="PIP'S MAZE ADVENTURE",
            font=("Segoe UI", 18, "bold"),
            fg="#e2e8f0",
            bg="#0b1220",
        ).pack(pady=(10, 1))
        tk.Label(
            root,
            text="Guide Pip from A to B",
            font=("Segoe UI", 9),
            fg="#94a3b8",
            bg="#0b1220",
        ).pack(pady=(0, 8))

        columns = max(len(row) for row in maze)
        self.canvas = tk.Canvas(
            root,
            width=columns * CELL_SIZE,
            height=len(maze) * CELL_SIZE,
            bg="#0b1220",
            highlightthickness=0,
        )
        self.canvas.pack(padx=PADDING, pady=(0, 6))

        route_controls = tk.Frame(root, bg="#0b1220")
        route_controls.pack(pady=(0, 7))
        tk.Label(
            route_controls,
            text="Choose a route:",
            font=("Segoe UI", 9, "bold"),
            fg="#cbd5e1",
            bg="#0b1220",
        ).pack(side="left", padx=(0, 8))
        route_options = [
            f"Route {index + 1} - {len(route) - 1} moves"
            for index, route in enumerate(self.routes)
        ]
        self.route_selector = ttk.Combobox(
            route_controls,
            values=route_options,
            state="readonly" if route_options else "disabled",
            width=25,
        )
        if route_options:
            self.route_selector.current(0)
        self.route_selector.pack(side="left", padx=(0, 8))
        self.play_route_button = tk.Button(
            route_controls,
            text="Play route",
            command=self.play_selected_route,
            font=("Segoe UI", 8, "bold"),
            bg="#0ea5e9",
            fg="#082f49",
            activebackground="#38bdf8",
            relief="flat",
            padx=10,
            pady=6,
            cursor="hand2",
            state="normal" if route_options else "disabled",
        )
        self.play_route_button.pack(side="left")

        legend = tk.Frame(root, bg="#0b1220")
        legend.pack(pady=(0, 5))
        for route_number, color in enumerate(ROUTE_COLORS, start=1):
            tk.Label(
                legend,
                text=f"Route {route_number}",
                font=("Segoe UI", 8, "bold"),
                fg=color,
                bg="#0b1220",
            ).pack(side="left", padx=7)
        tk.Label(
            legend,
            text="Quickest",
            font=("Segoe UI", 8, "bold"),
            fg=FASTEST_COLOR,
            bg="#0b1220",
        ).pack(side="left", padx=7)

        footer = tk.Frame(root, bg="#0b1220")
        footer.pack(fill="x", padx=14, pady=(0, 10))
        self.status = tk.Label(
            footer,
            text="Move Pip with the arrow keys or WASD.",
            font=("Segoe UI", 9),
            fg="#cbd5e1",
            bg="#0b1220",
            anchor="w",
        )
        self.status.pack(side="left", fill="x", expand=True)
        self.routes_button = tk.Button(
            footer,
            text="Show routes",
            command=self.toggle_routes,
            font=("Segoe UI", 8, "bold"),
            bg="#1e293b",
            fg="#e2e8f0",
            activebackground="#334155",
            relief="flat",
            padx=9,
            pady=6,
            cursor="hand2",
        )
        self.routes_button.pack(side="right", padx=(6, 0))
        tk.Button(
            footer,
            text="Race all robots",
            command=self.race_all_robots,
            font=("Segoe UI", 8, "bold"),
            bg="#facc15",
            fg="#422006",
            activebackground="#fde047",
            relief="flat",
            padx=9,
            pady=6,
            cursor="hand2",
        ).pack(side="right", padx=(6, 0))
        tk.Button(
            footer,
            text="Solve fastest",
            command=self.solve_automatically,
            font=("Segoe UI", 8, "bold"),
            bg="#22c55e",
            fg="#052e16",
            activebackground="#4ade80",
            relief="flat",
            padx=9,
            pady=6,
            cursor="hand2",
        ).pack(side="right", padx=(6, 0))
        tk.Button(
            footer,
            text="Restart",
            command=self.restart,
            font=("Segoe UI", 8, "bold"),
            bg="#1e293b",
            fg="#e2e8f0",
            activebackground="#334155",
            relief="flat",
            padx=9,
            pady=6,
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
                        x1 + 3, y1 + 3, x2 - 3, y1 + 3,
                        fill="#64748b", width=1,
                    )
                else:
                    self.canvas.create_rectangle(
                        x1, y1, x2, y2,
                        fill="#172554", outline="#1e3a5f", width=1,
                    )
                    if (row_index, column_index) in self.visited:
                        self.canvas.create_oval(
                            x1 + 8, y1 + 8, x2 - 8, y2 - 8,
                            fill="#22c55e", outline="",
                        )

        if self.show_routes:
            offsets = ((-4, -4), (4, -4), (-4, 4), (4, 4))
            for route_index, route in enumerate(self.routes):
                color = ROUTE_COLORS[route_index % len(ROUTE_COLORS)]
                offset_x, offset_y = offsets[route_index % len(offsets)]
                self.draw_path(route, color, 3, offset_x, offset_y)
            if self.solution is not None:
                self.draw_path(self.solution, FASTEST_COLOR, 2, 0, 0)

        for row_index, row in enumerate(maze):
            for column_index, cell in enumerate(row):
                if cell in ("A", "B"):
                    self.canvas.create_text(
                        column_index * CELL_SIZE + CELL_SIZE / 2,
                        row_index * CELL_SIZE + CELL_SIZE / 2,
                        text=cell,
                        fill="#86efac" if cell == "A" else "#fda4af",
                        font=("Segoe UI", 8, "bold"),
                    )

        row, column = self.player
        if self.robot_positions is None:
            center_x = column * CELL_SIZE + CELL_SIZE / 2
            center_y = row * CELL_SIZE + CELL_SIZE / 2
            self.draw_character(center_x, center_y)
        else:
            robot_offsets = ((-4, -4), (4, -4), (-4, 4), (4, 4))
            for index, (robot_row, robot_column) in enumerate(self.robot_positions):
                offset_x, offset_y = robot_offsets[index]
                center_x = robot_column * CELL_SIZE + CELL_SIZE / 2 + offset_x
                center_y = robot_row * CELL_SIZE + CELL_SIZE / 2 + offset_y
                self.draw_mini_robot(
                    center_x,
                    center_y,
                    ROUTE_COLORS[index],
                    self.character_frame,
                )

    def draw_mini_robot(self, center_x, center_y, color, frame):
        step = 1 if frame % 2 else -1
        self.canvas.create_oval(
            center_x - 4, center_y + 3, center_x + 4, center_y + 5,
            fill="#0b1220", outline="",
        )
        self.canvas.create_rectangle(
            center_x - 3, center_y - 1, center_x + 3, center_y + 3,
            fill=color, outline="#e2e8f0", width=1,
        )
        self.canvas.create_oval(
            center_x - 3, center_y - 5, center_x + 3, center_y,
            fill="#e2e8f0", outline=color, width=1,
        )
        self.canvas.create_rectangle(
            center_x - 2, center_y - 3, center_x + 2, center_y - 1,
            fill="#0f172a", outline="",
        )
        self.canvas.create_oval(
            center_x - 1, center_y - 3, center_x, center_y - 2,
            fill="#67e8f9", outline="",
        )
        self.canvas.create_oval(
            center_x + 1, center_y - 3, center_x + 2, center_y - 2,
            fill="#67e8f9", outline="",
        )
        self.canvas.create_line(
            center_x - 1, center_y + 3, center_x - 2 + step, center_y + 5,
            fill="#facc15", width=1,
        )
        self.canvas.create_line(
            center_x + 1, center_y + 3, center_x + 2 - step, center_y + 5,
            fill="#facc15", width=1,
        )

    def draw_character(self, center_x, center_y):
        step = 2 if self.character_frame % 2 else -2
        self.canvas.create_oval(
            center_x - 6, center_y + 7, center_x + 6, center_y + 9,
            fill="#0b1220", outline="",
        )
        self.canvas.create_rectangle(
            center_x - 7, center_y - 1, center_x - 4, center_y + 5,
            fill="#a78bfa", outline="#ddd6fe",
        )
        self.canvas.create_line(
            center_x - 2, center_y + 5, center_x - 3 + step, center_y + 8,
            fill="#facc15", width=2,
        )
        self.canvas.create_line(
            center_x + 2, center_y + 5, center_x + 3 - step, center_y + 8,
            fill="#facc15", width=2,
        )
        self.canvas.create_rectangle(
            center_x - 4, center_y, center_x + 4, center_y + 6,
            fill="#14b8a6", outline="#99f6e4", width=1,
        )
        self.canvas.create_line(
            center_x - 4, center_y + 2, center_x - 6, center_y + 4,
            fill="#e2e8f0", width=2,
        )
        self.canvas.create_line(
            center_x + 4, center_y + 2, center_x + 6, center_y + 4,
            fill="#e2e8f0", width=2,
        )
        self.canvas.create_oval(
            center_x - 6, center_y - 10, center_x + 6, center_y + 1,
            fill="#e2e8f0", outline="#38bdf8", width=1,
        )
        self.canvas.create_rectangle(
            center_x - 4, center_y - 6, center_x + 4, center_y - 2,
            fill="#0f172a", outline="#7dd3fc",
        )
        self.canvas.create_oval(
            center_x - 2, center_y - 5, center_x - 1, center_y - 4,
            fill="#67e8f9", outline="",
        )
        self.canvas.create_oval(
            center_x + 1, center_y - 5, center_x + 2, center_y - 4,
            fill="#67e8f9", outline="",
        )
        self.canvas.create_line(
            center_x + 4, center_y - 8, center_x + 5, center_y - 10,
            fill="#38bdf8", width=1,
        )
        self.canvas.create_oval(
            center_x + 4, center_y - 11, center_x + 6, center_y - 9,
            fill="#facc15", outline="",
        )

    def draw_path(self, path, color, width, offset_x, offset_y):
        for current, following in zip(path, path[1:]):
            row, column = current
            next_row, next_column = following
            self.canvas.create_line(
                column * CELL_SIZE + CELL_SIZE / 2 + offset_x,
                row * CELL_SIZE + CELL_SIZE / 2 + offset_y,
                next_column * CELL_SIZE + CELL_SIZE / 2 + offset_x,
                next_row * CELL_SIZE + CELL_SIZE / 2 + offset_y,
                fill=color,
                width=width,
                capstyle=tk.ROUND,
            )

    def handle_key(self, event):
        moves = {
            "Up": (-1, 0), "w": (-1, 0), "W": (-1, 0),
            "Down": (1, 0), "s": (1, 0), "S": (1, 0),
            "Left": (0, -1), "a": (0, -1), "A": (0, -1),
            "Right": (0, 1), "d": (0, 1), "D": (0, 1),
        }
        if (
            self.solving
            or self.robot_positions is not None
            or event.keysym not in moves
        ):
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
            self.character_frame += 1
            self.draw()
            if self.player == self.goal:
                self.status.config(text="You escaped the maze! Great job!")

    def solve_automatically(self):
        if self.solution is None:
            self.status.config(text="There is no route from A to B.")
            return
        self.start_animation(self.solution, "Quickest route")

    def play_selected_route(self):
        route_index = self.route_selector.current()
        if not 0 <= route_index < len(self.routes):
            self.status.config(text="Select a route to play.")
            return
        self.start_animation(self.routes[route_index], f"Route {route_index + 1}")

    def start_animation(self, route, label):
        self.cancel_animation()
        self.player = self.start
        self.visited = []
        self.character_frame = 0
        self.animation_route = route
        self.animation_label = label
        self.solving = True
        self.status.config(text=f"Playing {label}: {len(route) - 1} moves.")
        self.draw()
        self.animate_step(1)

    def race_all_robots(self):
        if not self.routes:
            self.status.config(text="There are no routes from A to B.")
            return

        self.cancel_animation()
        self.show_routes = False
        self.routes_button.config(text="Show routes")
        self.robot_positions = [route[0] for route in self.routes]
        self.robot_route_steps = [0 for _ in self.routes]
        self.character_frame = 0
        self.racing = True
        self.solving = True
        self.status.config(text=f"All {len(self.routes)} robots are racing to B!")
        self.draw()
        self.animation_id = self.root.after(55, self.animate_all_robots)

    def animate_all_robots(self):
        self.animation_id = None
        if not self.racing or self.robot_positions is None:
            return

        for index, route in enumerate(self.routes):
            if self.robot_route_steps[index] < len(route) - 1:
                self.robot_route_steps[index] += 1
                self.robot_positions[index] = route[self.robot_route_steps[index]]

        self.character_frame += 1
        self.draw()
        if all(
            self.robot_route_steps[index] >= len(route) - 1
            for index, route in enumerate(self.routes)
        ):
            self.racing = False
            self.solving = False
            fastest_moves = len(self.routes[self.shortest_route_number]) - 1
            self.status.config(
                text=(
                    f"Race finished! Route {self.shortest_route_number + 1} "
                    f"wins in {fastest_moves} moves."
                )
            )
            return

        self.animation_id = self.root.after(55, self.animate_all_robots)

    def animate_step(self, index):
        self.animation_id = None
        if self.animation_route is None:
            self.solving = False
            self.status.config(text="Animation stopped. Select a route to try again.")
            return

        if index >= len(self.animation_route):
            move_count = len(self.animation_route) - 1
            self.solving = False
            self.status.config(
                text=f"{self.animation_label} complete! Reached B in {move_count} moves."
            )
            self.animation_route = None
            return

        self.player = self.animation_route[index]
        self.visited.append(self.player)
        self.character_frame += 1
        self.draw()
        self.animation_id = self.root.after(55, self.animate_step, index + 1)

    def toggle_routes(self):
        if self.show_routes:
            self.show_routes = False
            self.routes_button.config(text="Show routes")
            self.draw()
            self.status.config(text="Move Pip with the arrow keys or WASD.")
            return

        self.restart()
        if not self.routes:
            self.status.config(text="There are no routes from A to B.")
            return

        self.show_routes = True
        self.routes_button.config(text="Hide routes")
        self.draw()
        fastest_moves = len(self.solution) - 1 if self.solution else 0
        self.status.config(
            text=(
                f"{len(self.routes)} routes shown. "
                f"Quickest: Route {self.shortest_route_number + 1}, "
                f"{fastest_moves} moves."
            )
        )

    def restart(self):
        self.cancel_animation()
        self.show_routes = False
        self.routes_button.config(text="Show routes")
        self.player = self.start
        self.visited = []
        self.character_frame = 0
        self.status.config(text="Move Pip with the arrow keys or WASD.")
        self.draw()

    def cancel_animation(self):
        if self.animation_id is not None:
            self.root.after_cancel(self.animation_id)
            self.animation_id = None
        self.solving = False
        self.racing = False
        self.animation_route = None
        self.animation_label = ""
        self.robot_positions = None
        self.robot_route_steps = []


if __name__ == "__main__":
    window = tk.Tk()
    MazeGame(window)
    window.mainloop()
