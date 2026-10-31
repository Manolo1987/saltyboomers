#!/usr/bin/env python3
"""Holt die letzten Stack-Matches der SaltyBoomers von der FACEIT Data API und schreibt stats.json.

Läuft an zwei Stellen:
  - auf der Hermes-VM (Astana) jede Minute per cron (schnell, mit Cache)
  - als Notlösung in GitHub Actions (alle 30 Min, ohne Cache)

Key: Umgebungsvariable FACEIT_API_KEY, sonst Datei aus FACEIT_ENV_FILE
(Standard ~/.config/saltyboomers/faceit.env, Zeile FACEIT_API_KEY=...).
Der Key wird nie ausgegeben.

stats.json wird nur neu geschrieben, wenn sich der Inhalt wirklich geändert hat.
Fehlende Werte bleiben null, nie 0. Bei Fehlern bleibt die alte stats.json stehen.
Exit-Codes: 0 = ok (Ausgabe "changed" oder "unchanged"), 1 = Fehler.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

API = "https://open.faceit.com/data/v4"
ROOT = os.path.dirname(os.path.abspath(__file__))
PLAYERS_FILE = os.path.join(ROOT, "players.json")
OUT_FILE = os.environ.get("SB_OUT_FILE", os.path.join(ROOT, "stats.json"))
CACHE_DIR = os.environ.get("SB_CACHE_DIR", "")          # leer = kein Cache (GitHub Actions)
MATCH_LIMIT = 30          # so viele Stack-Matches landen in stats.json
HISTORY_LIMIT = 30        # pro Spieler abgefragte Historie
MIN_STACK = 2             # ab so vielen SaltyBoomers im selben Team zählt ein Match
PROFILE_EVERY = 300       # Spielerprofile (ELO) höchstens alle 5 Min neu holen
THROTTLE = 0.25           # Pause zwischen zwei Requests (Sekunden)
NEMESIS_TOP = 8           # so viele Gegner bekommen ELO/Level (Profil-Abfrage)
NEMESIS_EVERY = 86400     # Gegner-Profile höchstens alle 24 h neu holen
ENEMY_FIELDS = ("Kills", "Assists", "Deaths", "K/D Ratio", "ADR", "Headshots %", "MVPs")

REQUESTS = 0


class NotReady(Exception):
    """Match-Statistik bei FACEIT noch nicht fertig (404)."""


def load_key():
    key = os.environ.get("FACEIT_API_KEY", "").strip()
    if key:
        return key
    path = os.environ.get("FACEIT_ENV_FILE", os.path.expanduser("~/.config/saltyboomers/faceit.env"))
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("FACEIT_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return ""


def get(path, key):
    """GET mit Drosselung und Wiederholung bei 429/5xx. Gibt den Key nie aus."""
    global REQUESTS
    for attempt in range(4):
        time.sleep(THROTTLE)
        REQUESTS += 1
        req = urllib.request.Request(
            API + path,
            headers={"Authorization": f"Bearer {key}", "User-Agent": "saltyboomers-dashboard/2"},
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise NotReady(path)
            if e.code in (429, 500, 502, 503, 504) and attempt < 3:
                wait = e.headers.get("Retry-After") if e.headers else None
                try:
                    wait = min(float(wait), 30.0)
                except (TypeError, ValueError):
                    wait = 3.0 * (attempt + 1)
                print(f"WARN: HTTP {e.code} bei {path.split('?')[0]}, warte {wait:.0f}s", file=sys.stderr)
                time.sleep(wait)
                continue
            raise RuntimeError(f"HTTP {e.code} bei {path.split('?')[0]} | body={e.read()[:140]!r} | cf-ray={e.headers.get('cf-ray')}") from None
        except urllib.error.URLError as e:
            if attempt < 3:
                time.sleep(3.0 * (attempt + 1))
                continue
            raise RuntimeError(f"Netzwerkfehler bei {path.split('?')[0]}: {e.reason}") from None
    raise RuntimeError(f"aufgegeben: {path.split('?')[0]}")


def num(v):
    """FACEIT liefert Zahlen als Strings. '12' -> 12, '1.25' -> 1.25, sonst None."""
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return v
    try:
        f = float(str(v).replace(",", "."))
    except ValueError:
        return None
    return int(f) if f.is_integer() else round(f, 3)


# ---------- Cache (nur auf der VM) ----------

def cache_path(name):
    return os.path.join(CACHE_DIR, name) if CACHE_DIR else ""


def cache_read(name):
    p = cache_path(name)
    if not p or not os.path.exists(p):
        return None
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def cache_write(name, data):
    p = cache_path(name)
    if not p:
        return
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, p)


# ---------- Datenaufbereitung ----------

def stack_players_in(team, pids):
    return [p.get("player_id") for p in (team or {}).get("players", []) if p.get("player_id") in pids]


def build_match(hist_item, stats, pids, nick_by_pid):
    """Kompakter Datensatz für ein Match. Stack-Spieler vollständig, Gegner kompakt."""
    rnd = (stats.get("rounds") or [{}])[0]
    rs = rnd.get("round_stats", {})
    teams = rnd.get("teams", [])
    ours, theirs = None, None
    for t in teams:
        if stack_players_in(t, pids):
            ours = t
        else:
            theirs = t
    if ours is None:
        return None
    ts = ours.get("team_stats", {})
    win = None
    if ts.get("Team Win") is not None:
        win = str(ts.get("Team Win")) == "1"
    elif rs.get("Winner"):
        win = rs.get("Winner") == ours.get("team_id")

    our_score = num(ts.get("Final Score"))
    their_score = num((theirs or {}).get("team_stats", {}).get("Final Score"))

    players = {}
    for p in ours.get("players", []):
        pid = p.get("player_id")
        if pid not in pids:
            continue
        ps = {k: num(v) for k, v in (p.get("player_stats") or {}).items()}
        players[nick_by_pid[pid]] = {k: v for k, v in ps.items() if v is not None}

    # Gegner kompakt (Nemesis-Liste + Match-Modal)
    enemies = {}
    for p in (theirs or {}).get("players", []):
        epid, enick = p.get("player_id"), p.get("nickname")
        if not epid or not enick:
            continue
        eps = {k: num(v) for k, v in (p.get("player_stats") or {}).items()}
        e = {"pid": epid}
        e.update({k: eps[k] for k in ENEMY_FIELDS if eps.get(k) is not None})
        enemies[enick] = e

    # Halbzeit-Scores -> Swing: Rundendifferenz der zweiten minus der ersten Halbzeit
    th_ts = (theirs or {}).get("team_stats", {})
    fh_us, fh_th = num(ts.get("First Half Score")), num(th_ts.get("First Half Score"))
    sh_us, sh_th = num(ts.get("Second Half Score")), num(th_ts.get("Second Half Score"))
    swing = None
    if None not in (fh_us, fh_th, sh_us, sh_th):
        swing = {"fh": [fh_us, fh_th], "sh": [sh_us, sh_th], "mom": (sh_us - sh_th) - (fh_us - fh_th)}

    return {
        "match_id": hist_item["match_id"],
        "started_at": hist_item.get("started_at"),
        "finished_at": hist_item.get("finished_at"),
        "map": rs.get("Map"),
        "rounds": num(rs.get("Rounds")),
        "score": [our_score, their_score],
        "win": win,
        "competition": hist_item.get("competition_name"),
        "v": 2,
        "players": players,
        "enemies": enemies,
        "swing": swing,
    }


def main():
    key = load_key()
    if not key:
        print("FEHLER: FACEIT_API_KEY fehlt (env oder ~/.config/saltyboomers/faceit.env).", file=sys.stderr)
        return 1

    with open(PLAYERS_FILE, encoding="utf-8") as f:
        roster = json.load(f)
    pids = {p["player_id"]: n for n, p in roster.items() if p.get("player_id")}
    nick_by_pid = dict(pids)

    # 1) Historie aller Spieler holen und zu Stack-Matches zusammenführen
    seen = {}
    for pid in pids:
        try:
            hist = get(f"/players/{pid}/history?game=cs2&offset=0&limit={HISTORY_LIMIT}", key)
        except NotReady:
            continue
        for it in hist.get("items", []):
            if str(it.get("status", "")).lower() != "finished":
                continue
            seen.setdefault(it["match_id"], it)

    candidates = []
    for mid, it in seen.items():
        n = max(
            len(stack_players_in(it.get("teams", {}).get(fac), pids))
            for fac in ("faction1", "faction2")
        ) if it.get("teams") else 0
        if n >= MIN_STACK:
            candidates.append(it)
    candidates.sort(key=lambda x: x.get("finished_at") or 0, reverse=True)
    candidates = candidates[:MATCH_LIMIT]
    if not candidates:
        print("FEHLER: keine Stack-Matches gefunden. stats.json bleibt unverändert.", file=sys.stderr)
        return 1

    # 2) Match-Statistiken (aus Cache, nur neue Matches kosten Requests)
    matches, pending = [], 0
    for it in candidates:
        mid = it["match_id"]
        cached = cache_read(f"matches/{mid}.json")
        if cached is None or cached.get("v") != 2:  # alte Caches ohne Gegner/Swing neu holen
            try:
                st = get(f"/matches/{mid}/stats", key)
            except NotReady:
                pending += 1        # FACEIT rechnet noch, nächster Lauf
                continue
            cached = build_match(it, st, pids, nick_by_pid)
            if cached is None:
                continue
            cache_write(f"matches/{mid}.json", cached)
        matches.append(cached)

    # 3) Spielerprofile (aktuelle ELO), höchstens alle PROFILE_EVERY Sekunden
    prof = cache_read("profiles.json") or {}
    if time.time() - prof.get("_ts", 0) > PROFILE_EVERY or not CACHE_DIR:
        fresh = {}
        for pid, nick in pids.items():
            try:
                p = get(f"/players/{pid}", key)
            except NotReady:
                continue
            g = (p.get("games") or {}).get("cs2", {})
            fresh[nick] = {"elo": g.get("faceit_elo"), "level": g.get("skill_level")}
        if fresh:
            prof = {"_ts": time.time(), "players": fresh}
            cache_write("profiles.json", prof)
    players = prof.get("players", {})

    # 4) Alte Felder für das jetzige Dashboard (bento/highlights) weiter befüllen
    hs, kills = 0, 0
    map_w, map_n = {}, {}
    for m in matches:
        for ps in m["players"].values():
            if ps.get("Headshots") is not None and ps.get("Kills") is not None:
                hs += ps["Headshots"]
                kills += ps["Kills"]
        if m["map"] and m["win"] is not None:
            map_n[m["map"]] = map_n.get(m["map"], 0) + 1
            map_w[m["map"]] = map_w.get(m["map"], 0) + (1 if m["win"] else 0)
    rates = {k: round(100 * map_w[k] / map_n[k], 1) for k in map_n}
    best = max(rates, key=rates.get) if rates else None
    worst = min(rates, key=rates.get) if rates else None

    # 4b) Advanced: Clutch/Pistol je Map, Swing-Bilanz, Nemesen (Gegner mit ELO)
    clutch_maps, clutch_pl, pistol_maps, pistol_pl, swing_maps = {}, {}, {}, {}, {}
    nem = {}
    comebacks = collapses = 0
    mom_all = []
    for m in matches:
        mp = m.get("map") or "?"
        for nick, ps in m["players"].items():
            for ck in ("1v1", "1v2"):
                c, w = ps.get(ck + "Count"), ps.get(ck + "Wins")
                if c:
                    cm = clutch_maps.setdefault(mp, [0, 0])
                    cm[0] += c
                    cm[1] += w or 0
                    cp = clutch_pl.setdefault(nick, [0, 0])
                    cp[0] += c
                    cp[1] += w or 0
            pk = ps.get("Pistol Kills")
            if pk:
                pm = pistol_maps.setdefault(mp, {})
                pm[nick] = pm.get(nick, 0) + pk
                pistol_pl[nick] = pistol_pl.get(nick, 0) + pk
        for enick, ps in (m.get("enemies") or {}).items():
            e = nem.setdefault(enick, {"nick": enick, "pid": ps.get("pid"), "n": 0, "wins": 0,
                                       "kills": 0, "deaths": 0, "_hss": 0.0, "_hsn": 0, "mvp": 0})
            e["n"] += 1
            if m.get("win") is False:
                e["wins"] += 1
            e["kills"] += ps.get("Kills") or 0
            e["deaths"] += ps.get("Deaths") or 0
            _hs = ps.get("Headshots %")
            if _hs is not None:
                e["_hss"] += _hs
                e["_hsn"] += 1
            e["mvp"] += ps.get("MVPs") or 0
        sw = m.get("swing")
        if sw:
            mom_all.append(sw["mom"])
            sm = swing_maps.setdefault(mp, [0, 0, 0, 0])  # Matches, Σ Momentum, Comebacks, Collapses
            sm[0] += 1
            sm[1] += sw["mom"]
            lead_fh = sw["fh"][0] - sw["fh"][1]
            if m.get("win") is True and lead_fh < 0:
                sm[2] += 1
                comebacks += 1
            if m.get("win") is False and lead_fh > 0:
                sm[3] += 1
                collapses += 1

    ranked = sorted((x for x in nem.values() if x.get("pid")),
                    key=lambda x: (x["kills"], x["kills"] - x["deaths"]), reverse=True)[:NEMESIS_TOP]
    np_cache = cache_read("nemeses.json") or {}
    nplayers = np_cache.get("players", {})
    if time.time() - np_cache.get("_ts", 0) > NEMESIS_EVERY or not CACHE_DIR:
        for x in ranked:
            if x["pid"] in nplayers:
                continue
            try:
                p = get(f"/players/{x['pid']}", key)
            except (NotReady, RuntimeError) as e:  # ein kaputtes Gegner-Profil darf den Lauf nicht abbrechen
                print(f"WARN: Nemesis-Profil {x['nick']} ({x['pid']}) nicht abrufbar: {e}", file=sys.stderr)
                continue
            g = (p.get("games") or {}).get("cs2", {})
            nplayers[x["pid"]] = {"elo": g.get("faceit_elo"), "level": g.get("skill_level")}
        if nplayers:
            cache_write("nemeses.json", {"_ts": time.time(), "players": nplayers})
    nemeses = [{
        "nick": x["nick"], "matches": x["n"], "wins": x["wins"],
        "kills": x["kills"], "deaths": x["deaths"],
        "kd": round(x["kills"] / x["deaths"], 2) if x["deaths"] else None,
        "hs_pct": round(x["_hss"] / x["_hsn"], 1) if x["_hsn"] else None,
        "mvp": x["mvp"],
        "elo": (nplayers.get(x["pid"]) or {}).get("elo"),
        "level": (nplayers.get(x["pid"]) or {}).get("level"),
    } for x in ranked]

    adv = {
        "clutch": {
            "maps": {k: {"count": v[0], "wins": v[1]} for k, v in clutch_maps.items()},
            "players": {k: {"count": v[0], "wins": v[1]} for k, v in clutch_pl.items()},
        },
        "pistol": {
            "maps": {k: {"total": sum(d.values()), "by": d} for k, d in pistol_maps.items()},
            "players": pistol_pl,
        },
        "swing": {
            "maps": {k: {"matches": v[0], "mom_avg": round(v[1] / v[0], 1),
                         "comebacks": v[2], "collapses": v[3]} for k, v in swing_maps.items()},
            "mom_avg": round(sum(mom_all) / len(mom_all), 1) if mom_all else None,
            "comebacks": comebacks, "collapses": collapses,
        },
        "nemeses": nemeses,
    }

    out = {
        "schema": 3,
        "updated_at": None,
        "match_count": len(matches),
        "pending_matches": pending,
        "players": players,
        "matches": matches,
        "bento": {
            "headshot_pct": round(100 * hs / kills, 1) if kills else None,
            "trade_kills": None, "eco_winrate": None, "pistol_winrate": None,
        },
        "highlights": {
            "best_map": {"map": best, "winrate": rates[best]} if best else None,
            "worst_map": {"map": worst, "winrate": rates[worst]} if worst else None,
            "elo_peak": None,
        },
        "adv": adv,
    }

    # 5) Nur schreiben, wenn sich inhaltlich etwas geändert hat
    old = None
    if os.path.exists(OUT_FILE):
        try:
            with open(OUT_FILE, encoding="utf-8") as f:
                old = json.load(f)
        except (OSError, ValueError):
            old = None
    if old is not None:
        cmp_old = dict(old, updated_at=None)
        if cmp_old == out:
            print(f"unchanged ({len(matches)} Matches, {REQUESTS} Requests)")
            return 0

    out["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    tmp = OUT_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    os.replace(tmp, OUT_FILE)
    print(f"changed ({len(matches)} Matches, {pending} noch offen, {REQUESTS} Requests)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # Fehlertext ohne Key
        print(f"FEHLER: {e}", file=sys.stderr)
        sys.exit(1)
