# bhckpt — a model checkpoint as a `.bh` envelope

> Minimal **usable** prototype of the Hierarchical Bits thesis in a third
> domain: ML model weights. *The same envelope as [`bhmem`](../bhmem/) and
> [`bhtrace`](../bhtrace/), a different domain.*

A checkpoint **is** a hierarchy: `model → layers → tensors`, and for MoE
`layer → experts → tensors`. The heavy residual is the raw weight bytes; the
structure (which tensor, which shape, which layer, which expert) is tiny.

`bhckpt` writes **one envelope** where the **structure** is the index — read
instantly — and the weight blocks are read only on demand:

```python
from bhckpt import Tensor, CheckpointStore, CheckpointReader

store = CheckpointStore({"dim": 256, "moe_layers": [2, 3], "n_experts": 6})
store.add(Tensor("model.embed_tokens.weight", [3000, 256], "fp16", data, codec="fp16"))
store.save("model.bckpt")

ck = CheckpointReader("model.bckpt")
ck.summary()          # architecture + tensor list (names/shapes/sizes) — no weights
ck.tensor("lm_head.weight")   # one tensor                              — its block
ck.layer(0)           # every tensor of one layer                       — those blocks
ck.expert(2, 0)       # ONE MoE expert of layer 2 (a sub-branch)        — those blocks
ck.full()             # all weights                                      — the baseline
```

Each reading returns `(result, stats)` with the **bytes actually read** (real
seeks) — gain measured, not claimed.

## The value: structure without the weights

Realistic demo (a small transformer, 2 dense + 2 MoE layers, 57 tensors, 16.2 MB):

| reading | % of file read | vs flat (reads all) |
|---|---|---|
| `summary()` — architecture, no weights | 0.06% | **1,779× less** |
| `expert(2, 0)` — one MoE expert | 4.91% | **20× less** |
| `layer(0)` — one dense layer | 8.15% | **12× less** |
| `tensor('embed_tokens')` — one tensor | 9.54% | **10× less** |
| `full()` | 100% | 1× (baseline) |

> **MoE routing:** loading **one** expert of layer 2 reads 0.80 MB vs **4.72 MB**
> for the whole layer — **~6× less** to activate a single expert. On a real
> multi-GB MoE, that is the difference between loading one expert and the whole
> mixture.

Inspect the architecture of a multi-GB checkpoint **instantly** (read the index,
not the weights); load **one expert** without the rest.

## The `.bckpt` format

```
MAGIC(4)
header_len(4) + header_json   {arch{...}, n_tensors, total_bytes}
table_len(4)  + table_json     [{name, shape, dtype, codec, nbytes, off, size}, ...]
weight_block_0 ... block_n     raw tensor bytes (the residual)
```

Position encodes the hierarchy via the dotted tensor names. The header + table
are the structure index; weight blocks are read by seek only for the tensors a
query asks for.

## Honest boundary (the same as the study)

Selective per-tensor read **already exists** — `safetensors` does
header + offsets + mmap. **That is the anchor (credibility, not novelty).** The
new piece is the **union**:

- **Hierarchy as a first-class read** — `layer(i)` and especially `expert(i, e)`
  (load one MoE expert without the mixture) are the natural units for partial
  loading and MoE serving.
- **Per-tensor codec routing** recorded in the index — each tensor can be
  delegated to its own best quantization/compression specialist (the dense
  residual). bhckpt records the routing; it does not re-implement quantization.
- **A Merkle face** over the blocks for verifiable provenance (a checkpoint you
  can prove wasn't tampered with) — same hierarchy, another reading.

## Run

```
X:/miniconda3/python.exe X:/bitH/bhckpt/demo.py        # measured demo → RESULTS_BHCKPT_DEMO.md
X:/miniconda3/python.exe -m pytest X:/bitH/bhckpt/tests/ -q   # correctness as a gate (8/8)
```

## Status

A minimal, usable prototype — not a product. It does the full loop (build a
checkpoint → save → read by structure → measure) with tested correctness. The
shape is deliberately identical to `bhmem` and `bhtrace`: one envelope, now a
third domain.
