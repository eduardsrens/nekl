MAZE ARCADE
===========

START HERE
Double-click PLAY_ARCADE.cmd on Windows.
Or run: python3.14 PLAY_ARCADE.py

The launcher works from any working directory. Python with Tkinter is required;
there are no third-party packages to install.

PLAY
Arrow keys or WASD: steer. Your character continues until a wall or a turn.
Space / P: pause or resume. Enter: start, continue, or advance to the next level.
H: hint. V: show/hide routes. N: new random maze. R: retry the same maze.
The game pauses when its window loses focus.

Pellet Hunt: collect every dot, avoid ghosts, then reach the green exit.
Power orbs let you eat ghosts for a short time. You have three lives.
Maze Run: reach the exit yourself, with no ghosts and optional pellets.

Choose Pocket, Classic, Grand, or Epic size and Chill, Arcade, or Expert difficulty.
There are 99 levels. Mazes grow every three levels, up to Epic size.
Generated layouts contain both corridors and open rooms.
The same seed, size, difficulty, and level reproduce the same maze.

Hint, Show ways, and Auto solve mark a run as assisted. Assisted runs do not
overwrite personal records. Room mazes show the shortest exit route plus a
bounded selection of alternative paths, ordered by length. These alternatives
are samples; the final one is not guaranteed to be the globally longest path.

FILES
PLAY_ARCADE.py / PLAY_ARCADE.cmd: launch the application.
core/: implementation and regression checks; no need to launch these files.
mazes/: the original two maze files and their exported text solutions.
saves/: local records and saved generated mazes, created when needed.

The Route Explorer button opens the original maze explorer.
Start directly there with: python3.14 PLAY_ARCADE.py --explorer
Export only the original maze text reports with: python3.14 PLAY_ARCADE.py --text

CHECKS
From this folder: python3.14 -B -m unittest discover -s core -p test_arcade.py
