# pack each shot's PNG frames into a near-lossless mp4, delete the PNGs only when the frame count matches
R="/c/Users/Sitesh Kumar Dash/Projects/yt-studio-assets/renders/$1"
for d in "$R"/s*/; do
  s=$(basename "$d"); n=$(ls "$d"*.png 2>/dev/null | wc -l); [ "$n" -eq 0 ] && continue
  out="$R/$s.mp4"
  ffmpeg -y -loglevel error -threads 4 -framerate 30 -i "$d%05d.png" -c:v libx264 -preset slow -crf 10 -pix_fmt yuv420p "$out" || { echo "FAIL $s"; continue; }
  m=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 "$out")
  if [ "$m" = "$n" ]; then rm -rf "$d"; echo "$s $n frames packed"; else echo "MISMATCH $s png=$n mp4=$m (kept)"; fi
done
echo ARCHIVE_DONE
