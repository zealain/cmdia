import pathlib
from typing import List
import natsort
import abc

from cmdia.config import Config
from cmdia.db import DB


class Entry(abc.ABC):
    @property
    @abc.abstractmethod
    def path(self) -> pathlib.Path:
        pass

    @property
    @abc.abstractmethod
    def display_name(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def watched(self) -> bool:
        pass

    @watched.setter
    @abc.abstractmethod
    def watched(self, value) -> bool:
        pass

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entry):
            return False

        return self.path == other.path

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Entry):
            return False

        return self.path < other.path

    def __str__(self):
        return str(self.path)


class BackButton(Entry):
    def __init__(self, parent: pathlib.Path):
        self._parent = parent

    @property
    def path(self) -> pathlib.Path:
        return self._parent

    @property
    def display_name(self) -> str:
        return '< Back'

    @property
    def watched(self):
        return False

    @watched.setter
    def watched(self, value) -> bool:
        raise NotImplementedError()


# For files that are not connected to the DB
class FileUntracked(Entry):
    def __init__(self, path: pathlib.Path):
        self._path = path

    @property
    def path(self) -> pathlib.Path:
        return self._path

    @property
    def display_name(self) -> str:
        return self.path.name

    @property
    def watched(self):
        return False

    @watched.setter
    def watched(self, value) -> bool:
        raise NotImplementedError()


class File(Entry):
    def __init__(self, path: pathlib.Path, config: Config, db: DB):
        self._path = path
        self._config = config
        self._db = db

        # Check if the file has been watched before
        is_watched = self._db.query('''
            SELECT EXISTS(
                SELECT 1
                FROM watched
                WHERE path = ?
            );
           ''', (str(self._path),))
        self._watched = is_watched is not None and is_watched[0] == 1

        self._update_display_name()

    @property
    def path(self) -> pathlib.Path:
        return self._path

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def watched(self):
        return self._watched

    @watched.setter
    def watched(self, value: bool):
        self._watched = value
        if value:
            self._db.query('''
                INSERT INTO watched
                    (path)
                VALUES
                    (?)
                ON CONFLICT DO NOTHING;
            ''', (str(self._path),))
        else:
            self._db.query('DELETE FROM watched WHERE path = ?;', (str(self._path),))
        self._update_display_name()

    def _update_display_name(self):
        # Mark the filename so that we don't only rely on color
        if self._watched:
            self._display_name = f'{self._config.watched_marker} {self._path.name}'
        else:
            self._display_name = self._path.name


class Directory(Entry):
    video_extensions = ['.webm', '.mkv', '.flv', '.vob', '.ogv', '.ogg', '.rrc', '.gifv', '.mng','.mov',
                        '.avi', '.qt', '.wmv', '.yuv', '.rm', '.asf', '.amv', '.mp4', '.m4p', '.m4v',
                        '.mpg', '.mp2', '.mpeg', '.mpe', '.mpv', '.m4v', '.svi', '.3gp', '.3g2', '.mxf',
                        '.roq', '.nsv', '.flv', '.f4v', '.f4p', '.f4a', '.f4b', '.mod']

    def __init__(self, path: pathlib.Path, config: Config, db: DB):
        self._path = path

        filtered = []
        for file in self._path.iterdir():
            if file.is_dir():
                # Show directories
                filtered.append(File(file, config, db))
            elif file.suffix in self.video_extensions:
                # Show video files
                filtered.append(File(file, config, db))

        # Make sure they are sorted naturally
        self._files: List[Entry] = natsort.natsorted(filtered, alg=natsort.ns.IGNORECASE)

        # Add back button
        self._files = [BackButton(self._path)] + self._files

    @property
    def path(self) -> pathlib.Path:
        return self._path

    @property
    def display_name(self) -> str:
        return self._path.name

    @property
    def watched(self) -> bool:
        return False

    @watched.setter
    def watched(self, value) -> bool:
        raise NotImplementedError()

    @property
    def files(self) -> List[Entry]:
        return self._files
