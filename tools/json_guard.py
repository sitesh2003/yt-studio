"""Run right after a workflow's `git pull --rebase` and before `git push` (20 Nov 2026).

A line-by-line merge of two edits to the same JSON file can produce text that is no longer JSON: on 19 Nov
history.json and bank.json were stitched together this way and the main daily run failed three times.
For every data file that no longer parses, put back the copy this run itself committed (ORIG_HEAD, the
run's own commit before the rebase), or failing that the last parseable copy, and amend the commit.
Never pushes a broken file. Prints what it fixed."""
import glob
import json
import subprocess
import sys


def ok(text):
    try:
        json.loads(text)
        return True
    except Exception:
        return False


def git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True, encoding="utf-8")


fixed = []
for f in sorted(glob.glob("data/*.json") + glob.glob("data/*/*.json")):
    if ok(open(f, encoding="utf-8").read()):
        continue
    for ref in ("ORIG_HEAD", "HEAD~1", "HEAD~2", "@{u}"):
        r = git("show", f"{ref}:{f}")
        if r.returncode == 0 and ok(r.stdout):
            open(f, "w", encoding="utf-8").write(r.stdout)
            fixed.append(f"{f} <- {ref}")
            break
    else:
        print(f"json_guard: {f} is broken and no good copy was found", flush=True)
        sys.exit(1)
# 21 Nov 2026: a long run saves the WHOLE history file it loaded an hour earlier, and the merge keeps its
# copy, so entries another run (or the laptop) added meanwhile were lost - two uploaded videos vanished from
# the records. Put back any entry the remote has that this copy lost (matched by job + video id).
for f in sorted(glob.glob("data/history.json") + glob.glob("data/*/history.json")):
    r = git("show", f"@{{u}}:{f}")
    if r.returncode != 0 or not ok(r.stdout):
        continue
    cur = json.loads(open(f, encoding="utf-8").read())
    have = {(h.get("job"), h.get("video_id")) for h in cur}
    lost = [h for h in json.loads(r.stdout) if (h.get("job"), h.get("video_id")) not in have
            and (h.get("video_id") or h.get("job", "").startswith("hero_"))]
    if lost:
        cur += lost
        open(f, "w", encoding="utf-8").write(json.dumps(cur, indent=2, ensure_ascii=False))
        fixed.append(f"{f} <- {len(lost)} entries kept from the remote")
if fixed:
    git("add", "-f", *[x.split(" <- ")[0] for x in fixed])
    git("commit", "--amend", "--no-edit", "-q")
    print("json_guard: repaired after merge: " + "; ".join(fixed), flush=True)
else:
    print("json_guard: all data files are valid JSON", flush=True)
