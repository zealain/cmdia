import pathlib
import subprocess
import curses
import curses.ascii
from typing import List

from cmdia.config import Config
from cmdia.db import DB
from cmdia.files import Directory, Entry, BackButton, FileUntracked


# Padding around the view so that the text isn't flush to the window border
PAD_X = 2
PAD_Y = 1


class Screen:
    _max_x: int
    _max_y: int
    _max_lines: int

    def __init__(self, stdscr: curses.window, config: Config):
        self.stdscr = stdscr
        self.watched_marker = config.watched_marker

        # Curses config
        curses.set_escdelay(25)
        curses.curs_set(0)

        # Static limits
        self.min_x = PAD_X
        self.min_y = PAD_Y + 2 # One line for the title, one line space

        # Initialize color for watched entries
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)

        # Get the initial window size
        self.update_geometry()

    @property
    def max_lines(self) -> int:
        return self._max_lines

    def update_geometry(self):
        self._max_y, self._max_x = self.stdscr.getmaxyx()
        self._max_x -= PAD_X
        self._max_y -= PAD_Y
        self._max_lines = self._max_y - self.min_y

    def draw(self, title: str, entries: List[Entry], cursor: int) -> None:
        # Clear screen because we will redraw it
        self.stdscr.erase()

        # The size might have changed
        self.update_geometry()

        # Print header
        self.stdscr.addstr(PAD_Y, PAD_X, title, curses.A_BOLD)

        # Setup
        i = 0
        max_line_len = self._max_x - 2 * PAD_X

        # List files
        for entry in entries:
            display_name = entry.display_name

            # Truncate long lines
            if len(display_name) > max_line_len:
                display_name = display_name[:max_line_len]

            # Highlight the selected row
            flags = 0
            if i == cursor:
                flags = curses.A_BOLD | curses.A_UNDERLINE

            # Color watched entries
            if entry.watched:
                flags |= curses.color_pair(1)

            # Print the row
            self.stdscr.addstr(self.min_y + i, PAD_X, display_name, flags)
            i += 1


class ScreenView:
    def __init__(self, stdscr: curses.window, config: Config, db: DB):
        self._config = config
        self._db = db
        self._screen = Screen(stdscr, config)

        # Default start location
        startup_dir = pathlib.Path('/')
        startup_file: Entry = BackButton(startup_dir)

        # Get state from when we last closed the application
        startup_state = self._db.query('SELECT selected_entry, directory FROM startup WHERE id = 0')
        if startup_state is not None:
            startup_file = FileUntracked(pathlib.Path(startup_state[0]))
            startup_dir = pathlib.Path(startup_state[1])

        self._directory = Directory(startup_dir, config, db)

        # Select the entry we had selected the last time we opened the program
        try:
            self._cursor = self._directory.files.index(startup_file)
        except ValueError:
            self._cursor = 0

        self._top_item = int(max(0, min(self._cursor - self._screen.max_lines / 2, self.file_count - self._screen.max_lines)))
        self.update()

    @property
    def file_count(self):
        return len(self._directory.files)

    @property
    def selected_entry(self) -> Entry:
        return self._directory.files[self._cursor]

    def save_state(self) -> None:
        self._db.query('''
            INSERT INTO startup (id, selected_entry, directory)
                VALUES (0, ?, ?)
            ON CONFLICT DO UPDATE SET
                selected_entry = excluded.selected_entry,
                directory = excluded.directory;
        ''', (str(self.selected_entry), str(self._directory.path)))

    def update(self) -> None:
        lines = self._directory.files[self._top_item:self._top_item + self._screen.max_lines]
        self._screen.draw(str(self._directory.path), lines, self._cursor - self._top_item)

    def select_entry(self) -> None:
        if self._cursor == 0:
            self.go_to_parent()
        elif self.selected_entry.path.is_dir():
            self.update_directory(self.selected_entry.path)
        else:
            subprocess.run(self._config.media_player + [str(self.selected_entry)],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
            self.selected_entry.watched = True
            self.update()

    def go_to_parent(self) -> None:
        self.update_directory(self._directory.path.parent)

    def update_directory(self, path: pathlib.Path) -> None:
        self._directory = Directory(path, self._config, self._db)
        self._cursor = 0
        self._top_item = 0
        self.save_state()
        self.update()

    def up(self) -> None:
        if self._cursor == 0:
            self._cursor = self.file_count - 1
            self._top_item = max(0, self.file_count - self._screen.max_lines)
        else:
            self._cursor -= 1
            self._top_item = min(self._top_item, self._cursor)
        self.update()

    def down(self) -> None:
        if self._cursor == self.file_count - 1:
            self._cursor = 0
            self._top_item = 0
        else:
            self._cursor += 1
            self._top_item = max(self._top_item, self._cursor - self._screen.max_lines + 1)
        self.update()


class ScreenController:
    def __init__(self, stdscr: curses.window, config: Config, db: DB):
        self._view = ScreenView(stdscr, config, db)

    def process_key(self, key):
        # Quit
        if key == ord('q'):
            self._view.save_state()
            return False
        # Go one entry up in the list
        elif key == curses.KEY_UP:
            self._view.up()
        # Go one entry down in the list
        elif key == curses.KEY_DOWN:
            self._view.down()
        # Go to parent folder
        elif key == curses.ascii.ESC:
            self._view.go_to_parent()
        # Select an entry
        elif key == curses.ascii.LF:
            self._view.select_entry()

        # Don't quit yet
        return True
