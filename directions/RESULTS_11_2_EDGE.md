# 11.2 Edge progressive transmission — measured

- 64 nodes × 300 windows · residual 1024 B/node-window · 774 true anomalies (4%)

| strategy | bytes sent | % of full | anomaly recall | vs full |
|---|---|---|---|---|
| (a) full transmission | 19,660,800 | 100.0% | 1.00 | 1× |
| (b) fixed-threshold filter (SOTA) | 792,576 | 4.0% | 1.00 | 25× |
| (c) BH-stream (summary + flagged) | 1,488,896 | 7.6% | 1.00 | 13× |

## Verdict (honest)

- **vs full transmission (naive):** BH-stream sends 13× fewer bytes. **Claim holds vs naive.**
- **vs the fixed-threshold filter (the real SOTA):** BH-stream is 1.88× the filter's bytes (MORE; recall 1.00 vs 1.00). The summary stream itself costs bytes every window, and a simple local filter already sends only the anomalous residuals.
- **Honest reading:** the win is *vs naive full transmission* — which is real, but is the already-known adaptive-telemetry / conditional-reporting result. BH adds a summary **round-trip** (latency) that the local filter avoids. This is an ANCHOR mechanism, not a novel BH win. (FCIR — rival interpretations — does not appear here at all.)
