from typing import TYPE_CHECKING


if TYPE_CHECKING:
    import curses

class Window():
    def __init__(self, window: 'curses._CursesWindow', border: bool):
        self.window = window
        self.border = border

    def refresh(self):
        self.window.refresh()

    def clear(self):
        self.window.clear()

    def draw_border(self, ignore_property: bool = False):
        if not self.border and not ignore_property:
            return
        rows, cols = self.window.getmaxyx()
        for i in range(1, rows - 1):
            self.window.addstr(i, 0, "│")
            self.window.addstr(i, cols - 1, "│")
        self.window.addstr(0       , 1       , "─" * (cols - 2))
        self.window.addstr(rows - 1, 1       , "─" * (cols - 2))
        self.window.addstr(0       , 0       , "┌")
        self.window.addstr(0       , cols - 1, "┐")
        self.window.addstr(rows - 1, 0       , "└")
        self.window.insstr(rows - 1, cols - 1, "┘")