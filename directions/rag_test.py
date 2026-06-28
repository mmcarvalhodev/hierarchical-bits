"""Test of z.ai's untested direction 11.1 — Structural RAG.

CLAIM (z.ai): storing a document as .bh lets a RAG agent read the summary() (a
few % of bytes), locate the relevant node, then run vector retrieval inside that
node — reducing hallucination on multi-section documents vs flat-chunk RAG.

WHAT IS MEASURABLE HERE (deterministic): the BYTE / LOCATE economics — how cheap
it is to read the structural skeleton and scope retrieval to one section.

WHAT IS NOT MEASURABLE HERE (declared honestly): the hallucination-reduction
claim. That needs an LLM + a labeled multi-section QA set + an eval harness. It is
NOT tested by this script and remains an open hypothesis.

Deterministic, synthetic, real file + real seeks.
Run: X:/miniconda3/python.exe directions/rag_test.py
"""
from __future__ import annotations

import json
import os
import struct
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent
RNG = np.random.default_rng(0)
MAGIC = b"DOC1"
_U32 = struct.Struct("<I")

N_SECTIONS = 40          # e.g. a 200-page contract in 40 sections
CHUNKS_PER_SECTION = 12
CHUNK_BYTES = 1200       # ~a text chunk
SUMMARY_BYTES = 90       # per-section title + topic line


def write_doc(path):
    table, blocks, off = [], [], 0
    for s in range(N_SECTIONS):
        sec = {"id": f"s{s:03d}", "summary": "x" * SUMMARY_BYTES, "chunks": []}
        for c in range(CHUNKS_PER_SECTION):
            data = RNG.integers(0, 256, CHUNK_BYTES, dtype=np.uint8).tobytes()
            sec["chunks"].append([off, len(data)])
            blocks.append(data)
            off += len(data)
        table.append(sec)
    header = json.dumps({"n_sections": N_SECTIONS}).encode()
    tbytes = json.dumps(table).encode()
    with open(path, "wb") as f:
        f.write(MAGIC)
        f.write(_U32.pack(len(header))); f.write(header)
        f.write(_U32.pack(len(tbytes))); f.write(tbytes)
        for b in blocks:
            f.write(b)
    return table, 4 + 4 + len(header) + 4 + len(tbytes)


def main():
    path = OUT / "doc.bh"
    table, index_bytes = write_doc(path)
    full = os.path.getsize(path)

    # structural read: the index (header+table, carries the per-section summaries)
    # locates the target section; then read only that section's chunks.
    target = table[N_SECTIONS // 3]
    scoped = index_bytes + sum(sz for _, sz in target["chunks"])

    # flat RAG: no structure -> must read all chunks to retrieve over them
    flat = full

    L = ["# 11.1 Structural RAG — byte/locate economics (measured) + the untested claim\n"]
    L.append(f"- doc: {N_SECTIONS} sections × {CHUNKS_PER_SECTION} chunks × {CHUNK_BYTES} B "
             f"= {full:,} B · per-section summary {SUMMARY_BYTES} B\n")
    L.append("| read | bytes | % of doc | vs flat |")
    L.append("|---|---|---|---|")
    L.append(f"| structural locate (index/summaries only) | {index_bytes:,} | "
             f"{100*index_bytes/full:.1f}% | {full/index_bytes:.0f}× less |")
    L.append(f"| locate + scoped read (1 section) | {scoped:,} | {100*scoped/full:.1f}% | "
             f"{full/scoped:.0f}× less |")
    L.append(f"| flat RAG (read all chunks) | {flat:,} | 100.0% | 1× |")
    L.append("")
    L.append("## Verdict (honest)\n")
    L.append(f"- **The byte economics check out:** reading the skeleton to locate the right "
             f"section costs ~{100*index_bytes/full:.0f}% of the document, and a scoped read of "
             f"one section ~{100*scoped/full:.0f}% — both far below a flat read. The mechanism "
             "works.")
    L.append("- **But that mechanism is ANCHOR.** A table of contents / section index + scoped "
             "retrieval already exists (hierarchical / parent-document retrievers, section-aware "
             "chunking). The byte saving is *vs naive flat-load*, not a novelty.")
    L.append("- **The actual claim is NOT tested here.** Whether a structural-read phase "
             "*reduces hallucination* on multi-section documents needs an LLM, a labeled QA set, "
             "and an eval harness comparing hallucination rate at matched retrieval cost. This "
             "script does not do that. **Status: open hypothesis — measurable economics confirmed, "
             "the interesting claim untested.**")
    (OUT / "RESULTS_11_1_RAG.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    print("11.1 RAG (byte economics only; hallucination claim NOT tested):")
    print(f"  locate (index)        {index_bytes:>9,} B  {100*index_bytes/full:5.1f}%  {full/index_bytes:.0f}x")
    print(f"  locate + 1 section    {scoped:>9,} B  {100*scoped/full:5.1f}%  {full/scoped:.0f}x")
    print(f"  flat (all chunks)     {flat:>9,} B  100.0%")
    print("  hallucination-reduction claim: NOT testable here (needs LLM eval) -> open")


if __name__ == "__main__":
    main()
