---
name: schnitt
description: Schneidet aus Talking-Head-Rohmaterial ein fertiges Video - Pausen raus, Versprecher und abgebrochene Sätze raus, bei doppelten Takes der letzte, Reihenfolge wie im Skript, Export als MP4 (z. B. Hochformat 1080x1920). Benutzen, wenn jemand sagt "schneid mein Video", "Pausen raus", "Versprecher raus", "mach aus dem Rohmaterial ein Video", "Jump Cuts", oder einen Ordner mit Rohmaterial und Skript übergibt.
---

# Schnitt

Du schneidest Talking-Head-Rohmaterial so, wie es ein guter Cutter machen würde: Alles Gesagte bleibt verständlich, aber alles, was stört, fliegt raus. Du arbeitest über das Transkript, nicht über eine Timeline.

Der Ablauf hat fünf Schritte. Arbeite sie der Reihe nach ab und sag dem Nutzer kurz, wo du gerade bist.

## 0. Einmalig: Werkzeuge prüfen

Prüfe, ob `ffmpeg` und `faster-whisper` da sind:

```bash
ffmpeg -version
python3 -c "import faster_whisper"
```

Fehlt etwas, installiere es (vorher kurz sagen, was du installierst):

- **ffmpeg:** Mac `brew install ffmpeg` (ohne Homebrew zuerst Homebrew installieren), Windows `winget install Gyan.FFmpeg`
- **faster-whisper:** `python3 -m pip install faster-whisper` (unter Windows `py -m pip install faster-whisper`)

Die Skripte liegen im Ordner `scripts/` neben dieser Datei. Ruf sie mit vollem Pfad auf.

## 1. Material sichten

Im Arbeitsordner liegen Videodateien (Rohmaterial) und optional ein Skript (`.txt`, `.md`, `.docx`, `.pdf`).

- Liste die Videodateien auf. Bei mehreren Dateien: Reihenfolge nach Dateiname, wenn nichts anderes gesagt wird.
- Lies das Skript, falls vorhanden. Es bestimmt die Reihenfolge im fertigen Video.
- Prüf kurz, wo der gute Ton liegt (`ffmpeg -i <datei> -af volumedetect -f null -`). Liegt das Ansteck-Mikro auf einer anderen Aufnahme (z. B. Bildschirmaufnahme am Laptop) und die Kamera ist fast stumm, dann transkribiere die Datei mit dem guten Ton und leg das Kamerabild beim Rendern darunter. Den Versatz findest du per Kreuzkorrelation der Tonspuren, die Startzeiten aus den Metadaten (`creation_time`) sind nur sekundengenau.
- Fehlen Angaben zum Format, frag einmal nach: Hochformat 1080x1920 (Reels, TikTok, Shorts) oder Querformat 1920x1080 (YouTube). Alles andere hat sinnvolle Standards.

## 2. Transkribieren

```bash
python3 scripts/transcribe.py <video1> [<video2> ...] --lang de --out schnitt-arbeit
```

Das erzeugt in `schnitt-arbeit/`:

- `words.json`: jedes Wort mit Index, Datei, Start und Ende
- `transkript.txt`: lesbares Transkript, eine Zeile pro Phrase, mit Wort-Indizes vorne, z. B. `[120-134] 02:14.3  Das hat mich ungefähr fünf Minuten gekostet.`

Die Wort-Zeitstempel werden dabei mit einer Spracherkennung (VAD) nachgeschärft. Whisper zieht Wörter nach einer Pause oft über die Stille, ohne das Nachschärfen würde Schritt 4 diese Pausen nicht finden.

Standard-Modell ist `small` (schnell, gut genug für Deutsch). Bei schlechter Tonqualität `--model medium`.

## 3. Entscheiden, was bleibt (das ist deine eigentliche Arbeit)

Lies `transkript.txt` komplett. Leg dann `schnitt-arbeit/keep.json` an: die Wortbereiche, die ins Video kommen, **in der Reihenfolge, in der sie im Video laufen sollen**.

```json
{
  "segments": [
    {"from": 120, "to": 134, "note": "Hook, letzter Take"},
    {"from": 151, "to": 170, "note": ""}
  ]
}
```

`from` und `to` sind Wort-Indizes aus `words.json`, beide inklusive.

Regeln:

- **Mehrere Takes vom selben Satz:** nimm den letzten vollständigen Take. Ausnahme: der letzte ist hörbar schlechter (abgebrochen, verhaspelt), dann den besten davor und das in `note` schreiben.
- **Versprecher, Hänger, abgebrochene Sätze:** raus. Wenn jemand mitten im Satz neu ansetzt, beginnt dein Segment beim Neuansatz.
- **Füllwörter** ("ähm", "äh", "also" am Satzanfang): raus, wenn sie allein stehen. Ein Segment darf dafür mitten im Satz enden und das nächste dahinter weitergehen.
- **Kommentare an sich selbst** ("nochmal", "warte", "okay, Cut", "wie war das"): raus.
- **Reihenfolge:** wie im Skript. Ohne Skript: wie aufgenommen.
- **Nichts umformulieren, nichts erfinden.** Du kannst nur weglassen und umstellen. Fehlt ein Satz aus dem Skript ganz, sag es dem Nutzer.
- Whisper verhört sich manchmal. Wenn ein Take im Transkript komisch aussieht, aber sonst passt, lass ihn drin und vermerke es in `note` ("bitte gegenhören").

Pausen musst du hier nicht beachten, die kürzt Schritt 4 automatisch.

## 4. Schnittliste bauen

```bash
python3 scripts/cuts.py schnitt-arbeit --max-pause 0.5
```

- `--max-pause`: Pausen zwischen Wörtern, die länger sind, werden rausgeschnitten (Standard 0,5 s; für Reels auch 0,3). Übrig bleibt etwas Luft vor und nach jedem Wort, damit nichts angeschnitten klingt.
- Ergebnis: `schnitt-arbeit/cuts.json` (für den Render) und `schnitt-arbeit/schnittliste.md` (für den Menschen: jeder Clip mit Quelle, Zeit und Text, plus Liste aller rausgeschnittenen Stellen).

## 5. Rendern

```bash
python3 scripts/render.py schnitt-arbeit --format 9:16 --out fertig.mp4
```

- `--format`: `9:16` (1080x1920, mittig zugeschnitten), `16:9` (1920x1080) oder `original`
- `--fps 30` ist Standard.
- An jedem Schnitt kommt eine sehr kurze Audio-Blende, damit es nicht knackst.

## 6. Übergabe

Sag dem Nutzer:

1. wo `fertig.mp4` liegt und wie lang es ist (vorher / nachher)
2. was rausgeflogen ist, kurz zusammengefasst (Anzahl Pausen, welche doppelten Takes, welche Versprecher), ausführlich steht es in `schnittliste.md`
3. Stellen mit "bitte gegenhören"
4. die Bitte, das Video einmal komplett anzuschauen. Du schneidest nach dem, was gesagt wird. Ein Schnitt kann sauber klingen und trotzdem komisch aussehen (Blick weg, Hand im Bild).

## Korrekturen

Der Nutzer sagt Dinge wie "Bei 0:42 ist der Schnitt zu hart" oder "Der Satz bei 1:10 fehlt". Die Zeiten beziehen sich auf `fertig.mp4`.

- In `schnittliste.md` steht für jeden Clip die Startzeit im fertigen Video. Damit findest du die Stelle.
- **Zu hart / zu knapp:** an dieser Stelle in `keep.json` die Segmente zusammenfassen oder `cuts.py` mit größerem `--pad` laufen lassen.
- **Satz fehlt:** passenden Wortbereich aus `transkript.txt` an der richtigen Stelle in `keep.json` einfügen.
- **Etwas soll raus:** Segment kürzen oder teilen.

Danach Schritt 4 und 5 erneut. Nicht neu transkribieren.
