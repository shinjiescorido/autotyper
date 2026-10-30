#!/usr/bin/env bash
# Builds dist/autotyper_<version>_all.deb for Ubuntu 24.04+ (no sudo needed to build).
# Install it with:   sudo apt install ./dist/autotyper_<version>_all.deb
# Uninstall with:    sudo apt remove autotyper
#
# The package holds only the two .py files, a launcher and a menu entry; Qt and
# pynput come from Ubuntu's own packages (python3-pyqt6, python3-pynput), which
# apt pulls in. PySide6 isn't in Ubuntu's archive; the GUI falls back to PyQt6.
set -euo pipefail
cd "$(dirname "$0")"

VERSION=1.0.0
PKG=autotyper
STAGE=build/deb/${PKG}_${VERSION}_all
OUT=dist/${PKG}_${VERSION}_all.deb

rm -rf "$STAGE"
install -d "$STAGE/DEBIAN" "$STAGE/usr/lib/$PKG" "$STAGE/usr/bin" "$STAGE/usr/share/applications"

install -m 644 autotyper.py autotyper_gui.py "$STAGE/usr/lib/$PKG/"

cat > "$STAGE/usr/bin/$PKG" <<'EOF'
#!/bin/sh
exec /usr/bin/python3 /usr/lib/autotyper/autotyper_gui.py "$@"
EOF
chmod 755 "$STAGE/usr/bin/$PKG"

cat > "$STAGE/usr/share/applications/$PKG.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Auto Typer
Comment=Auto typer + mouse mover
Exec=autotyper
Icon=input-keyboard
Terminal=false
Categories=Utility;
StartupWMClass=autotyper
EOF
chmod 644 "$STAGE/usr/share/applications/$PKG.desktop"

cat > "$STAGE/DEBIAN/control" <<EOF
Package: $PKG
Version: $VERSION
Architecture: all
Maintainer: Shinji Escorido <shinji.escorido@gmail.com>
Depends: python3 (>= 3.10), python3-pyqt6, python3-pynput, python3-xlib, libxcb-cursor0
Section: utils
Priority: optional
Installed-Size: $(du -sk "$STAGE/usr" | cut -f1)
Description: Auto typer + mouse mover (Qt GUI)
 Types random code into the focused window and moves the mouse periodically.
 Start/Stop in the window turn it on and off; while started, DEL starts and
 pauses typing.
EOF

mkdir -p dist
dpkg-deb --root-owner-group --build "$STAGE" "$OUT"
echo "Built $OUT"
echo "Install: sudo apt install ./$OUT"
