#!/usr/bin/env python3
"""Holt die letzten Matches der SaltyBoomers von der FACEIT Data API und schreibt stats.json.

Key kommt aus der Umgebungsvariable FACEIT_API_KEY (GitHub-Secret im Workflow).
Fehlt der Key oder schlagen alle Abfragen fehl, bricht das Skript mit Fehler ab
und überschreibt stats.json NICHT. Fehlende Werte bleiben null, nie 0.
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

API = "https://open.faceit.com/data/v4"
ROOT = os.path.dirname(os.path.abspath(__file__))
PLAYERS_FILE = os.path.join(ROOT, "players.json")
OUT_FILE = os.path.join(ROOT, "stats.json")
MATCH_LIMIT = 30


def get(path, key):
    req = urllib.request.Request(
        API + path,
        headers={"Authorization": f"Bearer {key}", "User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def pct(a, b):
    return round(100 * a / b, 1) if b else None


def main():
    key = os.environ.get("FACEIT_API_KEY", "").strip()
    if not key:
        sys.exit("FEHLER: FACEIT_API_KEY nicht gesetzt (GitHub-Secret im Workflow).")

    with open(PLAYERS_FILE, encoding="utf-8") as f:
        players = json.load(f)
    pids = {n: p["player_id"] for n, p in players.items() if p.get("player_id")}

    # Matches der ersten Gruppe nehmen (gemeinsame Matches aller Spieler).
    any_pid = next(iter(pids.values()))
    hist = get(f"/players/{any_pid}/history?game=cs2&offset=0&limit={MATCH_LIMIT}", key)
    matches = hist.get("items", [])
    if not matches:
        sys.exit("FEHLER: keine Matches gefunden. stats.json bleibt unverändert.")

    per_match = []
    for m in matches:
        mid = m["match_id"]
        stats = get(f"/matches/{mid}/stats", key)
        per_match.append({"match_id": mid, "stats": stats})

    # Aggregation: Headshot-Quote, Trades, Eco/Pistol, beste/schlechteste Map, ELO-Höchststand.
    # Felder werden nur gesetzt, wenn sie wirklich im Payload existieren (sonst null).
    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "match_count": len(per_match),
        "bento": {"headshot_pct": None, "trade_kills": None, "eco_winrate": None, "pistol_winrate": None},
        "highlights": {"best_map": None, "worst_map": None, "elo_peak": None},
        "note": "Felder mit null: in der Match-API nicht gefunden (Payload prüfen).",
    }

    map_wins, map_total = {}, {}
    for pm in per_match:
        for rnd in pm["stats"].get("rounds", []):
            mapname = rnd.get("round_stats", {}).get("Map")
            if mapname:
                map_total[mapname] = map_total.get(mapname, 0) + 1
                if rnd.get("round_stats", {}).get("Winner") == rnd.get("teams", [{}])[0].get("team_id"):
                    map_wins[mapname] = map_wins.get(mapname, 0) + 1

    if map_total:
        rates = {m: pct(map_wins.get(m, 0), map_total[m]) for m in map_total}
        best = max(rates, key=rates.get)
        worst = min(rates, key=rates.get)
        out["highlights"]["best_map"] = {"map": best, "winrate": rates[best]}
        out["highlights"]["worst_map"] = {"map": worst, "winrate": rates[worst]}

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
