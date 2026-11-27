#!/usr/bin/env bash
# Render only the shots listed by reuse_shots.py (renders/<name>/_render_list.txt). Resumable.
#   bash tools/blender/hero/render_list.sh <name> <shots.py|micro.py>
set -u
NAME="$1"; ENGINE="${2:-shots.py}"
B="/c/Program Files/Blender Foundation/Blender 5.1/blender.exe"
ROOT="$(cd "$(dirname "$0")/../../.." && pwd -W)"
cd "$ROOT"                      # shots.py loads assets/3d by relative path
SPEC="$ROOT/research/hero/$NAME/spec.json"
OUT="$ROOT/../yt-studio-assets/renders/$NAME"
for i in $(cat "$OUT/_render_list.txt"); do
  "$B" -b --disable-autoexec --python "$ROOT/tools/blender/hero/$ENGINE" -- --spec "$SPEC" --shot $i --out "$OUT/s$i" 2>&1 | grep -E "rendered shot|Error|Traceback"
done
echo "LIST DONE $NAME"
