"""bhmem demo — an agent's memory as a .bh envelope, measured.

Populates a realistic memory (many topics over time), writes it as .bh, and
shows that each reading reads only the fraction it needs — against the honest
baseline (a flat store that loads everything for any query).

Run:  X:/miniconda3/python.exe X:/bitH/bhmem/demo.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from bhmem import Memory, MemoryReader, MemoryStore  # noqa: E402

OUT = Path(__file__).resolve().parent

# --- deterministic time (no Date.now — reproducible) ---
T0 = 1_700_000_000.0
HOUR = 3600.0
DAY = 24 * HOUR


def build() -> MemoryStore:
    """Plausible memory of an agent that has been running for ~90 days.

    Realistic on purpose: dozens of topics (the agent worked on many things),
    each TEMPORALLY LOCALIZED in a window of a few days (you focus on a topic,
    then move on) — only a few stay "active" up to today. It is this structure
    (many branches + skewed access) that makes selective reading pay off,
    exactly as the study's law predicts.
    """
    store = MemoryStore()
    kinds = ["fact", "event", "relation", "observation"]
    areas = ["project", "bug", "infra", "person", "meeting", "billing",
             "deploy", "review", "incident", "spec", "tooling", "decision"]
    n = 0
    n_topics = 60
    for ti in range(n_topics):
        area = areas[ti % len(areas)]
        topic = f"{area}_{ti:02d}"
        # topic window: starts on some day, lasts 2–6 days
        start_day = (ti * 37) % 86  # deterministic spread over ~86 days
        span_days = 2 + (ti % 5)
        # a few topics stay active up to "today" (day 90)
        ongoing = ti % 17 == 0
        # varied density: large and small topics
        reps = 8 + (ti * 13) % 60  # 8..67 memories
        for k in range(reps):
            frac = k / max(reps - 1, 1)
            day = (start_day + frac * span_days) if not ongoing else (start_day + frac * (90 - start_day))
            ts = T0 + day * DAY
            kind = kinds[(ti + k) % len(kinds)]
            store.add(Memory(
                id=f"m{n:05d}",
                ts=ts,
                kind=kind,
                topic=topic,
                text=f"[{topic}] {kind}: note {k+1} about {area} "
                     f"— context the agent accumulated on this branch.",
                source=f"turn#{n} · tool:{'read' if k % 2 else 'bash'}",
                meta={"rep": k, "ongoing": ongoing},
            ))
            n += 1
    return store


def flat_baseline_query(path: Path) -> int:
    """Honest baseline: a flat store (JSONL) reads the WHOLE file for any
    query, because it has no structure to navigate — no selective seek."""
    return path.stat().st_size


def main() -> None:
    store = build()
    bh_path = OUT / "agent_memory.bh"
    store.save(bh_path)

    # equivalent flat baseline (same memories, raw JSONL)
    flat_path = OUT / "agent_memory.jsonl"
    with open(flat_path, "w", encoding="utf-8") as f:
        for m in store._mem:  # noqa: SLF001 (demo)
            f.write(json.dumps(m.__dict__, ensure_ascii=False) + "\n")

    reader = MemoryReader(bh_path)
    flat_size = flat_baseline_query(flat_path)
    bh_size = reader.file_size

    L: list[str] = []
    p = L.append
    p("# bhmem — agent memory as .bh (measured demo)\n")
    p(f"- memories: **{len(store)}** · topics: **{len(reader.table)}**")
    p(f"- `.bh` file: **{bh_size:,} bytes** · flat JSONL: **{flat_size:,} bytes**\n")
    p("## Each reading reads only what it needs (REAL bytes read from the file)\n")
    p("The flat baseline reads the **whole** file for any query "
      f"({flat_size:,} B). The `.bh` reads only the requested branch.\n")
    p("| reading | what it returns | bytes read | % of file | vs flat |")
    p("|---|---|---|---|---|")

    def row(label: str, what: str, stats, n: int) -> None:
        ratio = flat_size / stats.bytes_read if stats.bytes_read else float("inf")
        p(f"| `{label}` | {what} ({n}) | {stats.bytes_read:,} B | "
          f"{stats.fraction*100:.1f}% | **{ratio:.0f}× less** |")

    target_topic = reader.table[7]["topic"]  # some middle topic
    sample_id = "m00000"

    sm, st = reader.summary()
    row("summary()", "digest of all topics", st, len(sm))

    rc, st = reader.recall(target_topic)
    row(f"recall('{target_topic}')", "the topic's memories", st, len(rc))

    recent_t = T0 + 85 * DAY  # last ~5 of 90 days
    sc, st = reader.since(recent_t)
    row("since(last 5d)", "recent memories", st, len(sc))

    pv, st = reader.provenance(sample_id)
    row(f"provenance('{sample_id}')", "source+path of 1 memory", st, 1 if pv else 0)

    fl, st = reader.full()
    row("full()", "everything (baseline)", st, len(fl))

    p("\n## What this demonstrates\n")
    p("- **Not another compression number.** It's the CAPABILITY: the agent reads "
      "the summary, a topic, a window or the provenance **without loading the whole "
      "memory**. The cost of each reading is proportional to what it asks for.")
    p("- **Structure is part of the format.** Belonging (topic), time and "
      "provenance are navigable in the file itself — not across four systems "
      "bolted on top.")
    p("- **Honest boundary.** *Dense semantic* recall (vector) is not done here — "
      "it delegates to an HNSW index that the envelope references. The `.bh` calls "
      "the specialist; it does not compete with it.")

    out = OUT / "RESULTS_BHMEM_DEMO.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")

    # console (ascii-safe)
    print(f"memories={len(store)} topics={len(reader.table)} "
          f"bh={bh_size}B jsonl={flat_size}B")
    for label, fn in [
        ("summary", lambda: reader.summary()),
        (f"recall({target_topic})", lambda: reader.recall(target_topic)),
        ("since(last5d)", lambda: reader.since(recent_t)),
        (f"provenance({sample_id})", lambda: reader.provenance(sample_id)),
        ("full", lambda: reader.full()),
    ]:
        _, s = fn()
        ratio = flat_size / s.bytes_read if s.bytes_read else 0
        print(f"  {label:18s} {s.bytes_read:7d} B  {s.fraction*100:5.1f}%  {ratio:5.0f}x less")
    print(f"report: {out}")


if __name__ == "__main__":
    main()
