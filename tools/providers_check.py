"""Does each free key work? (20 Nov 2026) One tiny request per provider; prints only OK / FAIL and
the model that answered, never a key. Saves research/providers_check.txt."""
import os
import subprocess
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
lines = []


def say(s):
    print(s, flush=True)
    lines.append(s)


def k(n):
    return (os.getenv(n) or "").strip()


say("Secrets present: " + ", ".join(n for n in ["GEMINI_API_KEY", "GROQ_API_KEY", "OPENROUTER_API_KEY", "MISTRAL_API_KEY",
                                                 "CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN", "KAGGLE_USERNAME",
                                                 "KAGGLE_API_TOKEN", "KAGGLE_KEY"] if k(n)))

# Groq, OpenRouter, Mistral through the same code the videos use
from agents import free_llm  # noqa: E402
for p in free_llm.PROVIDERS:
    name, kname = p[0], p[1]
    if not k(kname):
        say(f"{name}: no key (skipped)")
        continue
    saved = free_llm.PROVIDERS[:]
    free_llm.PROVIDERS[:] = [p]
    try:
        out = free_llm.ask_json('Return {"ok": true, "capital_of_france": "..."} with the real capital.')
        live = free_llm._LIVE.get(name) or []
        say(f"{name}: {'OK ' + str(out) if out else 'FAIL (no answer)'}; {len(live)} models offered"
            + (" (free ones only)" if name == "openrouter" else ""))
    except Exception as e:
        say(f"{name}: FAIL {type(e).__name__}: {str(e)[:120]}")
    free_llm.PROVIDERS[:] = saved

# Cloudflare Workers AI: a small free text model
if k("CLOUDFLARE_ACCOUNT_ID") and k("CLOUDFLARE_API_TOKEN"):
    try:
        r = requests.post(f"https://api.cloudflare.com/client/v4/accounts/{k('CLOUDFLARE_ACCOUNT_ID')}/ai/run/@cf/meta/llama-3.1-8b-instruct",
                          headers={"Authorization": f"Bearer {k('CLOUDFLARE_API_TOKEN')}"},
                          json={"messages": [{"role": "user", "content": "Say OK in one word."}]}, timeout=60)
        j = r.json()
        say(f"cloudflare: {'OK ' + str(j.get('result', {}).get('response', ''))[:40] if j.get('success') else 'FAIL ' + str(j.get('errors'))[:160]}")
    except Exception as e:
        say(f"cloudflare: FAIL {type(e).__name__}: {str(e)[:120]}")
else:
    say("cloudflare: missing account ID or token")

# Kaggle: the official CLI, with the new-style token (or the legacy username + key)
if k("KAGGLE_API_TOKEN") or k("KAGGLE_KEY"):
    env = dict(os.environ)
    if not k("KAGGLE_API_TOKEN") and k("KAGGLE_KEY"):
        env["KAGGLE_API_TOKEN"] = k("KAGGLE_KEY") if k("KAGGLE_KEY").startswith("KGAT_") else ""
    try:
        r = subprocess.run(["kaggle", "kernels", "list", "--mine", "--page-size", "1"], capture_output=True, text=True,
                           env=env, timeout=90)
        ok = r.returncode == 0
        msg = (r.stdout if ok else r.stderr or r.stdout).strip().splitlines()
        say(f"kaggle: {'OK (signed in)' if ok else 'FAIL ' + (msg[-1] if msg else '')[:160]}")
    except Exception as e:
        say(f"kaggle: FAIL {type(e).__name__}: {str(e)[:120]}")
else:
    say("kaggle: no token")

(ROOT / "research/providers_check.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
