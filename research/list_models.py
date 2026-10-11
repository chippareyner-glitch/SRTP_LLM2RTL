"""List model IDs available to the configured DeepSeek key (free endpoint; never prints the key)."""
import json
import urllib.error
import urllib.request
from pathlib import Path

env = {}
for line in (Path(__file__).resolve().parents[1] / ".env").read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.lstrip().startswith("#"):
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
req = urllib.request.Request("https://api.deepseek.com/models",
                             headers={"Authorization": "Bearer " + env["DEEPSEEK_API_KEY"]})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print([m.get("id") for m in json.load(r).get("data", [])])
except urllib.error.HTTPError as e:
    print("HTTP", e.code)
print("configured DEEPSEEK_MODEL =", env.get("DEEPSEEK_MODEL"))
