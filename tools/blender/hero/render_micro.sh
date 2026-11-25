#!/usr/bin/env bash
# Render every shot of a micro-world spec, one after another (resumable: existing frames are skipped).
#   bash tools/blender/hero/render_micro.sh <name>
set -u
NAME="$1"
B="/c/Program Files/Blender Foundation/Blender 5.1/blender.exe"
ROOT="$(cd "$(dirname "$0")/../../.." && pwd -W)"
SPEC="$ROOT/research/hero/$NAME/spec.json"
OUT="$ROOT/../yt-studio-assets/renders/$NAME"
K=$(python -c "import json;print(len(json.load(open(r'$SPEC'))['shots']))")
for ((i=0; i<K; i++)); do
  "$B" -b --disable-autoexec --python "$ROOT/tools/blender/hero/micro.py" -- --spec "$SPEC" --shot $i --out "$OUT/s$i" 2>&1 | grep -E "rendered shot|Error|Traceback"
done
echo "ALL SHOTS DONE $NAME"
