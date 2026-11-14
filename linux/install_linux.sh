#!/usr/bin/env bash
# Adds Boltsmith to the application menu (and Desktop) with its icon,
# and downloads the CAD kernel once so the first start is fast.
set -e
DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
chmod +x "$DIR/boltsmith.sh"
export PATH="$HOME/.local/bin:$PATH"
if ! command -v uv >/dev/null 2>&1; then
  echo "Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
echo "Downloading the CAD kernel (once, a few minutes)..."
uv run --python 3.12 --with build123d==0.13.0 --with bd_warehouse==0.4.0 python -c "import build123d, bd_warehouse, tkinter; print('CAD kernel ready')"
APPS="$HOME/.local/share/applications"
mkdir -p "$APPS"
cat > "$APPS/boltsmith.desktop" <<EOT
[Desktop Entry]
Type=Application
Name=Boltsmith
Comment=Fastener generator -> STEP (real threads)
Exec="$DIR/boltsmith.sh"
Icon=$DIR/boltsmith.png
Terminal=false
Categories=Graphics;Engineering;
EOT
chmod +x "$APPS/boltsmith.desktop"
DESK="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
if [ -d "$DESK" ]; then
  cp "$APPS/boltsmith.desktop" "$DESK/"
  chmod +x "$DESK/boltsmith.desktop"
  command -v gio >/dev/null && gio set "$DESK/boltsmith.desktop" metadata::trusted true 2>/dev/null || true
fi
command -v update-desktop-database >/dev/null && update-desktop-database "$APPS" 2>/dev/null || true
echo "Done: Boltsmith is in the application menu (and on the Desktop)."
