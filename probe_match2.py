import json, urllib.request

PID = "e0fea518-3b2c-4bfd-9ed5-beb730cd335f"  # theunc666
UA = {"User-Agent": "Mozilla/5.0"}

def try_get(url, label):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read().decode("utf-8", "replace")
        print(f"OK   {label}: {len(body)} bytes  -> {body[:300]}")
        return body
    except Exception as e:
        print(f"FAIL {label}: {repr(e)}")
        return None

try_get(f"https://api.faceit.com/stats/v1/stats/players/{PID}/games/cs2?size=3", "stats/v1 players games")
try_get(f"https://api.faceit.com/api/users/{PID}/games?game=cs2", "api/users games")
try_get(f"https://api.faceit.com/api/match/v1/matches?player_id={PID}&game=cs2&size=3", "api/match/v1 matches")
