"""Deterministic maze generation and the display-independent arcade rules."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import random
import tempfile


Cell = tuple[int, int]
DIRECTIONS = ((-1, 0), (0, 1), (1, 0), (0, -1))
SIZES = (("Pocket", 11, 19), ("Classic", 15, 25), ("Grand", 21, 35), ("Epic", 25, 41))
DIFFICULTIES = {"Chill": (1, 0.28, 1), "Arcade": (2, 0.23, 3), "Expert": (3, 0.19, 4)}


@dataclass(frozen=True)
class Maze:
    grid: tuple[str, ...]
    start: Cell
    goal: Cell
    neighbors: dict[Cell, tuple[Cell, ...]]
    rooms: tuple[tuple[int, int, int, int], ...] = ()

    @property
    def rows(self) -> int:
        return len(self.grid)

    @property
    def columns(self) -> int:
        return len(self.grid[0])


def generate_maze(rows: int, columns: int, seed: str, loops: int = 3) -> Maze:
    """Carve a connected maze with winding corridors and open rectangular rooms."""
    if rows < 5 or columns < 5 or rows % 2 != 1 or columns % 2 != 1:
        raise ValueError("Maze dimensions must be odd numbers of at least five.")
    if not 0 <= loops <= 4:
        raise ValueError("The number of extra passages must be between zero and four.")
    rng = random.Random(str(seed))
    board = [["#"] * columns for _ in range(rows)]
    start, goal = (1, 1), (rows - 2, columns - 2)
    board[1][1] = " "
    stack = [start]
    while stack:
        row, column = stack[-1]
        choices = [
            (row + 2 * dr, column + 2 * dc, dr, dc)
            for dr, dc in DIRECTIONS
            if 0 < row + 2 * dr < rows - 1
            and 0 < column + 2 * dc < columns - 1
            and board[row + 2 * dr][column + 2 * dc] == "#"
        ]
        if not choices:
            stack.pop()
            continue
        nr, nc, dr, dc = rng.choice(choices)
        board[row + dr][column + dc] = board[nr][nc] = " "
        stack.append((nr, nc))

    candidates = [(r, c) for r in range(1, rows - 1) for c in range(1, columns - 1) if board[r][c] == "#"]
    rng.shuffle(candidates)
    for row, column in candidates:
        if not loops:
            break
        surrounding = [board[row + dr][column + dc] != "#" for dr, dc in DIRECTIONS]
        if surrounding in ([True, False, True, False], [False, True, False, True]):
            board[row][column] = " "
            loops -= 1
    rooms = []
    room_count = min(4, 1 + rows * columns // 150)
    for _ in range(100):
        if len(rooms) >= room_count:
            break
        height = rng.choice((3, 5)) if rows >= 15 else 3
        width = rng.choice((3, 5, 7)) if columns >= 25 else rng.choice((3, 5))
        if height >= rows - 1 or width >= columns - 1:
            continue
        row = rng.choice(range(1, rows - height, 2))
        column = rng.choice(range(1, columns - width, 2))
        if any(row <= r < row + height and column <= c < column + width for r, c in (start, goal)):
            continue
        if any(row < r + h + 1 and r < row + height + 1 and column < c + w + 1 and c < column + width + 1 for r, c, h, w in rooms):
            continue
        for r in range(row, row + height):
            for c in range(column, column + width):
                board[r][c] = " "
        rooms.append((row, column, height, width))

    board[start[0]][start[1]], board[goal[0]][goal[1]] = "A", "B"
    cells = {(r, c) for r, line in enumerate(board) for c, char in enumerate(line) if char != "#"}
    neighbors = {
        (r, c): tuple((r + dr, c + dc) for dr, dc in DIRECTIONS if (r + dr, c + dc) in cells)
        for r, c in cells
    }
    return Maze(tuple("".join(line) for line in board), start, goal, neighbors, tuple(rooms))


def distances(maze: Maze, start: Cell) -> dict[Cell, int]:
    found = {start: 0}
    pending = deque([start])
    while pending:
        current = pending.popleft()
        for following in maze.neighbors[current]:
            if following not in found:
                found[following] = found[current] + 1
                pending.append(following)
    return found


def shortest_path(maze: Maze, start: Cell, targets: Cell | set[Cell]) -> list[Cell]:
    targets = {targets} if isinstance(targets, tuple) else targets
    if not targets:
        return []
    previous = {start: None}
    pending = deque([start])
    while pending:
        current = pending.popleft()
        if current in targets:
            route = []
            while current is not None:
                route.append(current)
                current = previous[current]
            return route[::-1]
        for following in maze.neighbors[current]:
            if following not in previous:
                previous[following] = current
                pending.append(following)
    return []


def alternative_routes(maze: Maze, limit: int = 8) -> list[list[Cell]]:
    """Return the true shortest route and bounded, varied loop-free alternatives.

    Open rooms have exponentially many paths. Seeded DFS samples alternatives
    in linear passes instead of trying to enumerate every possible room traversal.
    The longest displayed route is the longest sample, not a global longest path.
    """
    if not 1 <= limit <= 32:
        raise ValueError("Request between one and 32 route alternatives.")
    shortest = shortest_path(maze, maze.start, maze.goal)
    if not shortest:
        return []
    if limit == 1:
        return [shortest]
    found = {tuple(shortest)}
    rng = random.Random(hashlib.sha256("\n".join(maze.grid).encode()).digest())
    for _ in range(limit * 4):
        path, visited = [maze.start], {maze.start}
        choices = list(maze.neighbors[maze.start])
        rng.shuffle(choices)
        stack = [iter(choices)]
        while stack:
            if path[-1] == maze.goal:
                found.add(tuple(path))
                break
            following = next(stack[-1], None)
            if following is None:
                stack.pop()
                path.pop()
            elif following not in visited:
                visited.add(following)
                path.append(following)
                choices = list(maze.neighbors[following])
                rng.shuffle(choices)
                stack.append(iter(choices))
    ranked = sorted(found, key=lambda route: (len(route), route))
    if len(ranked) > limit:
        ranked = [ranked[round(index * (len(ranked) - 1) / (limit - 1))] for index in range(limit)]
    return [list(route) for route in ranked]


@dataclass
class Ghost:
    position: Cell
    spawn: Cell
    previous: Cell | None = None
    respawn: float = 0.0


class ArcadeGame:
    """A deterministic, time-stepped game. Rendering never changes its rules."""

    def __init__(self, seed: str, size_index=1, difficulty="Arcade", mode="hunt", level=1, score=0, lives=3):
        if difficulty not in DIFFICULTIES or mode not in ("hunt", "maze"):
            raise ValueError("Unknown game mode or difficulty.")
        if not 0 <= size_index < len(SIZES) or not 1 <= level <= 99:
            raise ValueError("Invalid size or level.")
        self.seed = str(seed).strip()[:48] or "0"
        self.base_size = size_index
        self.size_index = min(3, size_index + (level - 1) // 3)
        self.difficulty, self.mode, self.level = difficulty, mode, level
        self.initial_score = score
        self.score, self.lives = score, lives
        self.rng = random.Random(f"{self.seed}|{level}|ghosts")
        _, rows, columns = SIZES[self.size_index]
        ghost_count, ghost_interval, loops = DIFFICULTIES[difficulty]
        self.maze = generate_maze(rows, columns, f"{self.seed}|{level}|{difficulty}|{self.size_index}", loops)
        self.player = self.previous_player = self.maze.start
        self.direction = self.queued_direction = None
        self.facing = (0, 1)
        self.pellets = set(self.maze.neighbors) - {self.maze.start, self.maze.goal}
        self.powers = set()
        corners = ((1, columns - 2), (rows - 2, 1), (rows - 2, columns - 4), (1, 3))
        for corner in corners:
            if corner in self.pellets:
                self.powers.add(corner)
        self.pellets -= self.powers
        far = distances(self.maze, self.maze.start)
        candidates = sorted(self.maze.neighbors, key=lambda cell: (-far[cell], cell))
        spawns = []
        for cell in candidates:
            if cell not in (self.maze.start, self.maze.goal) and all(abs(cell[0]-other[0])+abs(cell[1]-other[1]) >= 4 for other in spawns):
                spawns.append(cell)
            if len(spawns) >= min(4, ghost_count + (level - 1) // 4):
                break
        self.ghosts = [Ghost(cell, cell) for cell in spawns] if mode == "hunt" else []
        self.player_interval = max(0.085, 0.135 - (level - 1) * 0.002)
        self.ghost_interval = max(self.player_interval * 1.12, ghost_interval - (level - 1) * 0.005)
        self.elapsed = self.power_remaining = 0.0
        self.invulnerable = 2.5
        self.moves = 0
        self.state = "ready"
        self.assisted = False
        self.auto = False
        self.auto_path = deque()
        self.events = []
        self.player_clock = self.ghost_clock = 0.0
        self.visited = {self.player}

    @property
    def remaining(self) -> int:
        return len(self.pellets) + len(self.powers)

    @property
    def exit_open(self) -> bool:
        return self.mode == "maze" or self.remaining == 0

    def begin(self) -> None:
        if self.state in ("ready", "paused"):
            self.state = "playing"

    def toggle_pause(self) -> None:
        if self.state == "playing":
            self.state = "paused"
        elif self.state in ("ready", "paused"):
            self.begin()

    def turn(self, direction: Cell) -> None:
        if direction not in DIRECTIONS or self.state in ("won", "lost", "paused"):
            return
        self.begin()
        self.auto = False
        self.auto_path.clear()
        self.queued_direction = direction
        if self.direction is None:
            self.player_clock = self.player_interval

    def objective_path(self) -> list[Cell]:
        targets = self.pellets | self.powers if not self.exit_open else {self.maze.goal}
        return shortest_path(self.maze, self.player, targets)

    def hint(self) -> list[Cell]:
        self.assisted = True
        return self.objective_path()[:6]

    def toggle_auto(self) -> None:
        if self.state in ("won", "lost"):
            return
        self.auto = not self.auto
        self.auto_path.clear()
        self.direction = self.queued_direction = None
        if self.auto:
            self.assisted = True
            self.begin()

    def advance(self, elapsed: float) -> None:
        if self.state != "playing":
            return
        elapsed = max(0.0, min(elapsed, 0.1))
        self.elapsed += elapsed
        self.power_remaining = max(0.0, self.power_remaining - elapsed)
        self.invulnerable = max(0.0, self.invulnerable - elapsed)
        for ghost in self.ghosts:
            ghost.respawn = max(0.0, ghost.respawn - elapsed)
        self.player_clock += elapsed
        while self.player_clock >= self.player_interval and self.state == "playing":
            self.player_clock -= self.player_interval
            self.move_player()
        self.ghost_clock += elapsed
        if not self.auto and self.ghost_clock >= self.ghost_interval and self.state == "playing":
            self.ghost_clock %= self.ghost_interval
            self.move_ghosts()

    def move_player(self) -> bool:
        self.previous_player = self.player
        following = None
        if self.auto:
            if not self.auto_path:
                self.auto_path.extend(self.objective_path()[1:])
            if self.auto_path:
                following = self.auto_path.popleft()
        else:
            for direction in (self.queued_direction, self.direction):
                if direction is not None:
                    candidate = self.player[0] + direction[0], self.player[1] + direction[1]
                    if candidate in self.maze.neighbors[self.player]:
                        following, self.direction = candidate, direction
                        break
        if following is None:
            return False
        if following not in self.maze.neighbors[self.player]:
            raise ValueError("A move must follow an open adjacent cell.")
        self.previous_player, self.player = self.player, following
        self.facing = self.player[0] - self.previous_player[0], self.player[1] - self.previous_player[1]
        self.moves += 1
        self.visited.add(self.player)
        if self.player in self.pellets:
            self.pellets.remove(self.player)
            self.score += 10
        if self.player in self.powers:
            self.powers.remove(self.player)
            self.score += 50
            self.power_remaining = 8.0 if self.difficulty == "Chill" else 6.0
            self.events.append("power")
        self.check_collision()
        if self.state == "playing" and self.player == self.maze.goal and self.exit_open:
            self.score += self.level * 100 + self.lives * 100 + max(0, 500 - int(self.elapsed) * 2)
            self.state = "won"
            self.auto = False
            self.events.append("win")
        return True

    def move_ghosts(self) -> None:
        away = distances(self.maze, self.player)
        for index, ghost in enumerate(self.ghosts):
            if ghost.respawn:
                continue
            choices = list(self.maze.neighbors[ghost.position])
            if len(choices) > 1 and ghost.previous in choices:
                choices.remove(ghost.previous)
            if self.power_remaining:
                following = max(choices, key=lambda cell: away[cell])
            elif index % 3 == 2 and int(self.elapsed) % 6 < 3:
                following = self.rng.choice(choices)
            else:
                following = min(choices, key=lambda cell: away[cell])
            ghost.previous, ghost.position = ghost.position, following
            before = self.lives
            self.check_collision()
            if self.lives != before or self.state != "playing":
                break

    def check_collision(self) -> None:
        if self.state != "playing" or self.invulnerable or self.auto:
            return
        for ghost in self.ghosts:
            if ghost.position != self.player or ghost.respawn:
                continue
            if self.power_remaining:
                self.score += 200
                ghost.position, ghost.previous, ghost.respawn = ghost.spawn, None, 2.5
                self.events.append("ghost")
            else:
                self.lives -= 1
                self.player = self.previous_player = self.maze.start
                self.direction = self.queued_direction = None
                self.player_clock = self.ghost_clock = 0.0
                self.invulnerable = 2.5
                self.power_remaining = 0.0
                for other in self.ghosts:
                    other.position, other.previous = other.spawn, None
                self.events.append("hit")
                if not self.lives:
                    self.state = "lost"
                break

    def next_level(self) -> ArcadeGame:
        following = ArcadeGame(self.seed, self.base_size, self.difficulty, self.mode, min(99, self.level + 1), self.score, min(3, self.lives + (self.level % 3 == 0)))
        following.assisted = self.assisted
        return following


class ProfileStore:
    """Keep a small local record, replacing it atomically after a clean write."""

    def __init__(self, folder: Path):
        self.path = folder / "arcade_progress.json"
        self.data = {"version": 1, "high_score": 0, "clears": 0, "highest_level": 1}
        try:
            if self.path.stat().st_size <= 65536:
                loaded = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict) and loaded.get("version") == 1:
                    for key in ("high_score", "clears", "highest_level"):
                        value = loaded.get(key)
                        if type(value) is int and value >= 0:
                            self.data[key] = value
        except (OSError, ValueError, TypeError):
            pass

    def record(self, game: ArcadeGame) -> None:
        if game.assisted:
            return
        self.data["high_score"] = max(self.data["high_score"], game.score)
        if game.state == "won":
            self.data["clears"] += 1
            self.data["highest_level"] = max(self.data["highest_level"], min(99, game.level + 1))
        temporary = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent, prefix=".arcade-", suffix=".tmp", delete=False) as stream:
                temporary = Path(stream.name)
                json.dump(self.data, stream, indent=2)
                stream.write("\n")
            temporary.replace(self.path)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()


def maze_filename(game: ArcadeGame) -> str:
    identity = f"{game.seed}|{game.level}|{game.base_size}|{game.difficulty}"
    digest = hashlib.sha256(identity.encode()).hexdigest()[:12]
    return f"maze_{game.maze.rows}x{game.maze.columns}_{digest}.txt"
