# Schnitt: Claude schneidet dein Video

Ein Skill für Claude Code. Du gibst Claude dein Rohmaterial und dein Skript, Claude macht daraus ein fertiges Video:

- Pausen raus
- Versprecher und abgebrochene Sätze raus
- Bei doppelten Takes der letzte
- Reihenfolge wie im Skript
- Export als MP4, z. B. Hochformat 1080x1920

Claude arbeitet dabei über das Transkript (Whisper) und schneidet mit ffmpeg. Keine Timeline, kein Schnittprogramm.

## Einrichten

Öffne Claude Code (Desktop-App, Bereich **Code**, oder `claude` im Terminal) und schreib:

> Richte diesen Skill für mich ein: https://github.com/tinvss/claude-schnitt-skill

Claude kopiert dann den Ordner `schnitt/` nach `~/.claude/skills/schnitt/`.

Von Hand geht es so:

```bash
git clone https://github.com/tinvss/claude-schnitt-skill.git
mkdir -p ~/.claude/skills
cp -r claude-schnitt-skill/schnitt ~/.claude/skills/
```

ffmpeg und faster-whisper installiert Claude beim ersten Schnitt selbst, wenn sie fehlen.

## Benutzen

Leg einen Ordner pro Video an, pack Rohmaterial und Skript rein, öffne ihn in Claude Code und schreib zum Beispiel:

> In diesem Ordner liegt das Rohmaterial für ein Video und mein Skript.
> Schneid daraus ein fertiges Video:
> Alle Pausen raus, die länger als eine halbe Sekunde sind.
> Alle Versprecher und abgebrochenen Sätze raus. Wenn ich einen Satz mehrmals sage, nimm den letzten Take.
> Die Reihenfolge wie im Skript.
> Hochformat, 1080 mal 1920.
> Speicher das Ergebnis als fertig.mp4 im selben Ordner und sag mir, was du rausgeschnitten hast.

Danach einmal komplett anschauen. Korrekturen gibst du in normaler Sprache: „Bei 0:42 ist der Schnitt zu hart“, „Der Satz bei 1:10 fehlt“.

## Was drin ist

| Datei | Zweck |
|---|---|
| `schnitt/SKILL.md` | Anleitung für Claude: Ablauf und Schnittregeln |
| `schnitt/scripts/transcribe.py` | Transkript mit Wort-Zeitstempeln (faster-whisper) |
| `schnitt/scripts/cuts.py` | Schnittliste aus den gewählten Takes, kürzt Pausen |
| `schnitt/scripts/render.py` | Rendert das fertige Video mit ffmpeg |

Voraussetzung: Claude Pro oder Max (Claude Code), Mac oder Windows, Python 3.

Von [Tinus Klauser](https://www.instagram.com/tinus.klauser/).
