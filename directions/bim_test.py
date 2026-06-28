"""Test of z.ai's untested direction 11.3 — BIM / Digital Twins targeted read.

CLAIM (z.ai): if a BIM model is a BH envelope, a thermal analysis reads only the
thermal layer + geometry; the cost layer stays untransmitted. Big savings in
bytes read vs loading the full model.

FALSIFIABLE TEST (z.ai's own): bytes read for a targeted property query vs loading
the full model. (RAM peak is OS-noisy; we measure bytes read with REAL seeks.)

DECLARE: success = targeted query reads << full. honest caveat = this is partial
loading, which IFC/glTF/BIM viewers already do (ANCHOR), and it is NOT the FCIR
angle the sweep flagged for CAD/BIM (rival discipline overlays).

Deterministic, synthetic, seeded, real file + real seeks.
Run: X:/miniconda3/python.exe directions/bim_test.py
"""
from __future__ import annotations

import json
import os
import struct
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent
RNG = np.random.default_rng(0)
MAGIC = b"BIM1"
_U32 = struct.Struct("<I")

N_ELEMENTS = 4000
# per-element layers and their realistic byte weights (geometry dominates)
LAYER_BYTES = {"geometry": 2048, "thermal": 120, "cost": 80, "structural": 150}


def write_model(path):
    """Envelope: MAGIC + header + table[{id, {layer:(off,size)}}] + blocks."""
    table, blocks, off = [], [], 0
    for i in range(N_ELEMENTS):
        entry = {"id": f"e{i:05d}", "layers": {}}
        for layer, nb in LAYER_BYTES.items():
            data = RNG.integers(0, 256, nb, dtype=np.uint8).tobytes()
            entry["layers"][layer] = [off, len(data)]
            blocks.append(data)
            off += len(data)
        table.append(entry)
    header = json.dumps({"n": N_ELEMENTS, "layers": list(LAYER_BYTES)}).encode()
    tbytes = json.dumps(table).encode()
    with open(path, "wb") as f:
        f.write(MAGIC)
        f.write(_U32.pack(len(header))); f.write(header)
        f.write(_U32.pack(len(tbytes))); f.write(tbytes)
        for b in blocks:
            f.write(b)
    return table, 4 + 4 + len(header) + 4 + len(tbytes)


def read_query(path, table, index_bytes, wanted_layers):
    """Read only the wanted layers, with real seeks. Returns bytes actually read."""
    blocks_start = index_bytes
    read = index_bytes
    with open(path, "rb") as f:
        for entry in table:
            for layer in wanted_layers:
                off, size = entry["layers"][layer]
                f.seek(blocks_start + off)
                f.read(size)
                read += size
    return read


def main():
    path = OUT / "bim_model.bh"
    table, index_bytes = write_model(path)
    full = os.path.getsize(path)

    queries = {
        "thermal analysis (thermal+geometry)": ["thermal", "geometry"],
        "cost report (cost only)": ["cost"],
        "structural check (structural+geometry)": ["structural", "geometry"],
        "metadata only (no geometry: thermal+cost+structural)": ["thermal", "cost", "structural"],
    }

    L = ["# 11.3 BIM / Digital Twins — targeted property read (measured)\n"]
    L.append(f"- {N_ELEMENTS} elements · layers {LAYER_BYTES} · full model {full:,} B\n")
    L.append("| query | bytes read | % of full | vs full-load |")
    L.append("|---|---|---|---|")
    print("11.3 BIM:")
    for name, layers in queries.items():
        b = read_query(path, table, index_bytes, layers)
        L.append(f"| {name} | {b:,} | {100*b/full:.1f}% | **{full/b:.1f}× less** |")
        print(f"  {name:52s} {b:>9,} B  {100*b/full:5.1f}%  {full/b:.1f}x")
    L.append(f"| full load (baseline) | {full:,} | 100.0% | 1× |")
    L.append("")
    L.append("## Verdict (honest)\n")
    L.append("- **Claim holds, mechanically:** a targeted query reads far less than the full "
             "model — geometry dominates, so any query that skips it (cost report) is tiny, and "
             "even thermal/structural skip the other layers.")
    L.append("- **But this is partial loading — already SOTA.** IFC sub-model extraction, glTF "
             "`EXT_*` + 3D Tiles streaming, and BIM viewers already load only the needed "
             "elements/properties. The number is *vs naive full-load*, not vs those tools.")
    L.append("- **And it tests the wrong angle.** The applicability sweep flagged CAD/BIM as the "
             "one BUILD — but for the **rival discipline overlays** (arch/structural/MEP "
             "disagreeing on one element), i.e. the FCIR property. This test measures selective "
             "read (ANCHOR), not that. z.ai's framing measures the part that already exists.")
    (OUT / "RESULTS_11_3_BIM.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
