"""
Pure-Python ports of the LinkedIn puzzle-game solving algorithms
(originally solver.js). No DOM/Playwright dependency here — these
operate on plain data structures so they can be unit tested on their
own. Browser interaction (reading the board, clicking cells) lives in
check_and_solve.py.
"""

import itertools
from dataclasses import dataclass


class QueensSolver:
    """
    colors: flat list[int], len == size*size, color-group id per cell.
    solve() -> flat list[bool], True where a queen goes, or None if
    unsolvable.
    """

    def __init__(self, colors: list[int]):
        self.colors = colors
        self.size = round(len(colors) ** 0.5)
        self.board = [False] * len(colors)

    def _is_valid(self, r: int, c: int) -> bool:
        idx = r * self.size + c
        color = self.colors[idx]

        for i in range(self.size):
            if i != r and self.board[i * self.size + c]:
                return False

        for i in range(len(self.colors)):
            if i != idx and self.colors[i] == color and self.board[i]:
                return False

        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.size and 0 <= nc < self.size and self.board[nr * self.size + nc]:
                    return False
        return True

    def _solve(self, row: int = 0) -> bool:
        if row == self.size:
            return True
        for c in range(self.size):
            if self._is_valid(row, c):
                idx = row * self.size + c
                self.board[idx] = True
                if self._solve(row + 1):
                    return True
                self.board[idx] = False
        return False

    def solve(self) -> list[bool] | None:
        return self.board if self._solve() else None


class MiniSudokuSolver:
    """
    prefilled: flat list[int], len 36. 0 = empty, 1-6 = given digit.
    solve() -> flat list[int], len 36, fully solved board, or None.
    """

    def __init__(self, prefilled: list[int]):
        if len(prefilled) != 36:
            raise ValueError(f"expected 36 cells, got {len(prefilled)}")
        self.board = list(prefilled)

    def _is_valid(self, idx: int, val: int) -> bool:
        r, c = divmod(idx, 6)
        for i in range(6):
            if i != c and self.board[r * 6 + i] == val:
                return False
            if i != r and self.board[i * 6 + c] == val:
                return False

        box_r, box_c = (r // 2) * 2, (c // 3) * 3
        for dr, dc in itertools.product(range(2), range(3)):
            ni = (box_r + dr) * 6 + (box_c + dc)
            if ni != idx and self.board[ni] == val:
                return False
        return True

    def _next_empty(self, start: int) -> int:
        try:
            return self.board.index(0, start)
        except ValueError:
            return -1

    def _solve(self, idx: int | None = None) -> bool:
        if idx is None:
            idx = self._next_empty(0)
        if idx == -1:
            return True
        nxt = self._next_empty(idx + 1)
        for val in range(1, 7):
            if self._is_valid(idx, val):
                self.board[idx] = val
                if self._solve(nxt):
                    return True
                self.board[idx] = 0
        return False

    def solve(self) -> list[int] | None:
        return self.board if self._solve() else None


@dataclass
class TangoClue:
    idx1: int
    idx2: int
    type: str  # "equal" | "diff"


class TangoSolver:
    """
    size: board dimension (e.g. 6 -> 6x6).
    pre_placed: dict[idx -> 1|2] cells that already have Sun(1)/Moon(2).
    clues: list[TangoClue] equal/diff constraints between adjacent cells.
    solve() -> flat list[int] len size*size, 1=Sun 2=Moon, or None.
    """

    def __init__(self, size: int, pre_placed: dict[int, int], clues: list[TangoClue]):
        self.size = size
        self.clues = clues
        self.board = [[0] * size for _ in range(size)]
        for idx, val in pre_placed.items():
            r, c = divmod(idx, size)
            self.board[r][c] = val

    def _is_valid(self, r: int, c: int, val: int) -> bool:
        if self.board[r].count(val) >= self.size / 2:
            return False
        if sum(self.board[i][c] == val for i in range(self.size)) >= self.size / 2:
            return False

        if c >= 2 and self.board[r][c - 1] == val and self.board[r][c - 2] == val:
            return False
        if 1 <= c < self.size - 1 and self.board[r][c - 1] == val and self.board[r][c + 1] == val:
            return False
        if c + 2 < self.size and self.board[r][c + 1] == val and self.board[r][c + 2] == val:
            return False

        if r >= 2 and self.board[r - 1][c] == val and self.board[r - 2][c] == val:
            return False
        if 1 <= r < self.size - 1 and self.board[r - 1][c] == val and self.board[r + 1][c] == val:
            return False
        if r + 2 < self.size and self.board[r + 1][c] == val and self.board[r + 2][c] == val:
            return False

        idx = r * self.size + c
        for clue in self.clues:
            if clue.idx1 == idx or clue.idx2 == idx:
                other_idx = clue.idx2 if clue.idx1 == idx else clue.idx1
                other_val = self.board[other_idx // self.size][other_idx % self.size]
                if other_val != 0:
                    if clue.type == "equal" and val != other_val:
                        return False
                    if clue.type == "diff" and val == other_val:
                        return False
        return True

    def _solve(self) -> bool:
        for r in range(self.size):
            for c in range(self.size):
                if self.board[r][c] == 0:
                    for val in (1, 2):
                        if self._is_valid(r, c, val):
                            self.board[r][c] = val
                            if self._solve():
                                return True
                            self.board[r][c] = 0
                    return False
        return True

    def solve(self) -> list[int] | None:
        if not self._solve():
            return None
        return [self.board[r][c] for r in range(self.size) for c in range(self.size)]


class ZipSolver:
    """
    Zip: draw one continuous path through every cell exactly once
    (a Hamiltonian path), passing through numbered checkpoints in
    increasing order, never crossing a wall between two cells.

    size: grid dimension (size x size).
    checkpoints: dict[idx -> order], order is 1..N. The path must
                 start at the order=1 cell.
    walls: iterable of (idx_a, idx_b) pairs of orthogonally-adjacent
           cells that cannot be crossed.
    must_end_at_last_checkpoint: assumption that the path's final
        cell must be the highest-order checkpoint (typical Zip rule).
        Set False if your version allows continuing past the last dot.

    solve() -> list[int] of cell indices in visiting order (length
    size*size), or None if unsolvable.
    """

    def __init__(
        self,
        size: int,
        checkpoints: dict[int, int],
        walls: list[tuple[int, int]] | None = None,
        must_end_at_last_checkpoint: bool = True,
    ):
        self.size = size
        self.total = size**2
        self.checkpoints = dict(checkpoints)
        self.max_order = max(self.checkpoints.values()) if self.checkpoints else 0
        self.walls = {frozenset(w) for w in (walls or [])}
        self.must_end_at_last_checkpoint = must_end_at_last_checkpoint

    def _neighbors(self, idx: int):
        r, c = divmod(idx, self.size)
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.size and 0 <= nc < self.size:
                nidx = nr * self.size + nc
                if frozenset((idx, nidx)) not in self.walls:
                    yield nidx

    def solve(self) -> list[int] | None:
        if 1 not in self.checkpoints.values():
            return None
        start = next(idx for idx, order in self.checkpoints.items() if order == 1)

        visited = [False] * self.total
        path = [start]
        visited[start] = True

        def backtrack(idx: int, next_needed: int) -> bool:
            if idx in self.checkpoints:
                if self.checkpoints[idx] != next_needed:
                    return False
                next_needed += 1

            if len(path) == self.total:
                if self.must_end_at_last_checkpoint:
                    return next_needed - 1 == self.max_order
                return next_needed - 1 >= self.max_order

            for nidx in self._neighbors(idx):
                if visited[nidx]:
                    continue
                visited[nidx] = True
                path.append(nidx)
                if backtrack(nidx, next_needed):
                    return True
                path.pop()
                visited[nidx] = False
            return False

        return path if backtrack(start, 1) else None
