import json, urllib.request, urllib.parse

NICKS = ["theunc666", "amaseling", "-neon666", "kokolorez", "Shpooople"]

out = {}
for nick in NICKS:
    url = "https://api.faceit.com/users/v1/nicknames/" + urllib.parse.quote(nick)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            d = json.load(r)
        p = d.get("payload") or {}
        games = p.get("games") or {}
        cs2 = games.get("cs2") or {}
        out[nick] = {
            "nickname": p.get("nickname"),
            "player_id": p.get("id"),
            "elo": cs2.get("faceit_elo"),
            "level": cs2.get("skill_level"),
            "country": p.get("country"),
            "avatar": p.get("avatar"),
        }
    except Exception as e:
        out[nick] = {"error": repr(e)}

with open("/home/ubuntu/faceit-weekend/players.json", "w") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
print(json.dumps(out, indent=2, ensure_ascii=False))
