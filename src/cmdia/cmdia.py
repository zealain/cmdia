#!/usr/bin/python3

import curses

from cmdia.config import load_config
from cmdia.db import DB
from cmdia.screen import ScreenController


def curses_main(stdscr: curses.window) -> None:
    # Setup
    config = load_config()
    db = DB()

    controller = ScreenController(stdscr, config, db)

    # Event loop
    while controller.process_key(stdscr.getch()):
        pass


def main():
    # Make sure curses gets destroyed no matter how main() ends
    curses.wrapper(curses_main)

if __name__ == '__main__':
    main()
