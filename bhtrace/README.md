# bhtrace — a distributed trace as a `.bh` envelope

> Minimal **usable** prototype of the Hierarchical Bits thesis in a second
> domain: observability. *The same envelope as [`bhmem`](../bhmem/), a
> different domain* — proof the paradigm generalizes.

A distributed trace **is** a tree: `trace → spans → events`, with belonging
(service) and time. Today a trace lives in an index (Tempo/Loki/Elastic) bolted
on top; to ask "which spans are slow" you scan, and the heavy part — span
attributes, logs, stack traces — is paid for even when you only want the
skeleton.

`bhtrace` writes **one envelope** where the **structure** (the span tree +
timings) is the index — small, always read — and the heavy per-span payload
(attributes, events) lives in blocks read only on demand:

```python
from bhtrace import Span, TraceStore, TraceReader

store = TraceStore("checkout-7f3a")
store.add(Span("s1", None, "gateway", "POST /checkout", 0, 482_000, "ok",
               attributes={...}, events=[...]))
store.save("trace.bht")

tr = TraceReader("trace.bht")
tr.summary()          # per-service rollup + critical path + slowest — index only
tr.critical_path()    # the root→leaf chain that dominates latency  — index only
tr.subtree("s42")     # a span and all its descendants (one branch) — its blocks
tr.service("db")      # every span of one service                   — those blocks
tr.full()             # everything                                   — the baseline
```

Each reading returns `(result, stats)` with the **bytes actually read** from the
file (real seeks) — gain measured, not claimed.

## The value: read the skeleton without the payload

Realistic demo (a checkout request, 269 spans, OTel-style attribute-heavy spans):

| reading | % of file read | vs flat store (reads all) |
|---|---|---|
| `summary()` — per-service + critical path + slowest | 10.6% | **9× less** |
| `critical_path()` — the latency chain | 10.6% | **9× less** |
| `subtree(span)` — a typical drill-in | 11.5% | **9× less** |
| `service('db')` — one service (many spans) | 21.3% | **5× less** |
| `full()` | 100% | 1× (baseline) |

"Which spans are slow?" and "what's the critical path?" are answered from the
**structure index alone** — without loading a single attribute or stack trace.
The gain **scales with attribute weight**, and real traces are heavy (exception
stack traces, full SQL, headers, baggage) — heavier than this demo.

## The `.bht` format

```
MAGIC(4)
header_len(4) + header_json   {trace_id, n_spans, root_id, total_us}
tree_len(4)   + tree_json      the span tree + timings + payload locators (the index)
payload_block_0 ... block_n    per-span {attributes, events}  (the heavy residual)
```

Position encodes the tree. The header + tree are the structure index; the
blocks are read by seek only when a query drills into a span/service.

## Honest boundary (the same as the study)

- **Wins** on *structural* access over an attribute-heavy tree: rollups,
  critical path, subtree, by-service — proportional to the question.
- **Delegates** full-text search across attributes to an inverted index; the
  dense residual (the attribute/log text) is routed to whatever stores and
  searches text best. bhtrace makes the structure explicit and calls the
  specialist; it does not replace it.

## Run

```
X:/miniconda3/python.exe X:/bitH/bhtrace/demo.py        # measured demo → RESULTS_BHTRACE_DEMO.md
X:/miniconda3/python.exe -m pytest X:/bitH/bhtrace/tests/ -q   # correctness as a gate (9/9)
```

## Status

A minimal, usable prototype — not a product. It does the full loop (build a
trace → save → read via the structure index → measure) with tested correctness.
The shape is deliberately identical to `bhmem`: one envelope, two domains.
