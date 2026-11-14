#!/usr/bin/env bash
# Boltsmith Linux launcher
cd "$(dirname "$(readlink -f "$0")")"
export PATH="$HOME/.local/bin:$PATH"
if ! command -v uv >/dev/null 2>&1; then
  command -v notify-send >/dev/null && notify-send "Boltsmith" "First start: installing uv and the CAD kernel…"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
exec uv run --python 3.12 --with build123d==0.13.0 --with bd_warehouse==0.4.0 python fastener_gui.py "$@"
