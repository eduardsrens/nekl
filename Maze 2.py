import tkinter as tk
from pathlib import Path
from tkinter import messagebox


MAZE_FILE = Path(__file__).with_name("maze_25x41.txt")
CELL_SIZE = 18


def load_maze(path=MAZE_FILE):
	maze = tuple(path.read_text(encoding="utf-8").splitlines())
	if not maze or not maze[0]:
		raise ValueError("Labirinta fails ir tukšs.")

	width = len(maze[0])
	if any(len(row) != width for row in maze):
		raise ValueError("Visām labirinta rindām jābūt vienāda garuma.")

	starts = [(x, y) for y, row in enumerate(maze) for x, cell in enumerate(row) if cell == "A"]
	goals = [(x, y) for y, row in enumerate(maze) for x, cell in enumerate(row) if cell == "B"]
	if len(starts) != 1 or len(goals) != 1:
		raise ValueError("Labirintā jābūt tieši vienam sākumam A un vienai izejai B.")

	invalid = {cell for row in maze for cell in row} - {"#", " ", "A", "B"}
	if invalid:
		raise ValueError(f"Labirintā ir neatpazītas rakstzīmes: {''.join(sorted(invalid))}")

	return maze, starts[0], goals[0]


def find_shortest_path(maze, start, goal):
	if start == goal:
		return [start]

	start_frontier = {start}
	goal_frontier = {goal}
	start_parents = {start: None}
	goal_parents = {goal: None}

	while start_frontier and goal_frontier:
		if len(start_frontier) <= len(goal_frontier):
			frontier = start_frontier
			parents = start_parents
			other_parents = goal_parents
			expand_from_start = True
		else:
			frontier = goal_frontier
			parents = goal_parents
			other_parents = start_parents
			expand_from_start = False

		next_frontier = set()
		for x, y in frontier:
			for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
				neighbor = (x + dx, y + dy)
				nx, ny = neighbor
				if (
					0 <= ny < len(maze)
					and 0 <= nx < len(maze[ny])
					and maze[ny][nx] != "#"
					and neighbor not in parents
				):
					parents[neighbor] = (x, y)
					if neighbor in other_parents:
						path_from_start = []
						current = neighbor
						while current is not None:
							path_from_start.append(current)
							current = start_parents[current]
						path_from_start.reverse()

						path_to_goal = []
						current = goal_parents[neighbor]
						while current is not None:
							path_to_goal.append(current)
							current = goal_parents[current]
						return path_from_start + path_to_goal

					next_frontier.add(neighbor)

		if expand_from_start:
			start_frontier = next_frontier
		else:
			goal_frontier = next_frontier

	return []


class MazeApp:
	def __init__(self, root, maze, start, goal):
		self.root = root
		self.maze = maze
		self.start = start
		self.goal = goal
		self.animation_id = None

		root.title("25 x 41 labirints")
		width = len(maze[0]) * CELL_SIZE
		height = len(maze) * CELL_SIZE

		self.status = tk.StringVar(value="Labirints ielādēts no maze_25x41.txt")
		tk.Label(root, textvariable=self.status, font=("Segoe UI", 11)).pack(pady=(8, 4))
		self.canvas = tk.Canvas(root, width=width, height=height, bg="white", highlightthickness=1)
		self.canvas.pack(padx=10, pady=5)

		controls = tk.Frame(root)
		controls.pack(pady=(4, 10))
		tk.Button(controls, text="Atrisināt", command=self.solve, width=12).pack(side="left", padx=5)
		tk.Button(controls, text="Atiestatīt", command=self.draw_maze, width=12).pack(side="left", padx=5)

		self.draw_maze()
		self.root.after(150, self.solve)

	def draw_maze(self):
		if self.animation_id is not None:
			self.root.after_cancel(self.animation_id)
			self.animation_id = None

		self.canvas.delete("all")
		for y, row in enumerate(self.maze):
			for x, cell in enumerate(row):
				left = x * CELL_SIZE
				top = y * CELL_SIZE
				color = {"#": "#263238", "A": "#43A047", "B": "#E53935"}.get(cell, "#FFFFFF")
				self.canvas.create_rectangle(
					left,
					top,
					left + CELL_SIZE,
					top + CELL_SIZE,
					fill=color,
					outline="#CFD8DC",
				)

		self.status.set("Labirints ielādēts no maze_25x41.txt")

	def solve(self):
		self.draw_maze()
		path = find_shortest_path(self.maze, self.start, self.goal)
		if not path:
			self.status.set("Ceļš no A līdz B nav atrasts")
			return

		self.status.set(f"Īsākais ceļš: {len(path) - 1} soļi")
		self.animate_path(path, 1)

	def animate_path(self, path, index):
		if index >= len(path):
			self.animation_id = None
			return

		x, y = path[index]
		if (x, y) != self.goal:
			left = x * CELL_SIZE
			top = y * CELL_SIZE
			self.canvas.create_rectangle(
				left + 4,
				top + 4,
				left + CELL_SIZE - 4,
				top + CELL_SIZE - 4,
				fill="#1E88E5",
				outline="#1E88E5",
			)

		self.animation_id = self.root.after(15, self.animate_path, path, index + 1)


def main():
	root = tk.Tk()
	try:
		maze, start, goal = load_maze()
	except (OSError, ValueError) as error:
		messagebox.showerror("Nevar ielādēt labirintu", str(error), parent=root)
		root.destroy()
		return

	MazeApp(root, maze, start, goal)
	root.mainloop()


if __name__ == "__main__":
	main()
