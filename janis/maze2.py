import tkinter as tk

from labirints import MazePaths


def main():
    root = tk.Tk()
    MazePaths(root, maze_filename="Maze2", cell_size=20)
    root.mainloop()


if __name__ == "__main__":
    main()
