# `cmdia` - Command Line Media Browser

`cmdia` is a dead simple CLI media browser for local video files. It is designed for the following situation:
* You have very limited input methods (no mouse and no full keyboard, only for example a TV remote)
* All of your files are organized in directories
* You don't need any features (nice UI, search, metadata, images, online connectivity, none of all that)

What it actually does:
* Navigate files with `Up`/`Down` arrows
* Play video files with `Enter` (`mpv` by default)
* Remembers where you left off and what you already watched

## Installation
Works on Linux, maybe works on macOS, probably doesn't work on Windows. Needs `python3`.

```
$ pip install cmdia
```

## Usage
```
$ cmdia
```

* `Up`/`Down` arrows: Navigation
* `Enter`: Enter directory or play file
* `Esc`: Go to parent directory
* `q`: Quit

To change the media player used (default `mpv`), edit the following file (gets created on first startup):
```
$ ~/.config/cmdia/config.yaml
```
The `media_player` section is a list of the media player command and its arguments. For example:
```yaml
media_player:
- "vlc"
- "--fullscreen"
- "--loop"
```
