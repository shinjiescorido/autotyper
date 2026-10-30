# Auto Typer

An auto typer and mouse mover for testing activity tracking. It types randomly generated code into the focused window one character at a time, and it moves the mouse about an inch in a random direction at a set interval.

- **Text types:** `js` writes one random Next.js client component per round. `css` writes a set number of lines of random CSS rules per round.
- After each round it clears the editor (Ctrl+A, Backspace) and starts again.
- **DEL** starts and pauses typing from anywhere, as long as the typer has been started.

## Requirements

### Linux (Ubuntu 24.04+ / Debian)

You need an X11 session; pynput can't send keystrokes or mouse moves under Wayland. At the login screen, choose "Ubuntu on Xorg".

| To | Install |
| --- | --- |
| Run the `.deb` | Nothing extra. `sudo apt install ./autotyper_1.0.0_all.deb` pulls in everything. |
| Run from source with system packages | `sudo apt install python3 python3-pyqt6 python3-pynput python3-xlib libxcb-cursor0` |
| Run from source in a venv | `sudo apt install python3 python3-venv libxcb-cursor0`, then follow [Development setup](#development-setup-linux) |
| Build the `.deb` | `dpkg-deb`, which comes with every Ubuntu/Debian system |

### Windows (10/11, 64-bit)

| To | Install |
| --- | --- |
| Run `AutoTyperSetup.exe` or `AutoTyper.exe` | Nothing. Python and Qt are bundled. |
| Run from source | [Python 3](https://www.python.org/downloads/) (tick "Add python.exe to PATH"), then `pip install pynput PySide6` |
| Build the exe and installer | Python 3, plus [Inno Setup 6.3+](https://jrsoftware.org/isdl.php) (`winget install JRSoftware.InnoSetup`) for the installer. `build_windows.bat` installs pynput, PySide6 and PyInstaller into `.venv-win` itself. |

## Usage

### GUI

```bash
python3 autotyper_gui.py
```

1. Click **Start** to turn the typer on.
2. Focus a text editor and press **DEL** to start typing. Press **DEL** again to pause.
3. Click **Stop** to turn it off. DEL is then ignored, and the round and stats reset. Your editor isn't cleared, and the next run begins a fresh round on a new line.

Settings can only be changed while the typer is stopped:

| Setting | Default | Notes |
| --- | --- | --- |
| Text type | `js` | `js` or `css` |
| Delay per character | 0.3 s | |
| Mouse move every | 5 s | |
| Mouse move distance | 96 px | About 1 inch at 96 DPI |
| CSS lines per round | 800 | CSS only |
| Editor auto-indents | on | Leave on for VS Code or Sublime. Turn off for editors that don't indent for you. |

### Terminal only

```bash
python3 autotyper.py
```

It starts paused. Focus an editor and press **DEL** to start or pause typing. Press **Ctrl+C** in the terminal to quit. Settings are in `cfg` at the top of `autotyper.py`.

## Development setup (Linux)

```bash
python3 -m venv .venv
.venv/bin/pip install --no-deps -r requirements.txt   # skips evdev, which isn't needed on X11
.venv/bin/pip install PySide6
.venv/bin/python autotyper_gui.py
```

It needs an X11 session; pynput can't send input under Wayland. If Qt complains about `libxcb-cursor`, install `libxcb-cursor0`. Without sudo, you can instead unpack the library into `.libs/`:

```bash
apt download libxcb-cursor0 && dpkg-deb -x libxcb-cursor0_*.deb tmp && mkdir -p .libs && cp tmp/usr/lib/x86_64-linux-gnu/libxcb-cursor.so.0* .libs/
```

## Building

### Ubuntu / Debian package

```bash
./build_deb.sh
sudo apt install ./dist/autotyper_1.0.0_all.deb
```

This installs an `autotyper` command and an "Auto Typer" menu entry. Dependencies come from apt (`python3-pyqt6`, `python3-pynput`, `python3-xlib`, `libxcb-cursor0`). Uninstall it with `sudo apt remove autotyper`.

### Windows

Run `build_windows.bat` on Windows; it can't be cross-built from Linux. It needs Python 3 and, for the installer, Inno Setup 6.3+ (`winget install JRSoftware.InnoSetup`). It produces:

- `dist\AutoTyperSetup.exe`: an installer with a Start Menu entry, an optional desktop icon and an uninstaller
- `dist\AutoTyper.exe`: a portable single file that runs without installing
