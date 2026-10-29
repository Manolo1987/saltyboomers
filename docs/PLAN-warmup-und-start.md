# Plan: Aufwärm-Modus (letzte 30 Matches) + Start-Knopf mit Animation

Status: Entwurf, wartet auf Freigabe durch Manu.

## Ziel
- Vor dem Start: Die Seite zeigt die Form aus den letzten 30 Matches, damit nichts leer ist.
- Ab dem ersten Match nach dem Start: Nur noch echte Wochenend-Daten.
- Start-Knopf mit Animation und Sound, verschwindet danach.

## Drei Zustände
1. **Aufwärmen**: Daten = letzte 30 Matches. Banner „Form der letzten 30 Matches“. Großer Knopf „WOCHENENDE STARTEN“.
2. **Gestartet, wartet**: Knopf ist mit Animation verschwunden. Die alten Daten bleiben sichtbar, aber abgedunkelt, mit dem Badge „Live ab dem ersten Match“.
3. **Live**: Das erste Stack-Match nach dem Startzeitpunkt ist fertig. Die Zahlen laufen von alt auf neu (Count-up), und das Banner wechselt auf „Wochenende live“.

Der Wechsel von 2 nach 3 passiert automatisch, sobald die Daten das hergeben. Dafür muss niemand klicken.

## Daten (wichtigster Punkt)
- `fetch_stats.py` schreibt künftig **jedes Match einzeln** in `stats.json`, mit Zeitpunkt, Map, Ergebnis und den Werten pro Spieler. Bisher stehen da nur fertige Summen. Die Daten holt das Skript schon heute pro Match, sie werden nur noch nicht gespeichert.
- Der Browser rechnet selbst:
  - Aufwärmen = alle Matches in der Datei (letzte 30)
  - Live = nur Matches, die **nach dem Klick auf Start** zu Ende gegangen sind
- Der Startzeitpunkt wird im Browser gespeichert (localStorage). Vorteil: Der Knopf muss nichts zurück nach GitHub schreiben, also steht kein Token im Browser. Nachteil: Nur das Gerät, auf dem geklickt wurde (der TV), weiß vom Start. Optional kann man den Startzeitpunkt zusätzlich als Link-Parameter `?start=…` mitgeben, dann sehen Handys dasselbe.
- „Stack-Match“ = mindestens 2 Leute aus `players.json` haben im selben Match gespielt.

## Aktualisierung
- Heute läuft der GitHub-Workflow alle 30 Minuten. Das ist zu langsam: Nach einem Match würde man bis zu einer halben Stunde warten.
- Vorschlag: alle 5 Minuten, das ist das Minimum bei GitHub. GitHub startet geplante Läufe aber oft 5–15 Minuten zu spät. Realistisch sind die Daten also 5–20 Minuten nach Matchende auf der Seite.
- Den FACEIT-Key direkt im Browser zu benutzen, wäre schneller, ist aber **verboten**: Dann wäre der Key öffentlich. Wenn es schneller gehen soll, wäre die Alternative ein kleiner Abruf-Dienst auf Astana. Das wäre ein eigenes Projekt und braucht einen eigenen Security-Check.

## Animation und Sound
- Klick → der Knopf zieht sich kurz zusammen und explodiert dann in Partikel (Teamfarben). Ein heller Lichtstreifen läuft über die ganze Seite, dann der Text „GO GO GO“ groß in der Mitte für etwa 1,5 s, danach blendet er aus. Ohne Bibliothek, nur CSS und Canvas.
- Sound: wird im Browser selbst erzeugt (WebAudio: Whoosh, Bass-Schlag, kurzer Ton nach oben). **Keine CS2-Originalsounds**, die gehören Valve. Es braucht keine Datei und hat keine Lizenzprobleme.
- Browser spielen Ton nur nach einem Klick ab. Der Startknopf ist ein Klick, deshalb klappt das.
- Beim Wechsel in den Live-Modus (Zustand 3) gibt es eine zweite, kleinere Animation: Die Kacheln „flippen“ nacheinander auf die neuen Werte, dazu ein kurzer Ton.
- Wer `prefers-reduced-motion` eingestellt hat, bekommt nur eine Überblendung.

## Arbeitsschritte (nach Freigabe)
1. `fetch_stats.py`: Matches einzeln speichern, Workflow auf 5 Minuten stellen, lokal mit echtem Key testen.
2. Dashboard: Zahlen aus `stats.json` berechnen statt aus Demo-Werten (Kopfzeile, letztes Match, Verlauf, Bento, Highlights).
3. Die drei Zustände mit Banner/Badge einbauen und den Startzeitpunkt speichern.
4. Start-Animation und Sound, Live-Wechsel-Animation.
5. Test: Playwright auf 1080p/4K/1366. Den Start mit Fake-Matches vor und nach dem Startzeitpunkt simulieren.
6. Security-Check: kein Key im Frontend, keine neuen externen Skripte.

## Entscheidungen (29.10.)
- Nur TV, kein Handy-Link.
- Reset → zurück in den Aufwärm-Modus.

## Validierung der Limits (29.10.)
- GitHub Actions: Minimum 5 Minuten zwischen geplanten Läufen. Zur vollen Stunde gibt es oft Verzögerungen, Läufe können sogar ganz entfallen (offizielle GitHub-Doku). Bestätigt.
- FACEIT Data API: Die offizielle Doku nennt **keine Zahl**, sie dokumentiert nur den Fehlercode 429. Die Werte 100/s, 400/10 s, 10.000/h und 300/min kommen aus Community-Quellen und sind nicht verifiziert. Messen geht nur mit dem Key, und der liegt nur als GitHub-Secret vor.
- Früher stand im Chat: „5× pro Minute geht klar“. Das hat das FACEIT-Limit mit dem Takt von GitHub verwechselt. Mit GitHub Actions ist 1× pro Minute nicht möglich.

## Umgesetzt: Publisher auf Astana (29.10.)
- TV steht nicht im Netz von Astana, deshalb laufen die Daten über GitHub Pages. Kein offener Port.
- Hermes-VM: `~/sb-publisher/publish.sh`, cron jede Minute, `flock` gegen doppelte Läufe, Log `~/sb-publisher/publish.log`, Cache `~/sb-publisher/cache/`, eigener Clone `~/sb-publisher/repo`.
- Key: `~/.config/saltyboomers/faceit.env` (chmod 600, `FACEIT_API_KEY=...`). Fehlt die Datei, wartet das Skript still.
- Push: Deploy-Key `~/.ssh/sb_publisher_ed25519` mit Schreibrecht **nur** auf Repo saltyboomers (GitHub Key-ID 168116196).
- `fetch_stats.py` v2: Historie aller 5 Spieler → Matches mit ≥2 SaltyBoomers im selben Team, die letzten 30 einzeln mit Werten pro Spieler; neue Matches werden einzeln nachgeladen, Matches ohne fertige FACEIT-Statistik (404) beim nächsten Lauf erneut. Pause 0,25 s zwischen Requests, bei 429/5xx wiederholen. Schreibt nur bei inhaltlicher Änderung.
- Pro Minute ca. 5–6 Requests, alle 5 Min +5 für ELO.
- GitHub Actions bleibt alle 30 Min als Notlösung. Bei Konflikt gewinnt der Stand von Astana.
- Sicherheitsfolge: Jeder Code auf `master` läuft auf der VM mit dem Key. Nur Manu/Hermes pushen.
- Offen: echter Lauf mit Key, Payload-Felder prüfen, Zeit von Matchende bis TV messen.
