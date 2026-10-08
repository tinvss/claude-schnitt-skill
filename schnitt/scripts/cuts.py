#!/usr/bin/env python3
"""Baut aus keep.json die Schnittliste.

- Jedes Segment aus keep.json (Wortbereich, inklusive) wird zu einem oder mehreren Clips.
- Lücken zwischen zwei Wörtern über --max-pause werden herausgeschnitten.
- Vor dem ersten und nach dem letzten Wort eines Clips bleibt --pad Sekunden Luft,
  ohne in das Nachbarwort hineinzuragen.

Ausgabe: cuts.json (für render.py) und schnittliste.md

Benutzung:
  python3 cuts.py schnitt-arbeit [--max-pause 0.5] [--pad 0.12]
"""
import argparse
import json
from pathlib import Path


def mmss(sec):
    m, s = divmod(sec, 60)
    return f"{int(m):02d}:{s:04.1f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workdir")
    ap.add_argument("--max-pause", type=float, default=0.5)
    ap.add_argument("--pad", type=float, default=0.12)
    a = ap.parse_args()

    wd = Path(a.workdir)
    words = json.loads((wd / "words.json").read_text())
    sources = json.loads((wd / "sources.json").read_text())
    keep = json.loads((wd / "keep.json").read_text())["segments"]

    clips = []
    pauses = 0
    for seg_no, seg in enumerate(keep, 1):
        lo, hi = int(seg["from"]), int(seg["to"])
        if not (0 <= lo <= hi < len(words)):
            raise SystemExit(f"Segment {seg_no}: Wortbereich {lo}-{hi} ungültig")
        ws = words[lo:hi + 1]
        if len({w["src"] for w in ws}) > 1:
            raise SystemExit(f"Segment {seg_no}: Wortbereich {lo}-{hi} geht über zwei Dateien, bitte teilen")
        # an langen Pausen in Gruppen teilen
        groups = [[ws[0]]]
        for prev, cur in zip(ws, ws[1:]):
            if cur["s"] - prev["e"] > a.max_pause:
                groups.append([cur])
                pauses += 1
            else:
                groups[-1].append(cur)
        for g in groups:
            i0, i1 = g[0]["i"], g[-1]["i"]
            before = words[i0 - 1]["e"] if i0 > 0 and words[i0 - 1]["src"] == g[0]["src"] else 0.0
            after = words[i1 + 1]["s"] if i1 + 1 < len(words) and words[i1 + 1]["src"] == g[0]["src"] else None
            start = max(g[0]["s"] - a.pad, (before + g[0]["s"]) / 2, 0.0)
            end = g[-1]["e"] + a.pad
            if after is not None:
                end = min(end, (g[-1]["e"] + after) / 2)
            clips.append({"src": g[0]["src"], "in": round(start, 3), "out": round(end, 3),
                          "seg": seg_no, "text": " ".join(w["w"] for w in g), "note": seg.get("note", "")})

    # Material, das nicht im Video landet (für die Übersicht)
    used = set()
    for seg in keep:
        used.update(range(int(seg["from"]), int(seg["to"]) + 1))
    dropped, run = [], []
    for w in words:
        if w["i"] in used:
            if run:
                dropped.append(run)
                run = []
        else:
            run.append(w)
    if run:
        dropped.append(run)

    (wd / "cuts.json").write_text(json.dumps({"sources": sources, "clips": clips}, ensure_ascii=False, indent=1))

    t = 0.0
    raw_total = sum(max(w["e"] for w in words if w["src"] == s) for s in range(len(sources))) if words else 0
    rows = []
    for n, c in enumerate(clips, 1):
        rows.append(f"| {n} | {mmss(t)} | {Path(sources[c['src']]).name} {mmss(c['in'])}-{mmss(c['out'])} | {c['text']} | {c['note']} |")
        t += c["out"] - c["in"]
    md = [
        "# Schnittliste", "",
        f"Rohmaterial (gesprochen): ca. {mmss(raw_total)} · Fertiges Video: ca. {mmss(t)} · {len(clips)} Clips · {pauses} Pausen über {a.max_pause} s gekürzt",
        "", "Zeit = Startzeit im fertigen Video.", "",
        "| # | Zeit | Quelle | Text | Notiz |", "|---|---|---|---|---|", *rows, "",
        "## Rausgeschnitten", "",
    ]
    for d in dropped:
        md.append(f"- {Path(sources[d[0]['src']]).name} {mmss(d[0]['s'])}: {' '.join(w['w'] for w in d)}")
    (wd / "schnittliste.md").write_text("\n".join(md) + "\n")
    print(f"{len(clips)} Clips, fertig ca. {mmss(t)}, {pauses} Pausen gekürzt, {len(dropped)} Stellen rausgeschnitten")


if __name__ == "__main__":
    main()
