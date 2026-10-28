import json, urllib.request, urllib.parse

nick = "theunc666"
candidates = [
    "https://api.faceit.com/api/users/v1/nicknames/",
    "https://api.faceit.com/api/v2/players/nicknames/",
    "https://api.faceit.com/users/v1/nicknames/",
]
for base in candidates:
    url = base + urllib.parse.quote(nick)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read().decode("utf-8", "replace")
        print("OK:", base, "->", body[:400])
    except Exception as e:
        print("FAIL:", base, repr(e))
