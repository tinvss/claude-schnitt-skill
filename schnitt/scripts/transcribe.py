#!/usr/bin/env python3
"""Transkribiert ein oder mehrere Videos mit Wort-Zeitstempeln.

Ausgabe im Ordner --out:
  words.json      [{"i": 0, "src": 0, "w": "Hallo", "s": 1.23, "e": 1.51}, ...]
  sources.json    ["/pfad/video1.mov", ...]
  transkript.txt  eine Zeile pro Phrase: [von-bis] Datei MM:SS.s  Text

Benutzung:
  python3 transcribe.py video1.mov [video2.mov ...] --lang de --out schnitt-arbeit [--model small]
"""
import argparse
import json
import shutil
import subprocess
from pathlib import Path


def mmss(sec):
    m, s = divmod(sec, 60)
    return f"{int(m):02d}:{s:04.1f}"


def load_audio(path):
    """Tonspur als 16-kHz-Mono-Float über ffmpeg (unabhängig von PyAV-Versionen)."""
    raw = subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-i", path, "-vn",
                          "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    import numpy as np
    return np.frombuffer(raw, dtype=np.float32).copy()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("videos", nargs="+")
    ap.add_argument("--lang", default="de")
    ap.add_argument("--model", default="small")
    ap.add_argument("--out", default="schnitt-arbeit")
    a = ap.parse_args()

    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg nicht gefunden. Erst installieren (siehe SKILL.md, Schritt 0).")
    from faster_whisper import WhisperModel

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    model = WhisperModel(a.model, device="auto", compute_type="int8")

    sources = [str(Path(v).resolve()) for v in a.videos]
    words, lines = [], []
    for src_i, path in enumerate(sources):
        print(f"Transkribiere {Path(path).name} ...", flush=True)
        segments, _ = model.transcribe(
            load_audio(path),
            language=a.lang,
            word_timestamps=True,
            vad_filter=False,  # Versprecher und Neuansätze sollen im Transkript bleiben
            condition_on_previous_text=False,  # verhindert, dass Whisper Wiederholungen "glättet"
        )
        for seg in segments:
            first = len(words)
            for w in seg.words or []:
                text = w.word.strip()
                if not text:
                    continue
                words.append({"i": len(words), "src": src_i, "w": text,
                              "s": round(w.start, 3), "e": round(w.end, 3)})
            if len(words) > first:
                seg_words = words[first:]
                lines.append(f"[{first}-{len(words) - 1}] {Path(path).name} {mmss(seg_words[0]['s'])}  "
                             + " ".join(x["w"] for x in seg_words))

    (out / "words.json").write_text(json.dumps(words, ensure_ascii=False, indent=0))
    (out / "sources.json").write_text(json.dumps(sources, ensure_ascii=False, indent=2))
    (out / "transkript.txt").write_text("\n".join(lines) + "\n")
    print(f"{len(words)} Wörter, {len(lines)} Phrasen -> {out}/transkript.txt")


if __name__ == "__main__":
    main()
