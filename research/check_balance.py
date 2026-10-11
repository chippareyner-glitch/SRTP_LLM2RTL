"""Query the DeepSeek account balance (free endpoint; never prints the key)."""
import json
import urllib.error
import urllib.request
from pathlib import Path

env = {}
for line in (Path(__file__).resolve().parents[1] / ".env").read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.lstrip().startswith("#"):
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
req = urllib.request.Request("https://api.deepseek.com/user/balance",
                             headers={"Authorization": "Bearer " + env["DEEPSEEK_API_KEY"]})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print(json.dumps(json.load(r), ensure_ascii=False))
except urllib.error.HTTPError as e:
    print("HTTP", e.code)
