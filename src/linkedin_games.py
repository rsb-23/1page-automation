#!/usr/bin/env python3
"""
Check completion status of LinkedIn daily games and solve any that
are unfinished. Board reading uses small DOM-inspection snippets
(unavoidable for getComputedStyle/SVG attributes); the actual solving
happens in pure-Python solver.py, and moves are applied via native
Playwright clicks/keypresses (not synthetic dispatchEvent).

Requires: pip install playwright
(No `playwright install chromium` needed — drives your existing Brave
install directly via core.CREDS.BRAVE_PATH.)

Credentials:
    Expects core.CREDS.BRAVE_PATH and core.CREDS.LI_AT to already be
    populated (li_at is the LinkedIn session cookie value). Adjust the
    two lines below if CREDS is dict-like instead of attribute-style.

Cron (daily at 20:00):
    0 20 * * * /path/to/venv/bin/python /path/to/check_and_solve.py >> /path/to/li_games.log 2>&1
"""

import json
import sys

from playwright._impl._api_structures import SetCookieParam
from playwright.sync_api import sync_playwright

from core import CREDS
from solver import MiniSudokuSolver, QueensSolver, TangoClue, TangoSolver, ZipSolver

BRAVE_PATH = CREDS["browser_path"]
LI_AT = CREDS["linkedin"]["li_at"]

GAMES = ("mini-sudoku", "queens", "tango", "zip")

# Setting these avoids first-run tutorial overlays that would otherwise
# sit on top of the board and break cell detection.
SKIP_TUTORIAL_KEYS = [
    "play:tutorial:crossclimbplay:tutorial:lotka",
    "play:tutorial:patches",
    "play:tutorial:pinpoint",
    "play:tutorial:queensv2",
    "play:tutorial:wendplay:tutorial:zip",
]

CLICK_DELAY_MS = 150


def get_target_frame(page, keyword: str):
    """Games render inside an iframe whose src contains the game
    keyword; fall back to the main frame if none is found."""
    for frame in page.frames:
        if keyword in (frame.url or ""):
            return frame
    return page.main_frame


def check_completion(frame, wait_ms: int = 2500) -> bool:
    """True if a 'See Result' span appears within wait_ms, else False."""
    try:
        frame.wait_for_selector("div.pr-top__headline:text-is('See you tomorrow!')", timeout=wait_ms)
        return True
    except Exception:
        return False


def cell_locator(frame, idx: int):
    return frame.locator(f'[data-cell-idx="{idx}"]')


def solve_queens(frame) -> tuple[bool, str]:
    raw_colors = frame.evaluate(
        """() => Array.from(document.querySelectorAll('[data-cell-idx]'))
            .sort((a,b) => +a.dataset.cellIdx - +b.dataset.cellIdx)
            .map(c => getComputedStyle(c).backgroundColor)"""
    )
    if not raw_colors:
        return False, "board not found"

    color_ids = {}
    colors = []
    for rgb in raw_colors:
        if rgb not in color_ids:
            color_ids[rgb] = len(color_ids)
        colors.append(color_ids[rgb])

    solution = QueensSolver(colors).solve()
    if solution is None:
        return False, "no solution found"

    for idx, is_queen in enumerate(solution):
        if not is_queen:
            continue
        cell = cell_locator(frame, idx)
        if cell.get_attribute("aria-label").startswith("Empty"):
            cell.click()
        frame.page.wait_for_timeout(CLICK_DELAY_MS)
        if cell.get_attribute("aria-label").startswith("Cross"):
            cell.click()  # second click: Empty -> X -> Queen
        frame.page.wait_for_timeout(CLICK_DELAY_MS)

    return True, ""


def solve_sudoku(frame) -> tuple[bool, str]:
    raw = frame.evaluate(
        """() => Array.from(document.querySelectorAll('[data-cell-idx]'))
            .sort((a,b) => +a.dataset.cellIdx - +b.dataset.cellIdx)
            .map(c => {
                const val = parseInt(c.querySelector('.sudoku-cell-content')?.textContent?.trim());
                return {
                    val: (val >= 1 && val <= 6) ? val : 0,
                    prefilled: c.classList.contains('sudoku-cell-prefilled'),
                };
            })"""
    )
    if not raw or len(raw) != 36:
        return False, f"expected 36 cells, got {len(raw) if raw else 0}"

    prefilled_vals = [c["val"] for c in raw]
    solution = MiniSudokuSolver(prefilled_vals).solve()
    if solution is None:
        return False, "no solution found"

    for idx, cell_info in enumerate(raw):
        if cell_info["prefilled"]:
            continue
        val = solution[idx]
        if not val:
            continue
        cell = cell_locator(frame, idx)
        cell.click()
        frame.page.wait_for_timeout(200)
        cell.press(str(val))
        frame.page.wait_for_timeout(300)

    return True, ""


def solve_tango(frame) -> tuple[bool, str]:
    data = frame.evaluate(
        """() => {
            const cells = Array.from(document.querySelectorAll('[data-cell-idx]'))
                .sort((a,b) => +a.dataset.cellIdx - +b.dataset.cellIdx);
            const size = Math.round(Math.sqrt(cells.length));

            const prePlaced = {};
            cells.forEach((cell, idx) => {
                const label = cell.querySelector('svg[aria-label]')?.getAttribute('aria-label');
                if (label === 'Sun' || label === 'Moon') {
                    prePlaced[idx] = label === 'Sun' ? 1 : 2;
                }
            });

            const isDownEdge = (edgeDiv) => {
                const style = edgeDiv.style;
                if (style.bottom === '0' || style.bottom === '0px') return true;
                if (style.right === '0' || style.right === '0px') return false;
                const computed = getComputedStyle(edgeDiv);
                if (computed.bottom === '0px') return true;
                if (computed.right === '0px') return false;
                return false;
            };

            const clues = [];
            cells.forEach(cell => {
                const idx1 = +cell.dataset.cellIdx;
                const r1 = Math.floor(idx1 / size), c1 = idx1 % size;
                cell.querySelectorAll('svg[aria-label="Equal"], svg[aria-label="Cross"]').forEach(svg => {
                    const type = svg.getAttribute('aria-label') === 'Equal' ? 'equal' : 'diff';
                    const edgeDiv = svg.closest('div');
                    const isDown = isDownEdge(edgeDiv);
                    if (isDown && r1 + 1 >= size) return;
                    if (!isDown && c1 + 1 >= size) return;
                    const idx2 = isDown ? idx1 + size : idx1 + 1;
                    clues.push({idx1, idx2, type});
                });
            });

            return {size, prePlaced, clues};
        }"""
    )
    if not data or not data.get("size"):
        return False, "board not found"

    size = data["size"]
    pre_placed = {int(k): v for k, v in data["prePlaced"].items()}
    clues = [TangoClue(c["idx1"], c["idx2"], c["type"]) for c in data["clues"]]

    solution = TangoSolver(size, pre_placed, clues).solve()
    if solution is None:
        return False, "no solution found"

    for idx, target in enumerate(solution):
        if idx in pre_placed:
            continue
        cell = cell_locator(frame, idx)
        cell.click()  # -> Sun
        frame.page.wait_for_timeout(CLICK_DELAY_MS)
        if target == 2:
            cell.click()  # -> Moon
            frame.page.wait_for_timeout(CLICK_DELAY_MS)

    return True, ""


def solve_zip(frame) -> tuple[bool, str]:
    data = frame.evaluate(
        r"""() => {
            const cells = Array.from(document.querySelectorAll('[data-cell-idx]'))
                .sort((a,b) => +a.dataset.cellIdx - +b.dataset.cellIdx);
            const size = Math.round(Math.sqrt(cells.length));

            const checkpoints = {};
            cells.forEach((cell, idx) => {
                const label = cell.getAttribute('aria-label') || '';
                const m = label.match(/Number\s+(\d+)/);
                if (m) checkpoints[idx] = parseInt(m[1]);
            });

            // UNVERIFIED: guessing at wall-edge markup, modeled on Tango's
            // edge-div pattern (bottom/right positioned divs between cells).
            const isDownEdge = (edgeDiv) => {
                const style = edgeDiv.style;
                if (style.bottom === '0' || style.bottom === '0px') return true;
                if (style.right === '0' || style.right === '0px') return false;
                const computed = getComputedStyle(edgeDiv);
                if (computed.bottom === '0px') return true;
                if (computed.right === '0px') return false;
                return false;
            };

            const walls = [];
            cells.forEach(cell => {
                const idx1 = +cell.dataset.cellIdx;
                const r1 = Math.floor(idx1 / size), c1 = idx1 % size;
                cell.querySelectorAll('.zip-wall, [data-wall="true"]').forEach(wallEl => {
                    const edgeDiv = wallEl.closest('div');
                    const isDown = isDownEdge(edgeDiv);
                    if (isDown && r1 + 1 >= size) return;
                    if (!isDown && c1 + 1 >= size) return;
                    const idx2 = isDown ? idx1 + size : idx1 + 1;
                    walls.push([idx1, idx2]);
                });
            });

            return {size, checkpoints, walls};
        }"""
    )
    # def solve_zip(frame) -> tuple[bool, str]:
    #     data = frame.evaluate(
    #         """() => {
    #             const cells = Array.from(document.querySelectorAll('[data-cell-idx]'))
    #                 .sort((a,b) => +a.dataset.cellIdx - +b.dataset.cellIdx);
    #             const size = Math.round(Math.sqrt(cells.length));
    #
    #             // UNVERIFIED: guessing at how a checkpoint number is exposed.
    #             // Adjust selector once you've inspected a live Zip board.
    #             const checkpoints = {};
    #             cells.forEach((cell, idx) => {
    #                 const raw = cell.querySelector('[data-checkpoint-order]')?.dataset.checkpointOrder
    #                     ?? cell.querySelector('.zip-cell-number, [class*="checkpoint"]')?.textContent?.trim();
    #                 const n = parseInt(raw);
    #                 if (!isNaN(n)) checkpoints[idx] = n;
    #             });
    #
    #             // UNVERIFIED: guessing at wall-edge markup, modeled on Tango's
    #             // edge-div pattern (bottom/right positioned divs between cells).
    #             const isDownEdge = (edgeDiv) => {
    #                 const style = edgeDiv.style;
    #                 if (style.bottom === '0' || style.bottom === '0px') return true;
    #                 if (style.right === '0' || style.right === '0px') return false;
    #                 const computed = getComputedStyle(edgeDiv);
    #                 if (computed.bottom === '0px') return true;
    #                 if (computed.right === '0px') return false;
    #                 return false;
    #             };
    #
    #             const walls = [];
    #             cells.forEach(cell => {
    #                 const idx1 = +cell.dataset.cellIdx;
    #                 const r1 = Math.floor(idx1 / size), c1 = idx1 % size;
    #                 cell.querySelectorAll('.zip-wall, [data-wall="true"]').forEach(wallEl => {
    #                     const edgeDiv = wallEl.closest('div');
    #                     const isDown = isDownEdge(edgeDiv);
    #                     if (isDown && r1 + 1 >= size) return;
    #                     if (!isDown && c1 + 1 >= size) return;
    #                     const idx2 = isDown ? idx1 + size : idx1 + 1;
    #                     walls.push([idx1, idx2]);
    #                 });
    #             });
    #
    #             return {size, checkpoints, walls};
    #         }"""
    #     )
    if not data or not data.get("size"):
        return False, "board not found"
    if not data["checkpoints"]:
        return False, "no checkpoints found — verify checkpoint selector"

    size = data["size"]
    checkpoints = {int(k): v for k, v in data["checkpoints"].items()}
    walls = [tuple(w) for w in data["walls"]]

    solution = ZipSolver(size, checkpoints, walls=walls).solve()
    if solution is None:
        return False, "no solution found"

    # Zip is drawn via drag, not discrete clicks: press on the first
    # cell, drag through every cell in path order, release on the last.
    boxes = []
    for idx in solution:
        box = cell_locator(frame, idx).bounding_box()
        if not box:
            return False, f"couldn't get bounding box for cell {idx}"
        boxes.append((box["x"] + box["width"] / 2, box["y"] + box["height"] / 2))

    page = frame.page
    page.mouse.move(*boxes[0])
    page.mouse.down()
    for x, y in boxes[1:]:
        page.mouse.move(x, y, steps=5)
        page.wait_for_timeout(30)
    page.mouse.up()

    return True, ""


SOLVERS = {"queens": solve_queens, "tango": solve_tango, "mini-sudoku": solve_sudoku, "zip": solve_zip}
cookie: SetCookieParam = {
    "name": "li_at",
    "value": LI_AT,
    "domain": ".linkedin.com",
    "path": "/",
    "httpOnly": True,
    "secure": True,
}


def main():
    results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=BRAVE_PATH, headless=False, args=["--disable-brave-update"])
        context = browser.new_context()
        context.add_cookies([cookie])
        context.add_init_script(
            "(() => { const keys = %s; keys.forEach(k => localStorage.setItem(k, 'true')); })();"
            % json.dumps(SKIP_TUTORIAL_KEYS)
        )
        page = context.new_page()

        for game_key in GAMES:
            url = f"https://www.linkedin.com/games/{game_key}/results"
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                try:
                    page.wait_for_selector(f'iframe[src*="{game_key}"]', timeout=10000)
                except Exception:
                    pass

                if page.url.endswith("results/"):
                    results[game_key] = "already completed"
                    continue

                frame = get_target_frame(page, game_key)
                frame.wait_for_selector("[data-cell-idx]", timeout=15000)

                ok, err = SOLVERS[game_key](frame)
                if not ok:
                    results[game_key] = f"solve failed: {err}"
                    continue

                status_after = check_completion(frame, wait_ms=8000)
                results[game_key] = "solved" if status_after else "solve ran but not detected as complete"

            except Exception as e:
                results[game_key] = f"error: {e}"
                print(results[game_key])
                # raise Exception from e

        browser.close()

    print(json.dumps(results, indent=2))
    if any("error" in v or "failed" in v for v in results.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
