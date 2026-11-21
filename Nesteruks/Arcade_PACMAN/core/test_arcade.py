"""Headless regression checks: python3.14 -B -m unittest discover -s core."""

from pathlib import Path
import tempfile
import unittest

try:
    from .arcade_core import ArcadeGame, DIFFICULTIES, ProfileStore, SIZES, alternative_routes, distances, generate_maze, maze_filename, shortest_path
    from .solve_maze import find_routes, read_maze
except ImportError:
    from arcade_core import ArcadeGame, DIFFICULTIES, ProfileStore, SIZES, alternative_routes, distances, generate_maze, maze_filename, shortest_path
    from solve_maze import find_routes, read_maze


class GeneratorTests(unittest.TestCase):
    def test_all_sizes_are_connected_and_have_open_rooms(self):
        for _, rows, columns in SIZES:
            for seed in range(12):
                with self.subTest(size=(rows, columns), seed=seed):
                    maze = generate_maze(rows, columns, str(seed))
                    self.assertEqual(len(distances(maze, maze.start)), len(maze.neighbors))
                    self.assertTrue(maze.rooms)
                    self.assertEqual(maze.grid[0], "#" * columns)
                    self.assertEqual(maze.grid[-1], "#" * columns)
                    self.assertTrue(all(line[0] == line[-1] == "#" for line in maze.grid))
                    for row, column, height, width in maze.rooms:
                        self.assertGreaterEqual(height, 3)
                        self.assertGreaterEqual(width, 3)
                        self.assertTrue(all((r, c) in maze.neighbors for r in range(row, row+height) for c in range(column, column+width)))

    def test_seed_reproduces_the_same_maze_and_rooms(self):
        first = generate_maze(15, 25, "same-seed")
        second = generate_maze(15, 25, "same-seed")
        self.assertEqual(first.grid, second.grid)
        self.assertEqual(first.rooms, second.rooms)
        self.assertNotEqual(first.grid, generate_maze(15, 25, "different-seed").grid)

    def test_room_alternatives_are_valid_bounded_and_include_a_shortest_path(self):
        for _, rows, columns in SIZES:
            maze = generate_maze(rows, columns, "room-routes")
            routes = alternative_routes(maze)
            self.assertLessEqual(len(routes), 8)
            self.assertEqual(len(routes[0]), len(shortest_path(maze, maze.start, maze.goal)))
            self.assertEqual([len(route) for route in routes], sorted(len(route) for route in routes))
            self.assertEqual(len(routes), len({tuple(route) for route in routes}))
            for route in routes:
                self.assertEqual(route[0], maze.start)
                self.assertEqual(route[-1], maze.goal)
                self.assertEqual(len(route), len(set(route)))
                self.assertTrue(all(b in maze.neighbors[a] for a, b in zip(route, route[1:])))

    def test_original_maze_solutions_still_match(self):
        folder = Path(__file__).resolve().parent.parent / "mazes"
        for name, lengths in (("maze_15x25.txt", [42, 62, 90, 98]), ("maze_25x41.txt", [76, 116, 228, 240])):
            maze, start, goal = read_maze(folder / name)
            self.assertEqual([len(route)-1 for route in find_routes(maze, start, goal)], lengths)

    def test_invalid_dimensions_and_route_limits(self):
        for rows, columns in ((4, 9), (9, 4), (6, 9)):
            with self.assertRaises(ValueError):
                generate_maze(rows, columns, "bad")
        with self.assertRaises(ValueError):
            alternative_routes(generate_maze(11, 19, "valid"), 0)


class GameTests(unittest.TestCase):
    def test_wall_collision_pause_and_input(self):
        game = ArcadeGame("movement", mode="maze")
        game.turn((-1, 0))
        game.advance(0.05)
        self.assertEqual(game.player, game.maze.start)
        self.assertEqual(game.moves, 0)
        following = game.maze.neighbors[game.player][0]
        game.turn((following[0]-game.player[0], following[1]-game.player[1]))
        game.advance(game.player_interval)
        self.assertGreater(game.moves, 0)
        game.toggle_pause()
        before = game.player, game.elapsed, game.score
        game.advance(10)
        self.assertEqual((game.player, game.elapsed, game.score), before)

    def test_auto_solves_both_modes_at_every_size_and_difficulty(self):
        for mode in ("hunt", "maze"):
            for difficulty in DIFFICULTIES:
                for size in range(4):
                    with self.subTest(mode=mode, difficulty=difficulty, size=size):
                        game = ArcadeGame("full-game", size, difficulty, mode)
                        game.toggle_auto()
                        for _ in range(15000):
                            game.advance(0.1)
                            if game.state == "won":
                                break
                        self.assertEqual(game.state, "won")
                        self.assertEqual(game.player, game.maze.goal)
                        self.assertEqual(game.lives, 3)
                        self.assertTrue(game.assisted)
                        if mode == "hunt":
                            self.assertEqual(game.remaining, 0)

    def test_lives_shield_and_game_over(self):
        game = ArcadeGame("collision")
        game.begin()
        ghost = game.ghosts[0]
        for lives in (2, 1, 0):
            game.invulnerable = 0
            ghost.position = game.player
            game.check_collision()
            self.assertEqual(game.lives, lives)
            game.check_collision()
            self.assertEqual(game.lives, lives)
        self.assertEqual(game.state, "lost")
        game.advance(1)
        self.assertEqual(game.lives, 0)

    def test_power_allows_eating_a_ghost_once(self):
        game = ArcadeGame("powered")
        game.begin()
        game.invulnerable = 0
        game.power_remaining = 5
        game.ghosts[0].position = game.player
        game.check_collision()
        self.assertEqual(game.score, 200)
        self.assertEqual(game.lives, 3)
        game.check_collision()
        self.assertEqual(game.score, 200)

    def test_hints_and_level_progression_keep_assisted_status(self):
        game = ArcadeGame("levels", size_index=0, level=3)
        self.assertTrue(game.hint())
        self.assertTrue(game.assisted)
        game.score, game.lives = 1230, 2
        following = game.next_level()
        self.assertEqual(following.level, 4)
        self.assertEqual(following.size_index, 1)
        self.assertEqual(following.score, 1230)
        self.assertEqual(following.lives, 3)
        self.assertTrue(following.assisted)
        self.assertEqual(ArcadeGame("top", level=99).size_index, 3)

    def test_seed_cannot_escape_the_save_directory(self):
        filename = maze_filename(ArcadeGame("../../outside\\evil"))
        self.assertEqual(Path(filename).name, filename)
        self.assertNotIn("\\", filename)


class ProfileTests(unittest.TestCase):
    def test_corrupt_profile_atomic_record_and_assisted_exclusion(self):
        # Temporary files and their cleanup remain inside this application's folder.
        folder = Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory(prefix=".test-", dir=folder) as temporary:
            root = Path(temporary).resolve()
            self.assertTrue(root.is_relative_to(folder))
            path = root / "arcade_progress.json"
            path.write_text("invalid json", encoding="utf-8")
            profile = ProfileStore(root)
            self.assertEqual(profile.data["high_score"], 0)
            game = ArcadeGame("records")
            game.score, game.state = 1800, "won"
            profile.record(game)
            self.assertEqual(ProfileStore(root).data["high_score"], 1800)
            self.assertEqual(ProfileStore(root).data["clears"], 1)
            previous = path.read_bytes()
            game.assisted, game.score = True, 50000
            profile.record(game)
            self.assertEqual(path.read_bytes(), previous)
            self.assertEqual(list(root.glob(".arcade-*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
