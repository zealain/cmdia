import sys
import pathlib
import sqlite3
from typing import Any


class DB:
    def __init__(self):
        db_file = pathlib.Path(pathlib.Path.home(), '.local', 'share', '', 'state.db')
        db_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            self.db = sqlite3.connect(db_file, autocommit=True).cursor()
        except sqlite3.OperationalError as e:
            print('Failed to open watch status database', file=sys.stderr)
            print(e, file=sys.stderr)
            sys.exit(1)

        self.init_tables()

    def init_tables(self):
        self.db.execute('CREATE TABLE IF NOT EXISTS watched (path TEXT PRIMARY KEY);')
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS startup (
                id INT PRIMARY KEY,
                selected_entry TEXT NOT NULL,
                directory TEXT NOT NULL
            );
        ''')

    def query(self, q: str, variables: tuple[Any, ...] = ()) -> Any:
        return self.db.execute(q, variables).fetchone()
