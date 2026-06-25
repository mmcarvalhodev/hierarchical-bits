# bhckpt — model checkpoint as .bckpt (measured demo)

- tensors: **57** · total weights: **16.2 MB** · arch: 4 layers (MoE: [2, 3], 6 experts)

A flat checkpoint must read the whole file to reach any tensor. The `.bckpt` keeps the tensor table as the index and reads weights on demand.

| reading | what it returns | bytes read | % of file | vs flat (reads all) |
|---|---|---|---|---|
| `summary()` | architecture + tensor list, no weights (57) | 9,105 B | 0.06% | **1779× less** |
| `tensor('embed_tokens')` | one tensor (1) | 1,545,105 B | 9.54% | **10× less** |
| `layer(0)` | all tensors of a dense layer (8) | 1,320,849 B | 8.15% | **12× less** |
| `expert(2, 0)` | ONE MoE expert of layer 2 (2) | 795,537 B | 4.91% | **20× less** |
| `full()` | all weights (baseline) (57) | 16,199,057 B | 100.00% | **1× less** |

**MoE routing:** loading **one** expert of layer 2 reads 0.80 MB vs **5.26 MB** for the whole layer — **6.6× less** to activate a single expert.

## What this demonstrates

- **Architecture without weights.** `summary()` returns the full tensor map (names, shapes, codecs) reading only the index — inspect a multi-GB checkpoint instantly, without loading a single weight.
- **The MoE expert is a first-class hierarchical read.** `expert(i, e)` loads one expert's tensors and nothing else — the natural unit for MoE serving and partial loading.
- **Honest boundary.** Selective per-tensor read already exists (`safetensors` header+mmap) — that is the anchor, not the novelty. The new piece is the union: hierarchy (layer/expert) + per-tensor codec routing recorded in the index + a Merkle face for provenance.
