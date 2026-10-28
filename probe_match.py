import json, urllib.request

PID = "e0fea518-3b2c-4bfd-9ed5-beb730cd335f"  # theunc666
UA = {"User-Agent": "Mozilla/5.0"}

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)

# 1) letzte Matches des Spielers (unofficial, wie faceit.com-Profilseite)
hist = get(f"https://api.faceit.com/match-history/v1/players/{PID}?game=cs2&limit=3")
items = hist.get("payload", {}).get("matches", []) or []
print("history keys:", list(items[0].keys()) if items else "none")
print(json.dumps(items[0], indent=1)[:800] if items else "")

if items:
    mid = items[0].get("matchId") or items[0].get("match_id")
    # 2) ein echtes Match mit vollem Scoreboard
    m = get(f"https://api.faceit.com/api/match/v1/match/{mid}")
    data = m.get("payload", {})
    with open("/home/ubuntu/faceit-weekend/sample_match.json", "w") as f:
        json.dump(data, f, indent=1)
    print("\nsample_match.json bytes:", len(json.dumps(data)))
    # top-level Struktur zeigen
    print("match keys:", list(data.keys())[:20])
    rounds = data.get("rounds") or []
    if rounds:
        r0 = rounds[0]
        print("round keys:", list(r0.keys()))
        teams = r0.get("teams") or []
        if teams:
            t0 = teams[0]
            print("team keys:", list(t0.keys()))
            roster = t0.get("players") or t0.get("roster") or []
            if roster:
                print("player keys:", list(roster[0].keys()))
                ps = roster[0].get("stats") or roster[0].get("player_stats") or {}
                print("stats keys:", list(ps.keys()))
                print("stats sample:", json.dumps(ps, indent=1)[:1200])
