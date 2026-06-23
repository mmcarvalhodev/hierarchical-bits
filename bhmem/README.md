# bhmem — agent memory as a `.bh` envelope

> Minimal **usable** prototype of the Hierarchical Bits thesis, applied to a
> concrete domain: an agent's memory.

An agent's memory today is scattered across separate systems — documents,
embeddings, summaries, cache, indexes, metadata — that must be kept in sync.
`bhmem` writes **one hierarchical envelope** where *structure is part of the
format*. The agent does not load the whole memory to use a piece of it:

```python
from bhmem import Memory, MemoryStore, MemoryReader

store = MemoryStore()
store.add(Memory(id="m1", ts=1_700_000_000.0, kind="fact",
                 topic="project_auth", text="OAuth with PKCE, 15-min tokens.",
                 source="turn#42 · tool:read"))
store.save("agent_memory.bh")

mem = MemoryReader("agent_memory.bh")

mem.summary()                 # digest of ALL topics — reads only the index
mem.recall("project_auth")    # memories of ONE topic — reads only that branch
mem.since(1_700_500_000.0)    # recent memories — skips branches out of the window
mem.provenance("m1")          # source+path of 1 memory — reads only its block
mem.full()                    # everything — the baseline
```

Each reading returns `(result, stats)` where `stats` reports the **bytes it
actually read** from the file (real seeks) — so the gain is measured, not claimed.

## The value: read only what you need

Realistic demo (an agent running for ~90 days: 60 topics, 2,250 memories):

| reading | % of file read | vs flat store (reads all) |
|---|---|---|
| `summary()` | 2.5% | **35× fewer bytes** |
| `recall(topic)` | 4.0% | **22× fewer bytes** |
| `since(last 5 days)` | 9.8% | **9× fewer bytes** |
| `provenance(id)` | 10.8% | **8× fewer bytes** |
| `full()` | 100% | 1× (baseline) |

The honest baseline is a flat store (JSONL): for **any** query it loads the
whole file, because it has no structure to navigate. The `.bh` jumps to the
requested branch. The gain **scales with the number of branches** and with the
access skew — the same law as the study: selective reading pays off when there
are many branches and the index does not drown the payload.

## The `.bh` format

```
MAGIC(4)
header_len(4)  + header_json     {n_topics, n_mem}
table_len(4)   + table_json      per-topic summaries + offset/size  (structure index)
idindex_len(4) + idindex_json    {id -> topic}   (only provenance loads it)
topic_block_0 ... topic_block_n  memories per branch
```

**Position** encodes the hierarchy (there is no "hierarchy" field). The
structure index is small and always read; the blocks live at the end and are
read by seek, only when a query asks for them. The `id_index` is a separate
region so that the summary does not pay for the id map.

## Honest boundary (the same as the study)

- **Wins** on *structural* access: by topic (belonging), by time, by
  provenance. Selective reading over an explicit hierarchy.
- **Delegates** *dense semantic* recall: vector search (HNSW) is **not** done
  here. The envelope can *reference* a vector index; BH calls the specialist,
  it does not compete with it. This is the deliberate boundary — the `.bh` does
  what compact formats don't (navigate), and calls whoever does best what it
  doesn't (dense semantics).

## Run

```
X:/miniconda3/python.exe X:/bitH/bhmem/demo.py        # measured demo → RESULTS_BHMEM_DEMO.md
X:/miniconda3/python.exe -m pytest X:/bitH/bhmem/tests/ -q   # correctness as a gate (9/9)
```

## Status

A **minimal, usable** prototype — not a product. It does the full loop (write →
save → read via the multiple readings → measure) with tested correctness. Next
natural steps, if it becomes a product: incremental append (without rewriting
the file), a referenced vector index for semantic recall, multi-level topic
hierarchy, and per-block compaction (delegating to the specialist, as the
thesis dictates).
