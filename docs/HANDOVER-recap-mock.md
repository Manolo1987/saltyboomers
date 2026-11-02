# Handover: Recap-Mockups (Zusammenfassungsbilder)

**Stand:** 2026-11-02 · **Status:** fertig, visuell verifiziert · **Pfad:** `/home/ubuntu/faceit-weekend/recap_mock/`

Zusammenfassungsbilder zum LAN-Wochenende (Fr 30.10. – So 01.11.2026): 1 Teamkarte + 5 Spielerkarten, gerendert als JPEG. Basis ist ein statisches HTML-Template (kein Dashboard-Code), das die Daten aus `data.json` lädt.

## Dateien

| Datei | Zweck |
|---|---|
| `recap_mock.html` | Template (HTML/CSS/JS inline). Lädt `data.json` per fetch und baut alle 6 Karten. Setzt `document.title = "READY"`, wenn gerendert. |
| `data.json` | Datenbasis (verifiziert, siehe unten). Werte 1:1 mit dem Live-Dashboard abgestimmt. |
| `render.js` | Playwright-Renderer → 6 JPEGs (Element-Screenshots, q92). |
| `recap_team.jpg` | Teamkarte 1920×1080 (Beamer/Post-Format). |
| `recap_<nick>.jpg` | 5 Spielerkarten, je 1080×1350 (Instagram-Porträt-Format). |
| `../assets/logo_full.png` | SaltyBoomers-Crest mit Schriftzug (Pfad im Template: `/assets/logo_full.png`). |

## Datenbasis (verifiziert)

Filter wie im Live-Dashboard: nur Matches ab **Fr 30.10. 14:00 MEZ** (`started_at >= 1793365200`) → **exakt 23 Matches, 13 : 10** (57 %), Streak **5**, Runden **237 : 221** (+16), **+316 ELO**. Vorherige Versionen des Templates zeigten 30 Matches (Queue-Vorlauf ohne Zeitfilter) — korrigiert.

Maps: Anubis 5–1 · Dust2 5–2 · Nuke 2–2 · Cache 1–1 · Ancient 0–3 · Inferno 0–1.

Spieler (aus `data.json`; `elo`/`level` = aktueller FACEIT-Stand, `d_elo` = Wochenend-Saldo gemäß Start-Snapshot):

| Spieler | Matches | K/D | ADR | HS % | ELO / Level | d_elo |
|---|---|---|---|---|---|---|
| -neon666 | 23 | 1.48 | 111.3 | 50 | 2164 / 10 | +64 |
| theunc666 | 23 | 0.98 | 73.1 | 45 | 1796 / 9 | +81 |
| kokolorez | 23 | 0.94 | 72.2 | 44 | 1873 / 9 | +64 |
| Shpooople | 23 | 1.17 | 87.6 | 34 | 1492 / 7 | +132 |
| amaseling | 20 | 0.48 | 46.9 | 41 | 1127 / 5 | −25 |

Beteiligung ist NICHT einheitlich: amaseling fehlten 3 der 23 Matches („20 Stack-Matches" auf der Karte). Die Ringe/Badges je Spieler stehen im JS des Templates (`RING`, `BADGE`).

## Design (fest verankert)

- Dunkler Bento-Look (`#060607`), Radial-Glows in Faceit-Orange/Rot, Karten `border-radius 20px`.
- **Ringfarben pro Spieler** (Avatar-Rahmen 6px, via CSS-Var `--ring`): Shpooople Blau `#2f7bff` · kokolorez Orange `#ff9c1f` · amaseling Gelb `#ffd02e` · -neon666 Grün `#34d97b` · theunc666 Lila `#a855f7`.
- **Level-Badges:** SVG-Pentagon wie im Dashboard (`lvlSvg(lvl)`, Halbkreis-Progress mit `pathLength`, Farben je Level 1–10). Auf Spielerkarten XL-Variante neben dem Nick, auf der Teamkarte klein am Avatar.
- **Logo:** `assets/logo_full.png` immer mit `object-fit: contain` und fester Höhe — keine Verzerrung (alter Fehler: gestauchtes Emblem).
- **amaseling:** Extra-Badge „♥ MVP DER HERZEN" (herzförmig/rosa hervorgehoben), zusätzlich „◆ Immer dabei · 20 Matches".
- Teamkarte-Fußzeile: Streak 5 · Anubis 5–1 beste Map · Pistol-König -neon666 (94) · AWP Shpooople (59).
- **Unicode statt Emoji:** ★ ◆ ♥ ⚡ als Textsymbole — Emojis (🔥👑) fehlten im Headless-Font und zeigten Kästchen (Tofu).

## Neu rendern (z. B. nach Datenkorrektur)

```bash
cd /home/ubuntu/faceit-weekend
python3 -m http.server 8899 --bind 127.0.0.1 &   # Server: Root muss faceit-weekend sein (fetch + assets)
node recap_mock/render.js
```

Danach jede Karte mit `vision_analyze` gegen `data.json` prüfen (Zahlen, Ringfarben, Level-Badges, Logo).

## Pitfalls

- **Kein `file://`** — Template fetcht `data.json`, braucht den HTTP-Server.
- **CDN-Avatare:** render.js blockt externe Requests NICHT (anders als die Dashboard-Probes) und wartet via `title === READY` + 1,5 s Puffer — sonst leere Kreis-Platzhalter statt Gesichter.
- **Headless-Rendering:** voller Chromium-Build + `--no-sandbox` (Pfad in render.js), Element-Screenshots statt fullPage.
- Server auf Port 8899 läuft nicht als Dienst — nach VM-Neustart von Hand starten.

## Git

Committed in `Manolo1987/saltyboomers` (Branch master). Dashboard-/Publisher-Kontext: `/home/ubuntu/docs/proj-saltyboomers-dash.md`, `docs/HANDOVER-advanced-bento.md`.
