# Übergabe: Advanced-Bento (SaltyBoomers CS2/FACEIT-Dashboard)

Stand: Commit `23c1cb8` auf `origin/master`. Repo: `Manolo1987/saltyboomers`.
Dateien: `index.html` und `saltyboomers-dashboard.html` müssen identisch sein (`cmp index.html saltyboomers-dashboard.html`).

## Ziel
Das Advanced-Panel (`#advPanel`, Bento-Mosaik mit 17 Kennzahlen) soll auf dem TV ohne internes Scrollen und ohne abgeschnittene Kacheln oder Texte sichtbar sein.

## Wie das Panel sichtbar wird (wichtig)
- Die Startseite zeigt nur "STACK STARTEN". Das Panel existiert erst danach (`#viewLive`).
- Die Sichtbarkeit steuert `setTab()`. Das Panel bekommt nur dann `hidden` entfernt, wenn der Tab aktiv ist.
- Umschalter: `.vtab[data-tab="adv"]` (Tab-Button im Live-Bereich, Text "Advanced").
- Der Sidebar-Link "Advanced Stats" schaltet den Tab NICHT um. Darauf bin ich in einer früheren Sitzung hereingefallen und habe ein falsches Layoutproblem vermutet.
- Testablauf: Stack starten, dann `.vtab[data-tab="adv"]` klicken. Erwartet: Panel-Klasse `panel glow` (ohne `hidden`).

## Aktueller Zustand (verifiziert, 23c1cb8)
- Viewport 577 px hoch (Test-Setup).
- Panel 307 px, Bento-Inhalt 283 px, kein Scrollen (`scrollHeight == clientHeight`).
- Alle 17 Kacheln sichtbar, keine Kachel mit überlaufendem Text (gemessen per DOM, plus Screenshot-Prüfung).
- Kacheln sind bewusst klein: Höhe ca. 29 px, Werte 15 px, Untertext 9 px. Auf dem TV aus Distanz evtl. zu klein. Offene Frage an Manu.

## Relevante CSS-Regeln (index.html, ca. Zeile 900–935)
- `#advPanel { display:flex; flex-direction:column; min-height:0; max-height:calc(100vh - 140px); overflow:hidden; }`
- `#advPanel .bento.mosaic { display:grid !important; ...; grid-template-rows:repeat(5,minmax(0,1fr)) !important; gap:6px; padding:2px 10px 6px; }`
- `#advPanel .bento.mosaic .b-tile { min-height:0; padding:3px 7px; flex-direction:row; flex-wrap:wrap; ... }`
- Mehrere Regeln mit `!important` und doppelten `grid-template-rows`. Vor Umbau aufräumen.

## Commit-Verlauf (letzte Schritte)
- d7df517 Hero-Block, dense-Packing
- 8e8e71b Mosaik-Layout (klein/mittel/groß), K/D-Balken entfernt
- cad3885 Höhe an Panel angepasst
- 29f6f8a Kacheln mit Mindesthöhe, Text scrollbar
- a40a7cf Panel mit fester Höhe, Bento scrollt intern
- 23c1cb8 Kacheln kompakt, kein Scrollen (aktuell)

Die Commits ändern nur CSS unter `#advPanel`. Die Sichtbarkeitslogik (`setTab`) wurde nie verändert.

## Bekannte Probleme / Offen
1. Lesbarkeit auf dem TV: Schrift sehr klein. Entscheidung offen: weniger Kacheln oder mehr Panelhöhe.
2. Doppelte `grid-template-rows`-Deklaration (`none !important` und `repeat(5,...) !important`) in einer Regel. Das ist unsauber, funktioniert aber.
3. Farblogik der Kachel-Ränder (Deckkraft nach gut/schlecht) war in früheren Schritten gewünscht. Status nicht erneut geprüft.
4. Der Vorgang war bisher nicht durch einen sauberen Abnahmetest abgesichert. Empfehlung: einen Screenshot-Test mit Stack-Start und Tab-Klick als Abnahme festschreiben.

## Umgebung und Tests
- Lokal: `http://127.0.0.1:8765/index.html` (statischer Server, läuft auf dem Host).
- Browser-Cache: nach CSS-Änderungen `location.reload(true)` ausführen, sonst bleibt alte CSS.
- Screenshots: `/home/ubuntu/.hermes/cache/screenshots/`.
- FACEIT_API_KEY: liegt bereits in der Umgebung ab (Manu hat es freigegeben). Wert nicht in Doku oder Logs kopieren.

## Wie man nachprüft
1. `git log --oneline -3` und `git status` (sauber).
2. `cmp index.html saltyboomers-dashboard.html`.
3. Browser: Stack starten, `.vtab[data-tab="adv"]` klicken, dann prüfen: `#advPanel` ohne `hidden`, `.bento.mosaic` `scrollHeight <= clientHeight`.
