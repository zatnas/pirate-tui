import curses
from typing import overload

class Window():
    def __init__(
        self,
        size_y: int,
        size_x: int,
        pos_x: int = 0,
        pos_y: int = 0,
        border: bool = False,
    ):
        self.border = border
        if border:
            self.border_window = curses.newwin(size_y, size_x, pos_x, pos_y)
            self.window = curses.newwin(size_y - 2, size_x - 2, pos_x + 1, pos_y + 1)
        else:
            self.window = curses.newwin(size_y, size_x, pos_x, pos_y)
        (self.sy, self.sx) = self.window.getmaxyx()
        # self.window = curses.newwin(size_y, size_x, pos_x, pos_y)

    def refresh(self):
        if self.border:
            self.border_window.refresh()
        self.window.refresh()

    def clear(self):
        if self.border:
            self.border_window.erase()
        self.window.erase()

    def draw_border(self, ignore_property: bool = False):
        if not self.border and not ignore_property:
            return
        rows, cols = self.border_window.getmaxyx()
        for i in range(1, rows - 1):
            self.border_window.addstr(i, 0, "│")
            self.border_window.addstr(i, cols - 1, "│")
        self.border_window.addstr(0       , 1       , "─" * (cols - 2))
        self.border_window.addstr(rows - 1, 1       , "─" * (cols - 2))
        self.border_window.addstr(0       , 0       , "┌")
        self.border_window.addstr(0       , cols - 1, "┐")
        self.border_window.addstr(rows - 1, 0       , "└")
        self.border_window.insstr(rows - 1, cols - 1, "┘")

    @overload
    def addstr(self, text: str, attr: int) -> None:
        self.window.addstr(text, attr)

    @overload
    def addstr(self, y:int, x:int, text: str, attr: int) -> None:
        self.window.addstr(y, x, text, attr)

    def addstr(self, *args, **kwargs) -> None:
        self.window.addstr(*args, **kwargs)
