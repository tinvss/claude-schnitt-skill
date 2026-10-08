#!/usr/bin/env python3
"""Rendert cuts.json mit ffmpeg zu einem fertigen Video.

Jeder Clip wird einzeln bildgenau ausgeschnitten (mit kurzer Audio-Blende gegen Knackser),
danach werden alle Clips verlustfrei aneinandergehängt.

Benutzung:
  python3 render.py schnitt-arbeit [--format 9:16|16:9|original] [--fps 30] [--out fertig.mp4]
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

FORMATS = {
    "9:16": "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1",
    "16:9": "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1",
    "original": "setsar=1",
}
FADE = 0.015


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-3000:])
        raise SystemExit(f"ffmpeg ist fehlgeschlagen: {' '.join(cmd[:6])} ...")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workdir")
    ap.add_argument("--format", default="9:16", choices=FORMATS)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--out", default="fertig.mp4")
    ap.add_argument("--crf", type=int, default=18)
    a = ap.parse_args()

    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg nicht gefunden. Erst installieren (siehe SKILL.md, Schritt 0).")

    wd = Path(a.workdir)
    cfg = json.loads((wd / "cuts.json").read_text())
    sources, clips = cfg["sources"], cfg["clips"]
    tmp = wd / "clips"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir()

    vf = f"{FORMATS[a.format]},fps={a.fps},format=yuv420p"
    listing = []
    for n, c in enumerate(clips, 1):
        dur = c["out"] - c["in"]
        if dur <= 0.05:
            continue
        af = f"afade=t=in:d={FADE},afade=t=out:st={max(dur - FADE, 0):.3f}:d={FADE},aresample=48000"
        part = tmp / f"{n:04d}.mp4"
        run(["ffmpeg", "-y", "-loglevel", "error",
             "-ss", f"{c['in']:.3f}", "-i", sources[c["src"]], "-t", f"{dur:.3f}",
             "-vf", vf, "-af", af,
             "-c:v", "libx264", "-preset", "medium", "-crf", str(a.crf),
             "-c:a", "aac", "-b:a", "192k", "-ac", "2",
             str(part)])
        listing.append(f"file '{part.resolve().as_posix()}'")
        print(f"\rClip {n}/{len(clips)}", end="", flush=True)
    print()

    lst = tmp / "liste.txt"
    lst.write_text("\n".join(listing) + "\n")
    out = Path(a.out).resolve()
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-c", "copy", "-movflags", "+faststart", str(out)])
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"Fertig: {out}")


if __name__ == "__main__":
    main()
