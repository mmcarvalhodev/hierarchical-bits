"""Test of z.ai's untested direction 11.2 — progressive transmission at the edge.

CLAIM (z.ai): a sensor that packages data as a BH stream lets the cloud read the
summary, then request only the residual of the node that changed — sending far
fewer bytes than full transmission, at high anomaly recall.

FALSIFIABLE TEST (z.ai's own): bytes transmitted vs anomaly-detection recall, for
  (a) full transmission, (b) fixed-threshold local filter (the real SOTA),
  (c) BH-stream (summary -> request residual of flagged nodes).

DECLARE BEFORE MEASURING:
  - success for BH: << full bytes AND recall >= fixed-threshold recall.
  - honest failure: if BH ~= fixed-threshold filter on bytes, then the gain is
    "vs naive (full)", not "vs SOTA" — the adaptive filter already gets it.

Deterministic, synthetic, seeded. Run: X:/miniconda3/python.exe directions/edge_test.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent
RNG = np.random.default_rng(0)

N_NODES = 64          # e.g. 64 sensors / leaf nodes
WINDOWS = 300         # time windows
SAMPLES = 256         # samples per node per window
BYTES_PER_SAMPLE = 4  # float32
RESIDUAL_BYTES = SAMPLES * BYTES_PER_SAMPLE   # raw block per node-window
SUMMARY_BYTES = 16    # per node: min/max/energy/ts packed
ANOMALY_RATE = 0.04   # fraction of node-windows that are genuinely anomalous


def build():
    """Per node-window: an energy value + whether it is a true anomaly."""
    base = RNG.normal(1.0, 0.05, (WINDOWS, N_NODES))          # normal drift
    is_anom = RNG.random((WINDOWS, N_NODES)) < ANOMALY_RATE
    energy = base + is_anom * RNG.uniform(0.6, 2.0, (WINDOWS, N_NODES))  # spikes
    return energy, is_anom


def main():
    energy, is_anom = build()
    total_true = int(is_anom.sum())

    # (a) full transmission — every residual, every window
    full_bytes = WINDOWS * N_NODES * RESIDUAL_BYTES
    full_recall = 1.0

    # (b) fixed-threshold local filter (SOTA): sensor sends residual if local
    #     energy exceeds a fixed threshold. No summary round-trip.
    thr = 1.30
    sent_fixed = energy > thr
    fixed_bytes = int(sent_fixed.sum()) * RESIDUAL_BYTES
    fixed_recall = (sent_fixed & is_anom).sum() / total_true

    # (c) BH-stream: every window send the summary of all nodes; the cloud flags
    #     nodes whose energy deviates from a running per-node baseline, and
    #     requests only those residuals.
    flagged = np.zeros_like(is_anom)
    baseline = energy[0].copy()
    for w in range(WINDOWS):
        dev = np.abs(energy[w] - baseline)
        flag = dev > 0.25                       # adaptive deviation flag
        flagged[w] = flag
        baseline = 0.9 * baseline + 0.1 * energy[w]   # EWMA baseline update
    bh_summary_bytes = WINDOWS * N_NODES * SUMMARY_BYTES
    bh_residual_bytes = int(flagged.sum()) * RESIDUAL_BYTES
    bh_bytes = bh_summary_bytes + bh_residual_bytes
    bh_recall = (flagged & is_anom).sum() / total_true

    def pct(b):
        return 100 * b / full_bytes

    L = ["# 11.2 Edge progressive transmission — measured\n"]
    L.append(f"- {N_NODES} nodes × {WINDOWS} windows · residual {RESIDUAL_BYTES} B/node-window · "
             f"{total_true} true anomalies ({ANOMALY_RATE*100:.0f}%)\n")
    L.append("| strategy | bytes sent | % of full | anomaly recall | vs full |")
    L.append("|---|---|---|---|---|")
    L.append(f"| (a) full transmission | {full_bytes:,} | 100.0% | {full_recall:.2f} | 1× |")
    L.append(f"| (b) fixed-threshold filter (SOTA) | {fixed_bytes:,} | {pct(fixed_bytes):.1f}% | "
             f"{fixed_recall:.2f} | {full_bytes/max(fixed_bytes,1):.0f}× |")
    L.append(f"| (c) BH-stream (summary + flagged) | {bh_bytes:,} | {pct(bh_bytes):.1f}% | "
             f"{bh_recall:.2f} | {full_bytes/max(bh_bytes,1):.0f}× |")
    L.append("")
    # honest verdict
    bh_vs_fixed = bh_bytes / max(fixed_bytes, 1)
    L.append("## Verdict (honest)\n")
    L.append(f"- **vs full transmission (naive):** BH-stream sends "
             f"{full_bytes/max(bh_bytes,1):.0f}× fewer bytes. **Claim holds vs naive.**")
    L.append(f"- **vs the fixed-threshold filter (the real SOTA):** BH-stream is "
             f"{bh_vs_fixed:.2f}× the filter's bytes "
             f"({'MORE' if bh_vs_fixed > 1 else 'fewer'}; recall {bh_recall:.2f} vs {fixed_recall:.2f}). "
             "The summary stream itself costs bytes every window, and a simple local "
             "filter already sends only the anomalous residuals.")
    L.append("- **Honest reading:** the win is *vs naive full transmission* — which is real, but "
             "is the already-known adaptive-telemetry / conditional-reporting result. BH adds a "
             "summary **round-trip** (latency) that the local filter avoids. This is an ANCHOR "
             "mechanism, not a novel BH win. (FCIR — rival interpretations — does not appear here at all.)")
    (OUT / "RESULTS_11_2_EDGE.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    print("11.2 EDGE:")
    print(f"  full   : {full_bytes:>12,} B  recall {full_recall:.2f}")
    print(f"  fixed  : {fixed_bytes:>12,} B  recall {fixed_recall:.2f}  ({full_bytes/max(fixed_bytes,1):.0f}x vs full)")
    print(f"  BH     : {bh_bytes:>12,} B  recall {bh_recall:.2f}  ({full_bytes/max(bh_bytes,1):.0f}x vs full)")
    print(f"  BH vs fixed-filter (SOTA): {bh_vs_fixed:.2f}x bytes  -> {'ANCHOR (no SOTA win)' if bh_vs_fixed>=0.8 else 'check'}")


if __name__ == "__main__":
    main()
