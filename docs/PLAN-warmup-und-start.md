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

## Offene Fragen an Manu
- Startzeit nur auf dem TV oder auch per Link für Handys?
- Reichen 5–20 Minuten Verzögerung, oder lohnt sich ein Abruf-Dienst auf Astana?
- Soll Reset wieder zurück in den Aufwärm-Modus führen?
