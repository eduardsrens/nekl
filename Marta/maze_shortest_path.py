from collections import deque
from pathlib import Path
import argparse


MAZE_FILE = Path(__file__).with_name("maze_25x41_Marta.txt")
CELL_SIZE = 24
ANIMATION_STEP_MS = 250
PATH_COLORS = ("#facc15", "#3b82f6", "#22c55e", "#ef4444")
PATH_LIGHT_COLORS = ("#fef08a", "#bfdbfe", "#bbf7d0", "#fecaca")


def load_maze(path):
    maze = path.read_text(encoding="utf-8").splitlines()
    if not maze:
        raise ValueError("Labirinta fails ir tukšs.")

    width = len(maze[0])
    if any(len(row) != width for row in maze):
        raise ValueError("Visām labirinta rindām jābūt vienāda garuma.")

    start = end = None
    for row_index, row in enumerate(maze):
        for column_index, char in enumerate(row):
            if char == "A":
                start = (row_index, column_index)
            elif char == "B":
                end = (row_index, column_index)

    if start is None or end is None:
        raise ValueError("Labirintā jābūt termināļiem A un B.")

    return maze, start, end


def find_shortest_path(maze, start, end):
    queue = deque([start])
    previous = {start: None}

    while queue:
        row, column = queue.popleft()
        if (row, column) == end:
            break

        for next_row, next_column in (
            (row - 1, column),
            (row + 1, column),
            (row, column - 1),
            (row, column + 1),
        ):
            neighbor = (next_row, next_column)
            if not (0 <= next_row < len(maze) and 0 <= next_column < len(maze[0])):
                continue
            if maze[next_row][next_column] == "#" or neighbor in previous:
                continue
            previous[neighbor] = (row, column)
            queue.append(neighbor)

    if end not in previous:
        return None

    path = []
    current = end
    while current is not None:
        path.append(current)
        current = previous[current]
    path.reverse()
    return path


def find_all_paths(maze, start, end):
    paths = []
    visited = {start}
    current_path = [start]

    def visit(position):
        row, column = position
        if position == end:
            paths.append(current_path.copy())
            return

        for next_row, next_column in (
            (row - 1, column),
            (row + 1, column),
            (row, column - 1),
            (row, column + 1),
        ):
            neighbor = (next_row, next_column)
            if not (0 <= next_row < len(maze) and 0 <= next_column < len(maze[0])):
                continue
            if maze[next_row][next_column] == "#" or neighbor in visited:
                continue

            visited.add(neighbor)
            current_path.append(neighbor)
            visit(neighbor)
            current_path.pop()
            visited.remove(neighbor)

    visit(start)
    return paths


def print_maze(maze, path):
    path_cells = set(path)
    for row_index, row in enumerate(maze):
        output = []
        for column_index, char in enumerate(row):
            position = (row_index, column_index)
            if position in path_cells and char not in ("A", "B"):
                output.append(".")
            else:
                output.append(char)
        print("".join(output))


def print_path(maze, path, path_number):
    print(f"\nCeļš {path_number}:")
    print_maze(maze, path)
    print(f"Soļu skaits: {len(path) - 1}")


def show_graphical(maze, path):
    try:
        import tkinter as tk
    except ImportError:
        print("Tkinter nav pieejams; grafiskais loga attēlojums netika atvērts.")
        return

    try:
        root = tk.Tk()
    except tk.TclError:
        print("Grafiskā vide nav pieejama; parādīts tikai termināļa izvads.")
        return

    rows = len(maze)
    columns = len(maze[0])
    root.title("Labirints - īsākais ceļš no A līdz B")
    canvas = tk.Canvas(
        root,
        width=columns * CELL_SIZE,
        height=rows * CELL_SIZE,
        bg="white",
        highlightthickness=0,
    )
    canvas.pack(padx=10, pady=10)

    path_cells = set(path)
    for row_index, row in enumerate(maze):
        for column_index, char in enumerate(row):
            x1 = column_index * CELL_SIZE
            y1 = row_index * CELL_SIZE
            x2 = x1 + CELL_SIZE
            y2 = y1 + CELL_SIZE
            position = (row_index, column_index)

            if char == "#":
                color = "#1f2937"
            elif position in path_cells:
                color = "#4ade80"
            else:
                color = "#ffffff"
            canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#d1d5db")

            if char in ("A", "B"):
                canvas.create_text(
                    (x1 + x2) / 2,
                    (y1 + y2) / 2,
                    text=char,
                    fill="#111827",
                    font=("Arial", 12, "bold"),
                )

    root.mainloop()


def show_all_graphical(maze, paths):
    try:
        import tkinter as tk
    except ImportError:
        print("Tkinter nav pieejams; grafiskais loga attēlojums netika atvērts.")
        return

    try:
        root = tk.Tk()
    except tk.TclError:
        print("Grafiskā vide nav pieejama; parādīts tikai termināļa izvads.")
        return

    rows = len(maze)
    columns = len(maze[0])
    root.title("Labirints - visi iespējamie ceļi")
    canvas = tk.Canvas(
        root,
        width=columns * CELL_SIZE,
        height=rows * CELL_SIZE,
        bg="white",
        highlightthickness=0,
    )
    canvas.pack(padx=10, pady=10)
    step_label = tk.Label(root, font=("Arial", 11, "bold"))
    step_label.pack(pady=(0, 10))
    path_index = [0]
    step_index = [0]
    animation_id = [None]
    movement_mode = tk.StringVar(value="automatic")

    def draw_path():
        path = paths[path_index[0]]
        canvas.delete("all")
        color_index = path_index[0] % len(PATH_COLORS)
        path_color = PATH_COLORS[color_index]
        path_light_color = PATH_LIGHT_COLORS[color_index]
        path_cells = set(path)
        visited_cells = set(path[: step_index[0] + 1])

        for row_index, row in enumerate(maze):
            for column_index, char in enumerate(row):
                x1 = column_index * CELL_SIZE
                y1 = row_index * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE
                position = (row_index, column_index)

                if char == "#":
                    color = "#1f2937"
                    outline = "#d1d5db"
                    line_width = 1
                elif position == path[step_index[0]]:
                    color = path_color
                    outline = "#111827"
                    line_width = 2
                elif position in visited_cells:
                    color = path_color
                    outline = "#d1d5db"
                    line_width = 1
                elif position in path_cells:
                    color = path_light_color
                    outline = "#d1d5db"
                    line_width = 1
                else:
                    color = "#ffffff"
                    outline = "#d1d5db"
                    line_width = 1
                canvas.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill=color,
                    outline=outline,
                    width=line_width,
                )

                if char in ("A", "B"):
                    canvas.create_text(
                        (x1 + x2) / 2,
                        (y1 + y2) / 2,
                        text=char,
                        fill="#111827",
                        font=("Arial", 12, "bold"),
                    )

        step_label.config(
            text=(
                f"Ceļš {path_index[0] + 1}/{len(paths)}  |  "
                f"Solis {step_index[0]}/{len(path) - 1}"
            )
        )
        next_step_button.config(
            state=(
                "normal"
                if movement_mode.get() == "manual"
                and step_index[0] < len(path) - 1
                else "disabled"
            )
        )

    def cancel_animation():
        if animation_id[0] is not None:
            root.after_cancel(animation_id[0])
            animation_id[0] = None

    def schedule_animation():
        path = paths[path_index[0]]
        if (
            movement_mode.get() == "automatic"
            and step_index[0] < len(path) - 1
        ):
            animation_id[0] = root.after(
                ANIMATION_STEP_MS, advance_animation
            )

    def advance_one_step():
        path = paths[path_index[0]]
        if step_index[0] < len(path) - 1:
            step_index[0] += 1
            draw_path()

    def advance_animation():
        animation_id[0] = None
        if movement_mode.get() == "automatic":
            advance_one_step()
            schedule_animation()

    def advance_manually():
        if movement_mode.get() == "manual":
            advance_one_step()

    def change_movement_mode():
        cancel_animation()
        draw_path()
        schedule_animation()

    def select_path(index):
        cancel_animation()
        path_index[0] = index
        step_index[0] = 0
        draw_path()
        schedule_animation()

    path_buttons_frame = tk.Frame(root)
    path_buttons_frame.pack(pady=(0, 10))
    for index in range(len(paths)):
        color_index = index % len(PATH_LIGHT_COLORS)
        button = tk.Button(
            path_buttons_frame,
            text=f"{index + 1}. ceļš",
            bg=PATH_LIGHT_COLORS[color_index],
            activebackground=PATH_LIGHT_COLORS[color_index],
            command=lambda selected_index=index: select_path(selected_index),
        )
        button.grid(row=index // 8, column=index % 8, padx=3, pady=2)

    movement_frame = tk.Frame(root)
    movement_frame.pack(pady=(0, 10))
    tk.Radiobutton(
        movement_frame,
        text="Automātiski",
        variable=movement_mode,
        value="automatic",
        command=change_movement_mode,
    ).pack(side="left", padx=4)
    tk.Radiobutton(
        movement_frame,
        text="Manuāli",
        variable=movement_mode,
        value="manual",
        command=change_movement_mode,
    ).pack(side="left", padx=4)
    next_step_button = tk.Button(
        movement_frame,
        text="Nākamais solis",
        command=advance_manually,
    )
    next_step_button.pack(side="left", padx=4)

    draw_path()
    schedule_animation()
    root.mainloop()


def main(maze_path=MAZE_FILE):
    parser = argparse.ArgumentParser(description="Atrod ceļus labirintā no A līdz B.")
    parser.add_argument(
        "--console",
        action="store_true",
        help="izdrukā tikai termināļa rezultātu bez grafiskā loga",
    )
    path_mode = parser.add_mutually_exclusive_group()
    path_mode.add_argument(
        "--all",
        action="store_true",
        dest="all_paths",
        help="atrod un attēlo visus iespējamos ceļus (noklusējuma režīms)",
    )
    path_mode.add_argument(
        "--shortest",
        action="store_false",
        dest="all_paths",
        help="atrod tikai īsāko ceļu",
    )
    parser.set_defaults(all_paths=True)
    args = parser.parse_args()

    maze, start, end = load_maze(maze_path)
    if args.all_paths:
        paths = find_all_paths(maze, start, end)
        if not paths:
            print("No A līdz B nav iespējams nokļūt.")
            return

        print(f"Iespējamo ceļu skaits: {len(paths)}")
        for path_number, path in enumerate(paths, start=1):
            print_path(maze, path, path_number)

        shortest_length = min(len(path) - 1 for path in paths)
        print(f"\nĪsākais attālums: {shortest_length} soļi")
        if not args.console:
            show_all_graphical(maze, paths)
        return

    path = find_shortest_path(maze, start, end)
    if path is None:
        print("No A līdz B nav iespējams nokļūt.")
        return

    print_maze(maze, path)
    print(f"Soļu skaits: {len(path) - 1}")

    if not args.console:
        show_graphical(maze, path)


if __name__ == "__main__":
    main()
